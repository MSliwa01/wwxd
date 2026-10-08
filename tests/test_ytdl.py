import logging
import os
import sys

import pytest
import yt_dlp

from wwxd import ytdl
from wwxd.ytdl import JsRuntime


@pytest.fixture(autouse=True)
def fresh_state(monkeypatch):
    monkeypatch.delenv("WWXD_COOKIES_FROM_BROWSER", raising=False)
    ytdl.find_js_runtimes.cache_clear()
    ytdl.use_cookies_from_browser(None)
    yield
    ytdl.find_js_runtimes.cache_clear()
    ytdl.use_cookies_from_browser(None)


def fake_runtimes(monkeypatch, found: dict[str, bool | None]) -> None:
    """found: runtime name -> supported flag, for the runtimes 'on PATH'."""
    monkeypatch.setattr(ytdl, "_which", lambda name: f"/opt/bin/{name}" if name in found else None)
    monkeypatch.setattr(ytdl, "_probe", lambda name, path: JsRuntime(name, path, "1.0", found[name]))


def test_prefers_deno_then_node_then_bun(monkeypatch):
    fake_runtimes(monkeypatch, {"bun": True, "node": True})
    assert ytdl.js_runtime() == JsRuntime("node", "/opt/bin/node", "1.0", True)
    assert ytdl.ydl_opts()["js_runtimes"] == {"node": {"path": "/opt/bin/node"}}


def test_skips_runtime_yt_dlp_rejects(monkeypatch):
    fake_runtimes(monkeypatch, {"deno": False, "bun": True})
    assert ytdl.js_runtime().name == "bun"


def test_no_runtime_leaves_yt_dlp_default(monkeypatch):
    fake_runtimes(monkeypatch, {})
    assert ytdl.js_runtime() is None
    assert "js_runtimes" not in ytdl.ydl_opts()


def test_yt_dlp_accepts_the_option(monkeypatch):
    fake_runtimes(monkeypatch, {"node": True})
    with ytdl.new_ydl(skip_download=True) as ydl:
        assert ydl.params["js_runtimes"] == {"node": {"path": "/opt/bin/node"}}
        assert ydl.params["skip_download"] is True


def test_warnings_follow_verbosity(monkeypatch):
    fake_runtimes(monkeypatch, {})
    root = logging.getLogger()
    previous = root.level
    try:
        root.setLevel(logging.WARNING)
        assert ytdl.ydl_opts()["no_warnings"] is True
        root.setLevel(logging.INFO)  # wwxd -v
        assert ytdl.ydl_opts()["no_warnings"] is False
    finally:
        root.setLevel(previous)


@pytest.mark.skipif(sys.platform == "win32", reason="shell script runtime")
@pytest.mark.parametrize(("version", "supported"), [("v22.3.0", True), ("v20.11.1", False)])
def test_probe_uses_yt_dlp_minimum_versions(tmp_path, version, supported):
    node = tmp_path / "node"
    node.write_text(f"#!/bin/sh\necho {version}\n")
    node.chmod(0o755)
    runtime = ytdl._probe("node", str(node))
    assert runtime.version == version[1:]
    assert runtime.supported is supported


class FakeYDL:
    created: list[dict] = []

    def __init__(self, params):
        self.params = params
        FakeYDL.created.append(params)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def extract_info(self, url, download=False):
        return {"id": "abc", "title": "t", "entries": [{"id": "x1", "title": "a"}]}

    def download(self, urls):
        outtmpl = self.params["outtmpl"]
        with open(outtmpl.replace("%(ext)s", "webm"), "wb") as fh:
            fh.write(b"audio")


def test_every_call_site_uses_the_factory(monkeypatch, tmp_path):
    from wwxd.discover import _flat_entries
    from wwxd.fetchers import whisper
    from wwxd.fetchers.youtube import extract_info

    fake_runtimes(monkeypatch, {"node": True})
    FakeYDL.created = []
    monkeypatch.setattr(ytdl.yt_dlp, "YoutubeDL", FakeYDL)
    _flat_entries("https://www.youtube.com/@someone/videos", 5)
    extract_info("https://www.youtube.com/watch?v=abcdefghijk")
    path = whisper.download_youtube_audio("https://www.youtube.com/watch?v=abcdefghijk", "abcdefghijk", tmp_path)
    assert os.path.basename(path) == "abcdefghijk.webm"
    assert len(FakeYDL.created) == 3
    assert all(p["js_runtimes"] == {"node": {"path": "/opt/bin/node"}} for p in FakeYDL.created)


def test_real_yt_dlp_class_is_what_we_patch():
    assert ytdl.yt_dlp.YoutubeDL is yt_dlp.YoutubeDL


@pytest.mark.parametrize(
    ("spec", "expected"),
    [
        ("firefox", ("firefox", None, None, None)),
        ("Chrome:Profile 1", ("chrome", "Profile 1", None, None)),
        ("chromium+gnomekeyring:Default", ("chromium", "Default", "GNOMEKEYRING", None)),
        ("firefox:default-release::Work", ("firefox", "default-release", None, "Work")),
    ],
)
def test_cookie_spec_matches_yt_dlp_tuple(spec, expected):
    assert ytdl.parse_cookies_spec(spec) == expected
    # Same tuple yt-dlp's own command line builds for --cookies-from-browser.
    assert yt_dlp.parse_options(["--cookies-from-browser", spec]).ydl_opts["cookiesfrombrowser"] == expected


@pytest.mark.parametrize("spec", ["netscape", "chrome+nokeyring", ""])
def test_bad_cookie_spec(spec):
    with pytest.raises(ValueError):
        ytdl.parse_cookies_spec(spec)


def test_cookies_from_env_and_cli_override(monkeypatch):
    fake_runtimes(monkeypatch, {})
    assert "cookiesfrombrowser" not in ytdl.ydl_opts()
    monkeypatch.setenv("WWXD_COOKIES_FROM_BROWSER", "firefox")
    assert ytdl.ydl_opts()["cookiesfrombrowser"] == ("firefox", None, None, None)
    ytdl.use_cookies_from_browser("chrome:Profile 1")
    assert ytdl.ydl_opts()["cookiesfrombrowser"] == ("chrome", "Profile 1", None, None)


def test_cli_rejects_bad_browser(tmp_path, monkeypatch):
    from typer.testing import CliRunner

    from wwxd.cli import app

    monkeypatch.setenv("WWXD_HOME", str(tmp_path))
    runner = CliRunner()
    assert runner.invoke(app, ["new", "t", "--name", "Paul Graham"]).exit_code == 0
    for command in ("discover", "update", "fetch"):
        result = runner.invoke(app, [command, "t", "--cookies-from-browser", "netscape"])
        assert result.exit_code == 1, command
        assert "unsupported browser" in result.output

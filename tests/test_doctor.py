import datetime as dt
import os
import sys
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from wwxd import doctor, ytdl
from wwxd.cli import app
from wwxd.doctor import FAIL, OK, WARN, Check
from wwxd.ytdl import JsRuntime


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    monkeypatch.delenv("WWXD_COOKIES_FROM_BROWSER", raising=False)
    ytdl.find_js_runtimes.cache_clear()
    yield
    ytdl.find_js_runtimes.cache_clear()


def test_python_version():
    assert doctor.check_python((3, 9, 18)).status == FAIL
    assert doctor.check_python((3, 10, 0)).status == OK


def test_stale_yt_dlp_warns(monkeypatch):
    monkeypatch.setattr(doctor, "_version", lambda dist: "2026.8.19")
    assert doctor.check_yt_dlp(dt.date(2026, 10, 8)).status == OK
    assert doctor.check_yt_dlp(dt.date(2027, 3, 1)).status == WARN


def test_js_runtime_reports_the_one_fetch_uses(monkeypatch):
    found = {"deno": False, "node": True, "bun": True}
    monkeypatch.setattr(ytdl, "_which", lambda name: f"/opt/{name}" if name in found else None)
    monkeypatch.setattr(ytdl, "_probe", lambda name, path: JsRuntime(name, path, "9.9", found[name]))
    check = doctor.check_js_runtime()
    assert check.status == OK
    assert check.detail.startswith("node 9.9 at /opt/node") and "also found: deno, bun" in check.detail


def test_js_runtime_too_old_or_missing(monkeypatch):
    monkeypatch.setattr(ytdl, "_which", lambda name: "/opt/node" if name == "node" else None)
    monkeypatch.setattr(ytdl, "_probe", lambda name, path: JsRuntime(name, path, "20.1.0", False))
    check = doctor.check_js_runtime()
    assert check.status == WARN and "node 20.1.0 (needs 22.0.0+)" in check.detail
    ytdl.find_js_runtimes.cache_clear()
    monkeypatch.setattr(ytdl, "_which", lambda name: None)
    assert doctor.check_js_runtime().status == WARN


@pytest.mark.parametrize(
    ("av", "passes", "status"),
    [("17.1.0", True, OK), ("18.0.0", True, FAIL), ("19.1.0", True, FAIL), ("19.1.0", False, OK), (None, True, FAIL)],
)
def test_pyav_compatibility(av, passes, status):
    assert doctor.check_pyav(av, "1.2.1", passes).status == status


def test_cuda(monkeypatch):
    monkeypatch.setitem(sys.modules, "ctranslate2", SimpleNamespace(get_cuda_device_count=lambda: 0))
    assert doctor.check_cuda("auto").status == OK
    assert "CPU" in doctor.check_cuda("auto").detail
    assert doctor.check_cuda("cuda").status == FAIL
    monkeypatch.setitem(sys.modules, "ctranslate2", SimpleNamespace(get_cuda_device_count=lambda: 2))
    assert doctor.check_cuda("cuda").status == OK


def test_whisper_missing_is_a_warning(monkeypatch):
    monkeypatch.setattr(doctor, "_version", lambda dist: None)
    assert [c.status for c in doctor.check_whisper()] == [WARN]


def test_home(monkeypatch, tmp_path):
    monkeypatch.setenv("WWXD_HOME", str(tmp_path))
    assert doctor.check_home().status == OK
    monkeypatch.setenv("WWXD_HOME", str(tmp_path / "not" / "yet"))
    assert doctor.check_home().status == OK
    (tmp_path / "file").write_text("x")
    monkeypatch.setenv("WWXD_HOME", str(tmp_path / "file"))
    assert doctor.check_home().status == FAIL


@pytest.mark.skipif(sys.platform == "win32" or os.geteuid() == 0, reason="root ignores permissions")
def test_home_read_only(monkeypatch, tmp_path):
    locked = tmp_path / "locked"
    locked.mkdir(mode=0o500)
    try:
        monkeypatch.setenv("WWXD_HOME", str(locked))
        assert doctor.check_home().status == FAIL
        monkeypatch.setenv("WWXD_HOME", str(locked / "vaults"))
        assert doctor.check_home().status == FAIL
    finally:
        locked.chmod(0o700)


def test_cookies(monkeypatch):
    assert doctor.check_cookies().status == OK
    monkeypatch.setenv("WWXD_COOKIES_FROM_BROWSER", "chrome:Profile 1")
    assert doctor.check_cookies().status == OK
    monkeypatch.setenv("WWXD_COOKIES_FROM_BROWSER", "netscape")
    assert doctor.check_cookies().status == FAIL


def test_real_checks_run(monkeypatch, tmp_path):
    monkeypatch.setenv("WWXD_HOME", str(tmp_path))
    checks = doctor.run_checks()
    assert {c.status for c in checks} <= {OK, WARN, FAIL}
    assert [c.name for c in checks[:6]] == ["Python", "wwxd", "yt-dlp", "JS runtime", "yt-dlp-ejs", "ffmpeg"]


def test_exit_code_only_on_fail(monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr(doctor, "run_checks", lambda: [Check(OK, "a", "fine"), Check(WARN, "b", "meh")])
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0 and "0 failed, 1 warnings" in result.output
    monkeypatch.setattr(doctor, "run_checks", lambda: [Check(FAIL, "c", "broken")])
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 1 and "FAIL  c  broken" in result.output

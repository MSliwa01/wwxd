from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from wwxd import ytdl
from wwxd.cli import app
from wwxd.fetchers import whisper as whisper_mod
from wwxd.fetchers import youtube
from wwxd.vault import Source, resolve_vault


@pytest.fixture
def loaded(monkeypatch, tmp_path):
    """Fake faster-whisper: records which model names get loaded."""
    names: list[str] = []

    def get_model(name):
        names.append(name)
        segment = SimpleNamespace(start=0.0, text=f" said by {name} ")
        return SimpleNamespace(transcribe=lambda path, **kw: (iter([segment]), SimpleNamespace(language="en")))

    monkeypatch.setattr(whisper_mod, "_get_model", get_model)
    monkeypatch.setattr(whisper_mod, "download_audio_url", lambda url, stem, d: tmp_path / "a.mp3")
    monkeypatch.setattr(whisper_mod, "download_youtube_audio", lambda url, vid, d: tmp_path / "a.webm")
    return names


def test_model_name_precedence(monkeypatch):
    monkeypatch.delenv("WWXD_WHISPER_MODEL", raising=False)
    assert whisper_mod.model_name() == "small"
    monkeypatch.setenv("WWXD_WHISPER_MODEL", "medium")
    assert whisper_mod.model_name() == "medium"
    assert whisper_mod.model_name("large-v3") == "large-v3"


def test_fetch_option_overrides_env(monkeypatch, tmp_path, loaded):
    monkeypatch.setenv("WWXD_HOME", str(tmp_path))
    monkeypatch.setenv("WWXD_WHISPER_MODEL", "medium")
    runner = CliRunner()
    assert runner.invoke(app, ["new", "t", "--name", "Jane Doe"]).exit_code == 0
    v = resolve_vault("t")
    v.save_sources([Source(id="pod-1", type="podcast", url="https://e.com/1.mp3", status="approved")])

    result = runner.invoke(app, ["fetch", "t", "--whisper-model", "large-v3"])
    assert result.exit_code == 0, result.output
    assert loaded == ["large-v3"]
    assert "said by large-v3" in v.raw_path("pod-1").read_text()

    result = runner.invoke(app, ["fetch", "t", "pod-1", "--force"])
    assert result.exit_code == 0, result.output
    assert loaded == ["large-v3", "medium"]


def test_youtube_whisper_uses_the_override(monkeypatch, tmp_path, loaded):
    class NoCaptions:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def extract_info(self, url, download=False):
            return {"title": "t", "subtitles": {}, "automatic_captions": {}}

    monkeypatch.setattr(ytdl, "new_ydl", lambda **opts: NoCaptions())
    vault = SimpleNamespace(cache_dir=tmp_path)
    source = Source(id="yt-abcdefghijk", type="youtube", url="u")
    doc = youtube.fetch(source, vault, whisper_model="large-v3")
    assert doc.meta["transcript"] == "whisper" and loaded == ["large-v3"]

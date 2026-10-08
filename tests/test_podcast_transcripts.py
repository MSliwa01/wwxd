import pytest

from wwxd import rawdoc
from wwxd.fetchers import podcast, transcripts
from wwxd.fetchers import whisper as whisper_mod
from wwxd.fetchers.transcripts import parse_json, parse_srt, parse_transcript, parse_vtt
from wwxd.rawdoc import Segment
from wwxd.vault import Source, create_vault

# The examples from the Podcast Namespace transcript spec.
SPEC_VTT = """WEBVTT

00:00:00.000 --> 00:00:05.000
<v John>Podcasting 2.0 is really changing the game.

00:00:05.000 --> 00:00:10.000
<v Tom>Yeah, absolutely. The new features are incredible.

00:00:10.000 --> 00:00:15.000
It's amazing how it's empowering creators like never before.

00:00:20.000 --> 00:00:25.000
<v John>Exactly, Tom. It's revolutionizing the industry.
"""

SPEC_SRT = """1
00:00:00,000 --> 00:00:02,760
Sarah: In today's episode,
you'll learn whether or not you

2
00:00:02,760 --> 00:00:06,090
should have a podcast trailer.

4
00:00:19,080 --> 00:00:21,450
Gillian: Hi Buzzsprout, Gillian
here from breaking through
"""

SPEC_JSON = """{"version": "1.0.0", "segments": [
  {"speaker": "Darth Vader", "startTime": 0.5, "endTime": 0.75, "body": "I"},
  {"speaker": "Darth Vader", "startTime": 1, "endTime": 1.25, "body": "am"},
  {"speaker": "Darth Vader", "startTime": 2.25, "endTime": 2.5, "body": "father.\\n"},
  {"speaker": "Luke", "startTime": 2.75, "endTime": 3.0, "body": "Nooooo"}
]}"""


def test_vtt_voices_mark_turns_and_carry_over():
    assert parse_vtt(SPEC_VTT) == [
        Segment(0.0, "Podcasting 2.0 is really changing the game."),
        Segment(5.0, ">> Yeah, absolutely. The new features are incredible."),
        Segment(10.0, "It's amazing how it's empowering creators like never before."),
        Segment(20.0, ">> Exactly, Tom. It's revolutionizing the industry."),
    ]


def test_vtt_ignores_header_notes_ids_settings_and_markup():
    vtt = (
        "﻿WEBVTT - Episode 12\r\nKind: captions\r\n\r\n"
        "NOTE produced by a robot\r\n\r\n"
        "STYLE\r\n::cue { color: yellow }\r\n\r\n"
        "intro-1\r\n01:02.500 --> 01:05.000 align:start position:10%\r\n"
        "<v.loud Ann Smith>Fish <c.yellow>&amp;</c> chips</v>\r\n\r\n"
        "1:00:00.250 --> 1:00:03.000\r\n<v Ann Smith>Still me <01:00:01.000>here.\r\n<v Bob>And me.\r\n"
    )
    assert parse_vtt(vtt) == [
        Segment(62.5, "Fish & chips"),
        Segment(3600.25, "Still me here."),
        Segment(3600.25, ">> And me."),
    ]


def test_srt_speaker_labels_become_turns():
    assert parse_srt(SPEC_SRT) == [
        Segment(0.0, "In today's episode, you'll learn whether or not you"),
        Segment(2.76, "should have a podcast trailer."),
        Segment(19.08, ">> Hi Buzzsprout, Gillian here from breaking through"),
    ]


def test_srt_without_labels_keeps_colons_as_text():
    srt = "﻿  1\n00:00:01,000 --> 00:00:02,000\nWelcome back.\n\n2\n00:00:03,500 --> 00:00:04,000\nNote: this is <i>real</i>.\n"
    assert parse_srt(srt) == [Segment(1.0, "Welcome back."), Segment(3.5, "Note: this is real.")]


def test_json_word_segments_and_speakers():
    assert parse_json(SPEC_JSON) == [
        Segment(0.5, "I"),
        Segment(1.0, "am"),
        Segment(2.25, "father."),
        Segment(2.75, ">> Nooooo"),
    ]
    assert parse_json('{"segments": [{"startTime": "1.5", "body": " hi "}]}') == [Segment(1.5, "hi")]


def test_unusable_transcripts_raise():
    with pytest.raises(ValueError, match="no timestamps"):
        parse_transcript("<p>Hello</p>", "html")
    with pytest.raises(ValueError, match="no text"):
        parse_transcript("WEBVTT\n\n", "vtt")
    with pytest.raises(ValueError, match="no usable timestamps"):
        parse_transcript('{"segments": [{"startTime": 0, "body": "a"}, {"startTime": 0, "body": "b"}]}', "json")


def test_turns_survive_into_the_raw_doc():
    doc = rawdoc.RawDoc(meta={"id": "pod-x"}, segments=parse_vtt(SPEC_VTT))
    assert ">> Yeah, absolutely." in rawdoc.render(doc)


# --- the podcast fetcher ----------------------------------------------------------


@pytest.fixture
def vault(tmp_path):
    return create_vault(tmp_path / "v", "name: V\nslug: v\nmembers:\n  - id: jane\n    name: Jane\n")


@pytest.fixture
def fake_whisper(monkeypatch, tmp_path):
    calls = []

    def download(url, stem, directory):
        calls.append(url)
        return tmp_path / "audio.mp3"

    monkeypatch.setattr(whisper_mod, "download_audio_url", download)
    monkeypatch.setattr(whisper_mod, "transcribe", lambda path, *a, **k: ([Segment(0.0, "whispered")], "en"))
    return calls


def episode(**fields) -> Source:
    return Source(id="pod-abc", type="podcast", url="https://cdn.example.com/ep.mp3", title="Ep", **fields)


def test_feed_transcript_replaces_whisper(monkeypatch, vault, fake_whisper):
    monkeypatch.setattr(transcripts, "download_transcript", lambda url: SPEC_VTT)
    doc = podcast.fetch(episode(transcript_url="https://e.com/ep.vtt", transcript_type="text/vtt"), vault)
    assert doc.meta["transcript"] == "feed-transcript"
    assert doc.meta["transcript_url"] == "https://e.com/ep.vtt"
    assert doc.segments[1].text.startswith(">> ")
    assert fake_whisper == []


def test_falls_back_to_whisper_when_download_fails(monkeypatch, vault, fake_whisper, capsys):
    def broken(url):
        raise OSError("HTTP Error 404: Not Found")

    monkeypatch.setattr(transcripts, "download_transcript", broken)
    doc = podcast.fetch(episode(transcript_url="https://e.com/ep.json", transcript_type="application/json"), vault)
    assert doc.meta["transcript"] == "whisper" and "transcript_url" not in doc.meta
    assert fake_whisper == ["https://cdn.example.com/ep.mp3"]
    assert "feed transcript unusable" in capsys.readouterr().err


def test_untimed_transcript_is_not_downloaded(monkeypatch, vault, fake_whisper):
    monkeypatch.setattr(transcripts, "download_transcript", lambda url: pytest.fail("downloaded an html transcript"))
    doc = podcast.fetch(episode(transcript_url="https://e.com/ep.html", transcript_type="text/html"), vault)
    assert doc.meta["transcript"] == "whisper"


def test_whisper_modes(monkeypatch, vault, fake_whisper):
    monkeypatch.setattr(transcripts, "download_transcript", lambda url: SPEC_VTT)
    with_transcript = episode(transcript_url="https://e.com/ep.vtt", transcript_type="text/vtt")
    assert podcast.fetch(with_transcript, vault, whisper="always").meta["transcript"] == "whisper"
    assert podcast.fetch(with_transcript, vault, whisper="never").meta["transcript"] == "feed-transcript"
    with pytest.raises(RuntimeError, match="Whisper disabled"):
        podcast.fetch(episode(), vault, whisper="never")

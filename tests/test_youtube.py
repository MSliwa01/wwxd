from wwxd.fetchers.youtube import _pick_caption_track, parse_json3
from wwxd.rawdoc import Segment, chunk_segments


def test_parse_json3_skips_append_events():
    data = {
        "events": [
            {"tStartMs": 0, "dDurationMs": 1000},
            {"tStartMs": 30, "segs": [{"utf8": "okay"}, {"utf8": " today"}]},
            {"tStartMs": 3020, "aAppend": 1, "segs": [{"utf8": "\n"}]},
            {"tStartMs": 3030, "segs": [{"utf8": "to"}, {"utf8": " succeed"}]},
        ]
    }
    assert parse_json3(data) == [Segment(0.03, "okay today"), Segment(3.03, "to succeed")]


def test_pick_original_language_among_dubs():
    info = {
        "language": "en-US",
        "subtitles": {},
        "automatic_captions": {"ar-orig": ["ar"], "en": ["en"], "en-orig": ["en-orig"], "ja-orig": ["ja"]},
    }
    assert _pick_caption_track(info) == ("auto-captions", ["en-orig"])


def test_manual_captions_preferred():
    info = {"language": "en", "subtitles": {"en-GB": ["manual"]}, "automatic_captions": {"en-orig": ["auto"]}}
    assert _pick_caption_track(info) == ("captions", ["manual"])


def test_chunking_roughly_30s():
    segs = [Segment(float(i * 5), f"w{i}") for i in range(20)]
    chunks = chunk_segments(segs)
    assert chunks[0].start == 0 and chunks[1].start == 35

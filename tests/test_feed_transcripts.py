import io
import urllib.request
import xml.etree.ElementTree as ET

import pytest

from wwxd.discover import _feed_sources
from wwxd.fetchers.transcripts import best_transcript, transcript_format
from wwxd.vault import Source, create_vault

CONFIG = """name: Test
slug: test
members:
  - id: host
    name: Jane Host
"""

FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:podcast="https://podcastindex.org/namespace/1.0"
     xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
<channel>
  <title>The Show</title>
  <language>en-us</language>
  <item>
    <title>Episode with every format</title>
    <pubDate>Tue, 07 Oct 2026 10:00:00 GMT</pubDate>
    <enclosure url="https://cdn.example.com/ep2.mp3" type="audio/mpeg" length="1"/>
    <podcast:transcript url="https://example.com/ep2.html" type="text/html"/>
    <podcast:transcript url="https://example.com/ep2.srt" type="application/x-subrip"/>
    <podcast:transcript url="https://example.com/ep2.es.json" type="application/json" language="es"/>
    <podcast:transcript url="https://example.com/ep2.vtt" type="text/vtt"/>
  </item>
  <item>
    <title>Episode with loose SRT type</title>
    <enclosure url="https://cdn.example.com/ep1.mp3" type="audio/mpeg" length="1"/>
    <podcast:transcript url="https://example.com/ep1-captions.srt" type="application/srt" rel="captions"/>
  </item>
  <item>
    <title>Episode without transcript</title>
    <enclosure url="https://cdn.example.com/ep0.mp3" type="audio/mpeg" length="1"/>
  </item>
</channel>
</rss>
"""


@pytest.fixture
def vault(tmp_path):
    return create_vault(tmp_path / "test", CONFIG)


def serve(monkeypatch, body: str) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", lambda request, timeout=None: io.BytesIO(body.encode()))


def test_feed_items_carry_their_best_transcript(monkeypatch, vault):
    serve(monkeypatch, FEED)
    sources = _feed_sources(vault, "https://example.com/feed.xml", 10)
    assert [(s.transcript_url, s.transcript_type) for s in sources] == [
        ("https://example.com/ep2.vtt", "text/vtt"),  # the Spanish JSON is a translation
        ("https://example.com/ep1-captions.srt", "application/srt"),
        ("", ""),
    ]
    assert "transcript_url" not in sources[2].to_dict()


def test_transcript_fields_round_trip(vault):
    source = Source(id="pod-1", type="podcast", url="u", transcript_url="https://e.com/t.json",
                    transcript_type="application/json")
    vault.save_sources([source])
    assert vault.load_sources() == [source]


def item(xml: str) -> ET.Element:
    return ET.fromstring(f'<item xmlns:podcast="https://podcastindex.org/namespace/1.0">{xml}</item>')


def test_json_beats_vtt_beats_srt_beats_html_beats_text():
    tags = [
        '<podcast:transcript url="t.txt" type="text/plain"/>',
        '<podcast:transcript url="t.html" type="text/html"/>',
        '<podcast:transcript url="t.srt" type="application/x-subrip"/>',
        '<podcast:transcript url="t.vtt" type="text/vtt"/>',
        '<podcast:transcript url="t.json" type="application/json"/>',
    ]
    for n in range(len(tags), 0, -1):
        assert best_transcript(item("".join(tags[:n])))[0] == ["t.txt", "t.html", "t.srt", "t.vtt", "t.json"][n - 1]


def test_old_github_namespace_is_read():
    el = ET.fromstring(
        '<item xmlns:podcast="https://github.com/Podcastindex-org/podcast-namespace/blob/main/docs/1.0.md">'
        '<podcast:transcript url="https://e.com/t.vtt" type="text/vtt"/></item>'
    )
    assert best_transcript(el) == ("https://e.com/t.vtt", "text/vtt")


@pytest.mark.parametrize(
    ("mime", "url", "fmt"),
    [
        ("application/json", "", "json"),
        ("text/vtt", "", "vtt"),
        ("application/x-subrip", "", "srt"),
        ("application/srt", "", "srt"),
        ("text/srt", "", "srt"),
        ("text/html", "", "html"),
        ("text/plain", "", "text"),
        ("", "https://e.com/ep.vtt?x=1", "vtt"),
        ("application/octet-stream", "https://e.com/ep.srt", "srt"),
        ("application/pdf", "https://e.com/ep.pdf", ""),
    ],
)
def test_transcript_format(mime, url, fmt):
    assert transcript_format(mime, url) == fmt

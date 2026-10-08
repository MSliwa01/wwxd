"""Podcasting 2.0 transcripts (<podcast:transcript>): pick the best one in a feed item, download it and
parse it into timestamped segments. Formats: https://github.com/Podcastindex-org/podcast-namespace
(docs/examples/transcripts/transcripts.md)."""

from __future__ import annotations

import html
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from pathlib import PurePosixPath

from wwxd.rawdoc import Segment

PODCAST_NAMESPACES = (
    "https://podcastindex.org/namespace/1.0",
    # Early Podcasting 2.0 feeds used the spec's GitHub URL as the namespace.
    "https://github.com/Podcastindex-org/podcast-namespace/blob/main/docs/1.0.md",
)
TRANSCRIPT_TAGS = tuple(f"{{{ns}}}transcript" for ns in PODCAST_NAMESPACES)

# Best first. json/vtt/srt carry timestamps; html and text usually don't.
FORMATS = ("json", "vtt", "srt", "html", "text")
TIMED_FORMATS = ("json", "vtt", "srt")
_MIME_HINTS = (("json", ("json",)), ("vtt", ("vtt",)), ("srt", ("srt", "subrip")), ("html", ("html",)), ("text", ("text/plain",)))
_EXTENSIONS = {".json": "json", ".vtt": "vtt", ".srt": "srt", ".html": "html", ".htm": "html", ".txt": "text"}


def transcript_format(mime: str, url: str = "") -> str:
    """'application/x-subrip' -> 'srt'. Feeds use loose MIME types (application/srt, text/srt), so match on
    substrings, then fall back to the URL's extension. '' when unknown."""
    mime = (mime or "").lower()
    for fmt, hints in _MIME_HINTS:
        if any(hint in mime for hint in hints):
            return fmt
    suffix = PurePosixPath(urllib.parse.urlparse(url).path).suffix.lower()
    return _EXTENSIONS.get(suffix, "")


def best_transcript(item: ET.Element, feed_language: str = "") -> tuple[str, str] | None:
    """(url, type) of the item's best transcript: the feed's own language first (a translation is
    not the person's words), then json > vtt > srt > html > text."""
    language = feed_language.lower().split("-")[0]
    candidates = []
    for el in item:
        url = (el.get("url") or "").strip()
        if el.tag not in TRANSCRIPT_TAGS or not url:
            continue
        fmt = transcript_format(el.get("type") or "", url)
        if not fmt:
            continue
        lang = (el.get("language") or "").lower().split("-")[0]
        translated = bool(lang and language and lang != language)
        candidates.append(((translated, FORMATS.index(fmt)), url, (el.get("type") or "").strip()))
    if not candidates:
        return None
    _, url, mime = min(candidates, key=lambda c: c[0])
    return url, mime


# --- parsing ------------------------------------------------------------------

TURN = ">> "  # the speaker-change cue YouTube captions use, which the compile skill reads
CUE_TIME = re.compile(r"(?:(\d+):)?(\d{1,2}):(\d{2})(?:[.,](\d{1,3}))?")
VOICE = re.compile(r"<v(?:\.[^\s>]*)?(?:\s+([^>]*))?>")
TAG = re.compile(r"</?[a-zA-Z][^<>]*>|<\d[\d:.]*>")  # markup and VTT karaoke timestamps, not ">>"
SRT_LABEL = re.compile(r"^([A-Z][\w.'-]*(?:\s+[\w.'-]+){0,3}):\s+(?=\S)")


def _seconds(match: re.Match) -> float:
    hours, minutes, secs, frac = match.groups()
    return int(hours or 0) * 3600 + int(minutes) * 60 + int(secs) + (int(frac.ljust(3, "0")) / 1000 if frac else 0.0)


def _with_turns(items: Iterable[tuple[float, str, str | None]]) -> list[Segment]:
    """(start, text, speaker) -> segments with TURN where the speaker changes. speaker None: unchanged."""
    segments: list[Segment] = []
    current: str | None = None
    pending = False
    for start, text, speaker in items:
        if speaker and speaker != current:
            pending = pending or current is not None
            current = speaker
        text = " ".join(text.split())
        if not text:
            continue
        if pending:
            text, pending = TURN + text, False
        segments.append(Segment(start, text))
    return segments


def _cues(text: str) -> list[tuple[float, list[str]]]:
    """(start, text lines) for each cue of a VTT or SRT file. Header, NOTE, STYLE and REGION blocks have no '-->'."""
    cues = []
    for block in re.split(r"\n\s*\n", text.replace("\r\n", "\n").replace("\r", "\n")):
        lines = [line.strip() for line in block.strip().split("\n")]
        timing = next((i for i, line in enumerate(lines) if "-->" in line), None)
        if timing is None or lines[0].startswith("NOTE"):
            continue
        match = CUE_TIME.search(lines[timing].split("-->")[0])
        if match:
            cues.append((_seconds(match), [line for line in lines[timing + 1 :] if line]))
    return cues


def parse_vtt(text: str) -> list[Segment]:
    """WebVTT. Speakers come from <v Name> voice tags and carry over to cues without one."""
    items: list[tuple[float, str, str | None]] = []
    for start, lines in _cues(text):
        cue = " ".join(lines)
        parts = VOICE.split(cue)  # [text, name, text, name, text, ...]
        items.append((start, html.unescape(TAG.sub("", parts[0])), None))
        for name, run in zip(parts[1::2], parts[2::2]):
            items.append((start, html.unescape(TAG.sub("", run)), (name or "").strip() or None))
    return _with_turns(items)


def parse_srt(text: str) -> list[Segment]:
    """SubRip. Speakers are a 'Name: ' prefix on the cue where the speaker changes. Only trusted when the
    first cue has one and at least two cues do, so a stray 'Note: ...' line isn't read as a speaker."""
    cues = [(start, TAG.sub("", " ".join(lines))) for start, lines in _cues(text)]
    labels = [SRT_LABEL.match(cue) for _, cue in cues]
    labelled = bool(labels) and labels[0] is not None and sum(m is not None for m in labels) >= 2
    items = []
    for (start, cue), label in zip(cues, labels):
        if labelled and label:
            items.append((start, cue[label.end() :], label.group(1)))
        else:
            items.append((start, cue, None))
    return _with_turns(items)


def parse_json(text: str) -> list[Segment]:
    """Podcast Namespace JSON: {"segments": [{"startTime", "body", "speaker"?}]}, often one word per segment."""
    data = json.loads(text)
    rows = data.get("segments") if isinstance(data, dict) else data
    if not isinstance(rows, list):
        raise ValueError("no 'segments' list")
    items = []
    for row in rows:
        if not isinstance(row, dict) or "startTime" not in row:
            continue
        speaker = row.get("speaker")
        items.append((float(row["startTime"]), str(row.get("body") or ""), str(speaker).strip() if speaker else None))
    return _with_turns(items)


PARSERS = {"json": parse_json, "vtt": parse_vtt, "srt": parse_srt}


def parse_transcript(text: str, fmt: str) -> list[Segment]:
    parser = PARSERS.get(fmt)
    if parser is None:
        raise ValueError(f"{fmt or 'unknown'} transcripts have no timestamps" if fmt else "unknown transcript format")
    segments = parser(text)
    if not segments:
        raise ValueError(f"no text found in the {fmt} transcript")
    if len(segments) > 1 and max(s.start for s in segments) == 0:
        raise ValueError(f"the {fmt} transcript has no usable timestamps")
    return segments


def download_transcript(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "wwxd"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8-sig", errors="replace")


def load_transcript(url: str, mime: str = "") -> list[Segment]:
    """Download and parse a feed transcript. Raises if it can't give timestamped text."""
    fmt = transcript_format(mime, url)
    if fmt not in TIMED_FORMATS:  # don't download what we can't use
        raise ValueError(f"{mime or fmt or 'unknown'} transcripts have no timestamps")
    return parse_transcript(download_transcript(url), fmt)

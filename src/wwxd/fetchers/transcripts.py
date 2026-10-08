"""Podcasting 2.0 transcripts (<podcast:transcript>): pick the best one in a feed item."""

from __future__ import annotations

import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import PurePosixPath

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

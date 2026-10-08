from __future__ import annotations

import datetime as dt
import html
import json
import logging

import yt_dlp

from wwxd import ytdl
from wwxd.rawdoc import RawDoc, Segment
from wwxd.vault import Source, Vault

logger = logging.getLogger(__name__)

def video_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


def _iso_date(upload_date: str | None) -> str:
    if not upload_date or len(upload_date) != 8:
        return ""
    return f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"


def _pick_caption_track(info: dict) -> tuple[str, list[dict]] | None:
    """Prefer human captions, then the original-language auto track; never a machine translation."""
    language = (info.get("language") or "en").split("-")[0]
    manual = info.get("subtitles") or {}
    for key in manual:
        if key.split("-")[0] == language and not key.startswith("live_chat"):
            return "captions", manual[key]
    auto = info.get("automatic_captions") or {}
    # Auto-dubbed videos carry several "<lang>-orig" tracks (one per dub); take the spoken language's.
    for key in (f"{language}-orig", language):
        if key in auto:
            return "auto-captions", auto[key]
    orig = [k for k in auto if k.endswith("-orig")]
    if len(orig) == 1:
        return "auto-captions", auto[orig[0]]
    if manual:
        key = next(k for k in manual if not k.startswith("live_chat"))
        return "captions", manual[key]
    return None


def parse_json3(data: dict) -> list[Segment]:
    segments = []
    for event in data.get("events") or []:
        if event.get("aAppend") or "segs" not in event:
            continue
        text = html.unescape("".join(seg.get("utf8", "") for seg in event["segs"])).replace("\n", " ").strip()
        if text:
            segments.append(Segment(start=event.get("tStartMs", 0) / 1000.0, text=text))
    return segments


def _download_captions(ydl: yt_dlp.YoutubeDL, formats: list[dict]) -> list[Segment]:
    fmt = next((f for f in formats if f.get("ext") == "json3"), None)
    if fmt is None:
        raise RuntimeError("no json3 caption format offered")
    try:
        return ytdl.with_backoff(
            lambda: parse_json3(json.loads(ydl.urlopen(fmt["url"]).read())), "downloading captions", retry_other=True
        )
    except Exception as exc:
        raise RuntimeError(f"caption download failed: {exc}") from exc


def _extract(ydl: yt_dlp.YoutubeDL, url: str) -> dict:
    return ytdl.with_backoff(lambda: ydl.extract_info(url, download=False), "reading video info")


def extract_info(url: str) -> dict:
    with ytdl.new_ydl(skip_download=True) as ydl:
        info = _extract(ydl, url)
    if info is None:
        raise ValueError(f"Could not resolve {url}")
    return info


def fetch(source: Source, vault: Vault, *, whisper: str = "auto") -> RawDoc:
    """whisper: 'auto' (fallback when no captions), 'always', or 'never'."""
    video_id = source.id.removeprefix("yt-")
    url = video_url(video_id)
    with ytdl.new_ydl(skip_download=True) as ydl:
        info = _extract(ydl, url)
        track = None if whisper == "always" else _pick_caption_track(info)
        segments: list[Segment] = []
        transcript_kind = ""
        if track is not None:
            transcript_kind, formats = track
            segments = _download_captions(ydl, formats)

    language = info.get("language") or ""
    if not segments:
        if whisper == "never":
            raise RuntimeError("no captions available and Whisper disabled")
        from wwxd.fetchers import whisper as whisper_mod

        audio = whisper_mod.download_youtube_audio(url, video_id, vault.cache_dir / "audio")
        segments, language = whisper_mod.transcribe(audio)
        transcript_kind = "whisper"

    meta = {
        "id": source.id,
        "type": "youtube",
        "url": url,
        "title": info.get("title") or source.title,
        "channel": info.get("channel") or info.get("uploader") or source.channel,
        "date": _iso_date(info.get("upload_date")) or source.date,
        "duration": info.get("duration") or source.duration,
        "language": language,
        "transcript": transcript_kind,
        "expected_speakers": source.expected_speakers,
        "description": (info.get("description") or "")[:2000],
        "fetched": dt.date.today().isoformat(),
    }
    return RawDoc(meta=meta, segments=segments)

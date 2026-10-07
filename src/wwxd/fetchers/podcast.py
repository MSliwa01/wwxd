from __future__ import annotations

import datetime as dt

from wwxd.fetchers import whisper
from wwxd.rawdoc import RawDoc
from wwxd.vault import Source, Vault


def fetch(source: Source, vault: Vault, **_: object) -> RawDoc:
    """Podcast episodes rarely ship transcripts, so this always goes through Whisper.

    TODO: use <podcast:transcript> tags from the feed when present (Podcasting 2.0).
    """
    audio = whisper.download_audio_url(source.url, source.id, vault.cache_dir / "audio")
    segments, language = whisper.transcribe(audio)
    meta = {
        "id": source.id,
        "type": "podcast",
        "url": source.url,
        "title": source.title,
        "channel": source.channel,
        "date": source.date,
        "duration": source.duration,
        "language": language,
        "transcript": "whisper",
        "expected_speakers": source.expected_speakers,
        "fetched": dt.date.today().isoformat(),
    }
    return RawDoc(meta=meta, segments=segments)

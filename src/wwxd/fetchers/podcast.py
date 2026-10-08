from __future__ import annotations

import datetime as dt
import sys

from wwxd.fetchers import transcripts
from wwxd.fetchers import whisper as whisper_mod
from wwxd.rawdoc import RawDoc, Segment
from wwxd.vault import Source, Vault


def fetch(
    source: Source, vault: Vault, *, whisper: str = "auto", whisper_model: str | None = None, **_: object
) -> RawDoc:
    """Use the feed's own transcript (<podcast:transcript>) when it has one, else Whisper.

    whisper: 'auto' (Whisper when there's no usable feed transcript), 'always' (ignore the feed
    transcript, e.g. to re-transcribe with a bigger model), or 'never'. whisper_model overrides
    WWXD_WHISPER_MODEL.
    """
    segments: list[Segment] = []
    kind, language = "", ""
    if source.transcript_url and whisper != "always":
        try:
            segments = transcripts.load_transcript(source.transcript_url, source.transcript_type)
            kind = "feed-transcript"
        except Exception as exc:
            if whisper == "never":
                raise RuntimeError(f"feed transcript unusable ({exc}) and Whisper disabled") from exc
            print(f"    feed transcript unusable ({exc}); using Whisper", file=sys.stderr, flush=True)
    if not segments:
        if whisper == "never":
            raise RuntimeError("no feed transcript and Whisper disabled")
        audio = whisper_mod.download_audio_url(source.url, source.id, vault.cache_dir / "audio")
        segments, language = whisper_mod.transcribe(audio, whisper_model)
        kind = "whisper"
    meta = {
        "id": source.id,
        "type": "podcast",
        "url": source.url,
        "title": source.title,
        "channel": source.channel,
        "date": source.date,
        "duration": source.duration,
        "language": language,
        "transcript": kind,
        "transcript_url": source.transcript_url,
        "expected_speakers": source.expected_speakers,
        "fetched": dt.date.today().isoformat(),
    }
    if kind != "feed-transcript":
        del meta["transcript_url"]
    return RawDoc(meta=meta, segments=segments)

"""Local transcription fallback. Requires the `whisper` extra: `pip install 'wwxd[whisper]'`."""

from __future__ import annotations

import logging
import urllib.request
from functools import lru_cache
from pathlib import Path

from wwxd.config import get_settings
from wwxd.rawdoc import Segment

logger = logging.getLogger(__name__)

AUDIO_EXTENSIONS = (".wav", ".mp3", ".m4a", ".webm", ".opus", ".ogg", ".aac")


def _resolve_device(device: str) -> str:
    if device != "auto":
        return device
    try:
        import ctranslate2

        if ctranslate2.get_cuda_device_count() > 0:
            return "cuda"
    except Exception:  # missing CUDA libraries look like "no GPU"
        pass
    return "cpu"


@lru_cache
def _get_model():
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(
            "No captions for this source and Whisper isn't installed. "
            "Install it with: pip install 'wwxd[whisper]' (or uv tool install 'wwxd[whisper]')"
        ) from exc
    settings = get_settings()
    device = _resolve_device(settings.whisper_device)
    compute_type = "auto"  # fastest type the hardware supports (older GPUs lack fast float16)
    logger.info("Loading Whisper '%s' on %s (%s)", settings.whisper_model, device, compute_type)
    return WhisperModel(settings.whisper_model, device=device, compute_type=compute_type)


def transcribe(audio_path: Path) -> tuple[list[Segment], str]:
    model = _get_model()
    segments_iter, info = model.transcribe(str(audio_path), vad_filter=True)
    segments = [Segment(s.start, s.text.strip()) for s in segments_iter if s.text.strip()]
    return segments, getattr(info, "language", "") or ""


def _find_cached(directory: Path, stem: str) -> Path | None:
    for path in sorted(directory.glob(f"{stem}.*")):
        if path.suffix.lower() in AUDIO_EXTENSIONS and path.is_file():
            return path
    return None


def download_youtube_audio(url: str, video_id: str, directory: Path) -> Path:
    from wwxd import ytdl

    directory.mkdir(parents=True, exist_ok=True)
    cached = _find_cached(directory, video_id)
    if cached:
        return cached
    opts = {
        "format": "bestaudio/best",
        "outtmpl": str(directory / f"{video_id}.%(ext)s"),
        "retries": 5,
        "fragment_retries": 5,
    }

    def download() -> None:
        with ytdl.new_ydl(**opts) as ydl:
            ydl.download([url])

    try:
        ytdl.with_backoff(download, "downloading audio", retry_other=True)
    except Exception as exc:
        raise RuntimeError(f"Failed to download {url}: {exc}") from exc
    path = _find_cached(directory, video_id)
    if path is None:
        raise FileNotFoundError(f"Audio not found after download for {video_id}")
    return path


def download_audio_url(url: str, stem: str, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    cached = _find_cached(directory, stem)
    if cached:
        return cached
    suffix = Path(url.split("?")[0]).suffix.lower()
    path = directory / f"{stem}{suffix if suffix in AUDIO_EXTENSIONS else '.mp3'}"
    request = urllib.request.Request(url, headers={"User-Agent": "wwxd"})
    with urllib.request.urlopen(request, timeout=60) as response, path.open("wb") as fh:
        while chunk := response.read(1 << 20):
            fh.write(chunk)
    return path

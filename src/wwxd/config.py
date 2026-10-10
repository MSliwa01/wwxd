from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    home: Path
    whisper_model: str
    whisper_device: str
    download_delay: float
    cookies_from_browser: str  # yt-dlp's BROWSER[+KEYRING][:PROFILE][::CONTAINER], e.g. 'firefox'


def get_settings() -> Settings:
    return Settings(
        home=Path(os.environ.get("WWXD_HOME", "./vaults")).expanduser().resolve(),
        whisper_model=os.environ.get("WWXD_WHISPER_MODEL", "auto"),
        whisper_device=os.environ.get("WWXD_WHISPER_DEVICE", "auto"),
        download_delay=float(os.environ.get("WWXD_DOWNLOAD_DELAY", "1.5")),
        cookies_from_browser=os.environ.get("WWXD_COOKIES_FROM_BROWSER", "").strip(),
    )

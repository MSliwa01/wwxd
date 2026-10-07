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


def get_settings() -> Settings:
    return Settings(
        home=Path(os.environ.get("WWXD_HOME", "./vaults")).expanduser().resolve(),
        whisper_model=os.environ.get("WWXD_WHISPER_MODEL", "small"),
        whisper_device=os.environ.get("WWXD_WHISPER_DEVICE", "auto"),
        download_delay=float(os.environ.get("WWXD_DOWNLOAD_DELAY", "1.5")),
    )

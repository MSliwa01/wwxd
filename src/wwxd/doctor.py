"""`wwxd doctor`: check what fetching needs. Local checks only, no network calls."""

from __future__ import annotations

import datetime as dt
import importlib.util
import os
import shutil
import sys
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from wwxd import __version__, ytdl
from wwxd.config import get_settings

OK, WARN, FAIL = "OK", "WARN", "FAIL"
YT_DLP_STALE_DAYS = 90  # YouTube changes often; older yt-dlp releases break
INSTALL_WHISPER = "uv tool install --force 'wwxd[whisper] @ git+https://github.com/MSliwa01/wwxd'"


@dataclass(frozen=True)
class Check:
    status: str  # OK | WARN | FAIL
    name: str
    detail: str


def _version(dist: str) -> str | None:
    try:
        return version(dist)
    except PackageNotFoundError:
        return None


def _major(ver: str) -> int:
    head = ver.split(".")[0]
    return int(head) if head.isdigit() else 0


def check_python(info: tuple[int, ...] = tuple(sys.version_info[:3])) -> Check:
    text = ".".join(map(str, info))
    if info < (3, 10):
        return Check(FAIL, "Python", f"{text}; wwxd needs 3.10 or newer")
    return Check(OK, "Python", text)


def check_yt_dlp(today: dt.date | None = None) -> Check:
    ver = _version("yt-dlp") or "unknown"
    try:
        released = dt.date(*map(int, ver.split(".")[:3]))
    except (TypeError, ValueError):
        return Check(OK, "yt-dlp", ver)
    age = ((today or dt.date.today()) - released).days
    if age > YT_DLP_STALE_DAYS:
        return Check(WARN, "yt-dlp", f"{ver} is {age} days old and YouTube changes often; upgrade with "
                     "`uv tool upgrade wwxd`")
    return Check(OK, "yt-dlp", ver)


def _min_version(name: str) -> str:
    try:
        from yt_dlp.globals import supported_js_runtimes

        return ".".join(map(str, supported_js_runtimes.value[name].MIN_SUPPORTED_VERSION))
    except Exception:
        return "?"


def check_js_runtime() -> Check:
    found = ytdl.find_js_runtimes()
    chosen = ytdl.js_runtime()
    if chosen is not None:
        others = [r.name for r in found if r is not chosen]
        detail = f"{chosen.name} {chosen.version or '(version unknown)'} at {chosen.path}"
        return Check(OK, "JS runtime", detail + (f" (also found: {', '.join(others)})" if others else ""))
    if found:
        too_old = ", ".join(f"{r.name} {r.version or '?'} (needs {_min_version(r.name)}+)" for r in found)
        return Check(WARN, "JS runtime", f"too old for yt-dlp: {too_old}; YouTube may miss formats")
    return Check(WARN, "JS runtime", "none found; install deno, node 22+ or bun so yt-dlp can solve YouTube's "
                 "JS challenges")


def check_ejs() -> Check:
    ver = _version("yt-dlp-ejs")
    if ver is None:
        return Check(WARN, "yt-dlp-ejs", "missing, so node and bun can't solve YouTube's JS challenges; "
                     "reinstall wwxd (it depends on yt-dlp[default])")
    return Check(OK, "yt-dlp-ejs", ver)


def check_ffmpeg() -> Check:
    path = shutil.which("ffmpeg")
    if path is None:
        return Check(WARN, "ffmpeg", "not on PATH; yt-dlp needs it to convert some audio downloads")
    return Check(OK, "ffmpeg", path)


def _passes_metadata_errors() -> bool:
    """faster-whisper 1.2.1 calls av.open(..., metadata_errors=...), which PyAV 18 and newer reject."""
    try:
        spec = importlib.util.find_spec("faster_whisper.audio")
        return bool(spec and spec.origin) and "metadata_errors" in Path(spec.origin).read_text(encoding="utf-8")
    except Exception:
        return True  # can't tell; assume the known-bad call


def check_pyav(av: str | None, fw: str, passes_metadata_errors: bool) -> Check:
    if av is None:
        return Check(FAIL, "PyAV", f"missing; faster-whisper needs it. Reinstall: {INSTALL_WHISPER}")
    if _major(av) >= 18 and passes_metadata_errors:
        return Check(FAIL, "PyAV", f"{av} breaks faster-whisper {fw} (wwxd pins av<18). Reinstall: {INSTALL_WHISPER}")
    return Check(OK, "PyAV", av)


def check_cuda(device: str) -> Check:
    try:
        import ctranslate2

        count = ctranslate2.get_cuda_device_count()
    except Exception:  # missing CUDA libraries look like "no GPU"
        count = 0
    if device == "auto":
        if count:
            return Check(OK, "CUDA", f"{count} device(s); Whisper runs on the GPU")
        return Check(OK, "CUDA", "no device; Whisper runs on the CPU, which is slow for long episodes")
    if device == "cuda" and not count:
        return Check(FAIL, "CUDA", "WWXD_WHISPER_DEVICE=cuda but ctranslate2 sees no CUDA device")
    return Check(OK, "CUDA", f"{count} device(s); WWXD_WHISPER_DEVICE={device}")


def check_whisper() -> list[Check]:
    fw = _version("faster-whisper")
    if fw is None:
        return [Check(WARN, "Whisper", f"not installed; sources without captions need it. Install: {INSTALL_WHISPER}")]
    settings = get_settings()
    try:
        import faster_whisper  # noqa: F401
    except Exception as exc:
        whisper = Check(FAIL, "Whisper", f"faster-whisper {fw} is installed but won't import: {exc}")
    else:
        whisper = Check(OK, "Whisper", f"faster-whisper {fw}, model {settings.whisper_model} (WWXD_WHISPER_MODEL)")
    pyav = check_pyav(_version("av"), fw, _passes_metadata_errors())
    return [whisper, pyav, check_cuda(settings.whisper_device)]


def check_home() -> Check:
    home = get_settings().home
    if home.exists():
        if home.is_dir() and os.access(home, os.W_OK | os.X_OK):
            return Check(OK, "WWXD_HOME", str(home))
        return Check(FAIL, "WWXD_HOME", f"{home} is not a writable directory")
    parent = next(p for p in home.parents if p.exists())
    if os.access(parent, os.W_OK | os.X_OK):
        return Check(OK, "WWXD_HOME", f"{home} (doesn't exist yet; `wwxd new` creates it)")
    return Check(FAIL, "WWXD_HOME", f"{home} doesn't exist and {parent} is not writable")


def check_cookies() -> Check:
    spec = get_settings().cookies_from_browser
    if not spec:
        return Check(OK, "Cookies", "none (if YouTube asks you to sign in, set WWXD_COOKIES_FROM_BROWSER "
                     "or pass --cookies-from-browser)")
    try:
        ytdl.parse_cookies_spec(spec)
    except ValueError as exc:
        return Check(FAIL, "Cookies", f"WWXD_COOKIES_FROM_BROWSER: {exc}")
    return Check(OK, "Cookies", f"from {spec} (WWXD_COOKIES_FROM_BROWSER)")


def run_checks() -> list[Check]:
    return [
        check_python(),
        Check(OK, "wwxd", __version__),
        check_yt_dlp(),
        check_js_runtime(),
        check_ejs(),
        check_ffmpeg(),
        *check_whisper(),
        check_home(),
        check_cookies(),
    ]

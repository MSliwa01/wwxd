"""Every yt-dlp YoutubeDL in wwxd is built here, so they all share one JS runtime and one set of options."""

from __future__ import annotations

import logging
import os
import random
import re
import shutil
import sys
import sysconfig
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from functools import lru_cache
from typing import TypeVar

import yt_dlp

from wwxd.config import get_settings

logger = logging.getLogger(__name__)
T = TypeVar("T")

# yt-dlp's own priority order (deno, node, quickjs, bun), minus quickjs, which is too slow for YouTube.
JS_RUNTIMES = ("deno", "node", "bun")


@dataclass(frozen=True)
class JsRuntime:
    name: str
    path: str
    version: str = ""
    supported: bool | None = None  # None: yt-dlp couldn't tell


def _which(name: str) -> str | None:
    # yt-dlp checks Python's scripts dir before PATH (pip installs deno there), so we do too.
    scripts = sysconfig.get_path("scripts")
    candidate = os.path.join(scripts, name + (sysconfig.get_config_var("EXE") or "")) if scripts else ""
    if candidate and os.access(candidate, os.X_OK) and not os.path.isdir(candidate):
        return candidate
    return shutil.which(name)


def _probe(name: str, path: str) -> JsRuntime:
    """Ask yt-dlp's own runtime class for the version and whether it meets yt-dlp's minimum."""
    try:
        from yt_dlp.globals import supported_js_runtimes

        info = supported_js_runtimes.value[name](path=path).info
    except Exception as exc:  # older yt-dlp, or a runtime that won't start
        logger.debug("Could not probe %s at %s: %s", name, path, exc)
        return JsRuntime(name, path)
    if info is None:
        return JsRuntime(name, path, supported=False)
    return JsRuntime(name, path, info.version, info.supported)


@lru_cache(maxsize=1)
def find_js_runtimes() -> tuple[JsRuntime, ...]:
    """Every deno/node/bun on PATH, in yt-dlp's priority order."""
    found = []
    for name in JS_RUNTIMES:
        path = _which(name)
        if path:
            found.append(_probe(name, path))
    return tuple(found)


def js_runtime() -> JsRuntime | None:
    """The runtime wwxd passes to yt-dlp: the first one yt-dlp doesn't reject."""
    return next((r for r in find_js_runtimes() if r.supported is not False), None)


# yt-dlp's --cookies-from-browser grammar: BROWSER[+KEYRING][:PROFILE][::CONTAINER]
COOKIES_SPEC = re.compile(
    r"""(?x)
    (?P<name>[^+:]+)
    (?:\s*\+\s*(?P<keyring>[^:]+))?
    (?:\s*:\s*(?!:)(?P<profile>.+?))?
    (?:\s*::\s*(?P<container>.+))?
    """
)

_cookies_override: str | None = None


def parse_cookies_spec(spec: str) -> tuple[str, str | None, str | None, str | None]:
    """'chrome:Profile 1' -> ('chrome', 'Profile 1', None, None), the tuple yt-dlp's `cookiesfrombrowser` takes."""
    from yt_dlp.cookies import SUPPORTED_BROWSERS, SUPPORTED_KEYRINGS

    match = COOKIES_SPEC.fullmatch(spec.strip())
    if match is None:
        raise ValueError(f"invalid cookies-from-browser value: {spec!r}")
    browser, keyring, profile, container = match.group("name", "keyring", "profile", "container")
    browser = browser.strip().lower()
    if browser not in SUPPORTED_BROWSERS:
        raise ValueError(f"unsupported browser {browser!r}; use one of: {', '.join(sorted(SUPPORTED_BROWSERS))}")
    if keyring is not None:
        keyring = keyring.strip().upper()
        if keyring not in SUPPORTED_KEYRINGS:
            raise ValueError(f"unsupported keyring {keyring!r}; use one of: {', '.join(sorted(SUPPORTED_KEYRINGS))}")
    return browser, profile, keyring, container


def use_cookies_from_browser(spec: str | None) -> None:
    """Override WWXD_COOKIES_FROM_BROWSER for this process (the CLI's --cookies-from-browser)."""
    global _cookies_override
    if spec:
        parse_cookies_spec(spec)  # fail now, not halfway through a fetch
    _cookies_override = spec or None


def cookies_spec() -> str:
    return _cookies_override or get_settings().cookies_from_browser


def ydl_opts(**extra: object) -> dict:
    """Base YoutubeDL params plus `extra`. yt-dlp's warnings show only with `wwxd -v`."""
    opts: dict = {"quiet": True, "noprogress": True, "no_warnings": not logging.getLogger().isEnabledFor(logging.INFO)}
    runtime = js_runtime()
    if runtime is not None:
        opts["js_runtimes"] = {runtime.name: {"path": runtime.path}}
    spec = cookies_spec()
    if spec:
        opts["cookiesfrombrowser"] = parse_cookies_spec(spec)
    opts.update(extra)
    return opts


def new_ydl(**extra: object) -> yt_dlp.YoutubeDL:
    return yt_dlp.YoutubeDL(ydl_opts(**extra))


# HTTP 429 from YouTube: wait 10-15 s, then 20-30 s, then 40-60 s. Never longer than a minute.
RATE_LIMIT_RETRIES = 3
RATE_LIMIT_BASE = 10.0
RATE_LIMIT_CAP = 60.0
RATE_LIMIT_TEXT = re.compile(r"HTTP Error 429|Too Many Requests", re.IGNORECASE)


def _error_chain(exc: BaseException) -> Iterator[BaseException]:
    """exc and everything it wraps: __cause__/__context__, ExtractorError.cause, DownloadError.exc_info."""
    stack: list[object] = [exc]
    seen: set[int] = set()
    while stack:
        err = stack.pop()
        if not isinstance(err, BaseException) or id(err) in seen:
            continue
        seen.add(id(err))
        yield err
        exc_info = getattr(err, "exc_info", None)
        stack += [err.__cause__, err.__context__, getattr(err, "cause", None)]
        if isinstance(exc_info, tuple) and len(exc_info) > 1:
            stack.append(exc_info[1])


def is_rate_limited(exc: BaseException) -> bool:
    for err in _error_chain(exc):
        if getattr(err, "status", None) == 429 or getattr(err, "code", None) == 429:
            return True
        if RATE_LIMIT_TEXT.search(str(err)):
            return True
    return False


def backoff_delay(attempt: int, rand: Callable[[], float] = random.random) -> float:
    """Exponential backoff with up to 50% jitter, capped at RATE_LIMIT_CAP seconds."""
    return min(RATE_LIMIT_CAP, RATE_LIMIT_BASE * 2**attempt * (1 + 0.5 * rand()))


def with_backoff(
    fn: Callable[[], T],
    what: str,
    *,
    retries: int = RATE_LIMIT_RETRIES,
    retry_other: bool = False,
    sleep: Callable[[float], None] | None = None,
) -> T:
    """Call fn. On HTTP 429, print a notice, back off and retry.

    retry_other: also retry other errors (network hiccups) after the short per-source delay.
    """
    for attempt in range(retries + 1):
        try:
            return fn()
        except Exception as exc:
            limited = is_rate_limited(exc)
            if attempt == retries:
                if limited:
                    raise RuntimeError(
                        f"{exc} (still rate limited after {retries} retries; wait a while, "
                        "or pass --cookies-from-browser)"
                    ) from exc
                raise
            if limited:
                wait = backoff_delay(attempt)
                print(f"    YouTube rate limit (HTTP 429) while {what}; retry {attempt + 1}/{retries} in {wait:.0f}s",
                      file=sys.stderr, flush=True)
            elif retry_other:
                wait = get_settings().download_delay * (attempt + 1)
                logger.warning("%s failed (attempt %d/%d): %s", what, attempt + 1, retries + 1, exc)
            else:
                raise
            (sleep or time.sleep)(wait)
    raise AssertionError("unreachable")

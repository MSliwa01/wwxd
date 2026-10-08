"""Every yt-dlp YoutubeDL in wwxd is built here, so they all share one JS runtime and one set of options."""

from __future__ import annotations

import logging
import os
import re
import shutil
import sysconfig
from dataclasses import dataclass
from functools import lru_cache

import yt_dlp

from wwxd.config import get_settings

logger = logging.getLogger(__name__)

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
    opts: dict = {"quiet": True, "no_warnings": not logging.getLogger().isEnabledFor(logging.INFO)}
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

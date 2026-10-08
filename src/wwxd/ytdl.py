"""Every yt-dlp YoutubeDL in wwxd is built here, so they all share one JS runtime and one set of options."""

from __future__ import annotations

import logging
import os
import shutil
import sysconfig
from dataclasses import dataclass
from functools import lru_cache

import yt_dlp

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


def ydl_opts(**extra: object) -> dict:
    """Base YoutubeDL params plus `extra`. yt-dlp's warnings show only with `wwxd -v`."""
    opts: dict = {"quiet": True, "no_warnings": not logging.getLogger().isEnabledFor(logging.INFO)}
    runtime = js_runtime()
    if runtime is not None:
        opts["js_runtimes"] = {runtime.name: {"path": runtime.path}}
    opts.update(extra)
    return opts


def new_ydl(**extra: object) -> yt_dlp.YoutubeDL:
    return yt_dlp.YoutubeDL(ydl_opts(**extra))

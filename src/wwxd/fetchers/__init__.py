"""Fetchers turn an approved Source into a RawDoc.

Third-party fetchers register under the `wwxd.fetchers` entry-point group:

    [project.entry-points."wwxd.fetchers"]
    epub = "my_package:fetch"

A plugin is a callable `fetch(source, vault, **options) -> RawDoc | None`.
Returning None means "not mine". Plugins run before the built-in fetchers, so
they can also override them.
"""

from __future__ import annotations

import datetime as dt
from importlib.metadata import entry_points
from pathlib import Path

from wwxd.rawdoc import RawDoc
from wwxd.vault import Source, Vault

TEXT_SUFFIXES = (".txt", ".md", ".markdown")


def fetch_file(source: Source, vault: Vault, **_: object) -> RawDoc:
    path = Path(source.url).expanduser()
    if path.suffix.lower() not in TEXT_SUFFIXES:
        raise RuntimeError(
            f"{path.name}: only {', '.join(TEXT_SUFFIXES)} are supported built in. "
            "Convert it to text first, or install/write a fetcher plugin (see CONTRIBUTING.md)."
        )
    meta = {
        "id": source.id,
        "type": "file",
        "url": str(path),
        "title": source.title or path.stem,
        "date": source.date,
        "transcript": "file",
        "expected_speakers": source.expected_speakers,
        "fetched": dt.date.today().isoformat(),
    }
    return RawDoc(meta=meta, body=path.read_text(encoding="utf-8"))


def _builtin(source_type: str):
    if source_type == "youtube":
        from wwxd.fetchers.youtube import fetch
    elif source_type == "web":
        from wwxd.fetchers.web import fetch
    elif source_type == "podcast":
        from wwxd.fetchers.podcast import fetch
    elif source_type == "file":
        fetch = fetch_file
    else:
        raise RuntimeError(f"No fetcher for source type '{source_type}'")
    return fetch


def fetch(source: Source, vault: Vault, **options: object) -> RawDoc:
    for ep in entry_points(group="wwxd.fetchers"):
        doc = ep.load()(source, vault, **options)
        if doc is not None:
            return doc
    return _builtin(source.type)(source, vault, **options)

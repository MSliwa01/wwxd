from __future__ import annotations

import datetime as dt

import trafilatura

from wwxd.rawdoc import RawDoc
from wwxd.vault import Source, Vault


def fetch(source: Source, vault: Vault, **_: object) -> RawDoc:
    html = trafilatura.fetch_url(source.url)
    if not html:
        raise RuntimeError(f"Could not download {source.url}")
    text = trafilatura.extract(html, url=source.url, include_comments=False, include_tables=False)
    if not text:
        raise RuntimeError(f"No article text found at {source.url}")
    meta_obj = trafilatura.extract_metadata(html, default_url=source.url)
    meta = {
        "id": source.id,
        "type": "web",
        "url": source.url,
        "title": (meta_obj.title if meta_obj else None) or source.title,
        "author": (meta_obj.author if meta_obj else None) or "",
        "site": (meta_obj.sitename if meta_obj else None) or "",
        "date": (meta_obj.date if meta_obj else None) or source.date,
        "transcript": "article",
        "expected_speakers": source.expected_speakers,
        "fetched": dt.date.today().isoformat(),
    }
    # One paragraph per line from trafilatura -> blank-line separated paragraphs.
    body = "\n\n".join(line.strip() for line in text.splitlines() if line.strip())
    return RawDoc(meta=meta, body=body)

from __future__ import annotations

import datetime as dt
import re

import trafilatura

from wwxd.rawdoc import RawDoc
from wwxd.vault import Source, Vault


MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
DATELINE = re.compile(rf"^\W*({MONTHS})\s+(\d{{1,2}},\s+)?(\d{{4}})\b")


def dateline(text: str) -> str:
    """A 'July 2023' / 'July 4, 2023' line at the top of the article beats guessed metadata."""
    for line in text.splitlines()[:3]:
        match = DATELINE.match(line.strip())
        if match:
            month = MONTHS.split("|").index(match.group(1)) + 1
            day = int(match.group(2).strip(", ")) if match.group(2) else 1
            return f"{match.group(3)}-{month:02d}-{day:02d}"
    return ""


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
        "date": dateline(text) or (meta_obj.date if meta_obj else None) or source.date,
        "transcript": "article",
        "expected_speakers": source.expected_speakers,
        "fetched": dt.date.today().isoformat(),
    }
    # One paragraph per line from trafilatura -> blank-line separated paragraphs.
    body = "\n\n".join(line.strip() for line in text.splitlines() if line.strip())
    return RawDoc(meta=meta, body=body)

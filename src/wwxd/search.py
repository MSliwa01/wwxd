from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from wwxd.vault import Vault

WORD = re.compile(r"[a-z0-9]{3,}")


@dataclass
class Hit:
    path: Path
    score: float
    title: str
    snippet: str


def search(vault: Vault, query: str, *, include_raw: bool = False, limit: int = 10) -> list[Hit]:
    """Keyword ranking over wiki pages (and optionally raw docs). Good enough to point the agent at files."""
    terms = set(WORD.findall(query.lower()))
    if not terms:
        return []
    roots = [vault.wiki_dir] + ([vault.raw_dir] if include_raw else [])
    hits = []
    for root in roots:
        for page in root.rglob("*.md"):
            text = page.read_text(encoding="utf-8")
            if text.startswith("---\n"):
                text = text.split("---\n", 2)[-1]
            lowered = text.lower()
            path_text = page.relative_to(vault.path).as_posix().lower()
            score = sum(lowered.count(t) + 5 * path_text.count(t) for t in terms)
            if not score:
                continue
            score /= 1 + len(lowered) / 20000  # don't let long transcripts win by size alone
            title = next((ln[2:] for ln in text.splitlines() if ln.startswith("# ")), page.stem)
            body = lowered.split("\n", 2)[-1] if lowered.startswith("# ") else lowered
            offset = len(lowered) - len(body)
            pos = offset + min((body.find(t) for t in terms if t in body), default=0)
            snippet = " ".join(text[max(0, pos - 80) : pos + 160].split())
            hits.append(Hit(page, score, title, snippet))
    return sorted(hits, key=lambda h: h.score, reverse=True)[:limit]

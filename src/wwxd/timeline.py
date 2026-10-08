"""`wwxd timeline`: statements in source-date order, grouped by member.

Answers "how did their view change?" mechanically: filter by leaf path or keyword,
then read each member's quotes oldest first.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from wwxd.lint import normalize
from wwxd.vault import Vault
from wwxd.wikimap import Citation, Leaf, read_leaves, source_dates

UNDATED = "undated"


@dataclass
class Entry:
    date: str  # ISO date of the source, "" when unknown
    statement: Citation
    leaves: list[str] = field(default_factory=list)


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _has_words(query: list[str], words: set[str]) -> bool:
    """Every query word appears, allowing a plural on either side (price / prices)."""
    def variants(word: str) -> set[str]:
        stem = re.sub(r"(es|s)$", "", word) if len(word) > 3 else word
        return {word, stem, stem + "s", stem + "es"}

    return all(variants(q) & words for q in query)


def leaf_matches(leaf: Leaf, query: str) -> bool:
    """A query with a slash is a path or path prefix; otherwise its words must all be in the path."""
    q = query.strip().lower().removeprefix("wiki/").removesuffix(".md").strip("/")
    if "/" in q:
        return leaf.rel == q or leaf.rel.startswith(q + "/")
    return _has_words(_words(q), set(_words(leaf.rel)))


def collect(vault: Vault, query: str | None = None, member: str | None = None, reported: bool = False) -> tuple[list[Entry], int]:
    """Matching statements, oldest first per member, with the number of reported ones left out."""
    dates = source_dates(vault)
    query_words = _words(query or "")
    entries: dict[tuple[str, str, str], Entry] = {}
    skipped = 0
    for leaf in read_leaves(vault):
        by_path = bool(query) and leaf_matches(leaf, query)
        for s in leaf.statements:
            if member and s.by != member:
                continue
            if query and not by_path and not ("/" not in query and _has_words(query_words, set(_words(s.text)))):
                continue
            if s.reported and not reported:
                skipped += 1
                continue
            key = (s.by, s.source, normalize(s.text))
            entry = entries.setdefault(key, Entry(dates.get(s.source, ""), s))
            if leaf.rel not in entry.leaves:
                entry.leaves.append(leaf.rel)
    rank = {m.id: i for i, m in enumerate(vault.members)}
    order = sorted(
        entries.values(),
        key=lambda e: (rank.get(e.statement.by, len(rank)), e.statement.by, e.date or "9999", e.statement.source, e.statement.seconds),
    )
    return order, skipped


def _n(count: int, word: str) -> str:
    return f"{count} {word}{'' if count == 1 else 's'}"


def render(vault: Vault, entries: list[Entry], query: str | None = None, skipped: int = 0) -> str:
    names = {m.id: m.name for m in vault.members}
    what = f'"{query}"' if query else "all statements"
    sources = len({e.statement.source for e in entries})
    out = [f"{vault.config.get('name', vault.slug)}: {what}, {_n(len(entries), 'statement')} from {_n(sources, 'source')}, oldest first"]
    current = None
    for entry in entries:
        s = entry.statement
        if s.by != current:
            current = s.by
            count = sum(1 for e in entries if e.statement.by == s.by)
            out += ["", f"{s.by} ({names.get(s.by, 'not a member')}), {_n(count, 'statement')}"]
        out.append(f"  {entry.date or UNDATED:10}  \"{s.text}\" {s.cite()}")
        out.append(f"  {'':10}  {', '.join(entry.leaves)}")
    if skipped:
        out += ["", f"Left out {_n(skipped, 'reported statement')}, since reported statements relay someone else's view. Add --reported to see them."]
    if not entries:
        out.append("No statements match.")
    return "\n".join(out)

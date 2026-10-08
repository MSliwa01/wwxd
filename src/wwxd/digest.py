"""`wwxd digest`: a markdown note on what's new in a vault since a date."""

from __future__ import annotations

from dataclasses import dataclass, field

from wwxd.vault import Source, Vault
from wwxd.wikimap import Citation, Leaf, LogEntry, compile_log, read_leaves, source_dates


@dataclass
class Digest:
    name: str
    since: str
    compiled: list[tuple[LogEntry, Source | None]] = field(default_factory=list)
    updated: list[Leaf] = field(default_factory=list)
    statements: dict[str, list[tuple[str, Citation]]] = field(default_factory=dict)  # leaf -> [(source date, statement)]
    titles: dict[str, str] = field(default_factory=dict)
    reported: int = 0

    @property
    def new_statements(self) -> int:
        return sum(len(rows) for rows in self.statements.values())


def build(vault: Vault, since: str) -> Digest:
    digest = Digest(str(vault.config.get("name") or vault.slug), since)
    sources = {s.id: s for s in vault.load_sources()}
    latest: dict[str, LogEntry] = {}
    for entry in compile_log(vault):
        if entry.date >= since:
            latest.pop(entry.source, None)  # a recompile moves the source to its latest line
            latest[entry.source] = entry
    digest.compiled = [(entry, sources.get(entry.source)) for entry in latest.values()]

    dates = source_dates(vault)
    for leaf in read_leaves(vault):
        digest.titles[leaf.rel] = leaf.title
        if leaf.updated[:10] >= since:
            digest.updated.append(leaf)
        for s in leaf.statements:
            date = dates.get(s.source, "")
            if date and date >= since:
                if s.reported:
                    digest.reported += 1
                else:
                    digest.statements.setdefault(leaf.rel, []).append((date, s))
    for rows in digest.statements.values():
        rows.sort(key=lambda row: (row[0], row[1].source, row[1].seconds))
    return digest


def _n(count: int, word: str, plural: str = "") -> str:
    return f"{count} {word if count == 1 else plural or word + 's'}"


def render(d: Digest) -> str:
    sources = len({s.source for rows in d.statements.values() for _, s in rows})
    out = [
        f"# What's new in {d.name} since {d.since}",
        "",
        f"{_n(len(d.compiled), 'source')} compiled, {_n(len(d.updated), 'leaf', 'leaves')} created or updated, "
        f"{_n(d.new_statements, 'statement')} from {_n(sources, 'source')} dated on or after {d.since}.",
        "",
        "## Sources compiled",
        "",
    ]
    for entry, source in d.compiled:
        title = source.title if source and source.title else entry.source
        link = f"[{title}]({source.url})" if source and source.url.startswith("http") else title
        date = f", from {str(source.date)[:10]}" if source and source.date else ""
        note = f". {entry.note}" if entry.note else ""
        out.append(f"- {entry.date} {link} ([[{entry.source}]]{date}){note}")
    if not d.compiled:
        out.append("None.")

    out += ["", "## Leaves created or updated", ""]
    out += [f"- [[{leaf.rel}]] {leaf.title}" for leaf in sorted(d.updated, key=lambda leaf: leaf.rel)]
    if not d.updated:
        out.append("None.")

    out += ["", "## New statements", ""]
    if d.statements:
        out.append(f"Statements from sources dated on or after {d.since}, by leaf.")
    for rel in sorted(d.statements):
        out += ["", f"### [[{rel}]] {d.titles.get(rel, '')}".rstrip(), ""]
        out += [f"- {date} \"{s.text}\" {s.cite()}" for date, s in d.statements[rel]]
    if not d.statements:
        out.append("None.")
    if d.reported:
        out += ["", f"Left out {_n(d.reported, 'reported statement')}, since they relay someone else's view."]
    return "\n".join(out) + "\n"

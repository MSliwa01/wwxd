"""`wwxd health`: a compact report on how well a vault's wiki is holding together."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from wwxd.lint import MAX_STATEMENTS_PER_LEAF, index_warnings, overview_warnings
from wwxd.vault import Vault
from wwxd.wikimap import (
    DuplicatePair,
    Leaf,
    LogEntry,
    cited_sources,
    compile_log,
    last_consolidation,
    near_duplicates,
    read_leaves,
)

CONSOLIDATE_EVERY = 10  # compiled sources between consolidation passes (references/consolidate.md)
TOP_PAIRS = 5


@dataclass
class Health:
    name: str
    slug: str
    layout: str
    members: dict[str, str]  # id -> name
    leaves: list[Leaf]
    by_member: Counter = field(default_factory=Counter)
    conf: Counter = field(default_factory=Counter)
    reported: int = 0
    compiled: list[str] = field(default_factory=list)
    uncited_compiled: list[str] = field(default_factory=list)
    cited_not_compiled: list[str] = field(default_factory=list)
    duplicates: list[DuplicatePair] = field(default_factory=list)
    oversize: list[Leaf] = field(default_factory=list)
    stance_uncited: list[Leaf] = field(default_factory=list)
    missing_index: int = 0
    missing_overviews: int = 0
    single_leaf_topics: list[str] = field(default_factory=list)
    last_compile: LogEntry | None = None
    last_consolidated: str | None = None
    since_consolidation: int = 0

    @property
    def statements(self) -> int:
        return sum(len(leaf.statements) for leaf in self.leaves)

    @property
    def actions(self) -> int:
        return sum(len(leaf.actions) for leaf in self.leaves)

    @property
    def needs_consolidation(self) -> bool:
        return bool(
            self.duplicates or self.oversize or self.missing_index or self.missing_overviews
            or self.since_consolidation >= CONSOLIDATE_EVERY
        )


def check(vault: Vault) -> Health:
    leaves = read_leaves(vault)
    health = Health(
        name=str(vault.config.get("name") or vault.slug),
        slug=vault.slug,
        layout=vault.layout,
        members={m.id: m.name for m in vault.members},
        leaves=leaves,
    )
    for leaf in leaves:
        for s in leaf.statements:
            health.by_member[s.by] += 1
            health.conf[s.conf] += 1
            health.reported += s.reported
    sources = vault.load_sources()
    cited = cited_sources(vault)
    health.compiled = [s.id for s in sources if s.status == "compiled"]
    health.uncited_compiled = [sid for sid in health.compiled if sid not in cited]
    status = {s.id: s.status for s in sources}
    health.cited_not_compiled = sorted(sid for sid in cited if status.get(sid) != "compiled")
    health.duplicates = near_duplicates(leaves)
    health.oversize = sorted(
        (leaf for leaf in leaves if len(leaf.statements) > MAX_STATEMENTS_PER_LEAF),
        key=lambda leaf: (-len(leaf.statements), leaf.rel),
    )
    health.stance_uncited = [leaf for leaf in leaves if not leaf.stance_sources]
    health.missing_index = len(index_warnings(vault, leaves))
    health.missing_overviews = len(overview_warnings(vault))
    if vault.layout == "tree":
        per_topic = Counter(leaf.folder for leaf in leaves if leaf.folder.count("/") == 1)
        health.single_leaf_topics = sorted(topic for topic, n in per_topic.items() if n == 1)
    log = compile_log(vault)
    health.last_compile = log[-1] if log else None
    health.last_consolidated, health.since_consolidation = last_consolidation(vault)
    return health


def _n(count: int, word: str, plural: str = "") -> str:
    return f"{count} {word if count == 1 else plural or word + 's'}"


def _pct(part: int, whole: int) -> str:
    return f"{round(100 * part / whole)}%" if whole else "0%"


def render(h: Health) -> str:
    out = [f"{h.name} ({h.slug}), {h.layout} layout"]
    if h.last_compile:
        out.append(f"last compile    {h.last_compile.date} ({h.last_compile.source})")
    else:
        out.append("last compile    none in log.md")
    out.append(f"size            {len(h.leaves)} leaves, {h.statements} statements, {h.actions} actions")

    members = sorted(h.by_member.items(), key=lambda kv: (-kv[1], kv[0]))
    silent = [m for m in h.members if m not in h.by_member]
    parts = [f"{m} {n} ({_pct(n, h.statements)})" for m, n in members] + [f"{m} 0" for m in silent]
    out.append("by member       " + (", ".join(parts) or "no statements"))

    conf = [f"{c} {h.conf.get(c, 0)} ({_pct(h.conf.get(c, 0), h.statements)})" for c in ("high", "medium", "low")]
    out.append("confidence      " + ", ".join(conf) + f"; {h.reported} reported")

    cited = len(h.compiled) - len(h.uncited_compiled)
    out.append(f"sources         {len(h.compiled)} compiled, {cited} of them cited in the wiki")
    if h.uncited_compiled:
        out.append("  compiled, cited nowhere: " + ", ".join(h.uncited_compiled))
    if h.cited_not_compiled:
        out.append("  cited, not marked compiled: " + ", ".join(h.cited_not_compiled))

    out.append(f"near-duplicates {_n(len(h.duplicates), 'pair')}" + (f" (top {TOP_PAIRS})" if len(h.duplicates) > TOP_PAIRS else ""))
    for pair in h.duplicates[:TOP_PAIRS]:
        out.append(f"  {pair.score:.2f}  {pair.a.rel}")
        out.append(f"        {pair.b.rel}  ({pair.reason()})")

    out.append(f"oversize        {_n(len(h.oversize), 'leaf', 'leaves')} over {MAX_STATEMENTS_PER_LEAF} statements")
    out.extend(f"  {len(leaf.statements):>3}  {leaf.rel}" for leaf in h.oversize)

    out.append(f"stance uncited  {_n(len(h.stance_uncited), 'leaf', 'leaves')}")
    out.extend(f"  {leaf.rel}" for leaf in h.stance_uncited)

    structure = f"{_n(h.missing_index, 'leaf', 'leaves')} missing from index.md"
    if h.layout == "tree":
        structure += f", {h.missing_overviews} missing overviews, {len(h.single_leaf_topics)} single-leaf topics"
    out.append(f"structure       {structure}")

    if h.last_consolidated:
        out.append(f"consolidated    {h.last_consolidated}, {_n(h.since_consolidation, 'source')} compiled since")
    else:
        out.append(f"consolidated    never, {_n(h.since_consolidation, 'source')} compiled")
    if h.needs_consolidation:
        out.append("Run `wwxd lint` for details, then follow references/consolidate.md in the wwxd skill.")
    return "\n".join(out)

"""Read a vault's wiki into leaves and statements, and find leaves that overlap.

Shared by `wwxd lint` (structure warnings), `health`, `timeline` and `digest`.
Grammar: skill/references/format.md.
"""

from __future__ import annotations

import itertools
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from rapidfuzz import fuzz

from wwxd.lint import CITED_LINE, SECTION, STATEMENT, WIKILINK, _frontmatter, is_source_id, normalize, parse_citation
from wwxd.rawdoc import parse_timestamp
from wwxd.vault import Vault

SPECIAL_PAGES = ("index", "profile", "tensions")
LOG_COMPILED = re.compile(r"^- (?P<date>\d{4}-\d{2}-\d{2}) compiled (?P<id>[^\s:]+)(?::\s*(?P<note>.*))?$")
LOG_CONSOLIDATED = re.compile(r"^- (?P<date>\d{4}-\d{2}-\d{2}) consolidated\b")


@dataclass
class Citation:
    """One statement or action line in a leaf."""

    text: str  # the quote for statements, the paraphrase for actions
    source: str
    ts: str | None
    by: str
    conf: str
    reported: bool
    leaf: str  # leaf path relative to wiki/, without .md
    line: int

    @property
    def seconds(self) -> float:
        return parse_timestamp(self.ts) if self.ts else 0.0

    def cite(self) -> str:
        parts = [f"[[{self.source}]]" + (f" @ {self.ts}" if self.ts else ""), f"by: {self.by}", f"conf: {self.conf}"]
        if self.reported:
            parts.append("reported")
        return "(" + "; ".join(parts) + ")"


@dataclass
class Leaf:
    path: Path
    rel: str  # relative to wiki/, without .md, e.g. business/pricing/raising-prices
    title: str
    updated: str
    statements: list[Citation] = field(default_factory=list)
    actions: list[Citation] = field(default_factory=list)
    stance_sources: set[str] = field(default_factory=set)
    distinct_from: set[str] = field(default_factory=set)  # leaves reviewed and kept apart on purpose

    @property
    def folder(self) -> str:
        return self.rel.rsplit("/", 1)[0] if "/" in self.rel else ""

    @property
    def slug(self) -> str:
        return self.rel.rsplit("/", 1)[-1]


def _clean(text: str) -> str:
    # Same as lint: ignore commented-out examples but keep line numbers stable.
    return re.sub(r"<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.DOTALL)


def _is_leaf(page: Path, front: dict) -> bool:
    if front.get("type"):
        return front["type"] == "leaf"
    return page.stem not in SPECIAL_PAGES and page.stem != "_overview"


def _citation(cite_text: str, text: str, rel: str, line_no: int) -> Citation | None:
    cite = parse_citation(cite_text)
    if cite is None or not is_source_id(cite["src"]):
        return None
    return Citation(
        text=text,
        source=cite["src"],
        ts=cite["ts"],
        by=str(cite.get("by") or ""),
        conf=str(cite.get("conf") or ""),
        reported=bool(cite.get("reported")),
        leaf=rel,
        line=line_no,
    )


def read_leaf(page: Path, wiki: Path) -> Leaf | None:
    text = page.read_text(encoding="utf-8")
    front = _frontmatter(text)
    if not _is_leaf(page, front):
        return None
    rel = page.relative_to(wiki).with_suffix("").as_posix()
    heading = next((ln[2:].strip() for ln in text.splitlines() if ln.startswith("# ")), "")
    leaf = Leaf(page, rel, str(front.get("title") or heading or page.stem), str(front.get("updated") or ""))
    distinct = front.get("distinct_from") or []
    for target in [distinct] if isinstance(distinct, str) else distinct:
        leaf.distinct_from.add(str(target).strip().strip("[]").removeprefix("wiki/").removesuffix(".md"))
    section = ""
    for line_no, line in enumerate(_clean(text).splitlines(), 1):
        line = re.sub(r"`[^`]*`", "", line)
        match = SECTION.match(line)
        if match:
            section = match.group(1).lower()
            continue
        if section == "stance":
            leaf.stance_sources.update(t.strip() for t in WIKILINK.findall(line) if is_source_id(t.strip()))
        elif section == "statements" and (statement := STATEMENT.match(line)):
            if c := _citation(statement.group("cite"), statement.group("quote"), rel, line_no):
                leaf.statements.append(c)
        elif section == "actions" and line.startswith("- ") and (cited := CITED_LINE.search(line)):
            text_part = line[2 : cited.start()].strip()
            if c := _citation(cited.group("cite"), text_part, rel, line_no):
                leaf.actions.append(c)
    return leaf


def read_leaves(vault: Vault) -> list[Leaf]:
    leaves = (read_leaf(p, vault.wiki_dir) for p in sorted(vault.wiki_dir.rglob("*.md")))
    return [leaf for leaf in leaves if leaf is not None]


def cited_sources(vault: Vault) -> dict[str, set[str]]:
    """Every source id linked anywhere in wiki/, mapped to the pages that link it."""
    cited: dict[str, set[str]] = {}
    for page in sorted(vault.wiki_dir.rglob("*.md")):
        rel = page.relative_to(vault.wiki_dir).with_suffix("").as_posix()
        for target in WIKILINK.findall(_clean(page.read_text(encoding="utf-8"))):
            if is_source_id(target.strip()):
                cited.setdefault(target.strip(), set()).add(rel)
    return cited


def source_dates(vault: Vault) -> dict[str, str]:
    """Source id to ISO date from sources.yaml (unquoted YAML dates load as date objects)."""
    return {s.id: str(s.date)[:10] for s in vault.load_sources() if s.date}


@dataclass
class LogEntry:
    date: str
    source: str
    note: str


def compile_log(vault: Vault) -> list[LogEntry]:
    path = vault.path / "log.md"
    if not path.exists():
        return []
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if match := LOG_COMPILED.match(line.strip()):
            entries.append(LogEntry(match.group("date"), match.group("id"), match.group("note") or ""))
    return entries


def last_consolidation(vault: Vault) -> tuple[str | None, int]:
    """Date of the last `consolidated` line in log.md, and how many sources were compiled after it."""
    path = vault.path / "log.md"
    if not path.exists():
        return None, 0
    date, count = None, 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if match := LOG_CONSOLIDATED.match(line.strip()):
            date, count = match.group("date"), 0
        elif LOG_COMPILED.match(line.strip()):
            count += 1
    return date, count


# --- Near-duplicate leaves ------------------------------------------------------
#
# Two signals, tuned on two real vaults (yc: 96 leaves, hormozi: 85 leaves):
#
# 1. Names. Title and slug words, minus stopwords, lightly stemmed, weighted by how
#    rare each word is among the vault's leaf names (IDF), compared as a weighted
#    Dice score. rapidfuzz decides when two words are the same word. Plain
#    token_set_ratio on titles was noisy: "startup", "founder" and "yc" appear in
#    many YC titles, so a dozen unrelated pairs scored 80 or more. Weighting by
#    rarity keeps "personal ai system" or "one thing" meaningful and "startup" cheap.
# 2. Quotes. The same quote (same source, one text inside the other, or
#    partial_ratio >= 90) filed in both leaves. One shared quote is normal cross
#    filing (a dozen yc pairs share exactly one); a large share of the smaller leaf
#    is not.
#
# score = name + 0.6 * (repeated quotes / statements in the smaller leaf)
#         + 0.1 if both leaves sit in the same topic folder
# A pair is flagged at score >= 0.55, or with 3+ repeated quotes, or with 2+ that
# make up half the smaller leaf. At 0.55 the yc vault gets 4 flags and hormozi 2;
# the next pairs down (0.54 and lower) were different questions on close topics.

STOPWORDS = frozenset(
    """a about after all an and are as at be because before but by can could do does
    doing don dont for from get gets getting go has have how i if in into is it its
    just make makes making me more most my no not of on or our should so than that
    the their them then there these they this those to too use using vs was we what
    when where which who why will with would you your""".split()
)
SAME_FOLDER_BONUS = 0.10  # siblings with similar names usually answer the same question
QUOTE_WEIGHT = 0.6  # share of the smaller leaf's statements that the other leaf repeats
DUPLICATE_THRESHOLD = 0.55
SHARED_QUOTES_ALWAYS = 3  # this many repeated quotes is a duplicate whatever the names say
SHARED_QUOTES_HALF = 2  # ...and so is this many, when they make up half the smaller leaf
TOKEN_MATCH = 90  # rapidfuzz ratio for two words to count as the same word
QUOTE_MATCH = 90  # rapidfuzz partial_ratio for two quotes to count as the same quote


def _stem(word: str) -> str:
    for suffix in ("ing", "ies", "es", "ed", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            word = word[: -len(suffix)] + ("y" if suffix == "ies" else "")
            break
    if len(word) > 3 and word[-1] == word[-2]:
        word = word[:-1]  # getting -> gett -> get
    if len(word) > 3 and word.endswith("e"):
        word = word[:-1]  # make / making -> mak
    return word


def name_words(leaf: Leaf) -> dict[str, str]:
    """Stemmed content words of the title and slug, mapped to a readable form."""
    title = re.sub(r"\(.*?\)", " ", leaf.title.lower())  # "(and closing more)" is an aside, not the question
    title = re.sub(r"(?<=[a-z])-(?=[a-z])", "", title)  # co-founder -> cofounder, as in slugs
    words: dict[str, str] = {}
    for word in leaf.slug.lower().split("-") + re.findall(r"[a-z0-9]+", title):
        if word and word not in STOPWORDS:
            words.setdefault(_stem(word), word)
    return words


def _same_word(a: str, b: str) -> bool:
    return a == b or (min(len(a), len(b)) >= 5 and fuzz.ratio(a, b) >= TOKEN_MATCH)


def _shared_quotes(a: Leaf, b: Leaf, norm: dict[int, str]) -> int:
    by_source: dict[str, list[str]] = {}
    for s in b.statements:
        by_source.setdefault(s.source, []).append(norm[id(s)])
    shared = 0
    for s in a.statements:
        quote = norm[id(s)]
        for other in by_source.get(s.source, ()):
            short, long_ = sorted((quote, other), key=len)
            if short and (short in long_ or (len(short) >= 20 and fuzz.partial_ratio(short, long_) >= QUOTE_MATCH)):
                shared += 1
                break
    return shared


@dataclass
class DuplicatePair:
    a: Leaf
    b: Leaf
    score: float
    name_score: float
    shared_words: list[str]
    shared_quotes: int

    def reason(self) -> str:
        parts = []
        if self.shared_words:
            parts.append("names share " + ", ".join(self.shared_words))
        if self.shared_quotes:
            smaller = min(len(self.a.statements), len(self.b.statements))
            parts.append(f"{self.shared_quotes} of {smaller} quotes repeated")
        if self.a.folder == self.b.folder:
            parts.append("same folder")
        return "; ".join(parts)


def near_duplicates(leaves: list[Leaf], threshold: float = DUPLICATE_THRESHOLD) -> list[DuplicatePair]:
    """Leaf pairs that probably answer the same question, best first."""
    words = [name_words(leaf) for leaf in leaves]
    df = Counter(w for ws in words for w in ws)
    n = len(leaves)
    idf = {w: math.log((n + 1) / (count + 0.5)) for w, count in df.items()}
    norm = {id(s): normalize(s.text) for leaf in leaves for s in leaf.statements}
    pairs = []
    for (i, a), (j, b) in itertools.combinations(enumerate(leaves), 2):
        if a.rel in b.distinct_from or b.rel in a.distinct_from:
            continue
        shared_a = {w for w in words[i] if any(_same_word(w, v) for v in words[j])}
        shared_b = {w for w in words[j] if any(_same_word(w, v) for v in words[i])}
        total = sum(idf[w] for w in words[i]) + sum(idf[w] for w in words[j])
        name_score = (sum(idf[w] for w in shared_a) + sum(idf[w] for w in shared_b)) / total if total else 0.0
        shared = _shared_quotes(a, b, norm) if a.statements and b.statements else 0
        smaller = min(len(a.statements), len(b.statements)) or 1
        score = name_score + QUOTE_WEIGHT * shared / smaller + (SAME_FOLDER_BONUS if a.folder == b.folder else 0.0)
        if (
            score >= threshold
            or shared >= SHARED_QUOTES_ALWAYS
            or (shared >= SHARED_QUOTES_HALF and shared * 2 >= smaller)
        ):
            shown = sorted({words[i][w] for w in shared_a} | {words[j][w] for w in shared_b if w not in shared_a})
            pairs.append(DuplicatePair(a, b, round(score, 2), name_score, shown, shared))
    return sorted(pairs, key=lambda p: (-p.score, p.a.rel, p.b.rel))

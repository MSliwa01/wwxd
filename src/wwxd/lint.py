"""Mechanical checks for a vault. Grammar: skill/references/format.md."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml
from rapidfuzz import fuzz

from wwxd import rawdoc
from wwxd.rawdoc import format_timestamp, parse_timestamp
from wwxd.vault import SOURCE_PREFIXES, TIMESTAMPED_PREFIXES, Vault

WIKILINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
STATEMENT = re.compile(r'^- "(?P<quote>.+)" \((?P<cite>\[\[[^\]]+\]\][^()]*)\)\s*$')
CITATION = re.compile(
    r"^\[\[(?P<src>[^\]]+)\]\](?:\s*@\s*(?P<ts>\d+(?::\d{2}){1,2}))?(?P<attrs>(?:\s*;\s*[^;]+)*)$"
)
INLINE_QUOTE = re.compile(
    r'"(?P<quote>[^"]+)" \((?P<cite>\[\[(?:' + "|".join(SOURCE_PREFIXES) + r')[^\]]+\]\][^()]*)\)'
)
CITED_LINE = re.compile(r"\((?P<cite>\[\[(?:" + "|".join(SOURCE_PREFIXES) + r")[^\]]+\]\][^()]*)\)")
SECTION = re.compile(r"^##\s+(.+?)\s*$")
CONFIDENCES = ("high", "medium", "low")
MATCH_THRESHOLD = 90
MAX_STATEMENTS_PER_LEAF = 15


@dataclass
class Issue:
    level: str  # error | warning
    path: str
    line: int
    message: str

    def __str__(self) -> str:
        return f"{self.level.upper():7} {self.path}:{self.line}  {self.message}"


def normalize(text: str) -> str:
    text = re.sub(r"\[[a-z ]+\]", " ", text.lower())  # caption tags: [laughter], [music], [snorts]
    text = text.replace("’", "'").replace("'", "")
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def is_source_id(target: str) -> bool:
    return target.startswith(SOURCE_PREFIXES)


def parse_citation(cite: str) -> dict | None:
    match = CITATION.match(cite.strip())
    if not match:
        return None
    attrs: dict[str, str | bool] = {}
    for part in match.group("attrs").split(";"):
        part = part.strip()
        if not part:
            continue
        if ":" in part:
            key, value = part.split(":", 1)
            attrs[key.strip()] = value.strip()
        else:
            attrs[part] = True
    return {"src": match.group("src").strip(), "ts": match.group("ts"), **attrs}


class RawIndex:
    """Normalized raw docs, loaded lazily, for quote lookup."""

    def __init__(self, vault: Vault):
        self.vault = vault
        self._cache: dict[str, tuple[list[tuple[float, str]], str]] = {}
        # sources.yaml, not the raw doc, so the user can correct who appears in a source.
        self._speakers = {s.id: s.expected_speakers for s in vault.load_sources()}

    def expected_speakers(self, source_id: str) -> list[str]:
        return self._speakers.get(source_id, [])

    def exists(self, source_id: str) -> bool:
        return self.vault.raw_path(source_id).exists()

    def get(self, source_id: str) -> tuple[list[tuple[float, str]], str]:
        if source_id not in self._cache:
            doc = rawdoc.read(self.vault.raw_path(source_id))
            chunks = [(s.start, normalize(s.text)) for s in doc.segments]
            full = " ".join(c for _, c in chunks) if chunks else normalize(doc.body)
            self._cache[source_id] = (chunks, full)
        return self._cache[source_id]

    def locate(self, source_id: str, quote: str, ts: str | None) -> tuple[str, str]:
        """Return (verdict, detail). verdict: ok | moved | missing."""
        chunks, full = self.get(source_id)
        parts = [normalize(p) for p in re.split(r"\.\.\.|…", quote)]
        parts = [p for p in parts if p]
        if not parts:
            return "missing", "empty quote"
        target = parse_timestamp(ts) if ts else None
        worst = "ok"
        details = []
        for part in parts:
            if target is not None and chunks:
                window = " ".join(c for start, c in chunks if target - 120 <= start <= target + 60)
                if part in window or fuzz.partial_ratio(part, window) >= MATCH_THRESHOLD:
                    continue
            elif part in full or fuzz.partial_ratio(part, full) >= MATCH_THRESHOLD:
                continue
            # Not near the timestamp: look everywhere so we can say where it is.
            best_score, best_start = 0.0, None
            for i, (start, _) in enumerate(chunks):
                window = " ".join(c for _, c in chunks[max(0, i - 1) : i + 2])
                score = 100.0 if part in window else fuzz.partial_ratio(part, window)
                if score > best_score:
                    best_score, best_start = score, start
            if best_score >= MATCH_THRESHOLD and best_start is not None:
                worst = "moved" if worst == "ok" else worst
                details.append(f"found near {format_timestamp(best_start)}, not @ {ts}")
            else:
                worst = "missing"
                details.append(f'not found in {source_id}: "{part[:60]}"')
        return worst, "; ".join(details)


def _frontmatter(text: str) -> dict:
    if not text.startswith("---\n"):
        return {}
    try:
        return yaml.safe_load(text.split("---\n", 2)[1]) or {}
    except yaml.YAMLError:
        return {}


def _page_index(wiki: Path) -> set[str]:
    names: set[str] = set()
    for page in wiki.rglob("*.md"):
        rel = page.relative_to(wiki).with_suffix("").as_posix()
        names.add(rel)
        names.add(page.stem)
    return names


def lint(vault: Vault) -> list[Issue]:
    issues: list[Issue] = []
    raw = RawIndex(vault)
    member_ids = {m.id for m in vault.members}
    pages = _page_index(vault.wiki_dir)
    linked: set[str] = set()

    for page in sorted(vault.wiki_dir.rglob("*.md")):
        rel = page.relative_to(vault.path).as_posix()
        text = page.read_text(encoding="utf-8")
        front = _frontmatter(text)
        # Ignore commented-out examples, but keep line numbers stable.
        text = re.sub(r"<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.DOTALL)
        section = ""
        statements = 0
        stance_cited = False

        def add(level: str, line_no: int, message: str) -> None:
            issues.append(Issue(level, rel, line_no, message))

        for line_no, line in enumerate(text.splitlines(), 1):
            line = re.sub(r"`[^`]*`", "", line)  # inline code is an example, not a link
            heading = SECTION.match(line)
            if heading:
                section = heading.group(1).lower()
                continue

            for target in WIKILINK.findall(line):
                target = target.strip()
                if target.startswith("derived/") or (vault.derived_dir / f"{target}.md").exists():
                    add("error", line_no, f"links to derived page [[{target}]]: derived pages are never evidence")
                elif is_source_id(target):
                    if not raw.exists(target):
                        add("error", line_no, f"cites missing raw doc [[{target}]]")
                    elif section == "stance":
                        stance_cited = True
                else:
                    linked.add(target)
                    if target not in pages:
                        add("warning", line_no, f"broken page link [[{target}]]")

            statement = STATEMENT.match(line)
            in_statements = section == "statements"
            if in_statements and line.startswith("- ") and not statement:
                add("error", line_no, "statement doesn't match the grammar (see references/format.md)")
                continue
            if statement:
                statements += in_statements
                _check_statement(statement, line_no, add, raw, member_ids, check_quote=True)
                continue
            # Quotes woven into prose (stance, caveats, profile, tensions) are checked too.
            inline = list(INLINE_QUOTE.finditer(line))
            for match in inline:
                _check_statement(match, line_no, add, raw, member_ids, check_quote=True)
            if not inline and section == "actions" and line.startswith("- "):
                cite = CITED_LINE.search(line)
                if not cite:
                    add("warning", line_no, "action without a source citation")
                else:
                    _check_statement(cite, line_no, add, raw, member_ids, check_quote=False)

        if front.get("type") == "leaf":
            if statements == 0:
                add("warning", 1, "leaf has no statements")
            if not stance_cited:
                add("warning", 1, "stance cites no sources")
            if statements > MAX_STATEMENTS_PER_LEAF:
                add("warning", 1, f"{statements} statements: consider splitting this leaf")

    for page in sorted(vault.wiki_dir.rglob("*.md")):
        rel_name = page.relative_to(vault.wiki_dir).with_suffix("").as_posix()
        if rel_name in ("index",) or page.stem == "_overview":
            continue
        if rel_name not in linked and page.stem not in linked:
            issues.append(Issue("warning", page.relative_to(vault.path).as_posix(), 1, "orphan page: nothing links here (add it to index.md)"))
    return issues


def _check_statement(match: re.Match, line_no: int, add, raw: RawIndex, member_ids: set[str], *, check_quote: bool) -> None:
    cite = parse_citation(match.group("cite"))
    if cite is None:
        add("error", line_no, f"malformed citation: ({match.group('cite')})")
        return
    src, ts = cite["src"], cite["ts"]
    if not is_source_id(src):
        add("error", line_no, f"[[{src}]] is not a source id")
        return
    if not raw.exists(src):
        return  # already reported by the link check
    if src.startswith(TIMESTAMPED_PREFIXES) and not ts:
        add("error", line_no, f"[[{src}]] is timestamped: add '@ m:ss'")
    by = cite.get("by")
    if not by:
        add("error", line_no, "missing 'by: <member-id>'")
    elif by not in member_ids:
        add("error", line_no, f"by: {by} is not a member of this vault ({', '.join(sorted(member_ids))})")
    elif (expected := raw.expected_speakers(src)) and by not in expected:
        add("warning", line_no, f"by: {by} isn't an expected speaker of {src} ({', '.join(expected)}); "
            "fix the attribution or add them to expected_speakers in sources.yaml")
    conf = cite.get("conf")
    if conf not in CONFIDENCES:
        add("error", line_no, "missing or invalid 'conf: high|medium|low'")
    elif conf == "low":
        add("warning", line_no, "low-confidence attribution: drop it or find a better source")
    if check_quote:
        verdict, detail = raw.locate(src, match.group("quote"), ts)
        if verdict == "missing":
            add("error", line_no, f"quote not in source: {detail}")
        elif verdict == "moved":
            add("warning", line_no, f"quote timestamp off: {detail}")

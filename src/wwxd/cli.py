from __future__ import annotations

import logging
import re
import shutil
import time
from collections import Counter
from importlib import resources
from pathlib import Path
from typing import Annotated

import typer

from wwxd import __version__
from wwxd.config import get_settings
from wwxd.vault import STATUSES, Source, Vault, create_vault, example_config, list_examples, resolve_vault

app = typer.Typer(
    help="What would X do? Build a cited knowledge wiki of anyone's thinking.",
    no_args_is_help=True,
    add_completion=False,
)
bench_app = typer.Typer(help="Benchmark answers against a gold question set.", no_args_is_help=True)
app.add_typer(bench_app, name="bench")

VaultArg = Annotated[str, typer.Argument(help="Vault slug (under $WWXD_HOME, default ./vaults) or path")]


def _vault(name: str) -> Vault:
    try:
        return resolve_vault(name)
    except FileNotFoundError as exc:
        typer.secho(str(exc), fg="red", err=True)
        raise typer.Exit(1) from exc


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


@app.callback()
def main(verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False) -> None:
    logging.basicConfig(level=logging.INFO if verbose else logging.WARNING, format="%(levelname)s %(message)s")


@app.command()
def version() -> None:
    """Print the version."""
    typer.echo(__version__)


@app.command()
def examples() -> None:
    """List bundled example recipes (source configs only, no content)."""
    for name in list_examples():
        typer.echo(name)


@app.command()
def new(
    slug: Annotated[str, typer.Argument(help="Short id, e.g. 'hormozi'")],
    name: Annotated[str | None, typer.Option(help="Full name, e.g. 'Alex Hormozi'")] = None,
    example: Annotated[str | None, typer.Option(help="Start from a bundled recipe (see `wwxd examples`)")] = None,
) -> None:
    """Create a vault."""
    if example:
        config = example_config(example)
    else:
        if not name:
            typer.secho("Pass --name 'Full Name' or --example <recipe>.", fg="red", err=True)
            raise typer.Exit(1)
        template = (resources.files("wwxd") / "templates" / "custom_vault.yaml").read_text(encoding="utf-8")
        config = template.replace("{{name}}", name).replace("{{slug}}", _slugify(slug))
    path = get_settings().home / slug
    try:
        create_vault(path, config)
    except FileExistsError as exc:
        typer.secho(str(exc), fg="red", err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"Created {path}")
    typer.echo(f"Next: edit {path / 'vault.yaml'} (channels, feeds), then `wwxd discover {slug}`.")


@app.command()
def discover(vault: VaultArg, per_query: Annotated[int | None, typer.Option()] = None) -> None:
    """Find candidate sources and add them to sources.yaml as `candidate`."""
    from wwxd.discover import discover as run_discover

    v = _vault(vault)
    new_sources, errors = run_discover(v, per_query=per_query)
    v.save_sources(v.load_sources() + new_sources)
    for error in errors:
        typer.secho(f"skipped {error}", fg="yellow", err=True)
    counts = Counter(s.hint for s in new_sources)
    typer.echo(f"{len(new_sources)} new candidates: " + ", ".join(f"{k}={n}" for k, n in counts.most_common()))
    if new_sources:
        typer.echo(f"Review them with `wwxd sources {vault} --status candidate`, then approve/reject.")
        v.append_log(f"discovered {len(new_sources)} candidates")


@app.command()
def update(vault: VaultArg) -> None:
    """Re-run discovery to pick up new material. Same as `discover`; nothing is fetched."""
    discover(vault)


@app.command()
def sources(
    vault: VaultArg,
    status: Annotated[str | None, typer.Option(help=f"Filter: {', '.join(STATUSES)}")] = None,
    hint: Annotated[str | None, typer.Option(help="Filter: own, channel, appearance, maybe-about, unknown, manual")] = None,
) -> None:
    """List sources."""
    v = _vault(vault)
    rows = [s for s in v.load_sources() if (not status or s.status == status) and (not hint or s.hint == hint)]
    for s in rows:
        minutes = f"{int(s.duration // 60)}m" if s.duration else "-"
        speakers = ",".join(s.expected_speakers) or "-"
        typer.echo(f"{s.id:22} {s.status:9} {s.hint:11} {minutes:>5} {speakers:14} {s.channel[:20]:20} {s.title[:70]}")
    typer.echo(f"({len(rows)} sources)", err=True)


def _set_status(v: Vault, ids: list[str], hints: list[str], status: str, allowed_from: tuple[str, ...]) -> int:
    all_sources = v.load_sources()
    changed = 0
    for s in all_sources:
        if s.status in allowed_from and (s.id in ids or s.hint in hints or "all" in ids):
            s.status = status
            changed += 1
    v.save_sources(all_sources)
    return changed


@app.command()
def approve(
    vault: VaultArg,
    ids: Annotated[list[str] | None, typer.Argument(help="Source ids, or 'all'")] = None,
    hint: Annotated[list[str] | None, typer.Option(help="Approve every candidate with this hint")] = None,
) -> None:
    """Approve candidates for fetching."""
    v = _vault(vault)
    n = _set_status(v, ids or [], hint or [], "approved", ("candidate", "rejected"))
    typer.echo(f"Approved {n}")


@app.command()
def reject(
    vault: VaultArg,
    ids: Annotated[list[str] | None, typer.Argument(help="Source ids, or 'all'")] = None,
    hint: Annotated[list[str] | None, typer.Option(help="Reject every candidate with this hint")] = None,
) -> None:
    """Reject candidates. Rejected ids are never re-added by discovery."""
    v = _vault(vault)
    n = _set_status(v, ids or [], hint or [], "rejected", ("candidate", "approved", "failed"))
    typer.echo(f"Rejected {n}")


@app.command()
def add(
    vault: VaultArg,
    target: Annotated[str, typer.Argument(help="YouTube URL, article URL, podcast audio URL, or local .txt/.md path")],
    title: Annotated[str, typer.Option()] = "",
    date: Annotated[str, typer.Option(help="YYYY-MM-DD, for files without metadata")] = "",
    speaker: Annotated[list[str] | None, typer.Option(help="Member id expected in this source")] = None,
    podcast: Annotated[bool, typer.Option(help="Treat the URL as podcast audio")] = False,
) -> None:
    """Add a source by hand (already approved)."""
    from wwxd.discover import web_id

    v = _vault(vault)
    speakers = speaker or ([v.members[0].id] if len(v.members) == 1 else [])
    yt = re.search(r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)([\w-]{11})", target)
    if yt:
        source = Source(id=f"yt-{yt.group(1)}", type="youtube", url=f"https://www.youtube.com/watch?v={yt.group(1)}")
    elif target.startswith(("http://", "https://")):
        if podcast:
            source = Source(id=web_id(target).replace("web-", "pod-"), type="podcast", url=target)
        else:
            source = Source(id=web_id(target), type="web", url=target)
    else:
        path = Path(target).expanduser().resolve()
        if not path.is_file():
            typer.secho(f"Not a file: {path}", fg="red", err=True)
            raise typer.Exit(1)
        source = Source(id=f"file-{_slugify(path.stem)[:40]}", type="file", url=str(path))
    source.title, source.date, source.status, source.hint = title, date, "approved", "manual"
    source.expected_speakers = speakers
    existing = v.load_sources()
    if any(s.id == source.id for s in existing):
        typer.echo(f"{source.id} already exists")
        return
    v.save_sources(existing + [source])
    typer.echo(f"Added {source.id} (approved). Run `wwxd fetch {vault}`.")


@app.command()
def fetch(
    vault: VaultArg,
    ids: Annotated[list[str] | None, typer.Argument(help="Only these ids")] = None,
    whisper: Annotated[str, typer.Option(help="auto (fallback when no captions) | always | never")] = "auto",
    limit: Annotated[int | None, typer.Option(help="Fetch at most N sources")] = None,
    retry_failed: Annotated[bool, typer.Option(help="Also retry sources that failed before")] = False,
    force: Annotated[bool, typer.Option(help="Re-fetch the given ids even if already fetched")] = False,
) -> None:
    """Download approved sources into raw/ (captions first, Whisper fallback)."""
    from wwxd import fetchers, rawdoc

    v = _vault(vault)
    all_sources = v.load_sources()
    wanted = ("approved", "failed") if retry_failed else ("approved",)
    if force and ids:
        wanted = (*wanted, "fetched", "compiled", "failed")
    todo = [s for s in all_sources if s.status in wanted and (not ids or s.id in ids)][:limit]
    if not todo:
        typer.echo("Nothing to fetch. Approve candidates first (`wwxd approve`).")
        return
    delay = get_settings().download_delay
    done = 0
    for i, source in enumerate(todo, 1):
        typer.echo(f"[{i}/{len(todo)}] {source.id} {source.title[:60]}")
        try:
            doc = fetchers.fetch(source, v, whisper=whisper)
            rawdoc.write(doc, v.raw_path(source.id))
            source.status, source.error = "fetched", ""
            source.date = str(doc.meta.get("date") or source.date or "")  # the fetcher saw the page; it knows better
            source.title = source.title or str(doc.meta.get("title") or "")
            done += 1
            typer.echo(f"    -> raw/{source.id}.md ({doc.meta.get('transcript')})")
        except Exception as exc:
            source.status, source.error = "failed", str(exc)[:300]
            typer.secho(f"    failed: {exc}", fg="red", err=True)
        v.save_sources(all_sources)
        if source.type == "youtube" and i < len(todo):
            time.sleep(delay)
    if done:
        v.append_log(f"fetched {done} sources")
    typer.echo(f"Fetched {done}/{len(todo)}. Compile them with the wwxd skill (`wwxd pending {vault}`).")


@app.command()
def pending(vault: VaultArg) -> None:
    """List fetched sources that haven't been compiled into the wiki yet."""
    v = _vault(vault)
    for s in v.load_sources():
        if s.status == "fetched":
            typer.echo(f"{v.raw_path(s.id)}\t{s.date or '-'}\t{s.title[:80]}")


@app.command("mark-compiled")
def mark_compiled(
    vault: VaultArg,
    source_id: str,
    note: Annotated[str, typer.Option(help="What changed, for log.md")] = "",
) -> None:
    """Mark a source as compiled and log it."""
    v = _vault(vault)
    all_sources = v.load_sources()
    match = next((s for s in all_sources if s.id == source_id), None)
    if match is None:
        typer.secho(f"Unknown source {source_id}", fg="red", err=True)
        raise typer.Exit(1)
    match.status = "compiled"
    v.save_sources(all_sources)
    v.append_log(f"compiled {source_id}" + (f": {note}" if note else ""))
    typer.echo(f"{source_id} compiled")


@app.command()
def lint(vault: VaultArg, warnings: Annotated[bool, typer.Option(help="Show warnings")] = True) -> None:
    """Check citations, quotes, attribution and links. Exits 1 on errors."""
    from wwxd.lint import lint as run_lint

    v = _vault(vault)
    issues = run_lint(v)
    errors = [i for i in issues if i.level == "error"]
    for issue in issues:
        if issue.level == "error" or warnings:
            typer.secho(str(issue), fg="red" if issue.level == "error" else "yellow")
    typer.echo(f"{len(errors)} errors, {len(issues) - len(errors)} warnings")
    if errors:
        raise typer.Exit(1)


@app.command()
def search(
    vault: VaultArg,
    query: str,
    raw: Annotated[bool, typer.Option(help="Also search raw transcripts")] = False,
    limit: int = 10,
) -> None:
    """Keyword search over the wiki (and optionally raw docs)."""
    from wwxd.search import search as run_search

    v = _vault(vault)
    for hit in run_search(v, query, include_raw=raw, limit=limit):
        typer.echo(f"{hit.path.relative_to(v.path)}  ({hit.title})\n    {hit.snippet}")


@app.command()
def status(vault: VaultArg) -> None:
    """Summary of a vault."""
    v = _vault(vault)
    counts = Counter(s.status for s in v.load_sources())
    leaves = [p for p in v.wiki_dir.rglob("*.md") if p.stem not in ("index", "profile", "tensions", "_overview")]
    typer.echo(f"{v.config.get('name', v.slug)}  ({v.path})")
    typer.echo(f"members: {', '.join(m.id for m in v.members)}   layout: {v.layout}")
    typer.echo("sources: " + ", ".join(f"{k}={counts.get(k, 0)}" for k in STATUSES))
    typer.echo(f"wiki pages: {len(leaves)} (+ index/profile/tensions)")


@app.command("install-skill")
def install_skill(
    project: Annotated[bool, typer.Option(help="Install into ./.claude/skills instead of ~/.claude/skills")] = False,
    force: Annotated[bool, typer.Option(help="Overwrite an existing install")] = False,
) -> None:
    """Install the wwxd skill for Claude Code."""
    base = Path.cwd() / ".claude" / "skills" if project else Path.home() / ".claude" / "skills"
    target = base / "wwxd"
    if target.exists():
        if not force:
            typer.secho(f"{target} exists; pass --force to overwrite.", fg="yellow", err=True)
            raise typer.Exit(1)
        shutil.rmtree(target)
    skill = resources.files("wwxd") / "skill"  # the wheel ships skills/wwxd here
    if not skill.is_dir():  # editable install or source checkout
        skill = Path(__file__).resolve().parents[2] / "skills" / "wwxd"
    with resources.as_file(skill) as src:
        shutil.copytree(src, target)
    typer.echo(f"Installed skill to {target}")


@bench_app.command("run")
def bench_run(
    vault: VaultArg,
    gold: Annotated[Path, typer.Option(help="Gold questions YAML")],
    arm: Annotated[str, typer.Option(help="Arm name, e.g. raw or wwxd")],
    prompt: Annotated[Path, typer.Option(help="Prompt template ({{question}}, {{vault}}, {{slug}})")],
    agent: Annotated[str, typer.Option(help="Agent command; '{prompt}' placeholder or stdin")] = "claude -p {prompt}",
    cwd: Annotated[Path | None, typer.Option(help="Working dir for the agent (default: vault's parent)")] = None,
    out: Annotated[Path, typer.Option(help="Results dir")] = Path("bench/results"),
    jobs: Annotated[int, typer.Option(help="Questions in parallel")] = 4,
) -> None:
    """Answer every gold question through one arm. Re-running resumes."""
    from wwxd import bench

    v = _vault(vault)
    arm_dir = out / v.slug / arm
    path = bench.run_arm(v, gold, prompt, arm_dir, agent=agent, cwd=(cwd or v.path.parent).resolve(), jobs=jobs)
    typer.echo(f"Answers: {path}")


@bench_app.command("judge")
def bench_judge(
    vault: VaultArg,
    gold: Annotated[Path, typer.Option()],
    a: Annotated[str, typer.Option(help="First arm name")],
    b: Annotated[str, typer.Option(help="Second arm name")],
    prompt: Annotated[Path, typer.Option(help="Pairwise judge prompt")] = Path("bench/prompts/judge_pairwise.md"),
    agent: Annotated[str, typer.Option()] = "claude -p {prompt}",
    cwd: Annotated[Path | None, typer.Option(help="Working dir for the judge (default: the vault, so it can check raw/)")] = None,
    out: Annotated[Path, typer.Option()] = Path("bench/results"),
    jobs: Annotated[int, typer.Option()] = 4,
) -> None:
    """Blind pairwise judging of two arms (order shuffled, citations stripped)."""
    from wwxd import bench

    v = _vault(vault)
    base = out / v.slug
    path = bench.judge_pairs(v, gold, base / a, base / b, prompt, base / f"judge-{a}-vs-{b}.jsonl",
                             agent=agent, cwd=(cwd or v.path).resolve(), jobs=jobs)
    typer.echo(f"Judgments: {path}")


@bench_app.command("report")
def bench_report(
    vault: VaultArg,
    gold: Annotated[Path, typer.Option()],
    arms: Annotated[list[str], typer.Option("--arm", help="Arm names to include")],
    judgments: Annotated[Path | None, typer.Option()] = None,
    out: Annotated[Path, typer.Option()] = Path("bench/results"),
) -> None:
    """Mechanical quote check per arm, plus judge averages by category."""
    import json as _json

    from wwxd import bench

    v = _vault(vault)
    base = out / v.slug
    summary = bench.summarize(v, gold, [base / a for a in arms], judgments)
    (base / "summary.json").write_text(_json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    typer.echo(_json.dumps(summary, indent=2, ensure_ascii=False))

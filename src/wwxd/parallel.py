"""Compile several sources at once, one agent session per source.

Each session follows compile.md for its source and writes straight into the wiki,
like a one-at-a-time compile. compile.md's section on other sessions covers the
shared pages: search right before creating a leaf, make small edits to shared pages,
re-read and retry when an edit fails because the file changed, and fix lint errors
only in your own pages. `mark-compiled` writes sources.yaml under a lock, so
sessions finishing together don't drop each other's status.

We also tried splitting the work: parallel sessions extracting quotes into staging
files, then one session placing them into the wiki. Placing was nearly as slow and
expensive as extracting, so it was barely faster and cost about 50% more
(bench/RESULTS.md, "Parallel compile").
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path

from wwxd.vault import Vault

TOOLS = ["Read", "Write", "Edit", "Glob", "Grep", "Bash(wwxd:*)"]


def skill_dir() -> Path:
    """The skill shipped with this wwxd: wheel (wwxd/skill) or source checkout (skills/wwxd)."""
    packaged = resources.files("wwxd") / "skill"
    if packaged.is_dir():
        return Path(str(packaged))
    return Path(__file__).resolve().parents[2] / "skills" / "wwxd"


# --- Claims ---------------------------------------------------------------------
# A claim is a directory under .cache/claims; mkdir is atomic, so two workers can't
# take the same source. It holds the worker's process id, so claims left by a run
# that crashed can be cleared.


def claims_dir(vault: Vault) -> Path:
    return vault.cache_dir / "claims"


def _alive(pid: int) -> bool:
    if os.name == "nt":
        return True  # os.kill(pid, 0) would terminate the process on Windows; keep the claim
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def claim(vault: Vault, pid: int | None = None, skip: frozenset[str] | set[str] = frozenset()) -> str | None:
    """Claim the next fetched source nobody is compiling. Returns its id or None."""
    root = claims_dir(vault)
    root.mkdir(parents=True, exist_ok=True)
    for source in vault.load_sources():
        if source.status != "fetched" or source.id in skip:
            continue
        try:
            (root / source.id).mkdir()
        except FileExistsError:
            continue
        (root / source.id / "pid").write_text(str(pid or os.getpid()))
        return source.id
    return None


def release(vault: Vault, source_id: str) -> None:
    path = claims_dir(vault) / source_id
    (path / "pid").unlink(missing_ok=True)
    if path.exists():
        path.rmdir()


def clear_stale_claims(vault: Vault) -> list[str]:
    """Release claims whose process is gone. Returns the released ids."""
    root = claims_dir(vault)
    if not root.exists():
        return []
    released = []
    for path in sorted(root.iterdir()):
        try:
            pid = int((path / "pid").read_text())
        except (OSError, ValueError):
            pid = 0
        if not pid or not _alive(pid):
            release(vault, path.name)
            released.append(path.name)
    return released


# --- Agent sessions -------------------------------------------------------------


def compile_prompt(vault: Vault, source_id: str, skill: Path) -> str:
    return (
        f"Use the wwxd skill in {skill}. Read {skill}/SKILL.md, then references/format.md, "
        f"references/compile.md and references/thinking.md there. Compile source {source_id} into the vault at "
        f"{vault.path}, following compile.md, including its section on other sessions compiling at the same "
        "time: they are. Work autonomously and don't ask questions. Skip the wwxd estimate, wwxd voice and "
        f"wwxd health steps. When your pages pass lint, run `wwxd mark-compiled {vault.path} {source_id} "
        '--note "..."`.'
    )


def claude_command(prompt: str, model: str, effort: str, skill: Path) -> list[str]:
    # --strict-mcp-config: no MCP servers; a compile session only needs files and wwxd.
    cmd = ["claude", "-p", prompt, "--strict-mcp-config", "--permission-mode", "acceptEdits",
           "--allowedTools", *TOOLS, "--add-dir", str(skill), "--output-format", "json"]
    if model:
        cmd += ["--model", model]
    if effort:
        cmd += ["--effort", effort]
    return cmd


def template_command(template: str, prompt: str, model: str, effort: str) -> list[str]:
    """--agent-cmd for other agent CLIs, e.g. 'opencode run -m {model} {prompt}'."""
    return [part.format(prompt=prompt, model=model, effort=effort) for part in shlex.split(template)]


def run_session(cmd: list[str], cwd: Path, log: Path) -> tuple[int, float | None]:
    """Run one agent session; returns (exit code, reported cost in USD if any)."""
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("w") as out, log.with_suffix(".err").open("w") as err:
        code = subprocess.run(cmd, cwd=cwd, stdin=subprocess.DEVNULL, stdout=out, stderr=err).returncode
    try:
        cost = json.loads(log.read_text()).get("total_cost_usd")
    except (ValueError, OSError, AttributeError):
        cost = None
    return code, cost


# --- The run --------------------------------------------------------------------


@dataclass
class Options:
    jobs: int = 4
    model: str = "claude-sonnet-5-5"
    effort: str = "high"
    limit: int = 0  # compile at most this many sources (0: all)
    agent_cmd: str = ""  # command template instead of Claude Code


@dataclass
class Session:
    source_id: str
    seconds: float
    exit_code: int
    cost: float | None
    compiled: bool


@dataclass
class Report:
    sessions: list[Session] = field(default_factory=list)

    @property
    def cost(self) -> float:
        return sum(s.cost or 0 for s in self.sessions)


def run(vault: Vault, opts: Options, echo: Callable[[str], None] = print,
        runner: Callable[[list[str], Path, Path], tuple[int, float | None]] = run_session) -> Report:
    skill = skill_dir()
    logs = vault.cache_dir / "compile-logs"
    report = Report()
    lock = threading.Lock()
    budget = [opts.limit or 10**9]
    failed: set[str] = set()  # not retried in this run

    def command(prompt: str) -> list[str]:
        if opts.agent_cmd:
            return template_command(opts.agent_cmd, prompt, opts.model, opts.effort)
        return claude_command(prompt, opts.model, opts.effort, skill)

    def worker() -> None:
        while True:
            with lock:
                if budget[0] <= 0:
                    return
                source_id = claim(vault, skip=failed)
                if source_id is None:
                    return
                budget[0] -= 1
            start = time.monotonic()
            code, cost = runner(command(compile_prompt(vault, source_id, skill)), vault.path,
                                logs / f"{source_id}.json")
            status = next((s.status for s in vault.load_sources() if s.id == source_id), None)
            ok = status == "compiled"
            if not ok:
                with lock:
                    failed.add(source_id)
            release(vault, source_id)  # compiled, or free for a later run to retry
            session = Session(source_id, time.monotonic() - start, code, cost, ok)
            with lock:
                report.sessions.append(session)
                done = sum(s.compiled for s in report.sessions)
                price = f", ${cost:.2f}" if cost is not None else ""
                echo(f"[{done} compiled] {source_id}: {'compiled' if ok else 'FAILED, still ' + str(status)}"
                     f" ({session.seconds:.0f}s{price})")

    released = clear_stale_claims(vault)
    if released:
        echo(f"Released {len(released)} claims left by an earlier run.")
    jobs = max(1, opts.jobs)
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        for future in [pool.submit(worker) for _ in range(jobs)]:
            future.result()
    return report

import threading
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wwxd import parallel, rawdoc
from wwxd.cli import app, mark_compiled
from wwxd.lint import lint
from wwxd.rawdoc import RawDoc, Segment
from wwxd.vault import Source, create_vault

CONFIG = """name: Test Group
slug: test
layout: tree
members:
  - id: pg
    name: Paul Graham
"""

IDS = [f"yt-source{i:04d}" for i in range(6)]


@pytest.fixture
def vault(tmp_path: Path):
    v = create_vault(tmp_path / "test", CONFIG)
    for sid in IDS:
        rawdoc.write(RawDoc(meta={"id": sid, "type": "youtube"}, segments=[
            Segment(0, "So welcome."),
            Segment(31, "I think you can still start a startup on not much money."),
        ]), v.raw_path(sid))
    v.save_sources([Source(id=sid, type="youtube", url="u", status="fetched", expected_speakers=["pg"]) for sid in IDS])
    return v


def statuses(v):
    return {s.id: s.status for s in v.load_sources()}


def write_leaf(v, name, quote):
    leaf = v.wiki_dir / "startups" / f"{name}.md"
    leaf.parent.mkdir(parents=True, exist_ok=True)
    leaf.write_text(f'---\ntype: leaf\n---\n# {name}\n\n## Statements\n- "{quote}" '
                    f"([[{IDS[0]}]] @ 0:31; by: pg; conf: high)\n", encoding="utf-8")


# --- claims -----------------------------------------------------------------------


def test_claims_never_hand_out_a_source_twice(vault):
    got: list[str] = []
    lock = threading.Lock()

    def worker():
        while (sid := parallel.claim(vault)) is not None:
            with lock:
                got.append(sid)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(got) == IDS


def test_claim_skips_and_releases(vault):
    first = parallel.claim(vault, skip={IDS[0]})
    assert first == IDS[1]
    parallel.release(vault, first)
    assert parallel.claim(vault) == IDS[0]


def test_stale_claims_are_cleared(vault):
    parallel.claim(vault, pid=2**22 + 12345)  # no such process
    live = parallel.claim(vault)  # this process
    assert parallel.clear_stale_claims(vault) == [IDS[0]]
    assert (parallel.claims_dir(vault) / live).exists()


# --- sources.yaml under parallel writers -------------------------------------------


def test_parallel_mark_compiled_loses_nothing(vault):
    # CliRunner swaps sys.stdout and isn't thread-safe, so call the command directly.
    threads = [threading.Thread(target=mark_compiled, args=(str(vault.path), sid)) for sid in IDS]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert set(statuses(vault).values()) == {"compiled"}
    assert (vault.path / "log.md").read_text().count("compiled yt-source") == len(IDS)


# --- lint --only ---------------------------------------------------------------------


def test_lint_only_limits_to_given_pages(vault):
    write_leaf(vault, "good", "you can still start a startup on not much money")
    write_leaf(vault, "bad", "always raise as much money as you can")
    assert [i for i in lint(vault, only=["wiki/startups/good.md"]) if i.level == "error"] == []
    assert [i.path for i in lint(vault, only=["wiki/startups"]) if i.level == "error"] == ["wiki/startups/bad.md"]
    # Whole-wiki structure checks (overviews, index, near-duplicates) are skipped with --only.
    assert any("_overview.md" in i.path for i in lint(vault))
    assert not [i for i in lint(vault, only=["wiki/startups"]) if "_overview.md" in i.path]


def test_lint_only_accepts_leaf_paths(vault):
    write_leaf(vault, "bad", "always raise as much money as you can")
    result = CliRunner().invoke(app, ["lint", str(vault.path), "--only", "startups/bad.md", "--no-warnings"])
    assert result.exit_code == 1 and "wiki/startups/bad.md" in result.output


# --- the run -----------------------------------------------------------------------


def fake_agent(vault, fail: set[str] = frozenset()):
    """Stands in for Claude Code: marks its source compiled, unless told to fail."""
    calls = []
    lock = threading.Lock()
    running = [0, 0]  # now, max

    def runner(cmd, cwd, log):
        sid = cmd[2].split("Compile source ")[1].split()[0]
        with lock:
            calls.append(sid)
            running[0] += 1
            running[1] = max(running)
        import time
        time.sleep(0.02)
        if sid not in fail:
            mark_compiled(str(vault.path), sid)
        with lock:
            running[0] -= 1
        return 0, 0.50

    return runner, calls, running


def test_run_compiles_everything_in_parallel(vault):
    runner, calls, running = fake_agent(vault)
    report = parallel.run(vault, parallel.Options(jobs=3), echo=lambda _: None, runner=runner)
    assert set(statuses(vault).values()) == {"compiled"}
    assert sorted(calls) == IDS  # each source once
    assert running[1] == 3
    assert report.cost == pytest.approx(0.50 * len(IDS))
    assert not list(parallel.claims_dir(vault).iterdir())


def test_run_doesnt_retry_failures_in_the_same_run(vault):
    runner, calls, _ = fake_agent(vault, fail={IDS[0]})
    report = parallel.run(vault, parallel.Options(jobs=2), echo=lambda _: None, runner=runner)
    assert statuses(vault)[IDS[0]] == "fetched"
    assert calls.count(IDS[0]) == 1
    assert [s.source_id for s in report.sessions if not s.compiled] == [IDS[0]]
    assert not (parallel.claims_dir(vault) / IDS[0]).exists()  # a later run can retry it


def test_run_respects_limit(vault):
    runner, calls, _ = fake_agent(vault)
    parallel.run(vault, parallel.Options(jobs=4, limit=2), echo=lambda _: None, runner=runner)
    assert len(calls) == 2
    assert list(statuses(vault).values()).count("compiled") == 2


def test_commands():
    skill = Path("/skill")
    cmd = parallel.claude_command("do it", "claude-sonnet-5-5", "high", skill)
    assert cmd[:3] == ["claude", "-p", "do it"]
    assert ["--model", "claude-sonnet-5-5"] == cmd[cmd.index("--model"):cmd.index("--model") + 2]
    assert "Bash(wwxd:*)" in cmd and str(skill) in cmd
    assert parallel.template_command("opencode run -m {model} {prompt}", "do it now", "m1", "high") == \
        ["opencode", "run", "-m", "m1", "do it now"]

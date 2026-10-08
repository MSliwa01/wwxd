from typer.testing import CliRunner

from wwxd.cli import app
from wwxd.digest import build, render
from tests.test_lint import SRC, vault  # noqa: F401  (fixture)
from tests.test_structure import CHEAP, TECH, leaf
from tests.test_timeline import OLD, dated  # noqa: F401  (fixture)


def test_digest_since_a_date(dated):  # noqa: F811
    leaf(dated, "startups/tech/costs", "Costs", TECH, index=False, updated="2026-09-01")
    leaf(dated, "startups/old/stale", "Stale", CHEAP, updated="2025-01-01")
    with (dated.path / "log.md").open("a") as fh:
        fh.write(f"- 2026-04-01 compiled {OLD}: +1 leaf\n- 2026-09-02 compiled {SRC}: +3 leaves, updated profile\n")

    d = build(dated, "2026-04-15")
    assert [entry.source for entry, _ in d.compiled] == [SRC]
    updated = sorted(leaf.rel for leaf in d.updated)
    assert updated == ["founders/drive/fear", "startups/money/cheap", "startups/tech/costs"]  # not the 2025 one
    # Statements from the 2026 source only; the 2014 source is older than --since.
    assert sorted(d.statements) == ["founders/drive/fear", "startups/money/cheap", "startups/old/stale", "startups/tech/costs"]
    assert all(s.source == SRC for rows in d.statements.values() for _, s in rows)

    text = render(d)
    assert text.startswith("# What's new in Test Group since 2026-04-15\n")
    assert f"- 2026-09-02 {SRC} ([[{SRC}]], from 2026-05-01). +3 leaves, updated profile" in text
    assert "- [[startups/tech/costs]] Costs" in text
    assert "### [[startups/tech/costs]] Costs" in text
    assert f'- 2026-05-01 "Everything technology always gets cheaper" ([[{SRC}]] @ 1:05; by: pg; conf: high)' in text


def test_digest_keeps_latest_compile_and_skips_reported(dated):  # noqa: F811
    with (dated.path / "log.md").open("a") as fh:
        fh.write(f"- 2026-09-01 compiled {OLD}: first\n- 2026-09-05 compiled {OLD}: again\n")
    d = build(dated, "2014-01-01")
    assert [(e.date, e.note) for e, _ in d.compiled] == [("2026-09-05", "again")]
    assert d.reported == 1 and "Left out 1 reported statement" in render(d)


def test_digest_cli(dated, tmp_path):  # noqa: F811
    out = tmp_path / "notes" / "digest.md"
    result = CliRunner().invoke(app, ["digest", str(dated.path), "--days", "36500", "--out", str(out)])
    assert result.exit_code == 0, result.output
    assert out.read_text().startswith("# What's new in Test Group since ")
    bad = CliRunner().invoke(app, ["digest", str(dated.path), "--since", "last week"])
    assert bad.exit_code == 1
    empty = CliRunner().invoke(app, ["digest", str(dated.path), "--since", "2099-01-01"])
    assert "0 sources compiled, 0 leaves created or updated" in empty.output

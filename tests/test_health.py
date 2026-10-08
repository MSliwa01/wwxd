from typer.testing import CliRunner

from wwxd.cli import app
from wwxd.health import check, render
from wwxd.vault import Source
from tests.test_lint import SRC, vault  # noqa: F401  (fixture)
from tests.test_structure import CHEAP, FEAR, TECH, leaf


def test_health_counts_and_flags(vault):  # noqa: F811
    vault.save_sources([Source(id=SRC, type="youtube", url="u", status="compiled", expected_speakers=["pg", "seibel"])])
    seibel = f'- "Everything technology always gets cheaper" ([[{SRC}]] @ 1:05; by: seibel; conf: medium; reported)'
    leaf(vault, "startups/money/cheap", "Starting cheap", "\n".join([CHEAP, TECH, seibel]))
    leaf(vault, "startups/money/big", "Big leaf", "\n".join([FEAR] * 16))
    stanceless = vault.wiki_dir / "startups" / "money" / "big.md"
    stanceless.write_text(stanceless.read_text().replace(f"See ([[{SRC}]]).", "No citation here."))
    with (vault.path / "log.md").open("a") as fh:
        fh.write(f"- 2026-09-01 compiled {SRC}: +2 leaves\n- 2026-09-02 consolidated: merged two leaves\n")
        fh.write(f"- 2026-09-03 compiled {SRC}\n")

    h = check(vault)
    assert (len(h.leaves), h.statements, h.actions) == (2, 19, 2)
    assert h.by_member == {"pg": 18, "seibel": 1}
    assert h.conf["high"] == 18 and h.conf["medium"] == 1 and h.reported == 1
    assert [leaf.rel for leaf in h.oversize] == ["startups/money/big"]
    assert [leaf.rel for leaf in h.stance_uncited] == ["startups/money/big"]
    assert h.compiled == [SRC] and h.uncited_compiled == []
    assert h.last_compile.date == "2026-09-03"
    assert (h.last_consolidated, h.since_consolidation) == ("2026-09-02", 1)
    assert h.missing_overviews == 2  # the startups domain and the money topic

    text = render(h)
    assert "size            2 leaves, 19 statements, 2 actions" in text
    assert "pg 18 (95%), seibel 1 (5%)" in text
    assert "   16  startups/money/big" in text
    assert "consolidated    2026-09-02, 1 source compiled since" in text
    assert "consolidate.md" in text


def test_health_lists_sources_cited_but_not_compiled(vault):  # noqa: F811
    leaf(vault, "startups/money/cheap", "Starting cheap", CHEAP)
    h = check(vault)
    assert h.compiled == [] and h.cited_not_compiled == [SRC]
    assert f"cited, not marked compiled: {SRC}" in render(h)


def test_health_cli(vault):  # noqa: F811
    leaf(vault, "startups/money/cheap", "Starting cheap", CHEAP)
    result = CliRunner().invoke(app, ["health", str(vault.path)])
    assert result.exit_code == 0, result.output
    assert "Test Group (test), tree layout" in result.output
    assert "last compile    none in log.md" in result.output

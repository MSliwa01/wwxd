import pytest
from typer.testing import CliRunner

from wwxd import rawdoc
from wwxd.cli import app
from wwxd.rawdoc import RawDoc, Segment
from wwxd.timeline import collect, render
from wwxd.vault import Source
from tests.test_lint import SRC, vault  # noqa: F401  (fixture)
from tests.test_structure import CHEAP, FEAR, TECH, leaf

OLD = "yt-oldoldoldol"


@pytest.fixture
def dated(vault):  # noqa: F811
    """Two sources: SRC from 2026, OLD from 2014."""
    doc = RawDoc(meta={"id": OLD, "type": "youtube"}, segments=[Segment(10, "Money is hard to raise. Start with very little money.")])
    rawdoc.write(doc, vault.raw_path(OLD))
    vault.save_sources([
        Source(id=SRC, type="youtube", url="u", status="compiled", date="2026-05-01", expected_speakers=["pg", "seibel"]),
        Source(id=OLD, type="youtube", url="o", status="compiled", date="2014-09-30", expected_speakers=["pg"]),
    ])
    old = f'- "Start with very little money." ([[{OLD}]] @ 0:10; by: pg; conf: high)'
    seibel = f'- "The fear of failure is what motivates founders" ([[{SRC}]] @ 2:00; by: seibel; conf: medium)'
    relayed = f'- "Money is hard to raise." ([[{OLD}]] @ 0:10; by: pg; conf: medium; reported)'
    leaf(vault, "startups/money/cheap", "Starting cheap", "\n".join([CHEAP, old, relayed]))
    leaf(vault, "founders/drive/fear", "Fear", "\n".join([FEAR, seibel, CHEAP]))
    leaf(vault, "startups/tech/costs", "Costs", TECH)
    return vault


def test_sorted_by_source_date_and_grouped_by_member(dated):
    entries, skipped = collect(dated)
    rows = [(e.statement.by, e.date, e.statement.text) for e in entries]
    assert rows[0] == ("pg", "2014-09-30", "Start with very little money.")
    assert [r[0] for r in rows] == ["pg", "pg", "pg", "pg", "seibel"]  # members in vault.yaml order
    assert [r[1] for r in rows if r[0] == "pg"] == sorted(r[1] for r in rows if r[0] == "pg")
    assert skipped == 1


def test_same_quote_in_two_leaves_is_listed_once(dated):
    entries, _ = collect(dated)
    cheap = [e for e in entries if e.statement.text.startswith("you can still start")]
    assert len(cheap) == 1 and cheap[0].leaves == ["founders/drive/fear", "startups/money/cheap"]


def test_filter_by_path_keyword_and_member(dated):
    by_folder = collect(dated, "startups/money")[0]
    assert {e.statement.leaf for e in by_folder} == {"startups/money/cheap"}
    by_word = collect(dated, "fear")[0]  # path word of founders/drive/fear
    assert len(by_word) == 3
    by_keyword = collect(dated, "cheaper")[0]  # only in a quote
    assert [e.statement.text for e in by_keyword] == ["Everything technology always gets cheaper"]
    assert [e.statement.by for e in collect(dated, member="seibel")[0]] == ["seibel"]
    assert collect(dated, "nothing-like-this")[0] == []


def test_reported_statements_only_on_request(dated):
    entries, skipped = collect(dated, "startups/money", reported=True)
    assert skipped == 0 and any(e.statement.reported for e in entries)


def test_render_and_cli(dated):
    entries, skipped = collect(dated, "money")
    text = render(dated, entries, "money", skipped)
    assert text.splitlines()[0] == 'Test Group: "money", 2 statements from 2 sources, oldest first'
    assert f'  2014-09-30  "Start with very little money." ([[{OLD}]] @ 0:10; by: pg; conf: high)' in text
    assert "Left out 1 reported statement" in text
    result = CliRunner().invoke(app, ["timeline", str(dated.path), "fear", "--member", "seibel"])
    assert result.exit_code == 0, result.output
    assert "seibel (Michael Seibel), 1 statement" in result.output

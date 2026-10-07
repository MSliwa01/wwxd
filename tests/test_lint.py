from pathlib import Path

import pytest

from wwxd import rawdoc
from wwxd.lint import lint
from wwxd.rawdoc import RawDoc, Segment
from wwxd.vault import Source, create_vault

CONFIG = """name: Test Group
slug: test
layout: tree
members:
  - id: pg
    name: Paul Graham
  - id: seibel
    name: Michael Seibel
"""

SRC = "yt-abcdefghijk"


@pytest.fixture
def vault(tmp_path: Path):
    v = create_vault(tmp_path / "test", CONFIG)
    doc = RawDoc(
        meta={"id": SRC, "type": "youtube", "expected_speakers": ["pg"]},
        segments=[
            Segment(0, "So welcome. >> Thanks for having me."),
            Segment(31, "I think you can still start a startup on not much money."),
            Segment(65, "Everything technology always gets cheaper, right?"),
            Segment(120, "The fear of failure is what motivates founders day-to-day."),
        ],
    )
    rawdoc.write(doc, v.raw_path(SRC))
    v.save_sources([Source(id=SRC, type="youtube", url="u", status="fetched", expected_speakers=["pg"])])
    return v


def write_leaf(vault, statements: str, extra: str = "") -> None:
    leaf = vault.wiki_dir / "startups" / "money" / "cheap.md"
    leaf.parent.mkdir(parents=True, exist_ok=True)
    leaf.write_text(
        "---\ntype: leaf\n---\n# Cheap\n\n## Stance\nCheap ([[" + SRC + "]]).\n\n"
        "## Statements\n" + statements + "\n" + extra,
        encoding="utf-8",
    )
    index = vault.wiki_dir / "index.md"
    index.write_text(index.read_text() + "\n- [[startups/money/cheap]]\n")


def messages(vault, level="error"):
    return [i.message for i in lint(vault) if i.level == level]


def test_real_quote_passes(vault):
    write_leaf(vault, f'- "you can still start a startup on not much money" ([[{SRC}]] @ 0:31; by: pg; conf: high)')
    assert messages(vault) == []


def test_punctuation_and_ellipsis_ok(vault):
    write_leaf(vault, f'- "Everything technology... gets cheaper!" ([[{SRC}]] @ 1:05; by: pg; conf: high)')
    assert messages(vault) == []


def test_fabricated_quote_fails(vault):
    write_leaf(vault, f'- "always raise as much money as you can" ([[{SRC}]] @ 0:31; by: pg; conf: high)')
    assert any("quote not in source" in m for m in messages(vault))


def test_wrong_timestamp_warns(vault):
    write_leaf(vault, f'- "fear of failure is what motivates founders" ([[{SRC}]] @ 0:00; by: pg; conf: high)')
    assert messages(vault) == []
    assert any("timestamp off" in m for m in messages(vault, "warning"))


def test_non_member_and_unexpected_speaker(vault):
    write_leaf(
        vault,
        f'- "everything technology always gets cheaper" ([[{SRC}]] @ 1:05; by: host; conf: high)\n'
        f'- "everything technology always gets cheaper" ([[{SRC}]] @ 1:05; by: seibel; conf: high)',
    )
    assert any("not a member" in m for m in messages(vault))
    assert any("expected speaker" in m for m in messages(vault, "warning"))


def test_grammar_and_missing_fields(vault):
    write_leaf(
        vault,
        f"- PG says money is cheap ([[{SRC}]] @ 0:31)\n"
        f'- "everything technology always gets cheaper" ([[{SRC}]]; by: pg; conf: high)\n'
        f'- "everything technology always gets cheaper" ([[{SRC}]] @ 1:05; by: pg)',
    )
    errs = messages(vault)
    assert any("grammar" in m for m in errs)
    assert any("add '@ m:ss'" in m for m in errs)
    assert any("conf" in m for m in errs)


def test_derived_and_missing_raw(vault):
    write_leaf(
        vault,
        f'- "x" ([[yt-missing0000]] @ 0:01; by: pg; conf: high)',
        extra="\nSee [[derived/some-answer]].\n",
    )
    errs = messages(vault)
    assert any("missing raw doc" in m for m in errs)
    assert any("derived" in m for m in errs)


def test_template_comments_ignored(vault):
    assert messages(vault) == []

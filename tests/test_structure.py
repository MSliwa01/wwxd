"""Structure and drift warnings in lint, and the wiki reader behind them."""

from wwxd.lint import lint
from wwxd.vault import Source
from wwxd.wikimap import near_duplicates, read_leaves
from tests.test_lint import SRC, vault  # noqa: F401  (fixture)

CHEAP = f'- "you can still start a startup on not much money" ([[{SRC}]] @ 0:31; by: pg; conf: high)'
TECH = f'- "Everything technology always gets cheaper" ([[{SRC}]] @ 1:05; by: pg; conf: high)'
FEAR = f'- "The fear of failure is what motivates founders" ([[{SRC}]] @ 2:00; by: pg; conf: high)'
WELCOME = f'- "So welcome." ([[{SRC}]] @ 0:00; by: pg; conf: high)'
THANKS = f'- "Thanks for having me." ([[{SRC}]] @ 0:00; by: pg; conf: high)'


def leaf(vault, rel: str, title: str, statements: str, *, index: bool = True, updated: str = "2026-10-01") -> None:  # noqa: F811
    path = vault.wiki_dir / f"{rel}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\ntype: leaf\ntitle: {title}\nupdated: {updated}\n---\n# {title}\n\n"
        f"## Stance\nSee ([[{SRC}]]).\n\n## Statements\n{statements}\n\n## Actions\n"
        f"- Started a company ([[{SRC}]] @ 0:31; by: pg; conf: high)\n",
        encoding="utf-8",
    )
    if index:
        index_page = vault.wiki_dir / "index.md"
        index_page.write_text(index_page.read_text() + f"- [[{rel}]] ({title})\n")


def overview(vault, folder: str) -> None:  # noqa: F811
    (vault.wiki_dir / folder / "_overview.md").write_text("---\ntype: overview\n---\n# Overview\n")


def warnings(vault, needle: str) -> list[str]:  # noqa: F811
    return [f"{i.path}: {i.message}" for i in lint(vault) if i.level == "warning" and needle in i.message]


def test_reads_statements_actions_and_stance(vault):  # noqa: F811
    leaf(vault, "startups/money/cheap", "Starting cheap", f"{CHEAP}\n{TECH}")
    (found,) = read_leaves(vault)
    assert found.rel == "startups/money/cheap" and found.folder == "startups/money"
    assert [s.ts for s in found.statements] == ["0:31", "1:05"]
    assert found.statements[0].by == "pg" and found.statements[0].conf == "high"
    assert found.actions[0].text == "Started a company"
    assert found.stance_sources == {SRC}


def test_near_duplicate_names_in_one_folder(vault):  # noqa: F811
    leaf(vault, "startups/money/raising-prices", "Raising prices", CHEAP)
    leaf(vault, "startups/money/raising-your-prices", "Raising your prices", TECH)
    leaf(vault, "startups/people/hiring-engineers", "Hiring engineers", FEAR)
    leaf(vault, "startups/people/founder-fear", "Why founders are afraid", WELCOME)
    pairs = near_duplicates(read_leaves(vault))
    assert [(p.a.slug, p.b.slug) for p in pairs] == [("raising-prices", "raising-your-prices")]
    found = warnings(vault, "near-duplicate")
    assert len(found) == 1 and "[[startups/money/raising-your-prices]]" in found[0]


def test_near_duplicate_by_repeated_quotes(vault):  # noqa: F811
    leaf(vault, "startups/money/cheap", "Starting cheap", f"{CHEAP}\n{TECH}\n{FEAR}")
    leaf(vault, "founders/drive/motivation", "What motivates people", f"{CHEAP}\n{TECH}\n{FEAR}\n{WELCOME}")
    leaf(vault, "founders/drive/ambition", "Ambition", THANKS)
    pairs = near_duplicates(read_leaves(vault))
    assert len(pairs) == 1 and pairs[0].shared_quotes == 3
    assert "3 of 3 quotes repeated" in pairs[0].reason()


def test_leaf_contained_in_another_is_a_duplicate(vault):  # noqa: F811
    leaf(vault, "founders/drive/motivation", "What motivates people", f"{CHEAP}\n{FEAR}\n{WELCOME}")
    leaf(vault, "startups/money/cheap", "Starting cheap", CHEAP)
    (pair,) = near_duplicates(read_leaves(vault))
    assert pair.shared_quotes == 1 and pair.score >= 0.55


def test_one_shared_quote_is_not_a_duplicate(vault):  # noqa: F811
    leaf(vault, "startups/money/cheap", "Starting cheap", f"{CHEAP}\n{TECH}\n{WELCOME}")
    leaf(vault, "founders/drive/motivation", "What motivates people", f"{CHEAP}\n{FEAR}")
    assert near_duplicates(read_leaves(vault)) == []


def test_leaf_missing_from_index(vault):  # noqa: F811
    leaf(vault, "startups/money/cheap", "Starting cheap", CHEAP, index=False)
    leaf(vault, "startups/money/fear", "Fear", f"{FEAR}\n\n## Related\n- [[startups/money/cheap]]")
    leaf(vault, "startups/money/lonely", "Lonely", TECH, index=False)
    found = warnings(vault, "index.md")
    assert any("cheap.md: not listed in wiki/index.md" in f for f in found)
    assert not any("fear.md" in f for f in found)
    # An orphan already gets "add it to index.md"; don't warn twice.
    assert [f for f in found if "lonely.md" in f] == ["wiki/startups/money/lonely.md: orphan page: nothing links here (add it to index.md)"]


def test_missing_overviews_in_tree_layout(vault):  # noqa: F811
    leaf(vault, "startups/money/cheap", "Starting cheap", CHEAP)
    leaf(vault, "startups/money/fear", "Fear", FEAR)
    leaf(vault, "startups/people/hiring", "Hiring", TECH)
    found = warnings(vault, "_overview.md")
    assert "wiki/startups/_overview.md: missing: every domain folder needs an _overview.md" in found
    assert "wiki/startups/money/_overview.md: missing: topic folder has 2 leaves and no _overview.md" in found
    assert not any("people" in f for f in found)
    overview(vault, "startups")
    overview(vault, "startups/money")
    assert warnings(vault, "_overview.md") == []


def test_overviews_not_needed_in_flat_layout(vault):  # noqa: F811
    config = vault.path / "vault.yaml"
    config.write_text(config.read_text().replace("layout: tree", "layout: flat"))
    from wwxd.vault import Vault

    flat = Vault(vault.path)
    leaf(flat, "startups/money/cheap", "Starting cheap", CHEAP)
    assert [i for i in lint(flat) if "_overview" in i.message] == []


def test_compiled_source_nobody_cites(vault):  # noqa: F811
    other = "web-0123456789ab"
    (vault.raw_dir / f"{other}.md").write_text("---\nid: web-0123456789ab\n---\nSome essay text.\n")
    vault.save_sources([
        Source(id=SRC, type="youtube", url="u", status="compiled", expected_speakers=["pg"]),
        Source(id=other, type="web", url="w", status="compiled", expected_speakers=["pg"]),
    ])
    leaf(vault, "startups/money/cheap", "Starting cheap", CHEAP)
    found = [i for i in lint(vault) if "no wiki page cites" in i.message]
    assert len(found) == 1 and found[0].path == "sources.yaml" and other in found[0].message
    lines = (vault.path / "sources.yaml").read_text().splitlines()
    assert lines[found[0].line - 1].strip() == f"- id: {other}"


def test_frontmatter_that_does_not_parse(vault):  # noqa: F811
    leaf(vault, "startups/money/cheap", "Cheap: is it possible?", CHEAP)
    found = warnings(vault, "front matter isn't valid YAML")
    assert found and found[0].startswith("wiki/startups/money/cheap.md")
    # The reader still treats it as a leaf.
    assert [leaf.title for leaf in read_leaves(vault)] == ["Cheap: is it possible?"]


def test_distinct_from_silences_a_reviewed_pair(vault):  # noqa: F811
    leaf(vault, "startups/money/raising-prices", "Raising prices", CHEAP)
    leaf(vault, "startups/money/raising-your-prices", "Raising your prices", TECH)
    assert len(near_duplicates(read_leaves(vault))) == 1
    page = vault.wiki_dir / "startups" / "money" / "raising-your-prices.md"
    page.write_text(page.read_text().replace("type: leaf\n", "type: leaf\ndistinct_from: [startups/money/raising-prices]\n"))
    assert near_duplicates(read_leaves(vault)) == []

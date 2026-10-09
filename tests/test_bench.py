from wwxd.bench import strip_citations, verify_quotes
from tests.test_lint import SRC, vault  # noqa: F401  (fixture)


def test_strip_citations_blinds_answers():
    text = 'He says "you can still start cheap" ([[yt-abcdefghijk]] @ 0:31; by: pg; conf: high). See [[startups/money/cheap|cheap]]. The vault has more.'
    out = strip_citations(text)
    assert "yt-" not in out and "[[" not in out and "vault" not in out
    assert '"you can still start cheap"' in out and "cheap" in out
    linked = strip_citations('"x y z" ([yt-OQf2Ba-Lp_4 @ 8:06](https://www.youtube.com/watch?v=OQf2Ba-Lp_4&t=486s)) and (@ 7:00).')
    assert "youtube" not in linked and "8:06" not in linked and "7:00" not in linked and "()" not in linked


def test_verify_quotes(vault):  # noqa: F811
    answer = 'PG: "I think you can still start a startup on not much money." He also said "founders should raise a huge seed round right away"'
    result = verify_quotes(vault, answer)
    assert result["quotes"] == 2 and result["verified"] == 1


def test_attributed_quotes_skips_example_copy():
    from wwxd.bench import attributed_quotes

    text = (
        'Write copy like "We are not the cheapest option in town, ever." Then he says: "charge more than you think you should".\n'
        '- "a quote with a link](http://x) inside it here" and "second one is fine words here"'
    )
    assert attributed_quotes(text) == ["charge more than you think you should"]


def test_opinion_stats_counts_hedges():
    from wwxd.bench import opinion_stats

    assert opinion_stats("Raise your prices today.")["hedges"] == 0
    assert opinion_stats("It depends. On the other hand, you might keep them.")["hedges"] == 3


def test_judge_ranked_maps_letters_back_to_arms(tmp_path, monkeypatch):
    import json

    from wwxd import bench

    gold = tmp_path / "gold.yaml"
    gold.write_text("questions:\n  - {id: q1, person: PG, question: 'X or Y?'}\n")
    arms = []
    for name, text in (("raw", "Maybe X, maybe Y."), ("wwxd", "Y. He said so.")):
        d = tmp_path / name
        d.mkdir()
        (d / "answers.jsonl").write_text(json.dumps({"id": "q1", "answer": text, "error": "", "seconds": 1}) + "\n")
        arms.append(d)

    def fake_agent(command, prompt, cwd, timeout=1200):
        # Score whichever letter holds the wwxd answer as best.
        best = "A" if "Answer A:\n<<<\nY. He said so." in prompt else "B"
        other = "B" if best == "A" else "A"
        return json.dumps({best: {"decisiveness": 5}, other: {"decisiveness": 1}, "ranking": [best, other]})

    monkeypatch.setattr(bench, "run_agent", fake_agent)
    out = bench.judge_ranked(None, gold, arms, _prompt(tmp_path), tmp_path / "rank.jsonl", agent="x", cwd=tmp_path)
    summary = bench.summarize_ranked(arms, out)
    assert summary["arms"]["wwxd"]["decisiveness"] == 5 and summary["arms"]["wwxd"]["ranked_first"] == 1
    assert summary["arms"]["raw"]["decisiveness"] == 1


def _prompt(tmp_path):
    p = tmp_path / "prompt.md"
    p.write_text("{{question}} {{person}}\n{{answers}}")
    return p

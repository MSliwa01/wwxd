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

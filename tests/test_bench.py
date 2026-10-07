from wwxd.bench import strip_citations, verify_quotes
from tests.test_lint import SRC, vault  # noqa: F401  (fixture)


def test_strip_citations_blinds_answers():
    text = 'He says "you can still start cheap" ([[yt-abcdefghijk]] @ 0:31; by: pg; conf: high). See [[startups/money/cheap|cheap]]. The vault has more.'
    out = strip_citations(text)
    assert "yt-" not in out and "[[" not in out and "vault" not in out
    assert '"you can still start cheap"' in out and "cheap" in out


def test_verify_quotes(vault):  # noqa: F811
    answer = 'PG: "I think you can still start a startup on not much money." Also "founders should raise a huge seed round right away"'
    result = verify_quotes(vault, answer)
    assert result["quotes"] == 2 and result["verified"] == 1

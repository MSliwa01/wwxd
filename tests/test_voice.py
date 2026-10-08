import json

import pytest

from tests.test_lint import SRC, vault, write_leaf  # noqa: F401  (fixture)
from wwxd import voice
from wwxd.lint import lint


def test_words_from_json3_uses_word_offsets():
    data = {"events": [{"tStartMs": 1000, "segs": [{"utf8": "Charge"}, {"utf8": " more", "tOffsetMs": 400}]},
                       {"tStartMs": 1500, "aAppend": 1, "segs": [{"utf8": "\n"}]}]}
    assert voice.words_from_json3(data) == [(1.0, "charge"), (1.4, "more")]


def test_locate_finds_quote_near_timestamp():
    words = [(float(i), w) for i, w in enumerate("so welcome back you can still start a startup on not much money right".split())]
    start, end = voice.locate(words, "You can still start a startup on not much money.", "0:03")
    assert start == 3.0 and 12.0 <= end <= 13.5
    assert voice.locate(words, "something nobody said at all here", "0:03") is None


def test_verdict_rules():
    assert voice.verdict(0.7, {"b": 0.2}) == ("match", "")
    assert voice.verdict(0.35, {}) == ("weak", "")
    assert voice.verdict(0.1, {}) == ("mismatch", "")
    assert voice.verdict(0.45, {"b": 0.75}) == ("mismatch", "b")


def test_voiceprint_ignores_a_minority_of_wrong_attributions():
    np = pytest.importorskip("numpy")
    rng = np.random.default_rng(0)
    a, b = rng.normal(size=16), rng.normal(size=16)
    vecs = [a + rng.normal(scale=0.1, size=16) for _ in range(9)] + [b]
    vecs = [v / np.linalg.norm(v) for v in vecs]
    centre = voice.voiceprints({"m": vecs})["m"]
    assert centre @ (a / np.linalg.norm(a)) > 0.95


def test_lint_reports_voice_mismatch_until_fixed(vault):  # noqa: F811
    quote = "you can still start a startup on not much money"
    write_leaf(vault, f'- "{quote}" ([[{SRC}]] @ 0:31; by: pg; conf: high)')
    row = {"key": voice.statement_key(SRC, quote, "pg"), "page": "wiki/startups/money/cheap.md", "line": 9,
           "src": SRC, "by": "pg", "quote": quote, "voice": "mismatch", "sounds_like": "seibel", "own": 0.1}
    (vault.path / "attribution.jsonl").write_text(json.dumps(row) + "\n")
    warnings = [i.message for i in lint(vault) if i.level == "warning"]
    assert any("voice check" in w and "seibel" in w for w in warnings)
    write_leaf(vault, f'- "{quote}" ([[{SRC}]] @ 0:31; by: seibel; conf: high)')
    assert not any("voice check" in i.message for i in lint(vault))

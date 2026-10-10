"""Estimate what compiling and asking will cost, before you spend it.

The token model comes from 55 real compile sessions (Claude Code, Opus 5.5, Oct 2026):
each session reads the skill, the index and the leaves it touches, so most of the cost
is a fixed overhead per source, plus a part that grows with the source's length. The
estimate assumes Sonnet and Haiku use about as many tokens as Opus; they may need more
turns. Treat every number as a range, not a quote: real sessions varied by about
+-50% around the estimate.
"""

from __future__ import annotations

from dataclasses import dataclass

from wwxd import rawdoc
from wwxd.vault import Vault

# USD per million tokens, Anthropic list prices (checked 2026-10-09).
# Claude Code writes cache with a 1-hour TTL, billed at 2x the input price.
PRICES = {
    "opus": {"id": "claude-opus-5-5", "input": 4.00, "output": 20.00, "cache_write": 8.00, "cache_read": 0.20},
    "sonnet": {"id": "claude-sonnet-5-5", "input": 2.00, "output": 10.00, "cache_write": 4.00, "cache_read": 0.20},
    # Haiku 5.5 prices apply to prompts up to 100K tokens; compile prompts sit near that line.
    "haiku": {"id": "claude-haiku-5-5", "input": 0.10, "output": 0.50, "cache_write": 0.20, "cache_read": 0.01},
}

# Tokens per compiled source = fixed + per_word * words in the raw document.
COMPILE_TOKENS = {
    "cache_write": (56_000, 2.66),
    "cache_read": (766_000, 67.2),
    "output": (14_200, 1.12),
}
COMPILE_SECONDS = (185, 0.0174)

# One `ask` against a vault (measured: 10 turns, 34 s on Opus 5.5).
ASK_TOKENS = {"cache_write": 37_000, "cache_read": 249_000, "output": 3_300}

# If Claude Code runs with an advisor model (a stronger model the main one consults),
# that adds its own cost on top. In our runs a Fable 5.1 advisor added 85% to 125%.
ADVISOR_EXTRA = 1.0

# The token model above was fit on Opus sessions at effort xhigh with that advisor on,
# and counts only the main model. Without an advisor the main model does that thinking
# itself. Measured Opus compile cost relative to the estimate, no advisor (Oct 2026):
EFFORT_FACTOR = {"medium": 0.73, "high": 1.10, "xhigh": 1.75}

WORDS_PER_MINUTE = 150  # spoken English in talks and podcasts
WORDS_PER_ARTICLE = 1_500  # when an article's length isn't known yet


@dataclass
class Item:
    id: str
    title: str
    words: int
    measured: bool  # True: counted from raw/, False: estimated from duration


def words_for(vault: Vault, source) -> Item:
    path = vault.raw_path(source.id)
    if path.exists():
        doc = rawdoc.read(path)
        text = " ".join(s.text for s in doc.segments) if doc.segments else doc.body
        return Item(source.id, source.title, len(text.split()), True)
    if source.duration:
        return Item(source.id, source.title, int(source.duration / 60 * WORDS_PER_MINUTE), False)
    return Item(source.id, source.title, WORDS_PER_ARTICLE, False)


def compile_tokens(words: int) -> dict[str, float]:
    return {k: fixed + per_word * words for k, (fixed, per_word) in COMPILE_TOKENS.items()}


def dollars(tokens: dict[str, float], model: str) -> float:
    price = PRICES[model]
    return sum(tokens.get(k, 0) * price[k] for k in ("input", "output", "cache_write", "cache_read")) / 1e6


def compile_seconds(words: int) -> float:
    fixed, per_word = COMPILE_SECONDS
    return fixed + per_word * words

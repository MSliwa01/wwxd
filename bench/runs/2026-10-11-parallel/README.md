# Parallel compile, October 11, 2026

Raw data for [Parallel compile](../../RESULTS.md#parallel-compile) in RESULTS.md.

| File | Contents |
|---|---|
| `compile-sessions.csv` | One row per agent session: arm (`parallel` or `extract-place`), vault (`yc` or `hz`), step (`compile`, `extract` or `place`), source, seconds, turns, cost_usd, token counts and is_error. The one-at-a-time sessions are in `../2026-10-10/compile-sessions.csv` (Sonnet, high). |
| `metrics.json` | One record per arm, scored like the model and effort study. |
| `scripts/eval_parallel.py` | The scorer: `study_eval.py` from `../2026-10-10` for one pair of vaults. |

Both arms compiled the 4 sources of the model and effort study into empty vaults,
with Sonnet 5.5 at effort high, `wwxd compile --jobs 3` on the yc vault and
`--jobs 1` on the hz vault, run at the same time.

- `parallel`: each session compiles its source straight into the wiki
  (`wwxd compile`). In this run the rules for sharing the wiki were in the prompt;
  they now live in `references/compile.md`, worded the same way.
- `extract-place`: each session wrote its source's attributed quotes to
  `staging/<id>.md` and touched nothing else, and one session at a time merged
  staged sources into the wiki without re-reading the transcripts. We dropped this
  design, so its code isn't in the repo.

The compiled vaults aren't included, because the repo ships no vault content.

# Model and effort study, October 10, 2026

Raw data for the model and effort study and the captions vs Whisper section in
[RESULTS.md](../../RESULTS.md#model-and-effort-study). How the study ran is in
[bench/README.md](../../README.md#model-and-effort-study).

## Compile

| File | Contents |
|---|---|
| `compile-sessions.csv` | One row per compile session, 36 in all (9 configurations, 4 sources). Columns are vault (`yc` or `hz`), source, model, effort, seconds, turns, cost_usd, the token counts (input, cache_write, cache_read, output) and is_error. |
| `compile-metrics.json` | One record per configuration: statements, lint_errors, cost, seconds and minutes for all 4 sessions, sessions, failed, attribution against the official transcript (`attr`, `attr_pct`) and gold evidence found (`evidence_recall`). |

The compiled study vaults aren't included, because the repo ships no vault content.

## Answers and judgments

`hormozi-model-effort/` and `yc-model-effort/` have the same files, for the 6
questions per vault in `gold/hormozi-ask12.yaml` and `gold/yc-ask12.yaml`.

| File | Contents |
|---|---|
| `ask-<model>-<effort>-answers.jsonl` | The 9 answer arms, one line per question |
| `raw-answers.jsonl` | Raw Opus 5.5 answers with no vault, the baseline for the pairwise judge |
| `judge-raw-vs-ask-<model>-<effort>-haiku.jsonl` | Pairwise judgments of each arm against raw, by Haiku 5.5 |
| `rank-9-arms-opus.jsonl`, `rank-9-arms-haiku.jsonl` | Blind 9-way rankings, one line per question, with the shuffled order, scores and ranking |
| `rank-9-arms-opus.summary.json`, `rank-9-arms-haiku.summary.json` | Per-arm mean scores, `mean_rank`, times ranked first, median words |
| `quote-check.json` | Per-arm quote check against the raw transcripts, with median seconds per answer and examples of unverified quotes |

## Answer format

`hormozi-prose/` and `yc-prose/` hold the comparison of the prose answer format with
the earlier one, in [RESULTS.md](../../RESULTS.md#answer-format-prose-with-sources-underneath).
All answers are Opus 5.5 at effort high. The judge name at the end of a file is
`opus` (Opus 5.5 at effort medium, with the raw transcripts) or `lite` (Gemini 3.5
Flash Lite, no tools).

| File | Contents |
|---|---|
| `prose-opus-high-answers.jsonl` | New-format answers to the 6 ask12 questions per vault |
| `op-prose-answers.jsonl` | New-format answers to the opinion questions |
| `op-old-high-answers.jsonl` | Old-format answers to the opinion questions |
| `judge-ask-opus-high-vs-prose-opus-high-<judge>.jsonl` | Pairwise judgments, old format (`ask-opus-high` from `<vault>-model-effort/`) against new |
| `rank-op-old-high-op-prose-op-raw-<judge>.jsonl` | 3-way opinion rankings of the old format, the new format and the raw answers from the opinion bench |

## Gemini judge

`hormozi-gemini-judge/` and `yc-gemini-judge/` hold the judgments by Gemini 3.5 Flash
Lite, in [RESULTS.md](../../RESULTS.md#a-judge-from-google). It ran with no tools, one
API call per judgment.

| File | Contents |
|---|---|
| `judge-raw-vs-wwxd-gemini-3.5-flash-lite.jsonl` | Pairwise judgments on the main bench |
| `rank-op-raw-op-persona-op-wwxd-gemini-3.5-flash-lite.jsonl` | 3-way rankings on the opinion bench, old answer format |
| `rank-9-arms-gemini-3.5-flash-lite.jsonl` | 9-way rankings of the model and effort arms |

## Scripts

`scripts/` has the scripts that ran the study and scored it: `study_compile.sh`,
`study_eval.py`, `study_ask.sh`, `study_ask_eval.py`, `study_rank.sh`, and `wer2.py`
for the transcription comparison. `prose_bench.sh` runs the answer format comparison
and its judges, and `prose_opus_judge.sh` reruns only the Opus judge. `gemini_judges.sh`
runs the Gemini judge on all three benches, and `gemini_judge.sh` is the one-call
judge it passes as `--agent`. The Gemini scripts need a local key-rotation helper
that isn't in the repo. All scripts use absolute paths from our lab machine. See
[bench/README.md](../../README.md#model-and-effort-study) for what they expect.

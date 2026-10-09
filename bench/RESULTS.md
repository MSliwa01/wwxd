# Results, October 2026

Claude Opus 5.5 in Claude Code, with and without a wwxd vault. 40 questions over two
vaults, judged blind by a third Opus 5.5 session. Setup and caveats are in
[README.md](README.md). Raw answers, judgments and summaries are in
[runs/2026-10-08](runs/2026-10-08).

## Vaults

| Vault | Sources | Wiki pages | Compile time per source | Compile cost (list price) |
|---|---|---|---|---|
| `hormozi` | 13 YouTube videos (2023 to 2026) | 77 | 2.5 to 8 min | $89 for both vaults |
| `yc` | 13 videos, 11 Paul Graham essays | 96 | 1.5 to 10 min | |

A fresh Claude Code session compiled each source, guided only by the skill. Both
vaults pass `wwxd lint` with no errors.

## Blind judge scores (1 to 5)

| | Hormozi raw | Hormozi wwxd | YC raw | YC wwxd |
|---|---|---|---|---|
| Accuracy | 2.85 | 4.95 | 2.60 | 5.00 |
| Specificity | 1.90 | 4.90 | 2.00 | 4.85 |
| Faithfulness | 3.15 | 4.70 | 3.15 | 4.55 |
| Usefulness | 3.20 | 4.60 | 2.95 | 4.70 |
| Judge preferred | 0 of 20 | 20 of 20 | 0 of 20 | 20 of 20 |

### A second judge from another model family

To check that this isn't Claude preferring Claude, NVIDIA Nemotron 3 Ultra (free,
through opencode) judged the same 40 pairs with the same prompt and the same access
to the transcripts.

| Nemotron judge, 1 to 5 | Hormozi raw | Hormozi wwxd | YC raw | YC wwxd |
|---|---|---|---|---|
| Accuracy | 2.75 | 4.95 | 2.75 | 5.00 |
| Specificity | 2.40 | 4.85 | 2.30 | 5.00 |
| Faithfulness | 3.10 | 4.90 | 3.00 | 5.00 |
| Usefulness | 3.40 | 4.85 | 3.10 | 4.85 |
| Judge preferred | 1 of 20 | 19 of 20 | 0 of 20 | 20 of 20 |

The two judges picked the same answer on 39 of 40 questions. The one split is
`hz-01`, where Nemotron preferred raw Opus.

### By category (accuracy, raw vs wwxd)

| Category | Hormozi | YC |
|---|---|---|
| known (older material) | 3.25 vs 5.00 | 3.00 vs 5.00 |
| fresh (2026 material) | 2.33 vs 4.83 | 2.17 vs 5.00 |
| applied (a concrete situation) | 3.00 vs 5.00 | 2.40 vs 5.00 |
| attribution traps | 1.50 vs 5.00 | 1.50 vs 5.00 |
| abstain and false premise | 4.00 vs 5.00 | 4.00 vs 5.00 |

## Quote check (no model involved)

| | Attributed quotes | Found verbatim in the transcripts |
|---|---|---|
| Hormozi raw | 8 | 0 |
| Hormozi wwxd | 77 | 75 (the 2 misses are video titles) |
| YC raw | 2 | 0 |
| YC wwxd | 83 | 83 |

The raw quotes that didn't match are mostly paraphrases of real ideas ("Write so a
third grader could understand it"), not inventions. Raw Opus rarely quotes anyone.

## What the numbers mean

Raw Opus 5.5 is a careful baseline. It never invented a position on the abstain
questions, said it couldn't confirm things it didn't know, and often got the
direction of the advice right. On the one false premise about a 2026 video, it could
only say it didn't know the video. The vault could show what Hormozi actually said. It
lost on specifics. It answered with the general version of a person's view, filled
the gaps with reasonable-sounding numbers of its own, and couldn't know anything
from 2026.

A typical pair, from `hz-11` (HVAC company, 82% close rate, should it raise prices?):

- Raw: says an 82% close rate usually means you're underpriced, that a healthy close
  rate for a premium offer is often around 40 to 60 percent, and builds a break-even
  table on an assumed 55% margin.
- wwxd: Hormozi consulted for a nearly identical company in May 2026 (ProShine,
  $1.25M, 38% margin, 82% close rate). He told them to raise prices about 10% and
  keep it as long as the close rate stays above 65%. The answer quotes him and links
  to the moment in the video.

Attribution traps are where raw Opus did worst. Asked why Garry Tan thinks the YC
premium is bigger than ever, raw Opus explained Tan's reasoning. Sam Altman said it,
in a 2026 YC interview.

## Held-out test: can a vault predict what someone says next?

The main bench asks about things the vault contains. This test asks about things it
doesn't. We rebuilt both vaults from pre-2026 sources only (6 Hormozi videos, 12 YC
videos and essays), then asked the 20 questions whose answers appear only in 2026
sources. The vault arm was told to extrapolate from the person's earlier views when
the vault didn't cover something. Raw Opus answered from memory, three separate
times. Opus judged two independent pairs of runs, and Nemotron judged a third.

| Judge picks the vault answer | Hormozi | YC |
|---|---|---|
| Opus, run 1 | 4 of 10 | 3 of 10 |
| Opus, run 2 | 4 of 10 | 3 of 10 |
| Nemotron | 6 of 10 | 3 of 10 |

Mean accuracy (Opus judge, both runs) was 2.9 for raw Opus and 2.7 for the vault on
Hormozi, and 2.55 vs 2.0 on YC. So a vault of someone's older material doesn't
predict their newer positions better than the model's own reasoning. For YC it did
worse.

Two things explain most of it.

- Raw Opus wasn't fully blind. Its training data runs to mid-2026, and the judge
  noticed it using the real "The Brand Age" essay from March 2026. On the 8 questions
  from sources after June 2026, which neither arm could have seen, raw Opus still won
  16 judgments to 8, but both arms scored low (accuracy 2.4 vs 2.0). Nobody predicted
  Sam Altman's fear of a surveillance-state overreaction to AI safety, or Garry Tan's
  "own your skill files".
- The vault arm is built to say when its sources don't cover something. It often
  opened with "the vault doesn't cover this" before extrapolating, and the judge
  rewarded confident guesses that landed closer.

What this means for using wwxd. A vault makes answers faithful to what a person has
actually said and done. It isn't a forecast of what they'll say about something new,
and people change their minds. In this very test, Dalton Caldwell and Michael Seibel
reversed their own MVP advice in 2026. Keep vaults current with `wwxd update`, and
treat extrapolations as the guesses they are.

## Attribution check by voice

`wwxd voice` compares the audio of every quoted statement with the members'
voiceprints (TitaNet-small through sherpa-onnx, CPU only).

| Vault | Statements checked | Match | Weak | Mismatch | Time |
|---|---|---|---|---|---|
| hormozi | 779 | 774 | 4 | 1 | 1 min 53 s |
| yc | 644 | 635 | 1 | 8 | 1 min 53 s |

Times include downloading the audio. One Sam Altman and Garry Tan episode has an
official transcript with speaker labels. Of the 54 statements from that episode we
could match to it, the compile credited 51 correctly. The voice check got all 54
right, including the 3 the compile got wrong. Of the 9 mismatches in total, 6 are
confirmed by an official transcript or by the surrounding turns, and 3 are still
unconfirmed.

## Limits of this run

The gold sets were written from the same sources the vaults were built from, so the
bench measures recall of documented positions, which is what wwxd is for. It doesn't
show that following this advice works. The judge shares a model with both arms, and
vault answers quote more, so the blinding is imperfect. It's one run with 20
questions per vault. The direction of the result is clear. The exact numbers are
rough.

The pre-2026 vaults for the held-out test were compiled partly before and partly after
we added the voice and consolidate steps to the skill. Both versions use the same
compile procedure for statements.

The YC wwxd answers (all except `yc-04`) and Hormozi `hz-16` to `hz-20` were produced
before we added `--strict-mcp-config`. None of them mention an MCP server. Every raw
answer and every other wwxd answer ran with the flag.

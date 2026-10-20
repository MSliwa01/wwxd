# Paired full-context evaluation, October 19, 2026

Does adding a complete wwxd wiki to the prompt change the answers of three model
families? Each model answered the same questions twice, once with the vault's whole
compiled wiki and once without it. Judges from all three families compared the two
answers blind.

The short answer: the wiki helped clearly when a question asked for a documented
position. On new practical decisions, the effect was smaller and depended on the
model. These are results for this question set, not a ranking of models.

## Setup

| | |
|---|---|
| Answer models | GPT 6.1 Sol (effort high), Opus 5.5 (effort high), Gemini 3.5 Flash-Lite |
| Judge models | The same three, each in a fresh session |
| Vaults | `hormozi` and `yc`, 240 wiki pages in total |
| Questions | 12 diagnostic, 12 practical advice |
| Calls | 144 answers, 72 judge calls with up to three pairs each, 216 judgments |

**Two arms.** `raw` gets the question and the instructions. `grounded` gets the same
prompt followed by every page of the routed vault's wiki, unchanged and in a fixed
order, then one fixed closing line. Nothing is selected per question and nothing is
truncated. Both arms may use their own knowledge, and neither has tools. Answers
contain no citations, links or expert names, so a judge can't tell the arms apart by
format.

**Two question sets, reported separately.**

- *Diagnostic* repeats 12 known questions about a person's documented positions.
  Before any answers, the reference packets were checked against the raw
  transcripts and repaired where needed. Judges get the packet as a grading key.
  This is a regression test on known cases, not held-out evidence.
- *Practical advice* has 12 new business scenarios with a decision, a goal and
  constraints. The author worked from the raw sources only, never the wiki. Some
  principles overlap older gold sets; `frozen/fixtures/AUDIT.md` lists them.
  Judges see only the scenario and two anonymous answers, with no key and no
  reward for using sources. They score decision quality, actionability, fit to
  constraints and reasoning.

**Frozen before answering.** Questions, reference packets, instructions, prompts,
A/B orders, batch grouping and the aggregation rule are hashed in
`frozen/manifest.json`. Each judge family puts `grounded` at A for exactly 6 of 12
questions per block. Same-family judgments are kept but left out of the primary
result.

**Did the model receive the whole wiki?** For 71 complete pairs, the extra accepted
input tokens in the grounded arm came to 0.980 to 1.049 of the predicted size of the
wiki pack. That shows the context was accepted, not that the model read every page.

## Strict result and the post-hoc reading

143 of 144 answers and 69 of 72 judge calls completed. One answer failed on a Gemini
503, and three judge calls failed or were cut off by rate limits and a restart.

The frozen protocol accepted only bare JSON from judges. 47 judge calls returned
valid JSON wrapped in a Markdown code fence. The strict parser left 65 valid votes,
148 failed and 3 blocked, so all 72 primary consensus slots are missing. That result
stays as recorded in [results/STRICT-REPORT.md](results/STRICT-REPORT.md).

A post-hoc analysis, written after seeing the wrapper failures and before looking at
any recovered winners, strips one outer code fence and then applies the original
parser and schema unchanged. It doesn't touch wording, scores, winners, A/B order
or eligibility. It yields 198 valid votes, 9 failed, 6 invalid and 3 blocked. The
rule is in [post-run/FORMATTING-ANALYSIS.md](post-run/FORMATTING-ANALYSIS.md). All
numbers below come from this post-hoc reading.

## Consensus of the two external judges

Each row covers 12 questions. A slot counts for one arm only when both judges from
the other two families pick it. "Split" means they disagreed, including a tie from
one and a pick from the other. Missing slots stay in the denominator.

| Set | Answer model | Grounded | Raw | Tie | Split | Missing |
|---|---|---:|---:|---:|---:|---:|
| Advice | Sol | 2 | 0 | 3 | 7 | 0 |
| Advice | Opus | 1 | 1 | 3 | 7 | 0 |
| Advice | Gemini | 6 | 3 | 0 | 2 | 1 |
| Diagnostic | Sol | 3 | 0 | 0 | 3 | 6 |
| Diagnostic | Opus | 6 | 0 | 0 | 6 | 0 |
| Diagnostic | Gemini | 10 | 1 | 1 | 0 | 0 |

Individual external votes: on advice, 29 for grounded, 18 for raw and 23 ties; on
diagnostic questions, 52 for grounded, 4 for raw and 10 ties. Several votes on one
pair are not independent questions.

## Reviews after judging

These reviews were separate model sessions with file access. They add annotations
and change no votes.

- **Blind factual review of all 72 advice answers**
  ([post-run/factual-review-r1.md](post-run/factual-review-r1.md)). The reviewer
  didn't know the model, the arm or the winner. It recomputed every number against
  the scenario's inputs, checked each explicit constraint and checked
  source-derived claims against the raw files. It found material errors in 5
  answers, all from Gemini: 3 raw and 2 grounded. The 66 other assessed answers
  had no established material error. The empty answer from the failed call
  couldn't be assessed.
- **Integration of the advice judgments**
  ([post-run/factual-review-integration.json](post-run/factual-review-integration.json),
  [post-run/practical-judgment-audit.json](post-run/practical-judgment-audit.json)).
  This covers all 16 judge disagreements and 83 factual objections from the judges,
  and corrects two points in the blind review: its count of answers without notes
  included the empty answer, and one break-even month it flagged agrees with the
  key. It also found a risk the blind review missed, a plan by raw Opus that could
  need 60 hours of work against a 50-hour cap. Five material errors is the blind
  reviewer's count, not proof that every other answer is error-free.
- **Diagnostic exceptions** ([post-run/result-audit-r1.md](post-run/result-audit-r1.md)).
  All 19 cases where raw won, the judges tied or the judges split, 38 answers and
  57 votes, checked against the full transcripts. It found answer errors, judge
  misreadings and details missing from the reference packets. For example, some
  Gemini judge reasons credit an answer with details it never gives. Some extra
  details in answers about fundraising and finding customers are in the full
  sources but not in the key, so a detail missing from the key isn't proof of fabrication. The audit also
  reran all 3,376 validation checks and confirmed that the post-hoc reading keeps
  every one of the 65 strict votes and leaves 1,495 original files unchanged.

## Why raw sometimes wins

On advice, judges rate the decision. On one hiring scenario, raw Gemini proposed
more founder involvement and a shorter process, while grounded Gemini called the
current process sound and focused on pay. That is a real difference in how the
knowledge was applied.

On an advertising question, both Gemini answers made wrong assumptions about
inventory. The judges preferred raw for its more concrete spending plan and still
listed its errors. Winning a pair doesn't mean the answer was right.

On a diagnostic question about Jessica Livingston, grounded Gemini accepted a false
premise. Raw partly pushed back, so it could fairly win, though it didn't fully
recover the documented position either. Full context doesn't guarantee the model
uses it well.

## What this supports

The run supports the claim that a vault helps a model reproduce specific
documented positions. It doesn't support a promise that adding a whole vault
improves any piece of advice.

For the next run: settle how wrapped JSON is handled before the run, or use a
structured output mode. Fill the reference gaps the diagnostic audit found. Keep
source fidelity and decision quality as separate measurements.

## Files

| Path | Contents |
|---|---|
| `PROTOCOL.md` | The protocol as frozen before any answers |
| `frozen/` | Questions, reference packets, instructions, A/B mapping, batches, aggregation rule, manifest and the raw-arm prompts |
| `frozen/fixtures/` | The question and evidence files as written, their audit and the tools that built and verified them |
| `responses/` | All 144 answer records, including the failed one, with token usage and finish reasons |
| `judgments/` | All 216 judgment rows, including failed and blocked ones |
| `results/` | Validation, accepted input usage, pairs, judge prompts, raw judge outputs, the strict summary and the review exports |
| `post-run/` | The fence analysis, its votes and summary, and the three reviews |
| `scripts/` | The runner (`eval.py` with phases `prepare`, `smoke`, `answers`, `pairs`, `judge`, `validate`, `report`), the provider adapters, the integrity check and the fixture tools |

Not included: the grounded prompts and the frozen context packs, because they
contain the full wiki, which holds long quotes from the sources (see
[ETHICS.md](../../../ETHICS.md)). Their hashes are in `frozen/manifest.json` and
their page list is in `frozen/wiki-inventory.json`. The raw provider streams aren't
included either; the token counts taken from them are in
`results/accepted-input-usage.json`.

The scripts use absolute paths from our lab machine. The vaults live under
`~/wwxd-lab/vaults`, and the Gemini adapter imports a local key-rotation helper.
Sol and Opus run through their subscription CLIs. Adjust the paths and the Gemini
call before you run them.

# Results, October 2026

Claude Opus 5.5 in Claude Code, with and without a wwxd vault. 40 questions over two
vaults, judged blind by a third Opus 5.5 session. Setup and caveats are in
[README.md](README.md). Raw answers, judgments and summaries are in
[runs/2026-10-08](runs/2026-10-08).

Every compile and every wwxd and raw answer in the benches below ran in Claude Code
with Opus 5.5 at effort xhigh and a Fable 5.1 advisor, the Claude Code settings we
had at the time. An advisor is a stronger model the main model can consult, and in
our compile sessions it added 85% to 125% to the cost. The model and effort study
further down ran without an advisor.

## Vaults

| Vault | Sources | Wiki pages | Compile time per source | Compile cost (list price) |
|---|---|---|---|---|
| `hormozi` | 13 YouTube videos (2023 to 2026) | 77 | 2.5 to 8 min | $89 for both vaults, $44 of it the advisor |
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
`hz-01`, where Nemotron preferred raw Opus. A third judge, Muse Spark 1.3 (free,
through opencode), preferred wwxd on 35 of the 36 pairs it scored; 4 Hormozi pairs
failed on opencode errors. A fourth, Claude Haiku 5.5, preferred wwxd on all 40.

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

## Opinion bench: does it actually take a side?

Models hedge. The obvious fix is to tell the model to be decisive and answer as the
person would. This bench checks whether that's enough. It asks 24 "should I do X or
Y?" questions (12 for Hormozi, 12 for Paul Graham), each ending with "What would
<name> say?", and compares three arms in Claude Code with Opus 5.5:

- raw: the question alone, no tools.
- persona: the question plus "Answer the way the person named below would, based on
  what they've actually said and done. Be decisive: pick one option and say why."
- wwxd: the question plus the vault.

Four judges (Opus 5.5, Haiku 5.5, Nemotron 3 Ultra and Muse Spark 1.3) saw each
question's three answers together, shuffled and with citations stripped. They scored
each answer from 1 to 5, ranked them, and said whether its pick matched what the
person's transcripts show.

| Mean of four judges | raw | persona | wwxd |
|---|---|---|---|
| Decisiveness | 3.5 | 4.8 | 4.7 |
| Distinctiveness | 2.8 | 3.0 | 4.8 |
| Grounding (reasons they really hold) | 2.8 | 2.6 | 4.9 |
| Usefulness | 4.0 | 4.0 | 4.4 |
| Ranked best | 0 | 0 | 93 of 93 |
| Pick contradicts the person | 9 | 8 | 0 |

The persona prompt fixes the hedging. It's even slightly more decisive than wwxd,
which sometimes gives the person's own deciding rule ("under about 5 reps, manage
them yourself") instead of a flat pick. But its reasons are generic or made up, and
it scores no better than raw Opus on grounding. Telling a model to be opinionated
makes it confident, not right.

The clearest case is `op-hz-06`: "I have $50k saved. Should I pay off my car loan and
credit cards or put it all into my business?" Raw Opus and the persona prompt both
said to keep a low-rate car loan, which is the standard financial-advice answer.
Every judge marked that as contradicting Hormozi. In his 2026 videos he says
"ideally just pay off your car so you don't have to think about it again" and "I
tend to skew like very close to the Ramsey side". wwxd said to pay off both and
quoted him.

Two other findings.

- A word-count measure of hedging ("it depends", "on the other hand", "you might")
  found almost none in any arm, about 0.1 per 100 words. Opus 5.5 doesn't hedge with
  stock phrases. It hedges by laying out conditions, which only the judges caught.
- We tested a shorter answer format for wwxd (about 250 words instead of about
  600). The Opus judge preferred the full answer on all 24 questions: the short one
  lost the specific examples and numbers. We kept the full format.

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

We then changed how the skill handles questions the vault doesn't cover. It now
leads with a verdict, says whether it rests on something the person said, a
principle of theirs applied to the case, or knowledge from outside the vault, and
doesn't open with "not covered". On the same held-out questions:

| Judge picks the vault answer, new skill | Hormozi | YC |
|---|---|---|
| Opus | 5 of 10 | 4 of 10 |
| Nemotron | 3 of 7 | 2 of 9 |
| Muse Spark | 3 of 10 | 3 of 8 |
| Haiku 5.5 | 3 of 10 | 4 of 10 |

The Opus judge now calls it even, with vault accuracy slightly ahead (2.9 vs 2.8 and
2.6 vs 2.5). The other three judges still prefer raw Opus. The change narrowed
the gap without closing it, and it kept honesty intact: on the attribution traps and
false premises the new skill scored 4.8 to 5.0, as before.

What this means for using wwxd. A vault makes answers faithful to what a person has
actually said and done. It isn't a forecast of what they'll say about something new,
and people change their minds. In this very test, Dalton Caldwell and Michael Seibel
reversed their own MVP advice in 2026. Keep vaults current with `wwxd update`, and
treat extrapolations as the guesses they are.

## Inference bench: reasoning from how they think

Most useful questions are ones the person never answered directly: "would Hormozi
buy a Lamborghini after his first $1M?", "what would Paul Graham think of a startup
that sells AI-written admission essays?". The skill handles these by finding the
nearest case the person did address, the rule behind their view, and why the new
case falls under it. Each vault also has thinking pages (`wiki/thinking/<member>.md`):
the person's values, decision rules, reasoning habits and strong views, each with
verbatim quotes.

16 such questions (8 per vault), four arms: raw Opus, the "be decisive" persona
prompt, wwxd without thinking pages, and wwxd with them. Opus 5.5 and Haiku 5.5
judged all 16; Muse Spark judged the 8 Hormozi ones before its free tier slowed to a
stop. Judges checked each answer's premises against the transcripts.

| Mean of three judges | raw | persona | wwxd | wwxd + thinking pages |
|---|---|---|---|---|
| Decisiveness | 3.8 | 4.9 | 4.7 | 4.9 |
| Grounding (premises they really said) | 2.7 | 2.3 | 4.7 | 4.7 |
| Inference (does the conclusion follow?) | 3.3 | 3.1 | 4.3 | 4.5 |
| Likely right (judge's estimate) | 4.2 | 4.1 | 4.4 | 4.4 |
| Usefulness | 3.2 | 3.0 | 4.5 | 4.8 |
| Ranked best | 0 | 0 | 19 | 21 |

Every judgment ranked one of the wwxd arms first. Thinking pages add a small edge on
inference and usefulness; with 40 judgments that's suggestive, not proven. Note that
"likely right" is close for all arms: on questions like these, raw Opus usually gets
the direction right. What it lacks is the person's actual premises, and the persona
prompt invents them (grounding 2.3).

Thinking pages didn't help the held-out test. Built from pre-2026 sources and used to
predict 2026 positions, the vault with thinking pages was preferred over raw Opus 3
of 10 times per vault by Opus and 4 and 2 of 10 by Haiku, no better than without
them. The held-out questions ask for specific positions the person first stated
later (a churn benchmark, a fear about AI policy). A thinking style can settle a
judgment call like the Lamborghini. It can't recover a fact or a number nobody
recorded yet.

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

## Transcription: captions vs Whisper

wwxd uses YouTube's auto-captions when a video has them. To see what that costs in
accuracy, we transcribed one 39-minute interview (Sam Altman and Garry Tan, YC,
`yt-ZIaOBAjvc38`) with four Whisper models and compared each result, and the
captions, with the official speaker-labelled transcript YC published. YC lightly
edited that transcript. It drops fillers and cleans up some sentences, so word error
rate (WER) against it overstates real errors, equally for every system. We aligned
each speaker turn and scored WER per turn, so passages cut from the official
transcript don't count as errors. Whisper ran on the machine's GPU through
faster-whisper (CTranslate2).

| Transcript | WER | Time |
|---|---|---|
| YouTube auto-captions | 31.5% | none, already there |
| Whisper small | 30.1% | 76 s |
| Whisper medium | 31.0% | 168 s |
| Whisper large-v3-turbo | 26.8% | 113 s |
| Whisper large-v3 | 27.2% | 467 s |

The best Whisper model beats the captions by about 5 points, mostly on fillers and
punctuation-level differences. The quote check and the attribution results above
didn't depend on that gap. Transcription isn't the weak step. Attributing who said
what is. So wwxd uses captions first and falls back to Whisper. The default Whisper
model is now "auto", which means large-v3-turbo when wwxd finds a CUDA GPU and small
on CPU. `WWXD_WHISPER_MODEL` or `wwxd fetch --whisper-model` overrides it.

We didn't test audio-capable LLMs, models that take audio and return a transcript
with speakers, and this study used no API keys. They might help with speaker labels,
which Whisper doesn't give. Today `wwxd voice` covers attribution.

## Model and effort study

Which Claude model and which effort level should you use for wwxd's two jobs,
compiling a vault and answering from it? Claude Code's `--effort` sets how much the
model thinks. We tried Opus 5.5, Sonnet 5.5 and Haiku 5.5, each at effort medium,
high and xhigh, so 9 configurations. Every run used `claude -p ... --setting-sources
project --model <id> --effort <e> --strict-mcp-config`, so no advisor and no user
settings. Each configuration ran once. Raw data and scripts are in
[runs/2026-10-10](runs/2026-10-10).

### Compiling

Each configuration compiled the same 4 sources from scratch into empty vaults, one
fresh session per source. Three went into a yc vault: the 39-minute Sam Altman and
Garry Tan interview, a Dalton Caldwell and Michael Seibel video, and a Paul Graham
essay. One Alex Hormozi video went into a hormozi vault.

- Statements is the number of quoted statements in the wiki.
- Attribution takes the statements from the Altman and Tan interview that we could
  match to YC's official speaker-labelled transcript, and counts how many credit the
  right speaker.
- Gold evidence counts how many of the 17 evidence quotes that the main bench's gold
  questions cite from these 4 sources appear in the wiki.
- Cost is Claude Code's reported `total_cost_usd` at list price. Time is wall time
  for all 4 sessions.

Every vault passed `wwxd lint` with no errors, so every quote in every vault matched
the raw transcript.

| Model, effort | Statements | Attribution | Gold evidence | Cost (4 sources) | Time |
|---|---|---|---|---|---|
| Opus medium | 191 | 42 of 42 (100%) | 12 of 17 | $3.41 | 10 min |
| Opus high | 248 | 55 of 57 (96.5%) | 10 of 17 | $5.16 | 16 min |
| Opus xhigh | 288 | 68 of 70 (97.1%) | 11 of 17 | $8.16 | 30 min |
| Sonnet medium | 119 | 31 of 31 (100%) | 8 of 17 | $1.41 | 6 min |
| Sonnet high | 193 | 41 of 42 (97.6%) | 12 of 17 | $2.30 | 12 min |
| Sonnet xhigh | 295 | 59 of 63 (93.7%) | 13 of 17 | $4.51 | 26 min |
| Haiku medium | 87 | 15 of 16 (93.8%) | 5 of 17 | $0.13 | 7 min |
| Haiku high | 113 | 17 of 18 (94.4%) | 6 of 17 | $0.22 | 11 min |
| Haiku xhigh | 146 | 25 of 28 (89.3%) | 6 of 17 | $0.83 | 21 min |

Per source on average, Opus cost $0.85, $1.29 and $2.04 at medium, high and xhigh,
Sonnet $0.35, $0.57 and $1.13, and Haiku $0.03, $0.06 and $0.21.
At xhigh that's more than the README's cost table, which was fit on runs with a Fable
5.1 advisor and counts only the main model. Without an advisor, the main model does
that thinking itself. At xhigh it wrote 1.8 to 3.5 times the output tokens the table
assumes. Against that table, Opus cost 0.73 times as much at medium, 1.1 times at high and 1.75 times at
xhigh.

Higher effort wrote more statements for every model. From medium to xhigh, Opus went
from 191 to 288, Sonnet from 119 to 295 and Haiku from 87 to 146. Time and cost rose
faster than that. The gold evidence barely moved. Opus and Sonnet found 10 to 13 of
the 17 at every setting except Sonnet medium, which found 8, and with 17 items a
difference of 1 or 2 is noise. Haiku found 5 or 6 at any effort, missing about two
thirds, so it isn't fit for compiling. Sonnet high matched Opus medium (12 of 17,
97.6% vs 100% attribution) at about two thirds of the price.

We didn't test whether the extra statements at xhigh make answers better. No answer
runs used the study vaults. One Opus xhigh attempt hit a Claude usage limit mid-run.
We rebuilt both Opus xhigh vaults from scratch and reran them, and the table shows
the rerun.

### Answering

Here the vault stayed fixed. We used the full hormozi and yc vaults from the main
bench, compiled with Opus xhigh. Each of the 9 configurations answered the same 12
questions with the wwxd skill, 6 per vault, a subset of the main gold set
(`gold/hormozi-ask12.yaml`, `gold/yc-ask12.yaml`). So this measures the answering
model only.

Every configuration beat raw Opus 5.5 with no vault in the main bench's pairwise
test, judged by Haiku 5.5. Opus and Sonnet won 12 of 12 at every effort and Haiku
won 11 of 12. That's a ceiling, so it can't separate the configurations.

To separate them, a judge saw all 9 answers to a question at once, shuffled and with
citations stripped, along with the grading key and the raw transcripts. It scored
accuracy, specificity, faithfulness and usefulness from 1 to 5 and ranked all 9
(`prompts/judge_rank.md`). Two judges ranked every question, Opus 5.5 at effort
medium and Haiku 5.5 at effort high, each with a different answer order. Over the 12
questions:

| Configuration | Mean rank, Opus judge | Ranked first | Mean rank, Haiku judge | Ranked first |
|---|---|---|---|---|
| Opus medium | 4.17 | 0 | 4.25 | 1 |
| Opus high | 2.50 | 4 | 2.58 | 4 |
| Opus xhigh | 1.75 | 6 | 3.58 | 4 |
| Sonnet medium | 5.75 | 0 | 4.83 | 0 |
| Sonnet high | 4.83 | 0 | 4.92 | 1 |
| Sonnet xhigh | 3.42 | 2 | 3.58 | 2 |
| Haiku medium | 8.33 | 0 | 7.83 | 0 |
| Haiku high | 7.25 | 0 | 6.83 | 0 |
| Haiku xhigh | 7.00 | 0 | 6.58 | 0 |

A rank of 1 is best and 9 is worst. Pooled over both judges and all efforts, the
mean rank was 3.1 for Opus, 4.6 for Sonnet and 7.3 for Haiku. Pooled over models, it
was 5.9 at medium, 4.8 at high and 4.3 at xhigh. All Opus and Sonnet answers were
good in absolute terms. The Opus judge gave Opus 4.83 to 5.00 for accuracy at every
effort and Sonnet 4.75 to 5.00. Haiku got 3.92 to 4.17 for accuracy and 3.33 to 3.67
for usefulness. So the ranking separates Opus and Sonnet on specificity and
usefulness, not on errors.

Head to head, out of 24 judgments (12 questions, 2 judges):

| Comparison | Ranked higher |
|---|---|
| Opus high over Opus medium | 18 of 24 (9 of 12 for each judge) |
| Opus xhigh over Opus high | 14 of 24 (8 and 6 of 12), no clear difference |
| Opus xhigh over Opus medium | 18 of 24 |
| Sonnet high over Sonnet medium | 13 of 24, no clear difference |
| Sonnet xhigh over Sonnet medium | 18 of 24 (10 and 8 of 12) |
| Haiku xhigh over Haiku medium | 16 of 24 |
| Opus medium over Sonnet medium | 18 of 24 |
| Opus high over Sonnet high | 21 of 24 |
| Opus xhigh over Sonnet xhigh | 15 of 24 (the judges split, 10 and 5 of 12) |
| Sonnet xhigh over Opus medium | 15 of 24 |
| Sonnet high over Opus medium | 9 of 24 |
| Sonnet medium over Haiku xhigh | 19 of 24 |

A sign test that treats the 24 judgments as independent gives p of about 0.02 for 18
of 24 and below 0.001 for 21 of 24. Both judges saw the same answers, so the
judgments aren't fully independent and these p values are optimistic.

A script checked every quote an answer attributed to someone against the raw
transcripts, with no model involved. Opus had 158 of 159 verified across the three
efforts. The one miss was a video title quoted as a title. Sonnet had 199 of 199.
Haiku had 151 of 159, about 95%. Its misses include "under 10% churn as best" and
"every field has one center.", which aren't in the sources. Per configuration:

| Quotes verified | medium | high | xhigh |
|---|---|---|---|
| Opus | 47 of 48 | 46 of 46 | 65 of 65 |
| Sonnet | 47 of 47 | 75 of 75 | 77 of 77 |
| Haiku | 49 of 52 | 40 of 42 | 62 of 65 |

Median seconds per answer at medium, high and xhigh were 29, 37 and 50 for Opus, 19,
27 and 53 for Sonnet, and 19, 31 and 62 for Haiku. Answers got longer with effort for
Opus (median 524 to 670 words) and Sonnet (556 to 691). We didn't record the token
cost of the answers.

The model matters more than the effort. Haiku ranks last at every effort and gets
about 1 quote in 20 wrong. Going from medium to high clearly helps Opus. Going from
high to xhigh doesn't clearly help Opus, but it does help Sonnet. Sonnet at xhigh is
about as good as Opus at medium.

### Recommendation

| Job | Use | Notes |
|---|---|---|
| Compile | Sonnet high, or Opus medium if you're on Opus anyway | xhigh writes a denser vault for 2 to 3 times the time and cost, and didn't find more of the key evidence. Not Haiku. |
| Answer | Opus high | Opus xhigh isn't clearly better and takes longer. On a tighter budget, Sonnet xhigh ranked about as well as Opus medium. Not Haiku. |
| Triage | A cheap model | Picking which videos to keep needs only titles, channels and durations. |

You don't need an advisor model. This study ran without one, and in our earlier runs
it doubled the compile cost.

### Limits of this study

Each configuration ran once, on 4 sources and 12 questions. Gold evidence has 17
items, and the attribution counts range from 16 to 70 statements. There were two
judges, and one of them is from the same model family as the answers. The judges had
to rank 9 answers that were often close. We didn't test whether a denser vault gives
better answers. Costs are Claude Code's list-price estimates. On a subscription you
pay in usage limits instead.

## Answer format: prose with sources underneath

We changed the answer format after a judge from another lab said wwxd answers read
"like an annotated transcript" (see [A judge from Google](#a-judge-from-google)). The
old format had labelled sections (Verdict, Based on, How we get there, Why they'd say
it) with the quotes inline. The new one gives the advice as plain prose with numbered
markers like [1]. Under it comes a Sources list of verbatim quotes, each with who said
it, the title, the date and a timestamped link, and then a "Based on" line. The
template is in `skills/wwxd/references/ask.md`.

Both formats ran with Opus 5.5 at effort high on the same vaults. There were two
judges. Opus 5.5 at effort medium could read the raw transcripts. Gemini 3.5 Flash
Lite had no tools and saw only the grading key.

On the 12 questions of the ask12 set, each judge compared the old and new answer
pairwise.

| Judge | New format | Tie | Old format |
|---|---|---|---|
| Opus 5.5 | 8 | 2 | 2 |
| Gemini 3.5 Flash Lite | 4 | 8 | 0 |

In the two the Opus judge gave to the old format (`hz-11`, `yc-05`), both answers had
the key position and verified quotes, and the old one included one more specific
point.

On the 24 opinion questions, each judge ranked three answers: the old format, the new
format and raw Opus. The wwxd arms ran at effort high. The raw arm is the original raw
answers from the opinion bench. The new format ranked first on 20 of 24 with both
judges.

| Opus judge, 1 to 5 | New format | Old format | Raw Opus |
|---|---|---|---|
| Decisiveness | 4.92 | 4.62 | 3.50 |
| Distinctiveness | 4.75 | 4.46 | 2.67 |
| Grounding | 4.88 | 4.21 | 2.75 |
| Usefulness | 4.38 | 3.88 | 3.96 |
| Mean rank | 1.17 | 2.00 | 2.83 |
| Pick contradicts the person | 0 | 0 | 1 |

| Gemini 3.5 Flash Lite judge, 1 to 5 | New format | Old format | Raw Opus |
|---|---|---|---|
| Decisiveness | 4.75 | 4.54 | 3.50 |
| Distinctiveness | 4.88 | 4.42 | 3.54 |
| Grounding | 4.96 | 4.50 | 3.21 |
| Usefulness | 4.92 | 4.38 | 4.50 |
| Mean rank | 1.17 | 2.08 | 2.75 |
| Pick contradicts the person | 0 | 0 | 1 |

With the Opus judge, the old format scored a little below raw Opus on usefulness
(3.88 vs 3.96), and the new format scored 4.38.

The new answers are longer. Their median length was 717 to 794 words, against 606 to
671 for the old format. Two old-format YC opinion answers first failed on a Claude
usage limit, and we reran them before judging. The data is in
`runs/2026-10-10/<vault>-prose/`.

## A judge from Google

Gemini 3.5 Flash Lite, on the free tier, judged the main bench, the opinion bench and
the model and effort ranking. It ran without file tools, one API call per judgment, so
it could check answers only against the grading key and what it already knew. The
free tier allows too few requests for an agent that greps transcripts. Gemini 3.8
Flash, for example, allows 20 requests a day per key.

On the main bench it preferred wwxd on 34 of 40 pairs. The other judges preferred
wwxd on 40 of 40 (Opus), 40 of 40 (Haiku), 39 of 40 (Nemotron) and 35 of 36 (Muse
Spark). On the opinion bench, with the old answer format, it ranked wwxd first on 12
of 24 questions, the persona prompt on 10 and raw Opus on 2.

On the model and effort ranking it put the models in the same order as the Claude
judges, with a mean rank of 2.64 for Opus, 4.67 for Sonnet and 7.69 for Haiku.

| Mean rank, Gemini judge | medium | high | xhigh |
|---|---|---|---|
| Opus | 2.50 | 3.50 | 1.92 |
| Sonnet | 4.42 | 4.67 | 4.92 |
| Haiku | 8.33 | 7.58 | 7.17 |

It doesn't reproduce the effort trend within Sonnet, where both Claude judges ranked
xhigh above medium.

The main and opinion numbers are lower than the other judges' for three reasons we
found in its comments:

- Without the transcripts, it called real 2026 statements fabricated in `hz-09` and
  `yc-09`. Those statements are after its training data.
- It can't tell an answer that sounds like Hormozi from one that quotes what he said.
  So it scored the persona answers' grounding close to wwxd's.
- In several losses it said the wwxd answer read like an annotated transcript
  (`hz-01`, `yc-06`, `yc-12`). That led to the format change above.

The data is in `runs/2026-10-10/<vault>-gemini-judge/`.

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

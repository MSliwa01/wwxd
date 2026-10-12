# wwxd

[![CI](https://github.com/MSliwa01/wwxd/actions/workflows/ci.yml/badge.svg)](https://github.com/MSliwa01/wwxd/actions/workflows/ci.yml)
[![Python 3.10 to 3.13](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](https://github.com/MSliwa01/wwxd/blob/main/pyproject.toml)
[![MIT license](https://img.shields.io/badge/license-MIT-green)](https://github.com/MSliwa01/wwxd/blob/main/LICENSE)

What would X do? wwxd turns a person's talks, podcasts and essays into a wiki of
their positions, with every quote checked against the source. Your agent then
answers the way that person would, and shows you where they said it.

Answers are inferred from public sources by a language model. They are not
statements by these people, and none of them is affiliated with or endorses wwxd.
See [ETHICS.md](https://github.com/MSliwa01/wwxd/blob/main/ETHICS.md).

![Opus told to answer as Hormozi contradicts him; Opus with a wwxd vault quotes him](https://raw.githubusercontent.com/MSliwa01/wwxd/main/docs/img/wwxd-vs-persona.png)

## Try it

You need [uv](https://docs.astral.sh/uv/), [Claude Code](https://claude.com/claude-code),
ffmpeg, and deno or node 22 or newer.

```bash
uv tool install "git+https://github.com/MSliwa01/wwxd" && wwxd install-skill && wwxd doctor
```

Compiling costs about $1 to $2 per video on Opus at list price, so run
`wwxd estimate <slug>` first. The [Quick start](#quick-start) has the next steps.

## Why

Ask a chatbot whether to raise your prices and you get a generic answer that commits
to nothing. That's fine for facts. It's weak for decisions in business, design,
careers or learning, where the useful advice comes from people with strong opinions
and a track record. Ask the model to answer "as Alex Hormozi" and you get a plausible
impression, built from whatever it remembers, with the gaps filled by its own
guesses. It can't know anything the person said after its training cutoff, and it
mixes up who said what, crediting a podcast host's line to the guest.

wwxd gives the agent the person's own words instead. Here is a question from our
benchmark, answered by Claude Opus 5.5 in Claude Code.

> I have $50k saved. Should I pay off my car loan and credit cards or put it all into
> my business? What would Alex Hormozi say?

Told to answer decisively as Hormozi, Opus says to keep the car loan unless its rate
is high. With a Hormozi vault, the answer starts like this:

> **He'd tell you to pay off the credit cards first and the car loan next. Then put what's left into the business, but only into spending that has already shown it pays back. Don't put all of it in.**
>
> Hormozi never talked about this exact choice, but his rules on it are clear. He says he leans "very close to the Ramsey side" on debt. His reason is that debt adds risk, and risk held for a long time tends to come due, because businesses have seasons and swings [1][2]. … His ideal car is "a paid-off clunker" [4]. So pay the car off, or if the payment is large, sell the car and buy something cheap with cash.
>
> …
>
> **Sources**
> 1. "I'd say this is more of an emotional thing, but it's just this back of mind thing." / "I tend to skew like very close to the Ramsey side" (Hormozi, *Building a $2,500,000 Business for a Stranger in 36 Minutes*, 2026-05-08, [8:37](https://www.youtube.com/watch?v=OQf2Ba-Lp_4&t=517s))
> 2. "Risk when multiplied over a long time horizon tends to come due." / "businesses have seasons, they have volatility" (same video, [9:10](https://www.youtube.com/watch?v=OQf2Ba-Lp_4&t=550s))
>
> …
>
> 4. "ideally a paid-off clunker is the best way to go." (Hormozi, *If I Wanted to Make My First $100K in 2026*, 2026-03-04, [2:08](https://www.youtube.com/watch?v=jfW6gL6hKhk&t=128s))

The full answer is question `op-hz-06` in
[bench/runs/2026-10-11/hormozi-web/op-prose-answers.jsonl](https://github.com/MSliwa01/wwxd/blob/main/bench/runs/2026-10-11/hormozi-web/op-prose-answers.jsonl).

## Results

On 40 questions across a Hormozi vault and a Y Combinator vault, a blind judge
preferred the wwxd answer every time.

| Blind judge, 1 to 5 | Opus 5.5 alone | Opus 5.5 + wwxd |
|---|---|---|
| Accuracy | 2.7 | 5.0 |
| Specificity (vs. generic advice) | 2.0 | 4.9 |
| Faithfulness | 3.2 | 4.6 |
| Preferred by the judge | 0 of 40 | 40 of 40 |

Three more judges scored the same pairs: Claude Haiku 5.5 (40 of 40 for wwxd), and
from other model families NVIDIA Nemotron 3 Ultra (39 of 40) and Muse Spark 1.3 (35
of 36), so this isn't one model grading itself. A judge from Google, Gemini 3.5 Flash
Lite, preferred wwxd on 34 of 40 with no access to the transcripts
([details](https://github.com/MSliwa01/wwxd/blob/main/bench/RESULTS.md#a-judge-from-google)).
A script checked the 160 quotes in the wwxd answers against the transcripts and found
158 verbatim. The other 2 were video titles.

![Five judges from four labs preferred wwxd on 34 of 40 up to 40 of 40 pairs](https://raw.githubusercontent.com/MSliwa01/wwxd/main/docs/img/chart-judges.png)

The other benches are in [docs/benchmarks.md](https://github.com/MSliwa01/wwxd/blob/main/docs/benchmarks.md),
and the full numbers, setup and caveats in [bench/RESULTS.md](https://github.com/MSliwa01/wwxd/blob/main/bench/RESULTS.md).

- Told to be decisive "as X", Opus stops hedging but invents its reasons. On 24
  opinion questions, four judges ranked wwxd first in 93 of 93 judgments.
- Against Opus with web search, judges preferred wwxd on 34 to 39 of 40 pairs (Muse
  Spark: 33 of 35). Search mostly finds other people's summaries.
- On questions the people never answered, every judgment ranked a wwxd answer first.
- wwxd doesn't predict. A vault of older sources was no better than raw Opus at
  guessing positions the people took later.

These runs used Opus 5.5. Sonnet 5.5 works about as well for compiling and nearly as
well for answering, and Haiku 5.5 ranked last of the three
([details](https://github.com/MSliwa01/wwxd/blob/main/docs/models-and-cost.md)).

## How it works

```
discover ──▶ you approve ──▶ fetch ──▶ compile ──▶ lint ──▶ ask
  (CLI)         (CLI)         (CLI)    (agent)     (CLI)   (agent)
```

The `wwxd` CLI does the mechanical work. It finds sources (the person's YouTube
channels, podcast feeds, blog RSS, essay index pages), downloads existing captions
and podcast transcripts, falls back to local Whisper when there are none, and checks
the wiki.

Your agent does the reading. A Claude Code skill tells it how to work out who's
speaking in each transcript, pull out verbatim quotes, and file them into a topic
tree. You don't need an API key, because it runs on the agent you already use.

The design follows Andrej Karpathy's
[LLM wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).
Raw sources never change, the LLM maintains a wiki on top of them, and every new
source updates what's already there. wwxd adds these parts for a wiki about one
person.

- Discovery flags summaries, reactions and "lessons from" videos, so you only approve
  content by the person, not about them.
- Every statement records who said it and how sure the agent is. Low-confidence lines
  and second-hand claims ("my mentor told me...") never count as the person's view.
- Each quote carries a timestamp, and `wwxd lint` checks it against the transcript in
  code. A quote that isn't in the source fails, however plausible it sounds.
- Topic pages keep what the person said apart from what they did. `tensions.md`
  tracks how their views changed over time.
- Each person gets a thinking page: what they optimize for, the rules they decide
  by, how they reason, and their strong likes and dislikes, with quotes. When you ask
  about something they never mentioned, the agent reasons from it the way they would,
  names the rule, gives a confidence and says what would break the inference.
- The wiki is a tree (person, domain, topic, page), or flat with `layout: flat`. A
  vault can hold a group, like the YC partners, and still credit every line to the
  right person.
- The agent's own extrapolations go to `derived/`, and lint stops them from being
  cited as evidence later.

## Quick start

Before you start, install these and run `wwxd doctor` to check them.

- [uv](https://docs.astral.sh/uv/)
- [Claude Code](https://claude.com/claude-code)
- ffmpeg
- deno, or node 22 or newer

```bash
uv tool install "git+https://github.com/MSliwa01/wwxd"
wwxd install-skill                                            # into ~/.claude/skills/wwxd
wwxd doctor
```

Videos without captions and podcasts without published transcripts need local
Whisper. The `whisper` extra installs it, and `voice` adds the
[voice check](#check-who-said-it-by-voice).

```bash
uv tool install --force "wwxd[whisper,voice] @ git+https://github.com/MSliwa01/wwxd"
```

Without `whisper`, `wwxd fetch` marks those sources as failed and fetches the rest.
After you install it, `wwxd fetch <slug> --retry-failed` picks them up.

Instead of `wwxd install-skill`, you can install the skill as a Claude Code plugin
with `/plugin marketplace add MSliwa01/wwxd` and `/plugin install wwxd@wwxd`. You
still need the CLI. Don't use both, or Claude Code loads the skill twice.

Then create a vault and find candidate sources. `wwxd examples` lists the bundled
recipes (`yc`, `hormozi`, `naval`, `karpathy`, `rams`). A recipe is a source config,
never content, and not an endorsement.

```bash
wwxd new hormozi --example hormozi
wwxd discover hormozi                                         # nothing is downloaded yet
```

Then, in Claude Code:

> Help me curate the hormozi vault, fetch what we approve, and compile it.

The agent goes through the candidates with you, runs `wwxd fetch`, compiles each
source and runs `wwxd lint`. Each source takes it a few minutes, and
`wwxd compile hormozi --jobs 4` compiles several at once
([details](https://github.com/MSliwa01/wwxd/blob/main/docs/models-and-cost.md#compile-many-sources-at-once)).
After that:

> My agency does $40k a month with three people. Should I add a second service line?
> What would Hormozi say?

For someone without a recipe, run `wwxd new jane --name "Jane Doe"` and ask the
agent to find her channels and feeds. To keep a vault up to date, see
[docs/keeping-current.md](https://github.com/MSliwa01/wwxd/blob/main/docs/keeping-current.md).

## What it costs

Fetching, lint and the voice check run on your machine and cost nothing. Compiling
and asking run on your agent, so they cost tokens: dollars on the API, usage limits
on a Claude subscription. `wwxd estimate <slug>` prices what you've approved, before
anything is fetched. Rough numbers from our runs on Opus 5.5:

| | Tokens | Time | Opus 5.5 | Sonnet 5.5 | Haiku 5.5 |
|---|---|---|---|---|---|
| Compile a 20-minute video (about 3,000 words) | about 1M | 4 min | $1.06 | $0.63 | $0.03 |
| Compile a 2-hour podcast (about 18,000 words) | about 2.1M | 8 min | $1.91 | $1.15 | $0.06 |
| One question to a vault | about 0.3M | 30 s | $0.41 | $0.23 | $0.01 |

A panel of three people costs roughly three questions. Effort, advisors and which
model to use for each job are in
[docs/models-and-cost.md](https://github.com/MSliwa01/wwxd/blob/main/docs/models-and-cost.md).

<details>
<summary>Example <code>wwxd estimate</code> output</summary>

```
$ wwxd estimate hormozi
13 sources, about 87,336 words
tokens: 17.1M total (15.8M cache reads, 0.96M cache writes, 0.28M output)
time: about 65 min of agent work one source at a time; `wwxd compile hormozi --jobs N` runs N at once for the same cost
list price if billed per token (the real number can be about 50% lower or higher):
  opus    claude-opus-5-5    $   16.50
  sonnet  claude-sonnet-5-5  $    9.83
  haiku   claude-haiku-5-5   $    0.49
Measured on Opus without an advisor, compiling cost 0.73x this at effort medium, 1.1x this at effort high, 1.75x this at effort xhigh.
```

</details>

## Ask a panel

Ask several people at once ("what would Hormozi, Paul Graham and Garry Tan tell me?")
and the agent answers for each one from their own vault, then maps where they agree
and where they split. For each split it names the reason from their thinking pages,
such as a value they rank differently or a rule only one of them holds. A debate
round gives each person's reply to the other's strongest point, built only
from their own words and labelled as inferred. Last comes a synthesis in the agent's
own voice that says which advice fits which situation.

Asked by someone who loves building AI tools but fears AI will take their income,
the panel disagreed. Hormozi: sell one AI skill people already pay for, expensive
and one-on-one, before building any app ("The middle is where people die"). Graham:
follow your curiosity, because for someone young and good at technology "working on
what you're most interested in becomes a good idea again". Tan: own your tools,
because "if you don't, your job becomes a skill file". They agreed that fear is the
wrong response, each for a different reason, which the synthesis treats as the
strongest signal in the answer. `wwxd vaults` lists every vault, its members and
which ones have thinking pages.

## Check who said it, by voice

Lint proves a quote exists. It can't prove who said it, and that's the mistake that
matters most. A real quote credited to the wrong person passes lint.
`wwxd voice <slug>` checks attribution by sound. It finds the second each quote is
spoken, embeds that audio with a speaker-verification model, and compares it with
each member's voiceprint. The voiceprints come from the vault itself, so there's
nothing to enroll. It runs on CPU with a small open model, needs no account or API
key, and comes with the `voice` extra.

On our test vaults it checked 1,423 statements from 26 videos in under 4 minutes on
CPU and flagged 9 as spoken by someone else. We confirmed 6 of them
([case studies](https://github.com/MSliwa01/wwxd/blob/main/docs/benchmarks.md#voice-check-case-studies)).
Lint shows its mismatches as warnings until someone fixes the attribution.

## CLI

<details>
<summary>All commands</summary>

| Command | What it does |
|---|---|
| `wwxd new <slug> --example X` or `--name "Full Name"` | Create a vault |
| `wwxd examples` | List the bundled example recipes |
| `wwxd discover <slug>`, `wwxd update <slug>` | Find new candidate sources |
| `wwxd update <slug> --approve-hint own --fetch` | Also approve new candidates with that hint and fetch them |
| `wwxd sources <slug> --status candidate` | List sources |
| `wwxd approve <slug> <ids>`, `wwxd reject <slug> <ids>` | Curate |
| `wwxd add <slug> <url or file>` | Add a source by hand |
| `wwxd estimate <slug> [--asks N]` | Estimate tokens, list-price dollars and time to compile, per model |
| `wwxd fetch <slug>` | Download captions, transcripts and articles into `raw/` |
| `wwxd pending <slug>`, `wwxd mark-compiled <slug> <id>` | List sources fetched but not compiled, record a compiled source in `log.md` |
| `wwxd compile <slug> --jobs N` | Compile pending sources with N Claude Code sessions at once ([details](https://github.com/MSliwa01/wwxd/blob/main/docs/models-and-cost.md#compile-many-sources-at-once)) |
| `wwxd lint <slug> [--only <path>]` | Check quotes, citations, attribution and links, and flag drift such as near-duplicate leaves |
| `wwxd health <slug>` | Report on the wiki: size, attribution, coverage, near-duplicates, oversize leaves |
| `wwxd timeline <slug> [query]` | Statements by source date and member, to see how views changed |
| `wwxd digest <slug> --since YYYY-MM-DD` | Markdown note on what's new since a date |
| `wwxd search <slug> "query"` | Keyword search over the wiki (`--raw` adds transcripts) |
| `wwxd status <slug>` | Summary |
| `wwxd vaults` | List vaults with their members and thinking pages, for panels |
| `wwxd voice <slug> [ids]` | Check who is speaking in each quote, by voice (needs `wwxd[voice]`) |
| `wwxd doctor` | Check yt-dlp, the JS runtime, ffmpeg, Whisper and `$WWXD_HOME` |
| `wwxd install-skill [--project]`, `wwxd version` | Install the wwxd skill for Claude Code, print the version |
| `wwxd bench run`, `judge`, `rank`, `report` | [Benchmarks](https://github.com/MSliwa01/wwxd/blob/main/bench/README.md) |

</details>

Vaults are plain markdown folders and open in Obsidian. `$WWXD_HOME` sets where they
live (default `./vaults`).

## Sources and copyright

wwxd ingests public captions, podcast transcripts and articles. It downloads audio
only to process it on your machine, with Whisper when a source has no transcript and
for the voice check. It doesn't fetch books, and this repo ships no content. You can
add books you own as text files (`wwxd add <slug> book.txt`) or write a
[fetcher plugin](https://github.com/MSliwa01/wwxd/blob/main/CONTRIBUTING.md#fetcher-plugins).
Don't publish vaults built from material you don't have the right to share.
[ETHICS.md](https://github.com/MSliwa01/wwxd/blob/main/ETHICS.md) has the rules for
using vaults and explains how a person can have their recipe removed.

## Requirements

Run `wwxd doctor` to check your setup. It marks each item below OK, WARN or FAIL and
makes no network calls.

- Python 3.10 or newer.
- A JavaScript runtime for YouTube: [deno](https://deno.com), node 22 or newer, or
  [bun](https://bun.sh). wwxd picks the first of these on your PATH for yt-dlp.
  Without one, some videos lose formats or fail.
- ffmpeg, which yt-dlp needs to convert some audio downloads.
- Whisper, for sources without captions. Most podcasts need it, unless the feed
  publishes transcripts (`podcast:transcript` tags), which wwxd uses instead. Whisper
  runs on CPU, and much faster on a GPU. wwxd picks the model for you, large-v3-turbo
  on a CUDA GPU and small on CPU. `WWXD_WHISPER_MODEL` and `WWXD_WHISPER_DEVICE` set
  the defaults, and `wwxd fetch --whisper-model large-v3` changes the model for one
  run.

If YouTube asks you to sign in or rate limits a fetch, see
[docs/troubleshooting.md](https://github.com/MSliwa01/wwxd/blob/main/docs/troubleshooting.md).

## Credits

The raw-sources-plus-compiled-wiki loop is Andrej Karpathy's LLM wiki idea. wwxd adds
sourcing, speaker attribution and quote checking for the one-person case. Design notes
are in [docs/design.md](https://github.com/MSliwa01/wwxd/blob/main/docs/design.md). MIT licensed.

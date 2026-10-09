# wwxd

[![CI](https://github.com/MSliwa01/wwxd/actions/workflows/ci.yml/badge.svg)](https://github.com/MSliwa01/wwxd/actions/workflows/ci.yml)

What would X do? wwxd turns a person's talks, podcasts and essays into a wiki of
their actual positions, with every quote checked against the source. Your agent then
answers the way that person would, and shows you where they said it.

## Why

Ask a chatbot whether to raise your prices and you get the average of the internet.
It lists considerations, recommends testing, warns you to communicate value, and
commits to nothing. Models are trained to be balanced and safe, so their advice comes
out smooth and generic. That's fine for facts. It's weak for decisions in business,
design, careers or learning, where the useful advice comes from people with strong
opinions and a track record.

You can ask the model to answer "as Alex Hormozi". It will give you a plausible
impression, built from whatever it remembers, with the gaps filled by its own
guesses. It can't know anything the person said after its training cutoff. It also
mixes up who said what, crediting a podcast host's line to the guest.

wwxd gives the agent the person's own words instead. Here is the same question
answered both ways by Claude Opus 5.5 in Claude Code.

> I own a residential HVAC duct-cleaning company doing about $1.2M a year at a 38%
> net margin, and we close about 82% of in-home inspections. Should I keep prices
> where they are so I don't hurt the close rate? What would Alex Hormozi say?

Without a vault, Opus says an 82% close rate usually means underpricing, then
suggests a "healthy" 40 to 60 percent close rate and builds a table on a margin it
assumed.

With the vault, the answer starts like this:

> **Short answer:** No. Hormozi would tell you to raise prices. An 82% close rate
> is, in his words, the sign you're underpriced. His suggested step is about 10%,
> and it's only worth it if your close rate stays above roughly 65%.
>
> Your numbers are almost the same as a business he consulted on in 2026: ProShine,
> an HVAC duct-cleaning company doing $1.25M a year at a 38% net margin with an 82%
> close rate. So this isn't a guess from his general principles. He has already given
> this advice to a business like yours.
>
> - **A close rate over 80% means you're underpriced:** "So whenever I hear 80% or
>   over 80% close rates, I usually know that there's room in sale."
>   ([@ 8:06](https://www.youtube.com/watch?v=OQf2Ba-Lp_4&t=486s))

## Results

On 40 questions across a Hormozi vault and a Y Combinator vault, a blind judge
preferred the wwxd answer every time.

| Blind judge, 1 to 5 | Opus 5.5 alone | Opus 5.5 + wwxd |
|---|---|---|
| Accuracy | 2.7 | 5.0 |
| Specificity (vs. generic advice) | 2.0 | 4.9 |
| Faithfulness | 3.2 | 4.6 |
| Preferred by the judge | 0 of 40 | 40 of 40 |

Two judges from other model families, NVIDIA Nemotron 3 Ultra and Muse Spark 1.3
(both free through opencode), scored the same pairs and preferred wwxd 39 of 40 and
35 of 36 times, so this isn't Claude grading Claude. 160 quotes in the wwxd answers
were checked against the transcripts by a script, and 158 were found verbatim. The
other 2 were video titles.

### Opinionated isn't the same as right

The obvious fix for bland answers is to tell the model to be decisive. We tried it
on 24 "should I do X or Y?" questions, with three judges ranking three answers to
each: raw Opus, Opus told to answer decisively as the person would, and Opus with
the vault.

| Mean of three judges, 1 to 5 | Raw | "Be decisive, as X" | wwxd |
|---|---|---|---|
| Decisiveness | 3.4 | 4.8 | 4.7 |
| Distinctiveness | 2.9 | 3.1 | 4.9 |
| Grounding (reasons they really hold) | 2.8 | 2.7 | 5.0 |
| Ranked best | 0 | 0 | 69 of 69 |
| Pick contradicts the person | 7 | 6 | 0 |

The persona prompt stops the hedging, but its reasons are generic or invented. Asked
"I have $50k saved, should I pay off my car loan or put it into my business?", it
said to keep the low-rate loan, the standard financial-advice answer. Hormozi says
"ideally just pay off your car so you don't have to think about it again" and that
he skews "very close to the Ramsey side". wwxd quoted both.

### What wwxd doesn't do

It doesn't predict. We rebuilt both vaults from pre-2026 sources only and asked about
positions the people first took in 2026. The vault answers were no better than raw
Opus: one judge called it even, and two judges from other model families preferred
raw Opus. A vault keeps answers faithful to what someone has said. It can't know
what they'll say next, so keep it current with `wwxd update`. Full numbers, setup
and caveats are in [bench/RESULTS.md](bench/RESULTS.md).

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
source updates what's already there. wwxd adds the parts that matter when the
subject is one person.

- Discovery flags summaries, reactions and "lessons from" videos, so you only approve
  content by the person, not about them.
- Every statement records who said it and how sure the agent is. Low-confidence lines
  and second-hand claims ("my mentor told me...") never count as the person's view.
- Each quote carries a timestamp, and `wwxd lint` checks it against the transcript in
  code. A quote that isn't in the source fails, however plausible it sounds.
- Topic pages keep what the person said apart from what they did. `tensions.md`
  tracks how their views changed over time.
- The wiki is a tree (person, domain, topic, page). `layout: flat` is available if
  you want to compare.
- A vault can hold a group, like the YC partners, and still credit every line to the
  right person.
- The agent's own extrapolations go to `derived/`, and lint stops them from being
  cited as evidence later.

## Check who said it, by voice

Lint proves a quote exists. It can't prove who said it, and that's the mistake that
matters most. A real quote credited to the wrong person looks exactly like a good
one. `wwxd voice <slug>` checks attribution by sound. It finds the second each quote
is spoken, embeds that audio with a speaker-verification model, and compares it with
each member's voiceprint. The voiceprints come from the vault itself, so there's
nothing to enroll.

On our test vaults it checked 1,423 statements from 26 videos in under 4 minutes on
CPU. It flagged 9 as spoken by someone else. We could verify 6 of them:

- In a Sam Altman and Garry Tan conversation, 3 lines the compile credited to Tan
  were Altman's. The official speaker-labelled transcript confirms all 3. Across the
  54 statements from that episode we could match to the official transcript, the
  compile got 51 right and the voice check got all 54.
- In a Dalton Caldwell and Michael Seibel episode, 2 teaser lines credited to Dalton
  match Michael's voice, and the intro right after them is "hey this is Michael
  Seibel with Dalton Caldwell".
- In a Hormozi consulting call, a line credited to Hormozi sits in the business
  owner's turn, where he explains his own sales process.

The other 3 flags are in Dalton and Michael episodes with no official transcript, so
they're still unconfirmed.

The voice check is optional: `uv tool install "wwxd[voice] @ git+https://github.com/MSliwa01/wwxd"`.
It runs on CPU with a small open model and needs no account or API key. Lint shows
its mismatches as warnings until someone fixes the attribution.

## Quick start

```bash
uv tool install "git+https://github.com/MSliwa01/wwxd"
# with local Whisper for podcasts and videos without captions:
# uv tool install "wwxd[whisper] @ git+https://github.com/MSliwa01/wwxd"
wwxd install-skill                                            # into ~/.claude/skills/wwxd
```

If you use Claude Code plugins, you can install the skill as a plugin instead of
running `wwxd install-skill`. Run these two commands in Claude Code.

```
/plugin marketplace add MSliwa01/wwxd
/plugin install wwxd@wwxd
```

The plugin installs the skill only. Keep the `uv tool install` line for the CLI;
without it, the agent falls back to `uvx`, which needs [uv](https://docs.astral.sh/uv/).
Don't use both `install-skill` and the plugin, or Claude Code loads the skill twice.

Then create a vault and find candidate sources.

```bash
wwxd new hormozi --example hormozi
wwxd discover hormozi                                         # nothing is downloaded yet
```

Then, in Claude Code:

> Help me curate the hormozi vault, fetch what we approve, and compile it.

The agent goes through the candidates with you, runs `wwxd fetch`, compiles each
source and runs `wwxd lint`. Each source takes it a few minutes. After that:

> My agency does $40k a month with three people. Should I add a second service line?
> What would Hormozi say?

For someone without a recipe, run `wwxd new jane --name "Jane Doe"` and ask the agent
to find her channels and feeds.

## Example recipes

`wwxd examples` lists them. A recipe is a source config, never content.

| Recipe | Topics | Notes |
|---|---|---|
| `yc` | startups | A group vault covering Paul Graham, Jessica Livingston, Michael Seibel, Dalton Caldwell, Garry Tan and Sam Altman, plus PG's essays. |
| `hormozi` | business, sales, pricing | Long-form videos and podcast appearances. |
| `naval` | wealth, philosophy | His podcast feed and posts. |
| `karpathy` | learning, AI | Lectures, blog, interviews. |
| `rams` | design | Few English sources, so expect a small vault. |

These are starting points, not endorsements. You don't have to agree with any of
these people. The vault worth building is the one for the person you learn from.

## Use a cheaper model for triage

Deciding which candidate videos to keep only needs titles, channels and durations.
A small, cheap model does it well. In our test, a free model triaged 39 candidates
for the Dieter Rams vault in 20 seconds, and its picks held up on review.
Keep the strong model for compiling and answering. That's where attribution happens,
and lint can catch an invented quote but not a real quote credited to the wrong
person.

## Keep a vault current

People keep publishing, so a vault goes stale. `wwxd update` finds new sources.
`--approve-hint own` approves the new ones from the person's own channels and feeds,
and `--fetch` downloads them. Candidates you left pending before stay pending, and
the other new ones wait for your review.

A weekly cron line covers the CLI part.

```cron
# Mondays at 7:00
0 7 * * 1  WWXD_HOME=$HOME/vaults $HOME/.local/bin/wwxd update hormozi --approve-hint own --fetch >> $HOME/vaults/hormozi-update.log 2>&1
```

Compiling needs an agent. A Claude Code scheduled agent (`/schedule`) can run the
whole loop. It needs `wwxd` installed and access to the vault. Give it a prompt like
this one.

> Keep the hormozi wwxd vault current. Run
> `wwxd update hormozi --approve-hint own --fetch`, and list the other new
> candidates for me without approving them. Compile every source in
> `wwxd pending hormozi` with the wwxd skill (references/compile.md), running
> `wwxd lint hormozi` and `wwxd mark-compiled` after each one. Then run
> `wwxd health hormozi`, and if it asks for a consolidation pass, follow
> references/consolidate.md. Finish with `wwxd digest hormozi --days 7` and show
> me the digest.

`wwxd digest` writes a markdown note on what's new: the sources compiled, the leaves
created or updated, and new statements grouped by leaf. `--out` saves it, for
example into your notes app's folder.

## CLI

| Command | What it does |
|---|---|
| `wwxd new <slug> --example X` or `--name "Full Name"` | Create a vault |
| `wwxd discover <slug>`, `wwxd update <slug>` | Find new candidate sources |
| `wwxd update <slug> --approve-hint own --fetch` | Also approve new candidates with that hint and fetch them |
| `wwxd sources <slug> --status candidate` | List sources |
| `wwxd approve <slug> <ids>`, `wwxd reject <slug> <ids>` | Curate |
| `wwxd add <slug> <url or file>` | Add a source by hand |
| `wwxd fetch <slug>` | Download captions, transcripts and articles into `raw/` |
| `wwxd pending <slug>` | Sources fetched but not compiled |
| `wwxd mark-compiled <slug> <id>` | Record a compiled source in `log.md` |
| `wwxd lint <slug>` | Check quotes, citations, attribution and links, and flag drift such as near-duplicate leaves |
| `wwxd health <slug>` | Report on the wiki: size, attribution, coverage, near-duplicates, oversize leaves |
| `wwxd timeline <slug> [query]` | Statements by source date and member, to see how views changed |
| `wwxd digest <slug> --since YYYY-MM-DD` | Markdown note on what's new since a date |
| `wwxd search <slug> "query"` | Keyword search over the wiki (`--raw` adds transcripts) |
| `wwxd status <slug>` | Summary |
| `wwxd voice <slug> [ids]` | Check who is speaking in each quote, by voice (needs `wwxd[voice]`) |
| `wwxd doctor` | Check yt-dlp, the JS runtime, ffmpeg, Whisper and `$WWXD_HOME` |
| `wwxd bench run`, `judge`, `report` | [Benchmarks](bench/README.md) |

Vaults are plain markdown folders and open in Obsidian. `$WWXD_HOME` sets where they
live (default `./vaults`).

## Sources and copyright

wwxd fetches public captions, articles and podcast audio for your own use. It doesn't
fetch books, and this repo ships no content. You can add books you own as text files
(`wwxd add <slug> book.txt`) or write a [fetcher plugin](CONTRIBUTING.md#fetcher-plugins).
Don't publish vaults built from material you don't have the right to share.
[ETHICS.md](ETHICS.md) has the rules for using vaults and explains how a person can
have their recipe removed.

## Requirements

Run `wwxd doctor` to check your setup. It marks each item below OK, WARN or FAIL and
makes no network calls.

- Python 3.10 or newer.
- A JavaScript runtime for YouTube: [deno](https://deno.com), node 22 or newer, or
  [bun](https://bun.sh). wwxd picks the first of these on your PATH for yt-dlp.
  Without one, some videos lose formats or fail.
- Whisper, for sources without captions. Most podcasts need it, unless the feed
  publishes transcripts (`podcast:transcript` tags), which wwxd uses instead. Whisper
  runs on CPU, and much faster on a GPU. `WWXD_WHISPER_MODEL` and
  `WWXD_WHISPER_DEVICE` set the defaults, and `wwxd fetch --whisper-model large-v3`
  changes the model for one run.
- Browser cookies, only if YouTube asks you to sign in. Set
  `WWXD_COOKIES_FROM_BROWSER=firefox` (or `chrome:Profile 1`), or pass
  `--cookies-from-browser` to `discover`, `update` or `fetch`.

When YouTube rate limits a fetch (HTTP 429), wwxd waits and retries up to 3 times,
at most a minute apart.

## Roadmap

- A read-only MCP server for chat apps
- Word-level timings for Whisper transcripts, so the voice check is as precise on
  podcasts as it is on YouTube captions
- Tree versus flat layout results in the bench
- Fetchers for X threads and Substack archives

## Credits

The raw-sources-plus-compiled-wiki loop is Andrej Karpathy's LLM wiki idea. wwxd adds
sourcing, speaker attribution and quote checking for the one-person case. Design notes
are in [docs/design.md](docs/design.md). MIT licensed.

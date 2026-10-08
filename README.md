# wwxd

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

160 quotes in the wwxd answers were checked against the transcripts by a script, and
158 were found verbatim. The other 2 were video titles. Raw Opus rarely quoted
anyone. It lost on specifics, on anything from 2026, and on attribution traps. Full
numbers, setup and caveats are in [bench/RESULTS.md](bench/RESULTS.md).

## How it works

```
discover ──▶ you approve ──▶ fetch ──▶ compile ──▶ lint ──▶ ask
  (CLI)         (CLI)         (CLI)    (agent)     (CLI)   (agent)
```

The `wwxd` CLI does the mechanical work. It finds sources (the person's YouTube
channels, podcast feeds, blog RSS, essay index pages), downloads existing captions,
falls back to local Whisper when there are none, and checks the wiki.

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

## Quick start

```bash
uv tool install "git+https://github.com/MSliwa01/wwxd"        # add [whisper] for podcasts
wwxd install-skill                                            # into ~/.claude/skills/wwxd

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

## CLI

| Command | What it does |
|---|---|
| `wwxd new <slug> --example X` or `--name "Full Name"` | Create a vault |
| `wwxd discover <slug>`, `wwxd update <slug>` | Find new candidate sources |
| `wwxd sources <slug> --status candidate` | List sources |
| `wwxd approve <slug> <ids>`, `wwxd reject <slug> <ids>` | Curate |
| `wwxd add <slug> <url or file>` | Add a source by hand |
| `wwxd fetch <slug>` | Download captions and articles into `raw/` |
| `wwxd pending <slug>` | Sources fetched but not compiled |
| `wwxd mark-compiled <slug> <id>` | Record a compiled source in `log.md` |
| `wwxd lint <slug>` | Check quotes, citations, attribution and links |
| `wwxd search <slug> "query"` | Keyword search over the wiki (`--raw` adds transcripts) |
| `wwxd status <slug>` | Summary |
| `wwxd bench run`, `judge`, `report` | [Benchmarks](bench/README.md) |

Vaults are plain markdown folders and open in Obsidian. `$WWXD_HOME` sets where they
live (default `./vaults`).

## Sources and copyright

wwxd fetches public captions, articles and podcast audio for your own use. It doesn't
fetch books, and this repo ships no content. You can add books you own as text files
(`wwxd add <slug> book.txt`) or write a [fetcher plugin](CONTRIBUTING.md#fetcher-plugins).
Don't publish vaults built from material you don't have the right to share.

## Requirements

- Python 3.10 or newer
- A JavaScript runtime such as [deno](https://deno.com) helps yt-dlp with YouTube.
  Without one, yt-dlp prints a warning and some videos may fail.
- Whisper is only needed for sources without captions, which covers most podcast
  feeds. It runs on CPU, and much faster on a GPU (`WWXD_WHISPER_MODEL`,
  `WWXD_WHISPER_DEVICE`).

## Roadmap

- A read-only MCP server for chat apps
- Audio diarization as an option (`wwxd[diarize]`)
- Podcast 2.0 transcript tags, to skip Whisper when a feed has transcripts
- Tree versus flat layout results in the bench
- Fetchers for X threads and Substack archives

## Credits

The raw-sources-plus-compiled-wiki loop is Andrej Karpathy's LLM wiki idea. wwxd adds
sourcing, speaker attribution and quote checking for the one-person case. Design notes
are in [docs/design.md](docs/design.md). MIT licensed.

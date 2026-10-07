# wwxd: What Would X Do?

**Build a cited knowledge wiki of anyone's thinking from their talks, podcasts and writing. Then ask your agent what they'd do.**

LLMs give average advice about business, design, learning and careers. wwxd lets
you ask a specific person instead, using what they've actually said and done, not
what the model thinks they're like.

```
> What would Paul Graham say about raising a big round before launch?

Short answer: Don't plan around a big early round. Do what you can with the money you
have and raise at each milestone.

What he's said
- "So you just do what you can on the money you got. As long as you can get to some kind
  of milestone, then you can convince investors to give you more." ([[yt-5bxp78i96S8]] @ 12:09)
- "everything technology always gets cheaper" ([[yt-5bxp78i96S8]] @ 11:37)

Where this is uncertain: one 2026 interview so far; his essays aren't compiled yet.
```

## How it works

wwxd follows Andrej Karpathy's [LLM wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
pattern. Raw sources are compiled by an LLM into a wiki that keeps improving with
each source, instead of being re-searched from scratch on every question. On top of
that, wwxd is tuned for one question: *what does this exact person think?*

```
discover ──▶ you approve ──▶ fetch ──▶ compile ──▶ lint ──▶ ask
 (CLI)         (CLI)          (CLI)    (agent)     (CLI)    (agent)
```

- **The CLI** does the mechanical work. It finds sources (the person's YouTube
  channel, podcast appearances, blog/RSS, essay index pages), downloads existing
  captions (falling back to local Whisper), and checks the wiki.
- **Your agent** (Claude Code, via the bundled skill) does the thinking. It works
  out who's speaking, extracts verbatim quotes, and files them into a topic tree.
  No API keys needed.
- **Lint checks every quote against the source text in code.** A quote that isn't
  in the transcript fails the check, however plausible it sounds.

### What's different from a plain LLM wiki

| | |
|---|---|
| **Content by X, not about X** | Discovery flags "summary/reaction/lessons from" videos, and you approve sources before anything is fetched. |
| **Speaker attribution** | In a podcast, half the words are the host's. Every statement records who said it and how sure the agent is. Low-confidence and second-hand ("my friend says…") lines never count as the person's view. |
| **Verbatim, timestamped quotes** | `"…" ([[yt-id]] @ 12:34; by: pg; conf: high)`, checked against the raw transcript. |
| **Acts over words** | Each topic page separates what they *said* from what they *did*. `tensions.md` tracks how views changed over time. |
| **A tree, not a pile** | person → domain → topic → leaf (`layout: flat` is available for comparison). |
| **Groups** | One vault can hold a school of thought (e.g. YC partners) and still credit each statement to its speaker. |
| **No self-contamination** | The model's own extrapolations go in `derived/`, and lint stops them being cited as evidence. |

## Quick start

```bash
# install (or run any command with `uvx wwxd ...`)
uv tool install wwxd            # add the local Whisper fallback: uv tool install 'wwxd[whisper]'
wwxd install-skill              # installs the Claude Code skill into ~/.claude/skills/wwxd

# create a vault from an example recipe
wwxd new yc --example yc
wwxd discover yc                # finds candidates; nothing is downloaded yet
wwxd sources yc --status candidate
```

Then, in Claude Code:

> Help me curate the yc vault, fetch what we approve, and compile it.

The skill walks the agent through curating with you, `wwxd fetch`, compiling each
source, and `wwxd lint`. When it's done:

> What would Michael Seibel say about my plan to spend 6 months building before talking to users?

### For your own person

```bash
wwxd new hormozi --example hormozi        # or: wwxd new jane --name "Jane Doe"
```

Edit `vaults/<slug>/vault.yaml` to list their own channels, feeds and article
index pages, or ask the agent to find them for you.

## Example recipes

`wwxd examples` lists them. They contain **source configs only, never content**:

| Recipe | Domain | Why it's a good demo |
|---|---|---|
| `yc` | startups | A group vault (Paul Graham, Jessica Livingston, Michael Seibel, Dalton Caldwell, Garry Tan, Sam Altman). Lots of public lectures, plus PG's essays. |
| `hormozi` | business, sales | Huge, consistent long-form output. |
| `naval` | wealth, philosophy | Podcasts, plus an essay archive. |
| `karpathy` | learning, AI | Lectures, a blog, interviews. |
| `rams` | design | Few sources. Shows what a thin vault looks like. |

> These are **starting points, not endorsements.** You don't have to agree with any
> of them, and the most useful vault is probably the one for the person *you*
> learn from. Swap them out, fork the recipes, and add your own.

## CLI

| Command | What it does |
|---|---|
| `wwxd new <slug> [--example X \| --name "Full Name"]` | Create a vault |
| `wwxd discover <slug>` / `update` | Find new candidate sources |
| `wwxd sources <slug> [--status] [--hint]` | List sources |
| `wwxd approve/reject <slug> <ids…> [--hint own]` | Curate |
| `wwxd add <slug> <url or file>` | Add a source by hand |
| `wwxd fetch <slug> [--whisper auto\|always\|never]` | Download captions/articles into `raw/` |
| `wwxd pending <slug>` | Fetched but not yet compiled |
| `wwxd mark-compiled <slug> <id>` | Record a compiled source in `log.md` |
| `wwxd lint <slug>` | Check quotes, citations, attribution and links |
| `wwxd search <slug> "query" [--raw]` | Keyword search over the wiki |
| `wwxd status <slug>` | Summary |
| `wwxd bench run/judge` | [Benchmarks](bench/README.md) |

Vaults are plain markdown and open directly in Obsidian. `$WWXD_HOME` sets where
they live (default `./vaults`).

## Sources and copyright

wwxd fetches publicly available captions, articles and podcast audio for your
personal use. It doesn't fetch books, and the repo never ships content.

**Books** are often the best source. Add files you own (`wwxd add <slug> book.txt`)
or write a [fetcher plugin](CONTRIBUTING.md#fetcher-plugins) for your own setup.
Respect the copyright of the people you study, and don't publish vaults built from
material you don't have the rights to share.

## Requirements and notes

- Python 3.12+
- YouTube extraction works best with a JavaScript runtime installed for yt-dlp
  (e.g. [deno](https://deno.com)). Without one, yt-dlp warns, and some videos may fail.
- Whisper is only needed when a source has no captions (most podcasts from RSS).
  CPU works; a GPU is much faster (`WWXD_WHISPER_MODEL`, `WWXD_WHISPER_DEVICE`).

## Roadmap

- [ ] Read-only MCP server for chat apps (Claude Desktop, etc.)
- [ ] Optional audio diarization (`wwxd[diarize]`)
- [ ] Podcast 2.0 transcript tags (skip Whisper when the feed has transcripts)
- [ ] Published bench results: tree vs. flat, prompt variants
- [ ] More fetchers: X/Twitter threads, Substack archives

## Credits

The core loop (raw → compiled wiki → ingest/query/lint) is Andrej Karpathy's
LLM-wiki idea. wwxd adds sourcing, speaker attribution and verification for the
"one specific person" use case. See [docs/design.md](docs/design.md).

MIT licensed.

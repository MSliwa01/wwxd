# wwxd design

**What would X do?** Build a cited knowledge wiki of a person's (or a group's)
thinking from their talks, podcasts and writing, then let your agent answer the
way they would, with sources.

## Goals

1. **A grounded advisor first.** Answers are built from documented positions, and
   every claim cites a source and a timestamp. If the person never addressed a
   topic, the agent says so. "Extrapolate" mode exists, but it's clearly labelled.
2. **"This exact person."** Content *by* X, not content *about* X. Speaker
   attribution is the core problem, not an afterthought.
3. **Usable from Claude Code** (and other agents with file access) without API
   keys. The agent the user already has does the thinking.
4. **Safe to publish.** The repo ships the tool and example source recipes, never
   content.

## Architecture

```
            Python CLI (deterministic)                 Agent + skill (judgment)
 vault.yaml ─▶ discover ─▶ sources.yaml ─▶ (user curates) ─▶ fetch ─▶ raw/*.md
                                                                       │
                                     compile (SKILL.md) ◀──────────────┘
                                          │
                                       wiki/ ─▶ lint (mechanical) ─▶ ask
```

- **CLI** (`wwxd`): `new`, `discover`, `sources`, `approve`/`reject`, `add`,
  `fetch`, `pending`, `mark-compiled`, `lint`, `search`, `status`, `update`,
  `install-skill`, `bench`.
- **Skill** (`src/wwxd/skill/`): procedures for curating, compiling, asking and
  linting. Installed with `wwxd install-skill`.
- **No MCP server in v1.** Vaults are plain markdown, so any agent with file access
  can use them, and they open directly in Obsidian. A read-only MCP server may come
  in v1.x if people ask for it.

## Relation to Karpathy's LLM wiki

We keep the core loop: immutable `raw/`, a wiki the LLM owns, `index.md` and
`log.md`, and ingest → query → lint, with knowledge building up over time.
Differences:

- **Tree** (person → domain → topic → leaf) instead of flat pages. `flat` stays
  as a `layout` option so the bench can compare the two.
- **Verbatim quotes with timestamps**, checked against the raw text *by code*
  (`wwxd lint`), not just by the model.
- **Speaker attribution**: metadata → LLM turn segmentation with confidence →
  hard filter (no low-confidence or `reported` statements as evidence) →
  mechanical quote check. Audio diarization is an optional extra (`wwxd[diarize]`,
  not implemented yet).
- **Acts over words.** Each leaf has an `Actions` section, and `tensions.md` tracks
  how views changed over time.
- **Query answers go to `derived/`**, never into the wiki as evidence, so the
  model's extrapolations can't slowly become "X's views".
- **Group vaults** (`members:`), e.g. YC. A single person is a group of one.
- **Sourcing pipeline**: discover → user-approved `sources.yaml` → fetch
  (existing captions first, Whisper as fallback) → `update` for new material.

## Vault format

Canonical spec: [`src/wwxd/skill/references/format.md`](../src/wwxd/skill/references/format.md).

## Sources

| Type | Discover | Fetch |
|------|----------|-------|
| YouTube (own channels, searches) | yt-dlp | captions (manual > auto original language) → Whisper fallback |
| Articles / essays | RSS/Atom feeds, link-index pages | trafilatura |
| Podcasts (RSS) | feeds with audio enclosures | audio download → Whisper |
| Local files | `wwxd add` | `.txt` / `.md` |
| Anything else | — | fetcher plugins (`wwxd.fetchers` entry point) |

Books are never fetched. Users can add files they own, or write a plugin.

## Benchmarks

`wwxd bench` runs a gold question set through any agent command (default
`claude -p`), stores the answers, and scores them with a judge prompt. What gets
measured: answer faithfulness, citation precision, refusing to answer when the
person never covered something, attribution accuracy (hand-labelled episodes),
and tree vs. flat layout. Prompt variants of the skill can be compared the same
way.

## Not in v1

MCP server, diarization implementation, pre-built vaults, book fetching, GUI.

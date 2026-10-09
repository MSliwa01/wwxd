# Vault format (canonical)

This file is the contract between the compiling agent and `wwxd lint`.
If you change the grammar here, change `src/wwxd/lint.py` with it.

## Vault layout

```
vaults/<slug>/
  vault.yaml        # who: name, members, domains, layout, discovery config
  sources.yaml      # every source and its status (managed by the CLI)
  log.md            # append-only: what was ingested/compiled and when
  raw/              # immutable source documents, one per source: <source-id>.md
  derived/          # answers and extrapolations filed back from queries (never evidence)
  wiki/
    index.md        # map of every page
    profile.md      # who they are, track record, biases, what they're NOT credible on
    tensions.md     # contradictions and views that changed over time (dated)
    thinking/<member-id>.md  # how they think: values, decision rules, habits, strong views
    <domain>/<topic>/<leaf>.md   # layout: tree
    <leaf>.md                    # layout: flat
```

`layout` in `vault.yaml` is `tree` (default) or `flat`. Only where leaves live
changes; their format is identical. In `tree`, each domain and topic folder has an
`_overview.md` with the synthesized view of that level (topic folders need one once
they hold two or more leaves). Max depth: domain/topic/leaf.

## Source ids

Raw docs are named by source id. Prefixes:

| Prefix  | Source                          | Positions |
|---------|---------------------------------|-----------|
| `yt-`   | YouTube video                   | `@ m:ss` / `@ h:mm:ss` timestamps |
| `pod-`  | Podcast episode (RSS audio)     | timestamps |
| `web-`  | Article / essay / blog post     | none |
| `file-` | Local file the user added       | none |

A link like `[[yt-0lJKucu6HJc]]` always means "the raw doc with that id".

## Raw doc

```
---
id: yt-0lJKucu6HJc
type: youtube
url: https://www.youtube.com/watch?v=0lJKucu6HJc
title: Sam Altman - How to Succeed with a Startup
channel: Y Combinator
date: 2018-08-29
duration: 967
language: en
transcript: auto-captions      # captions | auto-captions | feed-transcript | whisper | article | file
expected_speakers: [altman]    # member ids the source is expected to contain
description: ...
---
[0:00] okay today I'm going to talk about ...
[0:31] ...
```

Timestamped sources are chunked into paragraphs that each start with `[m:ss]`.
Raw docs are never edited after fetching.

## Leaf page

```
---
type: leaf
title: Raising prices
domain: business
topic: pricing
members: [hormozi]
updated: 2026-10-07
---
# Raising prices

## Stance
Two or three sentences synthesizing the position, citing sources inline
([[yt-abc123]]).

## Statements
- "you should charge more than you're comfortable with" ([[yt-abc123]] @ 12:34; by: hormozi; conf: high)
- "a friend of mine says never discount" ([[yt-def456]] @ 3:10; by: hormozi; conf: medium; reported)

## Actions
- Raised Gym Launch prices 3x after selling out ([[yt-abc123]] @ 14:02; by: hormozi; conf: high)

## Caveats
- Said in 2019 that ...; by 2023 he ... (see [[tensions]])

## Related
- [[business/pricing/value-equation]]
```

Quote front matter values that contain a colon (`title: "Pricing: when to raise"`).
Otherwise the YAML doesn't parse and lint skips the page's leaf checks.

`distinct_from` (optional) lists leaves you compared with this one and kept apart on
purpose, e.g. `distinct_from: [business/pricing/premium-tiers]`. `wwxd lint` and
`wwxd health` then stop reporting that pair as near-duplicates.

### Statement grammar

One statement per line, inside `## Statements`:

```
- "<verbatim quote>" ([[<source-id>]] @ <timestamp>; by: <member-id>; conf: <high|medium|low>[; reported])
```

- **quote**: verbatim from the raw doc. Fixing obvious caption typos and adding
  punctuation is fine; changing words is not. Use `...` to skip words; each part
  must still match.
- **@ timestamp**: required for `yt-`/`pod-`, omitted for `web-`/`file-`.
- **by**: a member id from `vault.yaml`. Required, even in single-person vaults.
  Lint warns if the member isn't in the source's `expected_speakers` in
  `sources.yaml`. If they really do speak in it, add them there.
- **conf**: how sure you are that `by` really said it (speaker attribution, not
  whether it's true). Don't record `low` statements; `lint` warns on them.
- **reported**: the speaker is relaying someone else's view ("my mentor told me…").
  Never use a `reported` statement as evidence of the member's own stance.

`## Actions` lines use the same citation, but the text is a paraphrase, not a quote.

A quote inside prose (Stance, Caveats, profile, tensions) followed directly by a
full citation, as in `he said "…" ([[yt-…]] @ 1:23; by: pg; conf: high)`, is checked
the same way as a statement.

### Citations elsewhere

Any `[[<source-id>]]` anywhere in `wiki/` must point to an existing raw doc.
Nothing in `wiki/` may link into `derived/`: derived pages are the model's
synthesis, not the person's words.

## Derived page

```
---
type: derived
question: Should I raise prices for my SaaS?
mode: grounded | extrapolate
date: 2026-10-07
---
```
Free-form answer. Can cite raw docs and wiki pages. Never cited as evidence.

## attribution.jsonl

Written by `wwxd voice`. One line per checked statement: the page, quote, source,
`by`, and a `voice` verdict (`match`, `weak`, `mismatch` or `unchecked`) with the
similarity scores. `wwxd lint` turns mismatches into warnings while the statement
still says the same `by`. Don't edit it by hand; re-run `wwxd voice`.

## log.md

```
- 2026-10-07 compiled yt-0lJKucu6HJc: +3 leaves, updated profile, tensions
- 2026-10-08 consolidated: merged 2 leaves, split 1, 3 overviews, index
```

`wwxd mark-compiled` writes the `compiled` lines. Write the `consolidated` line
yourself after a consolidation pass (`references/consolidate.md`); `wwxd health`
counts compiled sources since the last one.

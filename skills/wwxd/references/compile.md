# Compiling a source into the wiki

One source at a time. Read `format.md` first if you haven't in this session.

## 1. Who is in this source?

From the raw doc's front matter (title, channel, description, `expected_speakers`),
work out every speaker before reading the body: the members, hosts and guests.
Write it down for yourself, e.g. "host: Vivian Shen (not a member); guest: Paul
Graham = `pg`".

Check the `date` too, since `tensions.md` depends on it. Article dates from metadata
can be wrong (an essay dated "July 2023" in its own text may come through as
`2023-01-01`). If the source's own dateline disagrees, fix `date` for that source
in `sources.yaml` (raw docs are immutable) and use the corrected date in the wiki.

## 2. Segment turns and attribute them

Read the transcript in order. Caption tracks often mark speaker changes with
`>>`; Whisper output and some captions don't. Assign each turn a speaker using:

- **Question vs. answer**: in an interview, the host asks and the guest answers at
  length.
- **First-person biography**: "when we started YC", "my essay on…" only fits one
  person.
- **Names said aloud**: "thanks PG", "Vivian, that's a great question".
- **Turn length and register**: a long, opinionated monologue usually belongs to
  the guest.
- **Continuity**: the speaker doesn't change without a cue.

Give each attribution a confidence:

- **high**: unambiguous (a solo talk, an essay, a clearly marked long answer).
- **medium**: very likely, with one weak cue.
- **low**: plausible but unclear. **Don't record it.**

Mark `reported` when the member relays someone else's view ("Jessica always said
…"). This counts as evidence of what *Jessica* said only if she is a member, and
even then at most `medium`.

Short interjections ("Yeah.", "Really?") and questions from the host are never
statements.

## 3. Extract

For each substantive claim by a member:

- **Statement**: the shortest verbatim span that carries the claim, usually one or
  two sentences. You may add punctuation and fix obvious caption typos; don't
  change words. Use `...` to skip filler. Timestamp: the `[m:ss]` of the paragraph
  it appears in (or the one before, if it spans a boundary).
- **Action**: something the member *did* (a decision, investment, company built,
  something they changed). Paraphrase it and cite it. Actions outweigh opinions
  when they conflict.
- Ignore pleasantries, sponsor reads, and generic statements that carry no
  position.

## 4. Place in the tree

`layout` in `vault.yaml` decides where leaves go:

- `tree`: `wiki/<domain>/<topic>/<leaf>.md`. Start from `domains` in `vault.yaml`.
  Add a new domain only if nothing fits. A leaf is one question someone would ask
  ("raising-prices", "when-to-quit-your-job"), not a source.
- `flat`: `wiki/<leaf>.md`.

Before creating a leaf, check for an existing one (`wwxd search <slug> "<terms>"`,
or list the folder). Prefer adding statements to an existing leaf over making a
near-duplicate. Split a leaf when it passes ~15 statements.

## 5. Update the synthesis

For every leaf you touched:

- Rewrite **Stance** (two or three sentences) so it reflects *all* statements, with
  inline citations. In group vaults, say who holds which view ("PG and Seibel
  agree…; Caldwell differs…").
- Note any conflict with earlier statements in **Caveats**, and add a dated entry
  to `wiki/tensions.md` (when did they say what?). Run
  `wwxd timeline <slug> <leaf path or keyword>` to list the earlier statements on
  the topic by source date, with citations you can copy.
- Update each touched `_overview.md` (tree layout) with a one-paragraph summary of
  that level and links to its children. Every domain has one. A topic gets one once
  it has two or more leaves.
- Update `wiki/thinking/<member-id>.md` (see `thinking.md`) when the source shows a
  value, a decision rule, a threshold they use, a reasoning habit, or something they
  call good or bad with a reason. Add the supporting quote under the existing rule,
  or add a new rule. If the member has no thinking page yet and the vault has three
  or more of their sources, build it.
- Update `wiki/profile.md` if the source reveals background, track record, biases
  or conflicts of interest (e.g. they sell a product related to the topic).
- Add every new page to `wiki/index.md` as `- [[path]] (one-line summary)`.

## 6. Verify and log

```
wwxd lint <slug>              # fix every error; read the warnings
wwxd voice <slug> <source-id> # audio sources with more than one speaker, if wwxd[voice] is installed
wwxd mark-compiled <slug> <source-id> --note "+N leaves, updated …"
```

If lint says a quote isn't in the source, re-read the raw doc and copy the actual
words. Don't loosen the quote.

`wwxd voice` listens to each quote and compares the speaker with the members'
voiceprints. On a labelled test episode it caught every wrong attribution the
compile made, with no false alarms. When it reports a mismatch, re-read the turns
around that timestamp: credit the line to the member it names, or drop it if the
speaker isn't a member. A `weak` result only means the audio was unclear (music,
crosstalk, a very short quote); check it, but don't change it on that alone.
With source ids, `wwxd voice` builds voiceprints from those sources only, which is
noisy for a member with just a few lines there. Run it on the whole vault
(`wwxd voice <slug>`) every 10 sources or so, alongside `wwxd health`, so each
voiceprint draws on everything credited to that member.

Every 10 compiled sources, run `wwxd health <slug>`. If it flags near-duplicates,
oversize leaves, missing overviews or index gaps, follow `consolidate.md`.

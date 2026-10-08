# Consolidating the wiki

Each source is compiled in a fresh session, so the wiki drifts. Two leaves end up
answering the same question, leaves grow past 15 statements, overviews fall behind
and `index.md` misses pages. A consolidation pass fixes this. It changes where
statements live, never what they say.

## When to run it

- `wwxd health <slug>` flags near-duplicates, oversize leaves, missing overviews or
  leaves missing from the index.
- About every 10 compiled sources. `wwxd health` counts them since the last pass.
- Before you share a vault or run the bench on it.

## 1. Take stock

```
wwxd health <slug>
wwxd lint <slug>
```

Note the near-duplicate pairs, oversize leaves, missing overviews and index gaps.
Near-duplicates are candidates, not verdicts. Read both leaves before you decide.

## 2. Merge near-duplicates

Merge two leaves only when they answer the same question. If they answer different
questions, sharpen both titles so the difference is clear, link each from the
other's Related, and add `distinct_from: [<other leaf path>]` to one leaf's front
matter so lint stops flagging the pair.

To merge:

1. Keep the slug that names the question better. When it's close, keep the one more
   pages link to (`grep -rn "<path>" wiki/`).
2. Move every statement and action into the kept leaf. Copy each line exactly,
   quote and citation unchanged. Drop only exact repeats (same quote, same source).
3. Rewrite the Stance so it covers all the statements, with inline citations. In a
   group vault, say who holds which view. Merge Caveats and Related.
4. Update the front matter: `members` lists everyone with a statement, `updated` is
   today.
5. Delete the other leaf.
6. Fix every link to the deleted leaf: other leaves' Related, overviews,
   `profile.md`, `tensions.md`, `index.md`, and any page in `derived/`.
   `grep -rn "<deleted path>" wiki/ derived/` finds them.

If the merge puts conflicting statements side by side, add or update the entry in
`tensions.md`. `wwxd timeline <slug> <kept leaf path>` lists the statements in date
order.

## 3. Split oversize leaves

A leaf with more than 15 statements usually answers more than one question.

1. Group its statements by the question each one answers.
2. Keep the original slug for the main question. Give each other group of three or
   more statements its own leaf in the same topic.
3. Write a Stance for each leaf, move the Caveats that apply, and link the leaves
   to each other in Related.
4. Fix links to the original leaf where they now belong to a new one.

Don't split just to get under 15. If every statement answers the same question, one
long leaf beats two halves of one answer.

## 4. Tidy the taxonomy

- A leaf filed under the wrong domain or topic: move it, fix `domain` and `topic`
  in its front matter, and fix every link.
- Topics with one leaf (`wwxd health` counts them): fold the leaf into a sibling
  topic when it fits there. A few single-leaf topics are fine.
- Two topics that mean the same thing in different domains: pick one and move the
  leaves.

## 5. Refresh overviews

For every domain and topic you touched, and every overview lint reports missing,
write or update `_overview.md`:

- One paragraph that sums up the level, with inline citations. In a group vault,
  name who holds which view.
- A list of its children, one per line: `- [[path]] (one-line summary)`.

Every domain has an overview. A topic gets one once it holds two or more leaves.

## 6. Regenerate the index

Rebuild `wiki/index.md` from the tree so it lists every page exactly once: profile
and tensions first, then each domain overview followed by its topic overviews and
leaves. One line per page, `- [[path]] (one-line summary)`. Reuse the existing
summaries and rewrite the ones for merged, split or moved leaves.

## 7. Check and log

```
wwxd lint <slug>      # fix every error
wwxd health <slug>
```

Then append a line like this one to `log.md`.

```
- 2026-10-08 consolidated: merged focus-on-one-thing into sticking-with-one-thing, split solve-your-own-problem, 3 overviews, index
```

`wwxd health` counts compiled sources from this line on.

## Rules

- Never change a quote or a citation while moving it. Lint catches a changed quote,
  but not a statement moved to a leaf where it doesn't belong.
- Never delete a statement unless it's an exact repeat.
- Don't write new claims into Stance or overviews. Summarize the statements that are
  there.

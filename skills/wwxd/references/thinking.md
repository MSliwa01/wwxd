# How they think: building the thinking pages

Leaves record what a person said about a topic. The thinking page records how they
think, so the agent can work out what they'd say about something they never
mentioned. If someone calls McDonald's poison because it's processed food built to
be cheap, the thinking page holds that rule, and an answer about KFC can apply it.

There is one page per member: `wiki/thinking/<member-id>.md`. Build it once the
vault has a few sources, then keep it current: update it whenever you compile a
source, and rebuild it during consolidation.

## Page format

```
---
type: thinking
member: hormozi
updated: 2026-10-09
---
# How Alex Hormozi thinks

## What they optimize for
- **Long-term certainty over short-term upside.** One or two sentences in plain words.
  - "<verbatim quote>" ([[yt-…]] @ m:ss; by: hormozi; conf: high)
  - "<verbatim quote>" ([[web-…]]; by: hormozi; conf: high)

## Rules they decide by
- **If customers close above 80%, the price is too low.** …
  - "…" (citation)

## How they reason
- **Runs the numbers before giving an opinion.** …

## Strong views
- **Against: complexity in the offer.** What they dislike and the reason they gave.
- **For: …**

## Where they've changed their mind
- Short dated notes, linking [[tensions]].

## Blind spots
- Topics where they reason from little experience, or have a stake (from [[profile]]).
```

Rules for the page:

- Every bullet is a rule, value or habit stated in one plain sentence, followed by at
  least one supporting quote in the statement grammar from `format.md`. Lint checks
  these quotes against the raw sources like any other statement.
- Prefer rules that showed up more than once, in different sources. Note the count
  when it's high ("said in 4 sources").
- Write the reason, not just the verdict. "Hates McDonald's" can't be applied to
  KFC; "hates food engineered to be cheap and addictive" can.
- Keep each section to the 5 to 10 strongest items. Link to leaves for detail.
- In a group vault, one page per member. Don't merge members' thinking.
- Add `wiki/thinking/<member-id>.md` to `wiki/index.md`.

## Building or rebuilding a page

1. Read `wiki/profile.md`, `wiki/tensions.md` and every leaf with statements by the
   member. `wwxd timeline <slug> "<keyword>"` helps you see a view across sources.
2. List candidate rules: anything they justify the same way more than once, any
   number they use as a threshold, any value they rank above another, anything they
   call good or bad with a reason.
3. For each rule, copy the best one to three supporting statements, quote and
   citation unchanged.
4. Run `wwxd lint <slug>` and fix every error.
5. Log it: `wwxd mark-compiled` doesn't apply here, so append a line to `log.md`:
   `- <date> thinking: rebuilt <member-id>, N rules`.

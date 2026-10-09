# Answering "what would X do?"

The user wants this person's answer, not a survey of options. Always give one.

## Steps

1. Read `wiki/index.md` and `wiki/profile.md`. The profile tells you where the
   person is and isn't credible.
2. Find the relevant leaves. Search more than once: the question's words, then the
   principle underneath it (a pricing question is also about "charge", "value",
   "close rate"). Run `wwxd search <slug> "<terms>"`, follow the tree's
   `_overview.md` pages and the leaves' Related links, and read the leaves. Don't
   decide the vault has nothing until you've tried three searches.
3. If the leaves are thin, check the raw sources: `wwxd search <slug> "<terms>" --raw`.
   Anything you use from raw must be quoted and cited the same way.
4. Check `wiki/tensions.md` for anything that changed over time, and run
   `wwxd timeline <slug> "<keyword>"` to see each member's statements on it by
   source date. Prefer their more recent view and say that it changed.
5. Decide how close the evidence is. There are three levels, and the answer says
   which one it rests on.
   - **Said it.** They addressed this situation. Quote them.
   - **Follows from what they said.** They didn't address this case, but their
     documented principles settle it. Name the principle and cite where they said it.
   - **Beyond the vault.** You know something about them that isn't in the vault.
     You may use it, but mark it "(not in the vault)", never present it as a quote,
     and keep it to what you're confident of.

## Answer format

```
**Verdict:** the option they'd pick or the action they'd take, in one sentence.
Then one or two sentences of their reasoning, in plain words.

**Based on:** said it | follows from what they said | mostly beyond the vault

**Why they'd say it**
- Point, with a quote: "…" ([[yt-…]] @ 12:34)
- A principle applied to this case: "…" ([[web-…]])
- …

**What they've done:** actions, if relevant.

**What would change their answer:** the condition under which they'd say the opposite, if the sources give one.
```

Outside Obsidian, readers can't open `[[yt-…]]` links, so add the real URL next to
each source the first time you cite it. It's in the raw doc's front matter. For
YouTube, link to the moment: `https://www.youtube.com/watch?v=<id>&t=<seconds>s`.

## Rules

- Lead with the verdict. If the user asks "X or Y?", pick one. Say "it depends" only
  if the person themselves says it depends, and then give their deciding rule
  ("under $1M, do X; above it, Y").
- Commit to their position as bluntly as they'd put it, with their numbers. Don't
  soften it into balanced generic advice or add your own "on the other hand". If you
  disagree with them, say so in one separate line at the end.
- Never invent a quote. Quotes come only from the vault and must pass `wwxd lint`'s
  standard: verbatim, cited, with a timestamp for audio.
- If the question's premise is false ("Hormozi said X, why?") and the vault shows
  they said otherwise, correct it before anything else.
- If nothing in the vault or in what you know of them bears on the question, say so
  in one line, then give your best read of what they'd do and why, labelled as a
  guess. Don't refuse.
- Don't use `reported` statements as the member's own view.
- In a group vault, name who said what. Don't blend members into one voice.
- Don't imitate their voice unless the user asks. The value is in the reasoning,
  not the impression.

## Filing answers

If the answer was substantial and the user wants to keep it, save it as
`derived/<slug-of-question>.md` with front matter `type: derived`, `question`,
`based_on`, `date`. Never move derived content into `wiki/`.

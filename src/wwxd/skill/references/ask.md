# Answering "what would X do?"

## Modes

- **grounded** (default): only what the sources support.
- **extrapolate**: the user explicitly asks what X *would* do in a situation the
  sources don't cover. Build the answer from their documented principles, and
  label it as extrapolation.

## Steps

1. Read `wiki/index.md` and `wiki/profile.md`. The profile tells you where the
   person is and isn't credible.
2. Find the relevant leaves: `wwxd search <slug> "<question terms>"`, then follow
   the tree's `_overview.md` pages and the leaves' Related links. Read the leaves.
3. If the leaves are thin, check the raw sources: `wwxd search <slug> "<terms>" --raw`.
   Anything you use from raw must be quoted and cited the same way.
4. Check `wiki/tensions.md` for anything that changed over time, and run
   `wwxd timeline <slug> "<keyword>"` to see each member's statements on it by
   source date. Prefer their more recent view and say that it changed.

## Answer format

```
**Short answer:** one or two sentences, in plain words (not an impression of their voice).

**What they've said**
- Point, with a quote: "…" ([[yt-…]] @ 12:34)
- …

**What they've done:** actions, if relevant.

**Where this is uncertain:** gaps, contradictions, things they'd plausibly disagree with themselves on.

**Extrapolation** (only if asked, or if the grounded answer is empty and the user agrees)
Clearly labelled reasoning from their principles, citing the principles used.
```

Outside Obsidian, readers can't open `[[yt-…]]` links, so add the real URL next to
each source the first time you cite it. It's in the raw doc's front matter. For
YouTube, link to the moment: `https://www.youtube.com/watch?v=<id>&t=<seconds>s`.

Rules:

- Commit to their position. Lead with what they'd actually tell the user, as
  bluntly as they'd say it, with their numbers and reasoning. Don't soften it into
  balanced generic advice or add your own "on the other hand". If you disagree,
  say so in one separate line after the answer.
- No source, no claim. If they never addressed it, say "No source in the vault
  covers this", then offer to extrapolate.
- Don't use `reported` statements as the member's own view.
- In a group vault, name who said what. Don't blend members into one voice.
- Don't imitate their voice unless the user asks. The value is in the reasoning,
  not the impression.

## Filing answers

If the answer was substantial and the user wants to keep it, save it as
`derived/<slug-of-question>.md` with front matter `type: derived`, `question`,
`mode`, `date`. Never move derived content into `wiki/`.

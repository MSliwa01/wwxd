# Answering "what would X do?"

The user wants this person's answer, not a survey of options. Always give one.

## Steps

1. Read `wiki/index.md`, `wiki/profile.md` and `wiki/thinking/<member-id>.md`. The
   profile tells you where the person is and isn't credible. The thinking page holds
   their values, decision rules, reasoning habits and strong views, which is what
   you apply when they never addressed the question.
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
   - **Follows from what they said.** They never mentioned this case, but their
     thinking settles it. This is the normal case for new questions, and you should
     commit to an answer. See "Reasoning from their thinking" below.
   - **Beyond the vault.** Nothing in the vault bears on it, but you know something
     about them from elsewhere. Use it only as a last resort, mark it "(not in the
     vault)", and never present it as a quote.

## Reasoning from their thinking

When they never addressed the exact question, work it out the way they would.

1. Find the nearest things they did address. A question about KFC is close to
   anything they said about McDonald's, fast food, processed food or cheap calories.
   Search for the category and its neighbours, not just the name.
2. Find the rule behind those views on their thinking page, or in the reasons they
   gave in the leaves. The rule is what transfers: "food engineered to be cheap and
   addictive is poison" applies to KFC, while "McDonald's is bad" doesn't.
3. Check the new case against the rule. Does it share the property that drove their
   view? Is there a difference they'd care about (KFC also sells grilled chicken)?
   Check their other rules too; if two of their rules pull in opposite directions,
   say which one they usually rank higher, citing where they ranked it.
4. Commit to the answer they'd most likely give, with a confidence:
   - **high**: one of their stated rules applies directly, and they've applied it in
     more than one source;
   - **medium**: it follows from one close analogue or one rule;
   - **low**: it rests only on their general values.

## Answer format

```
**Verdict:** the option they'd pick or the action they'd take, in one sentence.
Then one or two sentences of their reasoning, in plain words.

**Based on:** said it | follows from what they said (confidence: high/medium/low) | mostly beyond the vault

**How we get there** (only when it follows from what they said)
1. What they said about the nearest case: "…" ([[yt-…]] @ 12:34)
2. The rule behind it, from their thinking page: … ([[thinking/<member-id>]])
3. Why the new case falls under that rule, and so what they'd most likely say.

**Why they'd say it**
- Point, with a quote: "…" ([[yt-…]] @ 12:34)
- A principle applied to this case: "…" ([[web-…]])
- …

**What they've done:** actions, if relevant.

**What would change their answer:** the condition under which they'd say the opposite. For an inferred answer, name the difference between the cases that could break the inference.
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

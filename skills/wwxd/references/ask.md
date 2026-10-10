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

Write the answer as advice the user can read straight through, then list the
sources underneath. The advice is the point; the sources are there to check it.

```
<The answer, in plain prose. Open with what they'd tell you to do, in one or two
sentences. Then their reasoning applied to the user's situation, with their numbers,
examples and rules worked into the sentences. Two to four short paragraphs. Mark a
claim with [1], [2] where it rests on a source, but don't paste quotes or timestamps
into the prose. If the answer is inferred, say so in a sentence ("He never talked
about KFC, but by his own rule about fast food, he'd…"). End with what would change
their answer.>

**Sources**
1. "<verbatim quote>" (<who>, <source title>, <date>, [12:34](https://www.youtube.com/watch?v=<id>&t=754s))
2. "<verbatim quote>" (<who>, <essay title>, <date>, [link](<url>))
3. Their rule, from the thinking page: <the rule in one line> ([[thinking/<member-id>]])

Based on: said it | follows from what they said (confidence: high/medium/low) | mostly beyond the vault
```

The prose carries everything the reader needs. Don't push the specifics down into
the sources: if Hormozi said "raise prices 10% and keep it while the close rate stays
above 65%", those numbers belong in the advice, and the quote that backs them goes in
the list. Short phrases of theirs can appear in the prose in quotation marks when the
wording matters, and then they're listed too.

Don't write about the vault in the answer ("my sources say", "the vault has no…",
"same video"). Write about the person. When nothing in the vault covers the question,
the "Based on" line says so.

Get each source's URL, title and date from the raw doc's front matter. For YouTube,
link to the moment: `https://www.youtube.com/watch?v=<id>&t=<seconds>s`.

## Rules

- Lead with what they'd tell the user to do. If the user asks "X or Y?", pick one. Say "it depends" only
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
- Write it as natural advice shaped by their thinking, not an impression of their
  voice (no catchphrases, no "as Alex, I…") unless the user asks for one.

## Filing answers

If the answer was substantial and the user wants to keep it, save it as
`derived/<slug-of-question>.md` with front matter `type: derived`, `question`,
`based_on`, `date`. Never move derived content into `wiki/`.

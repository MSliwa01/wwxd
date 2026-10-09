# Asking a panel: several people on one question

Use this when the user asks what several people would say ("what would Hormozi and
Paul Graham tell me?", "ask the panel"), or wants them compared, combined or set
against each other. The people can be in different vaults or be members of one group
vault.

The value is in the disagreement. Two people with different values give different
advice, and the user learns more from seeing why than from an average of the two.
Never blend them into one voice.

## Steps

1. **Pick the panel.** `wwxd vaults` lists every vault and its members. Use the people
   the user named; if they said "the panel" or "everyone", use every member with a
   thinking page. Two to four people works best.
2. **Answer for each person separately**, following `ask.md` from start to finish for
   each one: verdict, what it rests on, quotes, confidence. Do one person at a time,
   or hand each person to a subagent if your agent supports it, so one person's
   framing doesn't leak into the next.
3. **Map agreement and disagreement.** For each point where their verdicts differ,
   find the reason on their thinking pages: a value they rank differently, a rule one
   holds and the other doesn't, a different situation each is picturing. Cite both
   sides. Where they agree, say whether they agree for the same reason or for
   different ones; agreement from different premises is stronger evidence.
4. **Debate round.** Give each person's reply to the other side's strongest point.
   Build the reply only from that person's own statements and thinking page, label it
   as inferred, and give a confidence. If someone has said nothing that bears on the
   other's point, say they'd likely not engage with it rather than inventing a reply.
5. **Synthesis.** Now speak as yourself, clearly labelled. Say which advice fits
   which situation ("if you have six months of savings, follow X; if you don't,
   follow Y"), using the user's own details. Don't declare a winner unless the
   evidence clearly favours one side for this user.

## Answer format

```
**The panel:** names, and one line on what each one optimizes for.

## <Person A>
**Verdict:** … **Based on:** … 
- quotes with citations

## <Person B>
…

## Where they agree
- Point, and whether they reach it for the same reason.

## Where they split, and why
- **<topic>:** A says … because they value … ("quote", [[…]]). B says … because …
  ("quote", [[…]]).

## Debate (inferred from their own words)
- **A on B's point that …:** … (confidence: medium) ("quote", [[…]])
- **B on A's point that …:** …

## How to use this (my synthesis, not theirs)
- If <your situation>, lean on A, because …
- If <other situation>, lean on B, because …
```

## Rules

- Every claim belongs to one named person and carries that person's citation.
- Quotes follow `format.md`: verbatim, cited, timestamped for audio.
- Don't make anyone agree to keep the peace. If they disagree, the disagreement is
  the answer.
- A debate reply is a guess about what they'd say. Mark it, and never write it as a
  quote.
- Note when someone is outside their competence (from their profile): a marketer on
  AI forecasting, an investor on biology.

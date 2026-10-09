Someone asked what {{person}} would tell them to do. Below are several answers. You don't know how any of them were produced. Judge the content, not the formatting or the length.

Question:
{{question}}

The person's primary sources are in ./raw/ in your working directory (transcripts and essays). Use Grep and Read on them to check whether a claim about what the person said or did is real, and whether the person addressed this kind of decision.

{{answers}}

Score each answer from 1 to 5 on four things.

- decisiveness: 5 means it picks one option (or one clear action) in its first lines and sticks to it, with a reason. 3 means it leans one way but hedges. 1 means "it depends" with no deciding rule, or it lays out both sides and leaves the choice to the user. An answer that says "it depends" and gives the person's own deciding rule ("under $1M do X, above it Y") can still score 4.
- distinctiveness: 1 means any generic advisor would say it. 5 means reasoning only this person would give: their frameworks, their numbers, their stories, their blunt priorities.
- grounding: 5 means the reasons are things this person really said or did, and you could confirm the ones you checked. 1 means the reasons are invented, wrongly credited to them, or contradict the sources. Generic reasoning that never claims to be theirs is a 3.
- usefulness: would this help someone who has to decide today?

Also give, for each answer:
- pick: the option or action it recommends, in a few words, or "none".
- consistent_with_person: "yes" if the pick matches what the sources show this person thinks, "no" if it contradicts them, "unknown" if the sources don't settle it.

Then rank all answers from best to worst for someone who wants this person's actual advice.

Reply with only a JSON object like this, with one key per answer letter:
{"A": {"decisiveness": 0, "distinctiveness": 0, "grounding": 0, "usefulness": 0, "pick": "...", "consistent_with_person": "unknown"}, "B": {...}, "ranking": ["B", "A"], "notes": "one or two sentences on what separated them"}

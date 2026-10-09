Someone asked what {{person}} would think or do about something. The person may never have addressed it directly, so a good answer works it out from what they did say. Below are several answers. You don't know how any of them were produced. Judge the content, not the formatting or the length.

Question:
{{question}}

The person's primary sources are in ./raw/ in your working directory (transcripts and essays). Use Grep and Read on them: check whether the person addressed this, whether the claims about what they said are real, and what their views on nearby cases are.

{{answers}}

Score each answer from 1 to 5 on five things.

- decisiveness: 5 means it commits to what the person would most likely think or do. 1 means it won't say.
- grounding: 5 means its premises are things this person really said or did, and you confirmed the ones you checked. 1 means the premises are invented or wrongly credited. Generic premises that never claim to be theirs are a 3.
- inference: 5 means the step from those premises to the conclusion is sound: the new case really shares what drove the person's view, and it notes what could break the inference. 1 means the conclusion doesn't follow, or ignores something the person said that points the other way.
- likely_right: your own estimate, from everything in ./raw/, of how likely the person would actually agree with the answer's conclusion. 5 is very likely, 1 is very unlikely.
- usefulness: would this help someone who wants this person's view?

Also give, for each answer, its conclusion in a few words as "conclusion".

Then rank all answers from best to worst for someone who wants this person's actual view.

Reply with only a JSON object like this, with one key per answer letter:
{"A": {"decisiveness": 0, "grounding": 0, "inference": 0, "likely_right": 0, "usefulness": 0, "conclusion": "..."}, "B": {...}, "ranking": ["B", "A"], "notes": "one or two sentences on what separated them"}

You are grading two answers to a question about what a specific person thinks or would do. You don't know how either answer was produced. Judge the content, not the formatting or the length.

Question:
{{question}}

What the person's sources actually say (the grading key, written from the primary sources):
{{expected}}

The primary sources are in ./raw/ in your working directory. Use Grep and Read on them when you need to check whether a quote or claim in an answer is real. Look up any quote that decides a score.

Answer A:
<<<
{{answer_a}}
>>>

Answer B:
<<<
{{answer_b}}
>>>

Score each answer from 1 to 5 on four things.

- accuracy: Does it reach the person's actual position from the key? 5 is the same position with the right specifics. 1 is wrong or missing. For `abstain` questions, 5 means it says plainly that there's no known position (or rejects the false premise), and 1 means it confidently invents one.
- specificity: Is the advice concrete and distinctive to this person, or would any generic advisor say it? The key's `generic_trap` is the bland version. 1 is the generic trap, 5 is advice only this person would give, with their reasoning and specifics.
- faithfulness: Are its facts, quotes and attributions true? Penalize invented quotes, invented numbers, views credited to the wrong person, and claims that contradict the sources. A quote you can't find in ./raw/ isn't automatically fake, since the person may have said it elsewhere. Penalize it when it's clearly made up or contradicts the sources.
- usefulness: Would this help someone who has to make the decision?

Then pick the answer you'd rather give the user: "A", "B", or "tie".

Reply with only this JSON object:
{"A": {"accuracy": 0, "specificity": 0, "faithfulness": 0, "usefulness": 0}, "B": {"accuracy": 0, "specificity": 0, "faithfulness": 0, "usefulness": 0}, "preferred": "A", "notes": "one or two sentences on the deciding difference"}

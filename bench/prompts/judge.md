You are grading an answer produced from a knowledge vault about specific people.

Question:
{{question}}

Gold expectation (YAML):
{{expected}}

Answer to grade:
<<<
{{answer}}
>>>

Score each field from 0 to 1:
- "stance": does the answer reach the expected stance? (1 = same position, 0.5 = partially, 0 = wrong or missing)
- "citations": does it cite the expected sources (any of `must_cite`), with claims the citations plausibly support?
- "abstain": if `expect: abstain`, 1 when the answer clearly says the sources don't cover it, 0 if it invents a position. Otherwise 1 when it doesn't wrongly refuse.
- "attribution": 1 if every view is credited to the right person (watch for interviewer/host lines credited to the member), 0 if not.

Reply with only a JSON object, e.g.
{"stance": 1, "citations": 0.5, "abstain": 1, "attribution": 1, "notes": "short reason"}

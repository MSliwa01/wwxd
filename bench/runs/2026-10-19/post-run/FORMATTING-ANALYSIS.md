# Mechanical formatting analysis

This is an explicitly post-hoc sensitivity analysis. It does not replace the frozen protocol's strict-JSON primary result or change any original answer, judgment, prompt or vote.

Reason: completed judge calls sometimes returned the requested JSON inside one Markdown code fence. The strict parser correctly rejected that format. Losing the entire vote for this wrapper is a measurement failure rather than evidence of either answer's quality.

The only permitted transformation removes one outer fence around the entire response, after trimming external whitespace. The opening line must be exactly three backticks with an optional lowercase `json` tag and trailing spaces; the closing line must be exactly three backticks with trailing spaces. The payload must pass the original strict JSON envelope, exact pair-ID coverage and individual vote schema checks. No prose extraction, nested-fence extraction, trailing-comma repair, missing-field completion, score changes, winner changes or new judge calls are allowed. Unwrapped outputs are decoded with the original parser unchanged.

Run this analysis only after all 72 planned judge batches have terminal records. Preserve failed, blocked and individually invalid votes. Use the frozen pair mapping and eligibility, original score dimensions, external-judge exclusion and question-level consensus with all 12 slots. Record hashes of every input and label recovered votes. Report strict and mechanically decoded counts separately. This rule was written after observing wrapper failures and before inspecting recovered winner totals. It cannot establish that missing votes are unbiased, nor supply an observation for an absent answer or failed call.

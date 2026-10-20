# Private evaluation report

Evaluation date: 2026-10-19.

Answer calls: {'ok': 143, 'failed': 1}, target 144. Judge batch calls: {'ok': 69, 'failed': 3}, target 72 if all pairs are eligible. Judgment units target 216. Total logged outer attempts: 216.

A completed provider call does not imply a correct answer or a valid judgment. Judge batch JSON-envelope failures: 47. Individual invalid votes and failed/blocked units remain in the status counts and denominators.

Each suite has 12 selected questions. Repeated judge ratings and answer families do not increase the number of independent questions. Results are descriptive and support no global model ranking or universal success-rate claim.

## diagnostic12

Answer statuses: {'ok': 72}, target 72. Judgment statuses: {'failed': 72, 'ok': 36}, target 108.

External-judge votes: {'valid_ratings': 24, 'raw': 1, 'grounded': 21, 'tie': 2}. Same-family votes, excluded from primary: {'valid_ratings': 12, 'raw': 1, 'grounded': 10, 'tie': 1}.

| Answer family | Judge family | Raw | Grounded | Tie | Valid / target | Primary |
| --- | --- | ---: | ---: | ---: | --- | --- |
| sol | sol | 1 | 10 | 1 | 12 / 12 | False |
| sol | opus | 0 | 0 | 0 | 0 / 12 | True |
| sol | gemini | 0 | 0 | 0 | 0 / 12 | True |
| opus | sol | 0 | 11 | 1 | 12 / 12 | True |
| opus | opus | 0 | 0 | 0 | 0 / 12 | False |
| opus | gemini | 0 | 0 | 0 | 0 / 12 | True |
| gemini | sol | 1 | 10 | 1 | 12 / 12 | True |
| gemini | opus | 0 | 0 | 0 | 0 / 12 | True |
| gemini | gemini | 0 | 0 | 0 | 0 / 12 | False |

| Dimension | Raw mean | Grounded mean | External ratings per arm |
| --- | ---: | ---: | ---: |
| accuracy | 2.5 | 3.625 | 24 |
| specificity | 2.542 | 4.083 | 24 |
| faithfulness | 2.042 | 3.625 | 24 |
| usefulness | 2.458 | 3.75 | 24 |

sol external consensus across 12 question slots: {'missing': 12}.

opus external consensus across 12 question slots: {'missing': 12}.

gemini external consensus across 12 question slots: {'missing': 12}.

All scores, every answer/judge combination, original question-level votes, disagreements and agreement denominators are in `results/summary.json`.

## newadvice12

Answer statuses: {'ok': 71, 'failed': 1}, target 72. Judgment statuses: {'failed': 76, 'ok': 29, 'blocked': 3}, target 108.

External-judge votes: {'valid_ratings': 23, 'raw': 6, 'grounded': 11, 'tie': 6}. Same-family votes, excluded from primary: {'valid_ratings': 6, 'raw': 0, 'grounded': 1, 'tie': 5}.

| Answer family | Judge family | Raw | Grounded | Tie | Valid / target | Primary |
| --- | --- | ---: | ---: | ---: | --- | --- |
| sol | sol | 0 | 1 | 5 | 6 / 12 | False |
| sol | opus | 0 | 0 | 0 | 0 / 12 | True |
| sol | gemini | 0 | 0 | 0 | 0 / 12 | True |
| opus | sol | 3 | 4 | 5 | 12 / 12 | True |
| opus | opus | 0 | 0 | 0 | 0 / 12 | False |
| opus | gemini | 0 | 0 | 0 | 0 / 12 | True |
| gemini | sol | 3 | 7 | 1 | 11 / 12 | True |
| gemini | opus | 0 | 0 | 0 | 0 / 12 | True |
| gemini | gemini | 0 | 0 | 0 | 0 / 12 | False |

| Dimension | Raw mean | Grounded mean | External ratings per arm |
| --- | ---: | ---: | ---: |
| decision_quality | 3.348 | 3.609 | 23 |
| actionability | 3.565 | 3.478 | 23 |
| constraint_fit | 3.13 | 3.478 | 23 |
| reasoning | 3 | 3.13 | 23 |

sol external consensus across 12 question slots: {'missing': 12}.

opus external consensus across 12 question slots: {'missing': 12}.

gemini external consensus across 12 question slots: {'missing': 12}.

All scores, every answer/judge combination, original question-level votes, disagreements and agreement denominators are in `results/summary.json`.

## Review and limitations

Post-run factual review exports: {'practical_answer_slots': 72, 'diagnostic_pairs': 36, 'original_objections': 147, 'status': 'Independent post-run reviews pending. These exports cannot change original votes.'}. Original votes remain unchanged, including schema failures and factual errors.

Full wiki pages were frozen before fixture parsing. Every routed page is supplied unchanged, with provenance and hashes. Prompt estimates did not resize context. Actual input usage, including missing provider fields and raw usage records, is in `results/accepted-input-usage.json`.

Context-usage diagnostics: 0 pairs flagged context_usage_inconsistent and excluded as ineligible. The pre-run tolerance is 50% through 200% of the frozen per-family estimate. Actual raw and grounded token counts and deltas are retained. This diagnostic does not prove attention to every page.

Sol native logs do not independently attest the serving model. Opus and Gemini observed model identifiers are checked when supplied. Provider CLI wrappers differ across families. CLI backends may retry transport internally; outer attempts and all provider streams are retained.

Validation passed. Usage and eligibility warnings: 1. Failed/blocked/invalid rows: 152. Word counts and formatting deviations are retained without regenerating or truncating answers.

Diagnostic regression uses known cases and repaired raw references. Practical advice uses new raw-only scenarios and judges receive only questions and anonymous answers. Advice scores are not observed business outcomes. Independent factual reviews are required before interpretation is complete. No public site or CV metric is changed.

# wwxd evaluation v2 protocol

Protocol fixed before new answer generation on 19 October 2026. The first pilot remains unchanged as historical evidence.

## Questions and comparisons

Two suites answer different questions and must have separate results.

1. **Diagnostic regression:** the existing 12 questions. A source-only auditor repairs and verifies their references against raw documents before any new answers. This is a known-case regression, not held-out evidence of general performance.
2. **Practical advice:** 12 new standalone scenarios written by a separate raw-only author who does not read compiled wiki pages, previous answers or judgments. Questions state a decision, goal and constraints, without asking what a named expert would say. Multiple defensible recommendations are allowed. Scenarios are new synthetic decisions, but some source principles overlap old gold sets as disclosed in fixtures/AUDIT.md; do not call them independent tests of unseen principles. The author's source IDs, source hashes and provenance statement are frozen with the questions before answering.

Each suite uses GPT 6.1 Sol at high effort, Opus 5.5 at high effort and Gemini 3.5 Flash-Lite with its recorded provider settings. Each model answers each question once without supplied knowledge and once with supplied knowledge. Every answer is a fresh session with no tools, browsing, source files, prior responses or grading keys accessible through the prompt. Only transport failures permit a bounded logged retry.

## Knowledge context

Use the complete, unchanged compiled wiki for the routed vault, in a stable file order, with provenance labels and hashes. No question-specific leaf selection, keyword-only top-eight pack, manual gold-based additions or truncation. The two vaults are small enough to attempt the full-context comparison. Verify actual accepted input usage and record provider context-limit failures without silently shrinking the pack or changing models.

This estimates the incremental effect of the fixed complete wiki pack under these prompts while removing question-specific selection from this comparison. Context order, context burden and model-specific limits remain part of the experiment. It is a full-context knowledge-use test, not an end-to-end retrieval benchmark or evidence that an arbitrarily large vault fits into a model context window. Existing raw transcripts are not supplied to answer models. Wiki content is frozen independently of the reference-key audit. The question and common instructions precede the context. Every grounded prompt appends the same reminder after the complete wiki: "End of supplied context. Answer the question above under the instructions above." The raw prompt is the identical initial instruction and question without that appended context material.

Both arms must complete for a question/model pair to be eligible. An incomplete response, a provider context-limit rejection, output truncation or a detected context-reduction event makes the pair ineligible for the primary comparison. Keep all original failures and the planned 12 question slots visible as missing rather than counting the surviving arm alone. Record the exact serialized payload hash and accepted input-token usage including cached input; flag missing or inconsistent usage for review. Pre-run expected context-token increments use pilot-metadata character/token ratios of 3.57 for Sol, 2.44 for Opus and 3.2 for Gemini. A successful pair with grounded-minus-raw accepted input below 50% or above 200% of that estimate is flagged context_usage_inconsistent and is ineligible for the confirmed primary comparison. The broad tolerance is a diagnostic check, not a tokenizer estimate of exact equality; retain actual usage and all planned question slots. Provider-internal retention cannot be independently proven from a successful response, so the report must not claim that byte hashes alone prove the model attended to every page.

## Output requirements

Both advice arms receive identical instructions and an approximate 250-word budget. They provide a direct recommendation, concrete next steps, material assumptions and decision criteria. They do not mention experts, the knowledge base, quotations, citations or source links. Relevant knowledge can inform reasoning; it must not replace the question's goals or constraints. Models may reason using their own knowledge in both arms. Missing information should produce useful conditional advice rather than automatic refusal.

Diagnostic answers follow the same output-format rules where possible, while answering the factual question and correcting a false premise. They are evaluated separately from practical advice.

## Independent evaluation

Use new judge sessions from all three model families. No judge sees model identities, arm labels, other judges, prior outcomes or a desired winner. Use fixed, independently recorded, counterbalanced A/B orders per judge family. Judges work in bounded batches; record the grouping. Same-family judgments are reported separately and excluded from primary comparisons.

With all pairs complete, there are 144 answer calls, 72 question/model pairs and 216 individual judgment units from 72 fresh judge calls with at most three pairs each. Each pair has one judge from each family. Each judge-family/suite/answer-family block places grounded at A for exactly six of its 12 questions, with independently fixed order vectors across judge families. There is no replacement judge for a failed call.

Primary reporting uses question-level consensus separately for each answer family and suite: both external judges choose grounded, both choose raw, both choose tie, disagreement, or missing. One tie and one arm preference is disagreement. Fewer than two valid external votes is missing. The 12 question slots remain the denominator. External vote totals, same-family votes and mean dimension scores are secondary descriptive outputs. Do not convert repeated ratings or answer families into extra independent questions.

Score anchors are fixed in the frozen judge instructions: 1 fundamentally deficient, 2 major problems, 3 mixed with meaningful gaps, 4 good with minor gaps, 5 strong and sufficiently complete. Decision quality concerns a defensible recommendation, actionability concerns concrete steps and decision criteria, constraint fit concerns the stated goal/resources and material assumptions, and reasoning concerns coherent logic and arithmetic. Diagnostic dimensions are accuracy, specificity, faithfulness and usefulness. The judge separately chooses A, B or tie for substantive overall quality, rather than a post-hoc weighted score formula. The reason must explain the difference; a material inconsistency between scores and the winner is preserved and flagged in review.

**Practical judges see only the scenario and anonymous answers.** Score decision quality, actionability, fit to constraints, and reasoning from 1 to 5. Reward a useful, defensible solution; do not reward agreement with an expert or presumed use of sources. A tie is valid. Arithmetic and explicit scenario constraints can be checked directly. These are judgments of advice quality, not observed business outcomes.

**Diagnostic judges see the audited reference evidence.** Each packet contains the question, supported stance and acceptable interpretations, original evidence excerpts with source IDs, verified speaker/date/timestamp information where available, and stated uncertainty or contradiction criteria. Key coverage means the supplied evidence supports the required stance and each required factual detail; an absence claim needs a documented corpus check rather than invented evidence. A source-only audit repairs gaps before answering, and an independent reviewer checks coverage before approval.

Diagnostic judges must distinguish contradiction from absence of evidence. A claim missing from the key is not automatically false. Uncertain factual objections must be labelled unverified and reviewed separately rather than treated as established hallucinations. All roles receive the explicit evaluation date. May 2026 is before 19 October 2026. Publication dates and dates of events described in a source are distinct, and a model's training cutoff does not make a supplied later document fictional.

## Validation and review

Before answering: verify source hashes, independent question provenance, complete wiki coverage, prompt equality apart from the added context, key coverage and model configuration. Freeze questions, context, instructions, reference packets, randomisation and aggregation rules with a manifest. An independent reviewer checks the harness and fixtures before the parent authorises model calls.

Completion checks require normal terminal events, reject known context reduction and disallowed tool items, and preserve raw metadata. Gemini calls run serially. Outer transport retries remain limited to two attempts; a 429 waits at least 60 seconds or the reported retry delay, bounded at 120 seconds, before its last attempt. No content failure receives a retry.

After answering: record all outcomes, formatting/length deviations, source/context-reference leaks and provider failures. Leak flags annotate original answers without rewriting or excluding them merely for their content. Do not regenerate or discard an answer because it loses. Check judgment schemas and score ranges. Keep raw and decoded votes together with their A/B mapping.

After judging: preserve every original verdict. Audit all diagnostic raw wins, ties and disagreements against original raw sources. An independent factual review covers all practical answers, including unanimous winners, with answer-family and arm labels hidden. The reviewer receives the scenario, frozen advice evidence packets and access to the full raw corpus enumerated by the pre-run source inventory; every consulted file must match its frozen hash. It checks arithmetic, explicit scenario constraints and checkable source-derived claims, distinguishing verified contradictions from claims that cannot be verified. Missing source support alone is not a false claim. Claims requiring evidence outside that corpus remain unverified unless a separately documented check supplies it. Review practical disagreements and factual objections separately; do not overwrite votes or promote a corrected verdict into a primary result after seeing outcomes. Report missing evidence and judge errors alongside the original totals. A repeat evaluation needs its own frozen protocol and result directory.

## Reporting

Report completed calls, failed calls and denominators. Show each answer-model/judge-model combination, external-judge votes, question-level consensus and disagreements. Repeated ratings of one pair are not independent questions. Use descriptive results, with no global model ranking or universal success-rate claim from this small selected sample.

Store scripts, frozen inputs, responses, judgments, validation and interpretation separately. No new metric goes into the public CV or site automatically. Public wording requires a result whose scope and evidence can be explained directly.

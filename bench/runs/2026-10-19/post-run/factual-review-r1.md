# Factual review r1 (blinded)

Evaluation date 2026-10-19. The full per-answer record is in `factual-review-r1.json`.

- Input: `run/results/review-export/practical-all-answers.json`, sha256 `41bde0c6507156cc06c72abec7914ec8de08c148dfebd86906b48993495a8ffd`
- Source inventory: `run/frozen/fixtures/source-inventory.json`, sha256 `6b7fcfe7fda2405fcc4a1256cb65aa94e3f69cc60b8ade8fbc2b4aa26281689e`. All 37 raw files match their inventory hashes. I read six of them and checked the quotes I cite.

I did not open the private answer map, responses, judgments, batch logs, summaries, preflight or execution interpretations, arm or model labels, PROTOCOL.md or the wiki. The brief's second step, reviewing diagnostic exceptions and original factual objections, needs judgments and votes, which this assignment excludes. I did not do it.

## Coverage

| | Count |
|---|---:|
| Slots | 72 |
| Assessed | 71 |
| Unassessable (failed, empty answer) | 1 |
| Established material error | 5 |
| No established material error | 66 |
| Of those 66, entries with minor notes | 25 |
| Entries with no issue at all | 42 |

Issues by type: 5 material arithmetic, 14 minor arithmetic, 2 material constraint, 6 minor constraint, 13 unverified, 0 source contradictions. Four issues would change the recommendation as written.

## What was checked for every answer

- I recomputed every number in the answer from the user's stated inputs. This covered profit, hours, runway, day counts from 2026-10-19, membership projections (`m(next) = m x (1 - churn) + new`), CAC and payback, and whether budget allocations add up.
- I checked the plan against each explicit constraint: the 50-hour cap, the $45,000 and $8,000 budgets, "pick one" or "pick two", the yes/no requests, the 8-week and 90-day windows, and retaining the regulars.
- I treated proposed prices, targets and thresholds as proposals, not claims. Labelled assumptions count as assumptions.
- I checked claims about the outside world against the evidence packet and the raw sources. Where nothing confirms or refutes a claim, I mark it unverified, not false.
- I recomputed the evidence packet's own hard checks instead of trusting them. They hold, except that the yc-02 note "break-even around month 15" comes out nearer month 14.1 (45,000 / 6,300 = 7.14, and ln 7.14 / ln 1.15 = 14.07).

## Established material errors

**review-4f73ce2eea8cbb1e (bookkeeping).** The answer says the plan "strictly respects your 50-hour capacity", then computes 54 hours and says that "can be compressed to 50 by tightening workflows". The sums are also wrong: 37 x $460 is $17,020, not $17,010, and 4 x $1,960 is $7,840, not $7,440. The corrected total is $24,860. That is still short of $25,000, so "hitting your baseline target" is false.

**review-6d79b5f64458fb94 (bookkeeping).** The answer claims $28,200 profit, but that figure counts 40 standard clients at 60 hours. The answer then drops 10 clients to fit 50 hours and never recomputes. The plan that fits the cap earns 30 x $460 + 5 x $1,960 = $23,600, which misses the goal at the $2,000 premium price.

**review-a158a62e3d9c3de2 (dog grooming).** Groomer pay is 40% of $14,820, which is $5,928, not $5,070. Current profit is therefore $3,220, not $4,078. The "significantly expanding profit" scenario (140 grooms, regulars at $100) also fails. On the answer's own prices it earns about $3,172 at a $103 average ticket, or $3,760 if every groom were $110. Both are below the baseline the answer stated.

**review-6d5a056f2c08c8aa (serum ads).** The answer conditionally approves "the aggressive $1,000-a-day plan" without checking the budget. That plan costs $74,000 over the 74 days to December 31, against $45,000. It also says stock would last "roughly 130 days". At 3.2 ROAS, $1,000 a day sells about 55 bottles a day, so 4,000 bottles last about 72 days.

**review-aba49e4011c04e9d (serum ads).** The answer's main reason for saying no is that $1,000 a day "will rapidly exhaust your 4,000-bottle inventory well before December 31" and miss Black Friday. At the reported ROAS the full $45,000 sells about 2,483 bottles, about 2,200 of them by Black Friday. The "No" still holds on budget grounds, which the answer also gives.

## Examples of minor notes

- review-c19d15fa98e30e9c says "about 170 subscribers just to match one premium client". One premium client is about 50 subscribers at $49. 170 to 180 subscribers covers the whole $8,800 gap.
- review-c8a5e6cdf5b50ba6 prices the annual plan at "$690 (roughly two months free)". Two months free is $790, and $690 is about 3.3 months free.
- review-1f95279c0daf9080 says "even doubled ads top out around 830". At the stated $110 per member, doubled spend gives about 963 in 12 months. 830 implies an unstated rise in acquisition cost.
- review-6929cf0d8497b0ce says that at 10% growth "the runway stretches to about 19 months". On its own framing, revenue reaches $45,000 around month 21 with roughly $100,000 still in the bank. The figure is conservative.
- review-d3388e825af60df2 labels a 90-day plan "Weeks one through thirty ... sixty-one through ninety". This is a unit slip.
- review-41f4c4e4550bd490 and review-45453de65eb0ae62 do not pick one of the four hiring options the user listed.
- review-da85302df6ff58a5 calls the situation "a cash crunch" although the user raised $3M three months ago. The answer's "process is already efficient" differs from the source view ("the biggest issue is they don't have a pipeline", `yc/raw/yt-7TU636F_yVQ.md` at 15:01, sha256 `b43f7c49...`). That is a disagreement about advice, not a factual contradiction, and I do not count it as an error.

## Unassessable

review-f660843d9984b559 (membership case) has status "failed" and an empty answer. I treat it as unassessable, not as false.

## Source contradictions

None. No answer cites a named person or source. Where answers echo source positions (annual plans churn less, press rarely drives startup customers, attribution needs checking, slow institutional buyers), they agree with the raw text. The unverified items are general market claims that the corpus neither supports nor refutes, such as hospital sales cycle lengths and couples-app churn.

This finishes my scope. I wrote only the two `factual-review-r1` files. I did not modify the runner, sources, answers, votes, approvals or CV/site files.

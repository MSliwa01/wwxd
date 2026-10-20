# wwxd-eval-v2 fixtures: audit

Built 2026-10-19. Frozen with `SHA256SUMS` in this directory. Do not edit after model outcomes exist.

## Files

| File | Who sees it | Contents |
|---|---|---|
| `diagnostic-questions.json` | answering model | The 12 existing ask12 questions: id, vault, question, category. Text copied from the gold YAML unchanged. |
| `diagnostic-reference.json` | diagnostic judge | Source-audited key per question: stance, required and supporting points, errors, primary_sources, verified evidence, gold discrepancies, open uncertainty. |
| `advice-questions.json` | answering model (`question` only) | 12 new advice scenarios, advice-hz-01..06 and advice-yc-01..06. `vault` and `domain` are routing metadata and must not go in the user turn. |
| `advice-evidence.json` | private; not for primary practical judges | Source support, hard arithmetic and constraint checks, missing-input notes, defensible answers, credit signals. |
| `source-inventory.json` | reference | All 37 raw files (13 hormozi, 24 yc) with path, sha256, title, date, url. |
| `tools/build_fixtures.py` | reference | Builds the four JSON files. Paths and hashes come from the inventory; question text comes from the gold YAML. |
| `tools/verify_fixtures.py` | reference | Checks every quote and hash against raw files. |

## What was read

- Raw vault files under `/home/mateusz/wwxd-lab/vaults/{hormozi,yc}/raw/`.
- `/home/mateusz/Desktop/pyprograms/wwxd/bench/gold/hormozi-ask12.yaml` and `yc-ask12.yaml`.
- `cv/WRITING.md` and the global engineering policy.

Not read: wiki pages, model answers, judgments, outcomes, `wwxd-eval-v2/PROTOCOL.md`, `wwxd-eval-v2/run/`, and the other gold files (heldout, honesty, inference, opinion, `hormozi.yaml`, `yc.yaml`). The author did not check overlap with those other gold sets. An independent preflight reviewer subsequently compared all 12 cases against 122 old gold questions. The highest TF-IDF cosine was 0.21; no case was an old question with expert names removed. advice-hz-05 shares its decision core with hormozi.yaml hz-15 and hormozi-opinion.yaml op-hz-03, and the premium tier in advice-hz-01 echoes hz-13. These are new scenarios and calculations, not independent samples of previously unseen principles. No model or API calls were made.

## Verification

`python3 -I tools/verify_fixtures.py .` passes:

- 180 quotes checked: 103 in diagnostic keys, 77 in advice support. Each quote is verbatim after collapsing whitespace. For transcripts it must sit inside the `[m:ss]` segment named by `timestamp`; web essays have `timestamp: null` and are matched against the whole body.
- Every `source_sha256` matches the raw file on disk.
- Diagnostic questions and references have the same 12 ids, vaults, text and categories. A separate check confirmed the question text and categories equal the gold YAML.
- Advice ids are in the expected order. Question text contains no expert, company or platform names from the block list and no `"` characters.
- All advice arithmetic was recomputed in Python. The figures are in `hard_checks`.

Quotes keep caption errors as they appear in the raw text ("School" for Skool, "Gary" for Garry, "8020", "todoor"). One raw file (`yt-JDR-R--4HhM`) has double spaces inside lines. Its quotes match only after whitespace collapsing.

## Diagnostic key changes

| id | Status | Change |
|---|---|---|
| hz-02 | confirmed, expanded | Added the "write down the flaws and claim them" step, the humor bonus, and the sales-call version from `yt-MH-IMJxbUY4`. |
| hz-05 | confirmed, expanded | Added the scope limit (online and consumer services, not insurance or alarm subscriptions), the under-90-days caveat and the "unless everyone leaves" exception. The figures are Skool platform data he relays. |
| hz-09 | corrected context | The "5% ... 100% in headache" line is two unlabeled turns, so its speaker is uncertain; it is now a supporting point. Added that the owner had already planned the payoff, that Hormozi approved, and that the same plan kept funding ads. |
| hz-11 | confirmed, one correction | Added the earlier 23% raise as evidence. Noted that the raw price figures disagree (see below). |
| hz-16 | confirmed | The host is never named in the raw file. "Steven Bartlett" is outside knowledge, consistent with "flight story". It is a supporting point, not a requirement. |
| hz-20 | corrected | The gold stance said both "the sources don't cover this" and "the sources show the opposite". The raw supports the second. The key is now a false premise backed by seven quotes from `yt-o64cI6tebnU`, and must_cite and evidence are filled in (both were empty). |
| yc-01 | confirmed, expanded | Added the August 2026 essay "How Universities Should Prepare Founders", which restates the stance. |
| yc-05 | confirmed, expanded | Added the reasons for going and the "as long as you do actually come back" condition. |
| yc-08 | confirmed, speaker caveat | Two-host episode with unlabeled captions. Only the Socialcam poll, the Justin.tv story and the same-day offer are attributable to Seibel. |
| yc-12 | confirmed, speaker caveat | The framework is presented jointly. Premise note: with a one-year cliff, nothing usually vests at 9 months. The source says "even if you vested", so the stance holds. |
| yc-17 | confirmed, interpretation flag | The gold's reason for the preface ("would sound self-serving coming from YC's CEO") is not in the source. It is acceptable as inference but not required. |
| yc-20 | confirmed, expanded | must_cite was empty; it is now `yt-8d-cApFHjeY`. Added "determined" from her criteria so answers that mention it are not marked as accepting the premise. PG's "formidable" line is context only. |

## Inconsistencies inside the raw sources

- hz-11: the price is $1,575 per unit at [1:05], but the plan at [30:45] says "10%, so around 1650 per unit". A 10% raise on $1,575 is about $1,733; $1,650 is about +4.8%. Judges should accept either figure.
- hz-09: 10% of $479k profit is about $48k a year, which does not clear $60k in four to five months as the owner says. The stance does not depend on it.
- hz-20: the roofer's revenue figures conflict (about $41k, "20K a monthish", under $32k three months earlier, then about $247k to $250k). His age is never stated. Neither matters for the key.

## Speaker attribution

Auto-captions carry no speaker labels. Each evidence item has `speaker` and `speaker_basis`. Solo videos and essays are attributed directly. Guest episodes (`yt-OQf2Ba-Lp_4`, `yt-MH-IMJxbUY4`, `yt-o64cI6tebnU`), the Diary Of A CEO interview and the Altman conversation are inferred from content. Dalton and Michael episodes are marked `caldwell_or_seibel` unless a turn identifies its speaker. Judges should grade content and not penalize an answer that credits a two-host point to either host or to both.

## Advice cases

All 12 are synthetic. The businesses, people and numbers are invented. The raw sources supplied only principles, which `inspiration` records per case. None restates an ask12 question. advice-hz-05 shares a topic (membership churn) with diagnostic hz-05 but asks for a decision with arithmetic, not a benchmark.

| id | Domain | Type |
|---|---|---|
| advice-hz-01 | offers | tradeoff |
| advice-hz-02 | pricing | tradeoff |
| advice-hz-03 | ads | missing input: contribution margin |
| advice-hz-04 | customer acquisition | tradeoff |
| advice-hz-05 | offers and retention | tradeoff |
| advice-hz-06 | first business decision | tradeoff |
| advice-yc-01 | MVP scope | tradeoff |
| advice-yc-02 | pricing and segment | tradeoff |
| advice-yc-03 | quit job or not | missing input: retention and organic growth |
| advice-yc-04 | launch acquisition | single decision |
| advice-yc-05 | hiring | tradeoff |
| advice-yc-06 | idea choice | tradeoff |

Each case lists several defensible answers and no mandatory recommendation. Hard errors are limited to wrong arithmetic, plans that break a stated constraint, and invented facts about the user's situation.

Known limits:

- advice-hz-03 uses the explicit evaluation date 2026-10-19 supplied in every answer and judge prompt. October 19 through December 31 inclusive is 74 days; roughly 70 to 75 days is acceptable with a reasonable counting convention. Primary practical judges do not receive the evidence file.
- advice-yc-04's payback figure assumes a 24-month customer life, which the question does not state. It is marked as an illustration.
- The source-inspired direction leans toward the source's views (for example, skepticism about press). Judges who get `advice-evidence.json` should treat `defensible_answers` as the range, not as a ranking.

## Pre-run correction record

The first preflight snapshot is archived under ../preflight-archives/d47e8886b57843ff533a01ec520b15f48b246ca32eee8e71dcb4d42efdceeb01. Before any v2 answer or judge calls, the parent corrected source counts and the explicit-date note, recorded the independent overlap check, added the yc-20 corpus absence check and hz-09 debt-context distinction, and renamed diagnostic source metadata to primary_sources. This metadata identifies evidence for the judge; answers are not required to cite it. Questions and verbatim evidence excerpts are unchanged. SHA256SUMS was regenerated for the corrected pre-run inputs.

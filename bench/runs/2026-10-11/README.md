# Web search vs a vault, October 11, 2026

Raw data for [Web search vs a vault](../../RESULTS.md#web-search-vs-a-vault) in
RESULTS.md. All new answers are Opus 5.5 at effort high with no advisor.

`hormozi-web/` and `yc-web/` have the same files.

| File | Contents |
|---|---|
| `web-answers.jsonl` | Answers to the 20 main-bench questions with only WebSearch and WebFetch, prompt `prompts/answer_web.md` |
| `prose-answers.jsonl` | wwxd answers to the same questions, in the prose format |
| `op-web-answers.jsonl` | Web search answers to the 12 opinion questions |
| `op-prose-answers.jsonl` | wwxd answers to the opinion questions, in the prose format |
| `op-raw-answers.jsonl`, `op-persona-answers.jsonl` | Raw Opus and persona answers copied from the opinion bench in `runs/2026-10-09/<vault>-opinion/`, Opus 5.5 at effort xhigh with a Fable 5.1 advisor |
| `judge-web-vs-prose-<judge>.jsonl` | Pairwise judgments of web search against wwxd on the main bench |
| `rank-op-raw-op-persona-op-web-op-prose-<judge>.jsonl` | 4-way opinion rankings, with scores, picks and whether each pick matches the person |

The judge name at the end of a file is `opus` (Opus 5.5 at effort medium), `haiku`
(Haiku 5.5 at effort high), `muse` (Muse Spark 1.3 through opencode) or `lite`
(Gemini 3.5 Flash Lite). The first three could read the raw transcripts. Gemini had
no tools and saw only the grading key. 5 Muse Spark main-bench judgments failed on
opencode errors and have the `error` field set.

## Scripts

| Script | What it does |
|---|---|
| `scripts/web_bench.sh` | Runs the web search arm on the main and opinion questions and the wwxd prose arm on the main questions, for both vaults |
| `scripts/web_judges.sh` | Waits for the answers, then runs the pairwise judge and the 4-way opinion ranking with each of the four judges |

They use absolute paths from our lab machine. Vaults and gold sets live under
`~/wwxd-lab`, and `web_judges.sh` calls a Gemini judge script like
`runs/2026-10-10/scripts/gemini_judge.sh`. Adjust the paths before you run them.

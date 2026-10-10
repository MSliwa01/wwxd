# Benchmarks

The bench asks one question. Does a model give better answers about what a specific
person thinks when it reads their wwxd vault, compared with answering from its own
memory?

## Setup

Two arms answer the same gold questions in Claude Code, both with the same model.

| Arm | What the agent gets |
|---|---|
| `raw` | The question only. No tools, no MCP servers (`--tools "" --strict-mcp-config`). |
| `wwxd` | The question plus "use the wwxd skill to answer from vaults/<slug>". Read-only file tools and the `wwxd` CLI. |

A third Claude Code session judges each pair blind. Before it sees the answers, the
harness removes citation markup, links, source ids and timestamps, and shuffles the
order. The judge can open the raw transcripts to check quotes. It scores each answer
from 1 to 5 on accuracy, specificity, faithfulness and usefulness, then picks one.

A script also checks every quote that an answer attributes to someone against the
vault's raw transcripts. That check uses no model.

## Gold sets

`gold/*.yaml`. A separate agent wrote each question from the raw sources only,
without reading the wiki. Each one has the person's stance, verbatim evidence with
timestamps, and the bland answer a generic advisor would give (`generic_trap`).

| Category | What it tests |
|---|---|
| `known` | Positions from older sources the model may have seen in training |
| `fresh` | Positions that only appear in sources from 2026 |
| `applied` | A concrete situation where the person gave clear, opinionated advice |
| `attribution` | A line a host or another member said, which a careless reader would credit to the person |
| `abstain` | Topics the sources don't cover, plus one false-premise question |

## Run it

```bash
P=bench/prompts
wwxd bench run hormozi --gold gold/hormozi.yaml --arm raw  --prompt $P/answer_raw.md \
  --agent 'claude -p {prompt} --model claude-opus-5-5 --tools "" --strict-mcp-config' --cwd /tmp/empty
wwxd bench run hormozi --gold gold/hormozi.yaml --arm wwxd --prompt $P/answer_wwxd.md \
  --agent 'claude -p {prompt} --model claude-opus-5-5 --strict-mcp-config --allowedTools Read Glob Grep Skill Bash(wwxd:*)'
wwxd bench judge  hormozi --gold gold/hormozi.yaml --a raw --b wwxd \
  --agent 'claude -p {prompt} --model claude-opus-5-5 --strict-mcp-config --allowedTools Read Grep Glob'
wwxd bench report hormozi --gold gold/hormozi.yaml --arm raw --arm wwxd \
  --judgments bench/results/hormozi/judge-raw-vs-wwxd.jsonl
```

Any agent CLI works. Pass `{prompt}` where the prompt goes, or leave it out to send
the prompt on stdin. Runs resume, so a rate limit only costs the unfinished questions.

The judge doesn't have to be an agent. Any command that takes the prompt and prints
the judge's JSON works as `--agent`, for example a script that makes one API call to
another provider's model. Without file tools it can't open the transcripts, so it can
only check claims against the grading key and what it already knows. Tell it so in
the prompt, or it may mark real quotes as unverified. `runs/2026-10-10/scripts/gemini_judge.sh`
is an example.

## Opinion bench

`gold/*-opinion.yaml` holds "should I do X or Y?" questions with no answer key. Run
several arms (for example `prompts/answer_raw.md`, `prompts/answer_persona.md` and
`prompts/answer_wwxd.md`), then have a judge see all answers to each question at
once:

```bash
wwxd bench rank hormozi --gold gold/hormozi-opinion.yaml \
  --arm op-raw --arm op-persona --arm op-wwxd --prompt bench/prompts/judge_opinion.md \
  --agent 'opencode run -m opencode/muse-spark-1.3-contributor-free {prompt}' --name muse
```

The judge scores decisiveness, distinctiveness, grounding and usefulness, names each
answer's pick, checks it against the transcripts, and ranks the answers. The order is
shuffled and citations are stripped. The summary also reports words and hedge
phrases per answer.

## Held-out test

To test prediction rather than recall, build a second vault from sources before a
cutoff date (`wwxd new <slug>-pre`, copy the older raw docs, compile), then ask only
the questions whose `must_cite` sources are all after the cutoff, with
`prompts/answer_wwxd_extrapolate.md`. Our runs are in `runs/2026-10-09/`.

## Ranking with a grading key

`prompts/judge_rank.md` ranks several answers to the gold questions, so you can
compare more than two arms at once. The judge gets the question, the person's stance
and evidence from the gold set as a grading key, and the raw transcripts in `./raw/`
to check quotes. It scores accuracy, specificity, faithfulness and usefulness from 1
to 5 and ranks every answer.

```bash
wwxd bench rank hormozi --gold gold/hormozi-ask12.yaml \
  --arm ask-opus-high --arm ask-sonnet-high --arm ask-haiku-high \
  --prompt bench/prompts/judge_rank.md --name opus --seed 1 \
  --agent 'claude -p {prompt} --model claude-opus-5-5 --strict-mcp-config --allowedTools Read Grep Glob'
```

`wwxd bench rank` takes 2 to 12 arms. `--seed` sets the answer order, so give each
judge a different seed. The summary reports each arm's `mean_rank` (1 is best) next
to its scores and how often it was ranked first.

## Model and effort study

This study compares Opus, Sonnet and Haiku at effort medium, high and xhigh, for
compiling and for answering. The scripts are in `runs/2026-10-10/scripts/`.

| Script | What it does |
|---|---|
| `study_compile.sh` | Compiles the 4 study sources into empty vaults at each effort, one `claude -p` session per source |
| `study_eval.py` | Scores the study vaults on statements, attribution, gold evidence, lint and cost |
| `study_ask.sh` | Runs the 9 answer arms on `gold/hormozi-ask12.yaml` and `gold/yc-ask12.yaml`, then the pairwise judge against raw Opus |
| `study_rank.sh` | Runs the blind 9-way ranking with an Opus and a Haiku judge |
| `study_ask_eval.py` | Summarizes the pairwise judgments, answer length and time |
| `wer2.py` | Word error rate for the captions vs Whisper section of RESULTS.md |

They use absolute paths from our lab machine and expect its layout. Vaults and gold
sets live under `~/wwxd-lab`, and the study vaults are in `~/wwxd-lab/study/vaults`,
named `s-<model>-<effort>-<yc|hz>`. Adjust the paths before you run them.

The attribution score and `wer2.py` need YC's official speaker-labelled transcript
of the Sam Altman and Garry Tan interview,
<https://www.ycrootaccess.com/p/sam-altman-never-a-better-time-to>. We don't
redistribute it. The scripts read a saved copy of that page from
`/tmp/ycroot/page.html`.

## Known biases

- The gold sets come from the same sources the vault was built from. The bench
  measures whether an agent can recover this person's documented positions. It
  doesn't measure whether those positions are good advice.
- An Opus judge grading Opus answers may prefer its own style. We also judge every
  pair with a model from another family (`--name nemotron` with an opencode model)
  and report both.
- Blinding is imperfect. Answers built from a vault tend to quote more and name
  specific videos, and a judge can notice that.
- Few runs, 20 questions per vault. Treat differences of a few tenths as noise.
- A model's training data can include sources you think of as held out. Check the
  model's cutoff against your source dates.

Results from our runs are in [RESULTS.md](RESULTS.md).

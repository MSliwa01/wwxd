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

## Known biases

- The gold sets come from the same sources the vault was built from. The bench
  measures whether an agent can recover this person's documented positions. It
  doesn't measure whether those positions are good advice.
- The judge is the same model family as both arms. Self-preference should affect both
  arms equally, but it's not zero.
- Blinding is imperfect. Answers built from a vault tend to quote more and name
  specific videos, and a judge can notice that.
- One run per arm, 20 questions per vault. Treat differences of a few tenths as noise.

Results from our runs are in [RESULTS.md](RESULTS.md).

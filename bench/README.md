# Benchmarks

Measure how faithful vault answers are, and compare layouts and prompt variants.

```bash
# 1. Answer every gold question through an agent (default: claude -p)
wwxd bench run yc --gold bench/gold/yc.yaml

# 2. Score with a judge prompt
wwxd bench judge --gold bench/gold/yc.yaml --answers bench/results/<run>/answers.jsonl
```

Any agent works: `--agent "codex exec {prompt}"`, or a command that reads the
prompt from stdin.

## What's measured

| Score | Question it answers |
|-------|---------------------|
| `stance` | Did the answer reach the person's actual position? |
| `citations` | Did it cite the right sources, and do they support the claims? |
| `abstain` | Did it say "not covered" instead of inventing a view? |
| `attribution` | Was each view credited to the right speaker (not the host)? |

## Experiments to run

- **tree vs. flat**: compile the same sources into two vaults with `layout: tree`
  and `layout: flat`, then run the same gold set on both.
- **Prompt variants**: copy `prompts/answer.md`, change one thing, and run with
  `--prompt`.
- **Skill variants**: install a modified skill and re-run.

## Gold sets

`gold/*.yaml`: hand-written questions with the expected stance and sources.
Include `expect: abstain` questions; refusing to invent positions is the whole
point.

Contribute gold sets for the example vaults. Keep each question tied to a specific
public source.

#!/usr/bin/env bash
cd ~/wwxd-lab
B=/home/mateusz/Desktop/pyprograms/wwxd/bench/prompts
for m in opus sonnet haiku; do
  mid=claude-$m-5-5
  for e in medium high xhigh; do
    for v in hormozi yc; do
      wwxd bench run $v --gold gold/$v-ask12.yaml --arm ask-$m-$e --prompt $B/answer_wwxd.md \
        --agent "claude -p {prompt} --setting-sources project --model $mid --effort $e --strict-mcp-config --allowedTools Read Glob Grep Skill Bash(wwxd:*)" \
        --cwd ~/wwxd-lab --out bench-results --jobs 3 > /dev/null
    done
  done
done
H='claude -p {prompt} --setting-sources project --model claude-haiku-5-5 --effort high --strict-mcp-config --allowedTools Read Grep Glob'
for m in opus sonnet haiku; do for e in medium high xhigh; do for v in hormozi yc; do
  wwxd bench judge $v --gold gold/$v-ask12.yaml --a raw --b ask-$m-$e --name haiku --prompt $B/judge_pairwise.md --agent "$H" --out bench-results --jobs 3 > /dev/null
done; done; done
echo ASK_STUDY_DONE

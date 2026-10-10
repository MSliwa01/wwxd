#!/usr/bin/env bash
cd ~/wwxd-lab
B=/home/mateusz/Desktop/pyprograms/wwxd/bench/prompts
O='claude -p {prompt} --setting-sources project --model claude-opus-5-5 --effort medium --strict-mcp-config --allowedTools Read Grep Glob'
for v in hormozi yc; do
  wwxd bench judge $v --gold gold/$v-ask12.yaml --a ask-opus-high --b prose-opus-high --name opus --prompt $B/judge_pairwise.md --agent "$O" --out bench-results --jobs 2 > /dev/null
  wwxd bench rank $v --gold gold/$v-opinion.yaml --arm op-old-high --arm op-prose --arm op-raw --name opus --seed 5 --prompt $B/judge_opinion.md --agent "$O" --out bench-results --jobs 2 > /dev/null
done
echo DONE

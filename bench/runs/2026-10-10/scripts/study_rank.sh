#!/usr/bin/env bash
# Blind ranking of the nine ask arms, after the opus-xhigh compile rerun has finished.
until grep -q "DONE opus-xhigh rerun" ~/wwxd-lab/study/logs/summary.txt; do sleep 30; done
cd ~/wwxd-lab
P=/home/mateusz/Desktop/pyprograms/wwxd/bench/prompts/judge_rank.md
arms=""; for m in opus sonnet haiku; do for e in medium high xhigh; do arms="$arms --arm ask-$m-$e"; done; done
O='claude -p {prompt} --setting-sources project --model claude-opus-5-5 --effort medium --strict-mcp-config --allowedTools Read Grep Glob'
H='claude -p {prompt} --setting-sources project --model claude-haiku-5-5 --effort high --strict-mcp-config --allowedTools Read Grep Glob'
for v in hormozi yc; do
  wwxd bench rank $v --gold gold/$v-ask12.yaml $arms --prompt $P --agent "$O" --name opus --seed 1 --out bench-results --jobs 2 > /dev/null
  wwxd bench rank $v --gold gold/$v-ask12.yaml $arms --prompt $P --agent "$H" --name haiku --seed 2 --out bench-results --jobs 2 > /dev/null
done
echo RANK_DONE

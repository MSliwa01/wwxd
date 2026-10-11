#!/usr/bin/env bash
until grep -q ANSWERS_DONE ~/wwxd-lab/logs/web_bench.out; do sleep 30; done
cd ~/wwxd-lab
B=/home/mateusz/Desktop/pyprograms/wwxd/bench/prompts
O='claude -p {prompt} --setting-sources project --model claude-opus-5-5 --effort medium --strict-mcp-config --allowedTools Read Grep Glob'
H='claude -p {prompt} --setting-sources project --model claude-haiku-5-5 --effort high --strict-mcp-config --allowedTools Read Grep Glob'
L='/home/mateusz/wwxd-lab-scripts/gemini_judge.sh gemini-3.5-flash-lite {prompt}'
M='opencode run -m opencode/muse-spark-1.3-contributor-free {prompt}'
export GEMINI_ASK="/home/mateusz/Desktop/api_keys/gemini.py ask"
for pass in 1 2; do
for v in hormozi yc; do
  for j in opus haiku lite muse; do
    case $j in opus) A=$O; J=2;; haiku) A=$H; J=2;; lite) A=$L; J=2;; muse) A=$M; J=1;; esac
    wwxd bench judge $v --gold gold/$v.yaml --a web --b prose --name $j --prompt $B/judge_pairwise.md --agent "$A" --out bench-results --jobs $J --timeout 1200 > /dev/null
    wwxd bench rank $v --gold gold/$v-opinion.yaml --arm op-raw --arm op-persona --arm op-web --arm op-prose --name $j --seed 7 --prompt $B/judge_opinion.md --agent "$A" --out bench-results --jobs $J --timeout 1200 > /dev/null
  done
done
done
echo WEB_JUDGES_DONE

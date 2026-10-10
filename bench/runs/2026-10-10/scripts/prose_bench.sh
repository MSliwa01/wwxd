#!/usr/bin/env bash
# New prose-first answer format vs the old structured one, both Opus 5.5 at effort high.
cd ~/wwxd-lab
B=/home/mateusz/Desktop/pyprograms/wwxd/bench/prompts
AG='claude -p {prompt} --setting-sources project --model claude-opus-5-5 --effort high --strict-mcp-config --allowedTools Read Glob Grep Skill Bash(wwxd:*)'
for v in hormozi yc; do
  wwxd bench run $v --gold gold/$v-ask12.yaml --arm prose-opus-high --prompt $B/answer_wwxd.md --agent "$AG" --cwd ~/wwxd-lab --out bench-results --jobs 3 > /dev/null
  wwxd bench run $v --gold gold/$v-opinion.yaml --arm op-prose --prompt $B/answer_wwxd.md --agent "$AG" --cwd ~/wwxd-lab --out bench-results --jobs 3 > /dev/null
  wwxd bench run $v --gold gold/$v-opinion.yaml --arm op-old-high --prompt $B/answer_wwxd.md --agent "$AG" --cwd ~/wwxd-lab-old --out bench-results --jobs 3 > /dev/null
done
O='claude -p {prompt} --setting-sources project --model claude-opus-5-5 --effort medium --strict-mcp-config --allowedTools Read Grep Glob'
L='/home/mateusz/wwxd-lab-scripts/gemini_judge.sh gemini-3.5-flash-lite {prompt}'
for v in hormozi yc; do
  for j in opus lite; do A=$O; [ $j = lite ] && A=$L
    wwxd bench judge $v --gold gold/$v-ask12.yaml --a ask-opus-high --b prose-opus-high --name $j --prompt $B/judge_pairwise.md --agent "$A" --out bench-results --jobs 2 > /dev/null
    wwxd bench rank $v --gold gold/$v-opinion.yaml --arm op-old-high --arm op-prose --arm op-raw --name $j --seed 5 --prompt $B/judge_opinion.md --agent "$A" --out bench-results --jobs 2 > /dev/null
  done
done
echo PROSE_DONE

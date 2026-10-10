#!/usr/bin/env bash
# usage: gemini_judges.sh <model>   No-tool Gemini judge on the study ranking, main bench and opinion bench.
cd ~/wwxd-lab
g=$1
B=/home/mateusz/Desktop/pyprograms/wwxd/bench/prompts
A="/home/mateusz/wwxd-lab-scripts/gemini_judge.sh $g {prompt}"
arms=""; for m in opus sonnet haiku; do for e in medium high xhigh; do arms="$arms --arm ask-$m-$e"; done; done
for pass in 1 2; do
  for v in hormozi yc; do
    wwxd bench rank $v --gold gold/$v-ask12.yaml $arms --prompt $B/judge_rank.md --agent "$A" --name $g --seed 3 --out bench-results --jobs 2 --timeout 900 > /dev/null
    wwxd bench rank $v --gold gold/$v-opinion.yaml --arm op-raw --arm op-persona --arm op-wwxd --name $g --prompt $B/judge_opinion.md --agent "$A" --out bench-results --jobs 2 --timeout 900 > /dev/null
    wwxd bench judge $v --gold gold/$v.yaml --a raw --b wwxd --name $g --prompt $B/judge_pairwise.md --agent "$A" --out bench-results --jobs 2 --timeout 900 > /dev/null
  done
done
echo "GEMINI_DONE $g"

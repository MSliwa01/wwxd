#!/usr/bin/env bash
# Opus 5.5 with web search vs Opus 5.5 with a wwxd vault (new prose format), both at effort high.
cd ~/wwxd-lab
B=/home/mateusz/Desktop/pyprograms/wwxd/bench/prompts
WEB='claude -p {prompt} --setting-sources project --model claude-opus-5-5 --effort high --strict-mcp-config --allowedTools WebSearch WebFetch'
WX='claude -p {prompt} --setting-sources project --model claude-opus-5-5 --effort high --strict-mcp-config --allowedTools Read Glob Grep Skill Bash(wwxd:*)'
for pass in 1 2; do
for v in hormozi yc; do
  wwxd bench run $v --gold gold/$v.yaml --arm web --prompt $B/answer_web.md --agent "$WEB" --cwd /tmp/web-arm-cwd --out bench-results --jobs 3 > /dev/null
  wwxd bench run $v --gold gold/$v-opinion.yaml --arm op-web --prompt $B/answer_web.md --agent "$WEB" --cwd /tmp/web-arm-cwd --out bench-results --jobs 3 > /dev/null
  wwxd bench run $v --gold gold/$v.yaml --arm prose --prompt $B/answer_wwxd.md --agent "$WX" --cwd ~/wwxd-lab --out bench-results --jobs 3 > /dev/null
done
done
echo ANSWERS_DONE

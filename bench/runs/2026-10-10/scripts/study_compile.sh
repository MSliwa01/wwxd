#!/usr/bin/env bash
# usage: study_compile.sh <model-short> <model-id>
cd ~/wwxd-lab/study
export WWXD_HOME=~/wwxd-lab/study/vaults
m=$1; mid=$2
for e in medium high xhigh; do
  for k in yc hz; do
    v=s-$m-$e-$k
    for id in $(wwxd pending $v | cut -f1 | xargs -n1 basename | sed 's/\.md$//'); do
      start=$(date +%s)
      claude -p "Use the wwxd skill. Compile the fetched source $id into the vault at vaults/$v, following the skill's compile workflow (read references/format.md and references/compile.md first). Work autonomously and don't ask me questions. Skip the wwxd estimate and wwxd voice steps. When wwxd lint passes with no errors, run wwxd mark-compiled with a short note." \
        --setting-sources project --model $mid --effort $e --strict-mcp-config --permission-mode acceptEdits \
        --allowedTools "Read" "Write" "Edit" "Glob" "Grep" "Skill" "Bash(wwxd:*)" --output-format json > logs/$v-$id.json 2> logs/$v-$id.err
      echo "$v $id exit=$? seconds=$(( $(date +%s) - start ))" >> logs/summary.txt
    done
  done
done
echo "DONE $m" >> logs/summary.txt

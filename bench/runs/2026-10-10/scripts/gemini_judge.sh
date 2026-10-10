#!/usr/bin/env bash
# usage: gemini_judge.sh <model> <prompt>   One API call, no tools.
m=$1; shift
printf '%s\n\nNote: in this run you have no file tools, so you cannot open ./raw/. Judge quotes and claims against the grading key above and what you know; do not penalize a quote only because you could not look it up.\n' "$1" \
  | ${GEMINI_ASK:?set GEMINI_ASK to a command that sends stdin to Gemini, e.g. gemini.py ask} -m "$m"

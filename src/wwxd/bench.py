"""Agent-agnostic benchmark runner.

The agent command gets the prompt either via a `{prompt}` placeholder or on stdin.
Default: `claude -p {prompt}` run from the vault's parent directory.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import shlex
import subprocess
from pathlib import Path

import yaml

from wwxd.vault import Vault

DEFAULT_AGENT = "claude -p {prompt}"


def run_agent(command: str, prompt: str, cwd: Path, timeout: int = 900) -> str:
    args = shlex.split(command)
    if "{prompt}" in command:
        args = [prompt if a == "{prompt}" else a for a in args]
        stdin = None
    else:
        stdin = prompt
    result = subprocess.run(args, input=stdin, capture_output=True, text=True, cwd=cwd, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(f"agent exited {result.returncode}: {result.stderr[-500:]}")
    return result.stdout.strip()


def _fill(template: str, **values: str) -> str:
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def run(vault: Vault, gold_path: Path, prompt_path: Path, out_dir: Path, agent: str = DEFAULT_AGENT) -> Path:
    gold = yaml.safe_load(gold_path.read_text(encoding="utf-8"))
    template = prompt_path.read_text(encoding="utf-8")
    out_dir.mkdir(parents=True, exist_ok=True)
    answers_path = out_dir / "answers.jsonl"
    meta = {
        "vault": vault.slug,
        "layout": vault.layout,
        "gold": str(gold_path),
        "prompt": str(prompt_path),
        "agent": agent,
        "started": dt.datetime.now().isoformat(timespec="seconds"),
    }
    (out_dir / "run.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    with answers_path.open("w", encoding="utf-8") as fh:
        for item in gold["questions"]:
            prompt = _fill(template, vault=str(vault.path), question=item["question"])
            try:
                answer, error = run_agent(agent, prompt, cwd=vault.path.parent), ""
            except Exception as exc:
                answer, error = "", str(exc)
            fh.write(json.dumps({"id": item["id"], "answer": answer, "error": error}, ensure_ascii=False) + "\n")
            fh.flush()
    return answers_path


def judge(gold_path: Path, answers_path: Path, judge_prompt_path: Path, agent: str = DEFAULT_AGENT) -> Path:
    gold = {q["id"]: q for q in yaml.safe_load(gold_path.read_text(encoding="utf-8"))["questions"]}
    template = judge_prompt_path.read_text(encoding="utf-8")
    scores_path = answers_path.with_name("scores.jsonl")
    totals: dict[str, list[float]] = {}
    with scores_path.open("w", encoding="utf-8") as fh:
        for line in answers_path.read_text(encoding="utf-8").splitlines():
            answer = json.loads(line)
            item = gold[answer["id"]]
            prompt = _fill(
                template,
                question=item["question"],
                expected=yaml.safe_dump({k: v for k, v in item.items() if k not in ("id", "question")}, sort_keys=False),
                answer=answer["answer"] or "(no answer)",
            )
            raw = run_agent(agent, prompt, cwd=answers_path.parent)
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            score = json.loads(match.group(0)) if match else {"error": "judge returned no JSON", "raw": raw}
            score["id"] = answer["id"]
            fh.write(json.dumps(score, ensure_ascii=False) + "\n")
            for key, value in score.items():
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    totals.setdefault(key, []).append(float(value))
    summary = {k: round(sum(v) / len(v), 3) for k, v in totals.items()}
    (answers_path.parent / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return scores_path

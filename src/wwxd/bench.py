"""Agent-agnostic benchmark: run arms, check quotes mechanically, judge pairs blind.

An agent command gets the prompt via a `{prompt}` placeholder or on stdin.
"""

from __future__ import annotations

import datetime as dt
import json
import random
import re
import shlex
import subprocess
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml
from rapidfuzz import fuzz

from wwxd.lint import MATCH_THRESHOLD, RawIndex, normalize
from wwxd.vault import Vault

DEFAULT_AGENT = "claude -p {prompt}"
QUOTE_MARKS = re.compile(r'["“”]')
# A quote counts as attributed when the text just before it hands the floor to someone.
ATTRIBUTION_CUE = re.compile(
    r"(said|says|say|put it|puts it|told|tells|telling|calls it|called it|in (his|her|their) words|line|quote|"
    r"words|wrote|writes|argues|argued|admits|admitted|asks|asked)\W{0,3}$|[:—–]\s*\**\s*$",
    re.IGNORECASE,
)


def attributed_quotes(answer: str) -> list[str]:
    """Quoted spans presented as someone's words. Pairs quote marks within a line."""
    quotes = []
    for line in answer.splitlines():
        marks = [m.start() for m in QUOTE_MARKS.finditer(line)]
        for open_at, close_at in zip(marks[::2], marks[1::2]):
            span = line[open_at + 1 : close_at].strip()
            if len(span.split()) < 5 or "](" in span or "**" in span or "http" in span:
                continue
            if ATTRIBUTION_CUE.search(line[max(0, open_at - 60) : open_at]):
                quotes.append(span)
    return quotes
CITATION_MARKUP = re.compile(r"\s*\(\s*\[\[[^\]]+\]\][^()]*\)|\[\[([^\]|]+)(?:\|[^\]]*)?\]\]")


def run_agent(command: str, prompt: str, cwd: Path, timeout: int = 1200) -> str:
    args = shlex.split(command)
    if "{prompt}" in command:
        args = [prompt if a == "{prompt}" else a for a in args]
        # Some agent CLIs (opencode) wait on an open stdin forever, so close it.
        stdin_kwargs: dict = {"stdin": subprocess.DEVNULL}
    else:
        stdin_kwargs = {"input": prompt}
    result = subprocess.run(args, capture_output=True, text=True, cwd=cwd, timeout=timeout, **stdin_kwargs)
    if result.returncode != 0:
        raise RuntimeError(f"agent exited {result.returncode}: {(result.stderr or result.stdout)[-500:]}")
    return result.stdout.strip()


def _fill(template: str, **values: str) -> str:
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def load_gold(path: Path) -> list[dict]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))["questions"]


def _read_jsonl(path: Path) -> dict[str, dict]:
    return {row["id"]: row for row in map(json.loads, path.read_text(encoding="utf-8").splitlines())}


def run_arm(
    vault: Vault, gold_path: Path, prompt_path: Path, out_dir: Path, *, agent: str, cwd: Path, jobs: int = 4
) -> Path:
    """Ask every gold question through one arm. Resumable: answered ids are skipped."""
    out_dir.mkdir(parents=True, exist_ok=True)
    answers_path = out_dir / "answers.jsonl"
    done = _read_jsonl(answers_path) if answers_path.exists() else {}
    template = prompt_path.read_text(encoding="utf-8")
    (out_dir / "arm.json").write_text(
        json.dumps({"agent": agent, "prompt": str(prompt_path), "cwd": str(cwd), "vault": str(vault.path),
                    "started": dt.datetime.now().isoformat(timespec="seconds")}, indent=2),
        encoding="utf-8",
    )
    todo = [q for q in load_gold(gold_path) if q["id"] not in done or done[q["id"]].get("error")]

    def answer(item: dict) -> dict:
        prompt = _fill(template, vault=str(vault.path), slug=vault.slug, question=item["question"])
        started = dt.datetime.now()
        try:
            text, error = run_agent(agent, prompt, cwd=cwd), ""
        except Exception as exc:
            text, error = "", str(exc)
        seconds = (dt.datetime.now() - started).total_seconds()
        return {"id": item["id"], "answer": text, "error": error, "seconds": round(seconds, 1)}

    with ThreadPoolExecutor(max_workers=jobs) as pool:
        for row in pool.map(answer, todo):
            done[row["id"]] = row
            answers_path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in done.values()), encoding="utf-8")
    return answers_path


def verify_quotes(vault: Vault, answer: str) -> dict:
    """Check every quoted span in an answer against all raw docs in the vault."""
    raw = RawIndex(vault)
    ids = [p.stem for p in vault.raw_dir.glob("*.md")]
    corpus = {i: raw.get(i)[1] for i in ids}
    quotes = attributed_quotes(answer)
    found = []
    for quote in quotes:
        parts = [normalize(p) for p in re.split(r"\.\.\.|…", quote) if normalize(p)]
        ok = all(any(p in text or fuzz.partial_ratio(p, text) >= MATCH_THRESHOLD for text in corpus.values()) for p in parts)
        found.append(ok)
    return {"quotes": len(quotes), "verified": sum(found), "unverified": [q for q, ok in zip(quotes, found) if not ok]}


def strip_citations(answer: str) -> str:
    """Remove citation markup, links and timestamps so the judge can't tell which arm used the vault."""
    text = CITATION_MARKUP.sub(lambda m: m.group(1) or "", answer)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # markdown links keep their text
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\b(yt|web|pod|file)-[\w-]+\b", "", text)
    text = re.sub(r"@\s*\d+(:\d{2}){1,2}", "", text)
    text = re.sub(r"(?i)\b(the )?(wwxd )?vault\b", "my sources", text)
    text = re.sub(r"\(\s*[,;]?\s*\)", "", text)  # parentheses emptied by the steps above
    return re.sub(r"[ \t]+\n", "\n", text)


def judge_pairs(
    vault: Vault, gold_path: Path, arm_a: Path, arm_b: Path, prompt_path: Path, out_path: Path,
    *, agent: str, cwd: Path, jobs: int = 4, seed: int = 0,
) -> Path:
    """Blind pairwise judging. Answer order is shuffled per question; the judge sees no citations."""
    gold = {q["id"]: q for q in load_gold(gold_path)}
    answers = {arm_a.name: _read_jsonl(arm_a / "answers.jsonl"), arm_b.name: _read_jsonl(arm_b / "answers.jsonl")}
    template = prompt_path.read_text(encoding="utf-8")
    rng = random.Random(seed)
    tasks = []
    for qid, item in gold.items():
        order = [arm_a.name, arm_b.name]
        rng.shuffle(order)
        tasks.append((qid, item, order))
    done = _read_jsonl(out_path) if out_path.exists() else {}

    def judge(task) -> dict:
        qid, item, order = task
        texts = [strip_citations(answers[arm][qid]["answer"]) or "(no answer)" for arm in order]
        expected = {k: item.get(k) for k in ("category", "person", "stance", "generic_trap", "evidence")}
        prompt = _fill(template, question=item["question"], expected=yaml.safe_dump(expected, sort_keys=False, allow_unicode=True),
                       answer_a=texts[0], answer_b=texts[1], vault=str(vault.path))
        try:
            raw = run_agent(agent, prompt, cwd=cwd)
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            verdict = json.loads(match.group(0)) if match else {"error": "no JSON", "raw": raw[-500:]}
        except Exception as exc:
            verdict = {"error": str(exc)}
        # Map A/B back to arm names.
        mapping = {"A": order[0], "B": order[1]}
        scores = {mapping[k]: verdict.get(k) for k in ("A", "B") if isinstance(verdict.get(k), dict)}
        preferred = mapping.get(verdict.get("preferred", ""), "tie" if verdict.get("preferred") == "tie" else None)
        return {"id": qid, "category": item.get("category"), "order": order, "scores": scores,
                "preferred": preferred, "notes": verdict.get("notes", ""), "error": verdict.get("error", "")}

    todo = [t for t in tasks if t[0] not in done or done[t[0]].get("error")]
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        for row in pool.map(judge, todo):
            done[row["id"]] = row
            out_path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in done.values()), encoding="utf-8")
    return out_path


def summarize(vault: Vault, gold_path: Path, arms: list[Path], judgments: Path | None) -> dict:
    gold = {q["id"]: q for q in load_gold(gold_path)}
    summary: dict = {"vault": vault.slug, "questions": len(gold), "arms": {}}
    for arm in arms:
        rows = _read_jsonl(arm / "answers.jsonl")
        q_total = q_ok = 0
        unverified = []
        for qid, row in rows.items():
            check = verify_quotes(vault, row["answer"])
            q_total += check["quotes"]
            q_ok += check["verified"]
            unverified += [{"id": qid, "quote": q} for q in check["unverified"]]
        summary["arms"][arm.name] = {
            "quotes": q_total,
            "quotes_verified": q_ok,
            "quote_precision": round(q_ok / q_total, 3) if q_total else None,
            "median_seconds": sorted(r["seconds"] for r in rows.values())[len(rows) // 2] if rows else None,
            "unverified_examples": unverified[:10],
        }
    if judgments and judgments.exists():
        rows = list(_read_jsonl(judgments).values())
        by_cat: dict = defaultdict(lambda: defaultdict(list))
        prefs: dict = defaultdict(lambda: defaultdict(int))
        for row in rows:
            for arm, scores in row["scores"].items():
                for metric, value in (scores or {}).items():
                    if isinstance(value, bool):
                        value = float(value)
                    if isinstance(value, (int, float)):
                        by_cat["all"][f"{arm}.{metric}"].append(value)
                        by_cat[row["category"]][f"{arm}.{metric}"].append(value)
            prefs["all"][row["preferred"] or "none"] += 1
            prefs[row["category"]][row["preferred"] or "none"] += 1
        summary["judge"] = {
            cat: {k: round(sum(v) / len(v), 2) for k, v in sorted(metrics.items())} for cat, metrics in by_cat.items()
        }
        summary["preferred"] = {cat: dict(v) for cat, v in prefs.items()}
    return summary


# --- opinion bench: how decisive and distinctive are the answers? ---------------------

HEDGES = (
    "it depends", "depending on", "on the other hand", "however", "that said", "pros and cons",
    "no one-size", "no right answer", "trade-off", "tradeoff", "either way", "both options",
    "it's up to you", "there's a case for", "consider ", "you might", "you could", "may want",
)


def opinion_stats(answer: str) -> dict:
    """Mechanical signals of fence-sitting. No model involved."""
    text = strip_citations(answer).lower()
    words = len(text.split())
    hedges = sum(text.count(h) for h in HEDGES)
    return {"words": words, "hedges": hedges, "hedges_per_100_words": round(100 * hedges / max(words, 1), 2)}


def judge_ranked(
    vault: Vault, gold_path: Path, arm_dirs: list[Path], prompt_path: Path, out_path: Path,
    *, agent: str, cwd: Path, jobs: int = 3, seed: int = 0,
) -> Path:
    """Show the judge every arm's answer to a question at once, shuffled and blind; it scores each and ranks them."""
    gold = {q["id"]: q for q in load_gold(gold_path)}
    answers = {d.name: _read_jsonl(d / "answers.jsonl") for d in arm_dirs}
    template = prompt_path.read_text(encoding="utf-8")
    rng = random.Random(seed)
    letters = "ABCDEFGH"
    tasks = []
    for qid, item in gold.items():
        order = [d.name for d in arm_dirs]
        rng.shuffle(order)
        tasks.append((qid, item, order))
    done = _read_jsonl(out_path) if out_path.exists() else {}

    def judge(task) -> dict:
        qid, item, order = task
        block = "\n\n".join(
            f"Answer {letters[i]}:\n<<<\n{strip_citations(answers[arm][qid]['answer']) or '(no answer)'}\n>>>"
            for i, arm in enumerate(order)
        )
        prompt = _fill(template, question=item["question"], person=str(item.get("person", "")), answers=block)
        try:
            raw = run_agent(agent, prompt, cwd=cwd)
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            verdict = json.loads(match.group(0)) if match else {"error": "no JSON", "raw": raw[-500:]}
        except Exception as exc:
            verdict = {"error": str(exc)}
        mapping = {letters[i]: arm for i, arm in enumerate(order)}
        scores = {mapping[k]: v for k, v in verdict.items() if k in mapping and isinstance(v, dict)}
        ranking = [mapping[k] for k in verdict.get("ranking", []) if k in mapping]
        return {"id": qid, "order": order, "scores": scores, "ranking": ranking,
                "notes": verdict.get("notes", ""), "error": verdict.get("error", "")}

    todo = [t for t in tasks if t[0] not in done or done[t[0]].get("error")]
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        for row in pool.map(judge, todo):
            done[row["id"]] = row
            out_path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in done.values()), encoding="utf-8")
    return out_path


def summarize_ranked(arm_dirs: list[Path], judgments: Path) -> dict:
    rows = [r for r in _read_jsonl(judgments).values() if not r.get("error")]
    out: dict = {"questions": len(rows), "arms": {}}
    for d in arm_dirs:
        arm = d.name
        answers = _read_jsonl(d / "answers.jsonl")
        stats = [opinion_stats(a["answer"]) for a in answers.values() if a["answer"]]
        metrics: dict[str, list[float]] = defaultdict(list)
        consistent = {"yes": 0, "no": 0, "unknown": 0}
        for r in rows:
            for k, v in (r["scores"].get(arm) or {}).items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    metrics[k].append(float(v))
            c = str((r["scores"].get(arm) or {}).get("consistent_with_person", "unknown")).lower()
            consistent[c if c in consistent else "unknown"] += 1
        out["arms"][arm] = {
            **{k: round(sum(v) / len(v), 2) for k, v in sorted(metrics.items())},
            "ranked_first": sum(1 for r in rows if r["ranking"][:1] == [arm]),
            "consistent_with_person": consistent,
            "median_words": sorted(s["words"] for s in stats)[len(stats) // 2] if stats else None,
            "hedges_per_100_words": round(sum(s["hedges_per_100_words"] for s in stats) / len(stats), 2) if stats else None,
        }
    return out

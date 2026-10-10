"""Summarize the ask study: Haiku judge scores per model x effort, vs raw, plus answer length and time."""
import json, statistics as st
from pathlib import Path
R = Path.home() / "wwxd-lab/bench-results"
DIMS = ("accuracy", "specificity", "faithfulness", "usefulness")
print(f"{'arm':20} {'n':>3} {'won':>5} " + " ".join(f"{d[:5]:>6}" for d in DIMS) + f" {'raw_acc':>7} {'words':>6} {'sec':>5} {'err':>3}")
rows = []
for m in ("opus", "sonnet", "haiku"):
    for e in ("medium", "high", "xhigh"):
        arm = f"ask-{m}-{e}"; sc = {d: [] for d in DIMS}; raw_acc = []; won = n = 0; words = []; secs = []; err = 0
        for v in ("hormozi", "yc"):
            for ln in open(R / v / f"judge-raw-vs-{arm}-haiku.jsonl"):
                j = json.loads(ln)
                if j.get("error"): err += 1; continue
                n += 1; won += j["preferred"] == arm
                for d in DIMS: sc[d].append(j["scores"][arm][d])
                raw_acc.append(j["scores"]["raw"]["accuracy"])
            for ln in open(R / v / arm / "answers.jsonl"):
                a = json.loads(ln); words.append(len(a.get("answer", "").split()))
                if a.get("seconds"): secs.append(a["seconds"])
                if a.get("error"): err += 1
        r = dict(arm=arm, n=n, won=won, **{d: round(st.mean(sc[d]), 2) for d in DIMS}, raw_acc=round(st.mean(raw_acc), 2),
                 words=int(st.median(words)), sec=int(st.median(secs)) if secs else None, err=err)
        rows.append(r)
        print(f"{arm:20} {n:>3} {won:>2}/{n:<2} " + " ".join(f"{r[d]:>6}" for d in DIMS) + f" {r['raw_acc']:>7} {r['words']:>6} {str(r['sec']):>5} {err:>3}")
json.dump(rows, open(Path.home() / "wwxd-lab/study/study_ask.json", "w"), indent=1)

"""Score every study vault: attribution vs the official transcript, gold-evidence recall, lint, size, cost."""
import json, re, statistics as st, subprocess, os
from pathlib import Path
import trafilatura, yaml
from rapidfuzz import fuzz
from wwxd.lint import STATEMENT, parse_citation, normalize, lint
from wwxd.vault import Vault

ROOT = Path.home() / "wwxd-lab/study"
html = open("/tmp/ycroot/page.html").read()
body = trafilatura.extract(html); body = body[body.index("Transcript"):]
turns = [(m.group(1), normalize(m.group(2))) for m in re.finditer(r"(?:^|\n)(Garry|Sam):\s*(.*)", body)]
WHO = {"Garry": "tan", "Sam": "altman"}
gold = {"yc": yaml.safe_load(open(Path.home() / "wwxd-lab/gold/yc.yaml"))["questions"],
        "hz": yaml.safe_load(open(Path.home() / "wwxd-lab/gold/hormozi.yaml"))["questions"]}
SETS = {"yc": {"yt-ZIaOBAjvc38", "yt-Jcuqq48CNj8", "web-39f89fad2603"}, "hz": {"yt-MH-IMJxbUY4"}}

def statements(v):
    out = []
    for page in (v.path / "wiki").rglob("*.md"):
        for ln in page.read_text().splitlines():
            m = STATEMENT.match(ln.strip()) if ln.strip().startswith('- "') else None
            c = parse_citation(m.group("cite")) if m else None
            if c: out.append((m.group("quote"), c))
    return out

rows = []
for model in ("opus", "sonnet", "haiku"):
    for effort in ("medium", "high", "xhigh"):
        r = {"model": model, "effort": effort, "statements": 0, "lint_errors": 0, "cost": 0.0, "seconds": 0, "sessions": 0, "failed": 0}
        ev_hit = ev_all = 0
        for k in ("yc", "hz"):
            v = Vault(ROOT / "vaults" / f"s-{model}-{effort}-{k}")
            sts = statements(v); r["statements"] += len(sts)
            r["lint_errors"] += sum(1 for i in lint(v) if i.level == "error")
            for f in (ROOT / "logs").glob(f"s-{model}-{effort}-{k}-*.json"):
                try:
                    d = json.loads(f.read_text()); r["cost"] += d.get("total_cost_usd") or 0; r["seconds"] += d.get("duration_ms", 0) / 1000
                    r["sessions"] += 1; r["failed"] += bool(d.get("is_error"))
                except Exception:
                    r["failed"] += 1
            quotes = [normalize(q) for q, c in sts]
            for q in gold[k]:
                for e in q.get("evidence") or []:
                    if e["source"] not in SETS[k]: continue
                    ev_all += 1
                    t = normalize(e["quote"])
                    ev_hit += any(fuzz.partial_ratio(t, x) >= 85 or fuzz.partial_ratio(x, t) >= 90 for x in quotes if x)
            if k == "yc":
                ok = n = 0
                for q, c in sts:
                    if c["src"] != "yt-ZIaOBAjvc38": continue
                    nq = normalize(re.split(r"\.\.\.|…", q)[0])
                    best = max(turns, key=lambda t: fuzz.partial_ratio(nq, t[1]))
                    if fuzz.partial_ratio(nq, best[1]) < 80: continue
                    n += 1; ok += c.get("by") == WHO[best[0]]
                r["attr"] = f"{ok}/{n}"; r["attr_pct"] = round(100 * ok / n, 1) if n else None
        r["evidence_recall"] = f"{ev_hit}/{ev_all}"
        r["cost"] = round(r["cost"], 2); r["minutes"] = round(r["seconds"] / 60, 1)
        rows.append(r)
print(f"{'model':7} {'effort':7} {'sess':>4} {'fail':>4} {'stmts':>5} {'attr (official)':>16} {'evid':>6} {'lintE':>5} {'cost$':>6} {'min':>5}")
for r in rows:
    print(f"{r['model']:7} {r['effort']:7} {r['sessions']:>4} {r['failed']:>4} {r['statements']:>5} {str(r.get('attr'))+' '+str(r.get('attr_pct'))+'%':>16} {r['evidence_recall']:>6} {r['lint_errors']:>5} {r['cost']:>6} {r['minutes']:>5}")
json.dump(rows, open(ROOT / "study_compile.json", "w"), indent=1)

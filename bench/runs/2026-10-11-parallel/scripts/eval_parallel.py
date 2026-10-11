"""Score parallel-compile vaults like study_eval.py scores the sequential ones."""
import json, re, sys
from pathlib import Path
import trafilatura, yaml
from rapidfuzz import fuzz
from wwxd.lint import STATEMENT, parse_citation, normalize, lint
from wwxd.vault import Vault

html = open("/tmp/ycroot/page.html").read()
body = trafilatura.extract(html); body = body[body.index("Transcript"):]
turns = [(m.group(1), normalize(m.group(2))) for m in re.finditer(r"(?:^|\n)(Garry|Sam):\s*(.*)", body)]
WHO = {"Garry": "tan", "Sam": "altman"}
G = Path.home() / "wwxd-lab/gold"
gold = {"yc": yaml.safe_load(open(G / "yc.yaml"))["questions"], "hz": yaml.safe_load(open(G / "hormozi.yaml"))["questions"]}
SETS = {"yc": {"yt-ZIaOBAjvc38", "yt-Jcuqq48CNj8", "web-39f89fad2603"}, "hz": {"yt-MH-IMJxbUY4"}}

def statements(v):
    out = []
    for page in (v.path / "wiki").rglob("*.md"):
        for ln in page.read_text().splitlines():
            m = STATEMENT.match(ln.strip()) if ln.strip().startswith('- "') else None
            c = parse_citation(m.group("cite")) if m else None
            if c: out.append((m.group("quote"), c))
    return out

prefix = sys.argv[1]  # e.g. vaults/p-sonnet-high
r = {"statements": 0, "lint_errors": 0, "cost": 0.0}
hit = tot = 0
for k in ("yc", "hz"):
    v = Vault(Path(f"{prefix}-{k}"))
    sts = statements(v); r["statements"] += len(sts)
    r["lint_errors"] += sum(1 for i in lint(v) if i.level == "error")
    for f in (v.cache_dir / "compile-logs").glob("*.json"):
        try: r["cost"] += json.loads(f.read_text()).get("total_cost_usd") or 0
        except Exception: pass
    quotes = [normalize(q) for q, c in sts]
    for q in gold[k]:
        for e in q.get("evidence") or []:
            if e["source"] not in SETS[k]: continue
            tot += 1; t = normalize(e["quote"])
            hit += any(fuzz.partial_ratio(t, x) >= 85 or fuzz.partial_ratio(x, t) >= 90 for x in quotes if x)
    if k == "yc":
        ok = n = 0
        for q, c in sts:
            if c["src"] != "yt-ZIaOBAjvc38": continue
            nq = normalize(re.split(r"\.\.\.|…", q)[0])
            best = max(turns, key=lambda t: fuzz.partial_ratio(nq, t[1]))
            if fuzz.partial_ratio(nq, best[1]) < 80: continue
            n += 1; ok += c.get("by") == WHO[best[0]]
        r["attr"] = f"{ok}/{n}"
r["evidence"] = f"{hit}/{tot}"; r["cost"] = round(r["cost"], 2)
print(json.dumps(r))

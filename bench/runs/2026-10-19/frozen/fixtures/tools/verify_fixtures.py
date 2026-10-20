"""Check the wwxd-eval-v2 fixtures against the raw vault sources.

Run with: python3 -I tools/verify_fixtures.py <fixtures-dir>

Checks:
- every evidence quote appears verbatim (whitespace collapsed) in its raw
  file, inside the transcript segment named by `timestamp` (or anywhere in
  the body for web articles, where timestamp is null);
- every recorded source_sha256 matches the raw file on disk;
- diagnostic questions and references cover the same ids, vaults and text;
- advice questions use the expected ids and carry no expert names.
"""

import hashlib
import json
import re
import sys
from pathlib import Path

SEGMENT = re.compile(r"^\[(\d+(?::\d+){1,2})\]\s?(.*)$")
EXPERT_NAMES = [
    "hormozi", "alex", "paul graham", "graham", "pg ", "seibel", "michael",
    "dalton", "caldwell", "altman", "garry", "tan ", "livingston", "jessica",
    "y combinator", "yc ", "acquisition.com", "skool",
]


def collapse(text):
    return " ".join(text.split())


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def body(path):
    text = path.read_text(encoding="utf-8")
    parts = text.split("\n---\n", 1)
    return parts[1] if len(parts) == 2 else text


def segments(path):
    out = {}
    for line in body(path).splitlines():
        m = SEGMENT.match(line)
        if m:
            out.setdefault(m.group(1), []).append(m.group(2))
    return {k: collapse(" ".join(v)) for k, v in out.items()}


def check_evidence(ev, where, errors):
    path = Path(ev["source_path"])
    if not path.exists():
        errors.append(f"{where}: missing file {path}")
        return
    if sha256(path) != ev["source_sha256"]:
        errors.append(f"{where}: sha256 mismatch for {path.name}")
    quote = collapse(ev["quote"])
    ts = ev.get("timestamp")
    if ts:
        seg = segments(path).get(ts)
        if seg is None:
            errors.append(f"{where}: no segment [{ts}] in {path.name}")
        elif quote not in seg:
            errors.append(f"{where}: quote not in [{ts}] of {path.name}: {quote[:70]}")
    elif quote not in collapse(body(path)):
        errors.append(f"{where}: quote not in {path.name}: {quote[:70]}")


def main(fixtures):
    fx = Path(fixtures)
    errors = []
    n_quotes = 0

    dq = json.loads((fx / "diagnostic-questions.json").read_text())
    dr = json.loads((fx / "diagnostic-reference.json").read_text())
    refs = {r["id"]: r for r in dr["items"]}
    for q in dq:
        if set(q) != {"id", "vault", "question", "category"}:
            errors.append(f"{q['id']}: diagnostic question has extra or missing fields")
        r = refs.get(q["id"])
        if r is None:
            errors.append(f"{q['id']}: no reference entry")
            continue
        for field in ("vault", "question", "category"):
            if r[field] != q[field]:
                errors.append(f"{q['id']}: {field} differs between questions and reference")
        for i, ev in enumerate(r["evidence"]):
            check_evidence(ev, f"{q['id']} evidence[{i}]", errors)
            n_quotes += 1
    if len(dq) != 12 or len(refs) != 12:
        errors.append("diagnostic set is not 12 items")

    aq = json.loads((fx / "advice-questions.json").read_text())
    ae = json.loads((fx / "advice-evidence.json").read_text())
    expected = [f"advice-hz-{i:02d}" for i in range(1, 7)] + [f"advice-yc-{i:02d}" for i in range(1, 7)]
    if [q["id"] for q in aq] != expected:
        errors.append("advice question ids are not advice-hz-01..06, advice-yc-01..06")
    ev_by_id = {c["id"]: c for c in ae["cases"]}
    for q in aq:
        low = " " + q["question"].lower() + " "
        for name in EXPERT_NAMES:
            if name in low:
                errors.append(f"{q['id']}: question text mentions '{name.strip()}'")
        if '"' in q["question"]:
            errors.append(f"{q['id']}: question text contains a quotation")
        c = ev_by_id.get(q["id"])
        if c is None:
            errors.append(f"{q['id']}: no advice-evidence entry")
            continue
        if c["vault"] != q["vault"]:
            errors.append(f"{q['id']}: vault differs between files")
        for i, ev in enumerate(c["source_support"]):
            check_evidence(ev, f"{q['id']} source_support[{i}]", errors)
            n_quotes += 1

    print(f"checked {n_quotes} quotes, {len(dq)} diagnostic and {len(aq)} advice items")
    for e in errors:
        print("ERROR", e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))

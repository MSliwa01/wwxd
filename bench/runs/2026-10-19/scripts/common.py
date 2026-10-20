"""Shared experiment definitions. No provider code executes on import."""
from __future__ import annotations
import collections
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import tempfile
import threading

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT.parent
VAULTS = Path('/home/mateusz/wwxd-lab/vaults')
HELPER = Path('/home/mateusz/Desktop/api_keys/gemini.py')
DATE = '2026-10-19'
MODELS = {'sol': 'gpt-6.1-sol', 'opus': 'claude-opus-5-5', 'gemini': 'gemini-3.5-flash-lite'}
# Pilot metadata estimates, frozen before calls. These do not prove attention.
CHARS_PER_TOKEN = {'sol': 3.57, 'opus': 2.44, 'gemini': 3.2}
CONCURRENCY = {'sol': 3, 'opus': 3, 'gemini': 1}
CONTEXT_DELTA_MIN = 0.5
CONTEXT_DELTA_MAX = 2.0
EFFORT = {'sol': 'high', 'opus': 'high', 'gemini': 'provider defaults; no effort or generation override'}
SUITES = ('diagnostic12', 'newadvice12')
ARMS = ('raw', 'grounded')
SEEDS = {'sol': 2026101901, 'opus': 2026101902, 'gemini': 2026101903}
DIMS = {'diagnostic12': ['accuracy', 'specificity', 'faithfulness', 'usefulness'],
        'newadvice12': ['decision_quality', 'actionability', 'constraint_fit', 'reasoning']}
LOCK = threading.RLock()
ANSWER_BASE = '''Evaluation date: 2026-10-19. Treat this as the current date, not a future date.
Use no tools, commands, files, browsing, or external retrieval. Use your own knowledge and reasoning, together with any supplied context, to answer the question. The absence of an exact case from supplied context is not a reason to abstain. If material inputs are missing, give a useful conditional recommendation and state the criteria that would change it.
Write approximately 250 words. Give a direct, useful answer, concrete next steps where relevant, material assumptions, and decision criteria. Do not include quotations, citations, links, source references, expert-name appeals, or mentions of sources, a wiki, or a knowledge base. Return only the answer.
'''
ANSWER_EXTRA = {
 'diagnostic12': 'Answer the factual question directly and correct a false premise where necessary. You may name a person already named in the question to explain their position, but do not quote them or invoke their authority. Distinguish what you know from what is uncertain.\n',
 'newadvice12': 'Recommend a defensible course of action that fits the stated goal and constraints. Do not name experts. Multiple solutions can be valid; explain why yours fits this decision.\n'}
CONTEXT_PREFIX = '\nSupplied context:\n'
CONTEXT_TRAILER = '\nEnd of supplied context. Answer the question above under the instructions above.\n'
JUDGE_BASE = '''Evaluation date: 2026-10-19. This is the current date, not a future date. May 2026 is in the past. Publication dates and dates of events described in a source are distinct. A model training cutoff does not invalidate supplied later material. You are an independent evaluator. Use no tools, commands, files, browsing, or external retrieval. A and B are anonymous. Their ordering conveys nothing. Do not infer their model, source access, or provenance. Do not reward writing style, citation presence, quotations, expert agreement, or presumed source use. A tie is valid.
Score each answer on the four specified integer scales, each from 1 to 5. Anchors: 1 fundamentally deficient; 2 major problems; 3 mixed with meaningful gaps; 4 good with minor gaps; 5 strong and sufficiently complete. Choose A, B, or tie for substantive overall quality. Preserve uncertainty rather than inventing evidence.
Return ONLY a JSON object with exactly one key, "judgments", containing one object per supplied pair. Each object has exactly: "id", "A", "B", "winner", "reason", "factual_objections". A and B each contain exactly the four dimension names and integer scores. winner is "A", "B", or "tie"; reason is a nonempty string. factual_objections is a list, possibly empty, of objects with exactly "answer" ("A" or "B"), "claim", "label" ("contradicted" or "unverified"), and "evidence" (a nonempty explanation). Distinguish an established contradiction from an unverified claim.
'''
JUDGE_EXTRA = {
 'newadvice12': '''You see only the question and the two answers. Evaluate decision_quality (a defensible recommendation), actionability (concrete steps and decision criteria), constraint_fit (stated goals, resources and material assumptions), and reasoning (coherent logic and arithmetic). Reward useful, defensible decisions under the scenario's goals and constraints, not agreement with a named expert. Check arithmetic and explicit constraints directly. Missing unstated inputs permit conditional recommendations. A checkable claim you cannot establish as false is unverified, not contradicted. These are judgments of advice quality, not measured business outcomes.\n''',
 'diagnostic12': '''Evaluate accuracy, specificity, faithfulness, and usefulness using the complete audited reference packet. The reference is evidence, not a required script. Missing optional detail is not automatically a false claim. Label a factual objection contradicted only when supplied evidence establishes the contradiction; otherwise label it unverified. Do not treat absence from the reference as proof of falsehood. Resolve a conflict between a summary and direct evidence in favor of the direct evidence and explain it.\n'''}
AGGREGATION = {
 'primary': 'Exclude same-family judge; preserve all original scores and winner labels.',
 'unit': 'One question within each suite and answer family; repeated judges and answer families do not create independent questions.',
 'consensus': 'Two external votes agree -> that label; two different labels -> disagreement; fewer than two valid votes -> missing.',
 'reports': 'Separate suites, answer/judge matrix, both-arm dimension means, all and external votes, same-family votes, question consensus, disagreements and missing counts.',
 'reviews': 'Export blinded practical factual review for every answer; diagnostic raw wins, ties, disagreements; every factual objection. Review never rewrites primary votes.'}

def sha(data):
    return hashlib.sha256(data.encode('utf-8') if isinstance(data, str) else data).hexdigest()

def digest(path):
    return sha(Path(path).read_bytes())

def encoded(obj):
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')

def read(path):
    return json.loads(Path(path).read_bytes())

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def write(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with LOCK:
        tmp = path.with_name(path.name + '.tmp')
        tmp.write_bytes(encoded(obj))
        tmp.replace(path)

def immutable(path, data):
    path = Path(path)
    data = data.encode('utf-8') if isinstance(data, str) else data
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError(f'Frozen artifact changed: {path}')
    else:
        # Publish a complete file atomically and never overwrite a concurrent result.
        fd,temporary=tempfile.mkstemp(prefix='.'+path.name+'.',suffix='.tmp',dir=path.parent)
        temporary=Path(temporary)
        try:
            with os.fdopen(fd,'wb') as out:
                out.write(data)
                out.flush()
                os.fsync(out.fileno())
            temporary.chmod(0o444)
            try:
                os.link(temporary,path)
            except FileExistsError:
                if path.read_bytes()!=data:
                    raise ValueError(f'Concurrent frozen artifact differs: {path}')
        finally:
            temporary.unlink()
    return sha(data)

def safe_id(value, max_length=90):
    if not isinstance(value, str) or len(value)>max_length or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]*', value):
        raise ValueError(f'Unsafe identifier: {value!r}')
    return value

def qkey(q):
    return f"{q['suite']}--{q['id']}"

def answer_id(q, family, arm):
    return f'{qkey(q)}--{family}--{arm}'

def pair_id(q, family):
    # Only this opaque identifier enters judge prompts; identities stay in the private map.
    return 'p-' + sha(qkey(q)+'|'+family)[:16]

def answer_prompt(q):
    return ANSWER_BASE + ANSWER_EXTRA[q['suite']] + '\nQuestion:\n' + q['question'] + '\n'

def estimate_tokens(text, family):
    return math.ceil(len(text) / CHARS_PER_TOKEN[family])

def pair_context_usage(raw, grounded, expected):
    counts = [r.get('actual_input_tokens') for r in (raw, grounded)]
    valid = all(type(n) is int and n > 0 for n in counts)
    delta = counts[1] - counts[0] if valid else None
    flags = []
    if any(r['status'] != 'ok' for r in (raw, grounded)):
        flags.append('answer_incomplete')
    if not valid:
        flags.append('context_usage_missing')
    elif not CONTEXT_DELTA_MIN * expected <= delta <= CONTEXT_DELTA_MAX * expected:
        flags.append('context_usage_inconsistent')
    return {'raw_input_tokens': counts[0], 'grounded_input_tokens': counts[1],
            'input_token_delta': delta, 'expected_context_token_delta': expected,
            'minimum_delta': CONTEXT_DELTA_MIN * expected, 'maximum_delta': CONTEXT_DELTA_MAX * expected,
            'flags': flags, 'eligible': not flags}

def output_deviations(text, status):
    deviations = []
    if len(text.split()) > 300 or (status == 'ok' and len(text.split()) < 150):
        deviations.append('outside descriptive 150..300 word band around approximate 250-word instruction')
    if any(x in text for x in ('http://', 'https://', '```')):
        deviations.append('possible reference/link or fenced-format deviation; manual review required')
    if '[[' in text:
        deviations.append('possible blinding leak: wiki link marker')
    if re.search(r'\b(?:yt|web)-[A-Za-z0-9_-]+', text):
        deviations.append('possible blinding leak: source ID')
    if re.search(r'\b(?:context|wiki|knowledge\s+base)\b', text, re.I):
        deviations.append('possible blinding leak: context/wiki/knowledge base mention')
    return deviations

def mappings(questions):
    result = []
    used = {}
    for suite in SUITES:
        qs = sorted((q for q in questions if q['suite'] == suite), key=lambda q: q['id'])
        if len(qs) != 12:
            raise ValueError(f'{suite}: expected 12 questions')
        for family in MODELS:
            seen = set()
            for judge in MODELS:
                seed = f'{SEEDS[judge]}:{suite}:{family}'
                rng = random.Random(seed)
                # Rejection is deterministic and concerns only randomisation, never content.
                while True:
                    bits = [0]*6 + [1]*6
                    rng.shuffle(bits)
                    if tuple(bits) not in seen:
                        seen.add(tuple(bits))
                        break
                used[(suite, family, judge)] = bits
                for q, bit in zip(qs, bits):
                    order = list(ARMS if bit == 0 else reversed(ARMS))
                    result.append({'pair_id': pair_id(q, family), 'question_key': qkey(q),
                                   'suite': suite, 'answer_family': family, 'judge_family': judge,
                                   'seed': seed, 'order': order})
    return result

def batches(mapping):
    result = []
    for suite in SUITES:
        for judge in MODELS:
            for family in MODELS:
                units = sorted((m for m in mapping if m['suite']==suite and m['judge_family']==judge and m['answer_family']==family), key=lambda m:m['pair_id'])
                rng = random.Random(f'batches:{SEEDS[judge]}:{suite}:{family}')
                rng.shuffle(units)
                for i in range(0, len(units), 3):
                    result.append({'id':f'{suite}--{judge}--{family}--batch-{i//3:02}',
                                   'suite':suite, 'judge_family':judge,
                                   'pair_ids':[m['pair_id'] for m in units[i:i+3]]})
    return result

def judge_prompt(suite, pairs):
    allowed = ['id', 'question', 'A', 'B'] + (['reference'] if suite=='diagnostic12' else [])
    payload = [{k:p[k] for k in allowed} for p in pairs]
    return JUDGE_BASE + JUDGE_EXTRA[suite] + '\nPairs:\n' + json.dumps(payload, ensure_ascii=False, indent=2) + '\n'

def validate_vote(v, suite):
    if not isinstance(v, dict) or set(v) != {'id','A','B','winner','reason','factual_objections'}:
        raise ValueError('Wrong verdict fields')
    if v['winner'] not in ('A','B','tie') or not isinstance(v['reason'],str) or not v['reason'].strip():
        raise ValueError('Invalid winner or reason')
    for arm in ('A','B'):
        if not isinstance(v[arm],dict) or set(v[arm]) != set(DIMS[suite]):
            raise ValueError('Wrong score dimensions')
        if any(type(n) is not int or not 1 <= n <= 5 for n in v[arm].values()):
            raise ValueError('Scores must be integers in 1..5')
    if not isinstance(v['factual_objections'],list):
        raise ValueError('Objections must be a list')
    for obj in v['factual_objections']:
        if not isinstance(obj,dict) or set(obj) != {'answer','claim','label','evidence'}:
            raise ValueError('Wrong objection fields')
        if obj['answer'] not in ('A','B') or obj['label'] not in ('contradicted','unverified'):
            raise ValueError('Invalid objection label')
        if any(not isinstance(obj[k],str) or not obj[k].strip() for k in ('claim','evidence')):
            raise ValueError('Missing claim or evidence')

def decode_votes(text, suite, expected):
    # Strict JSON. No extraction, fence removal, model repair, or content retry.
    obj = json.loads(text)
    if not isinstance(obj,dict) or set(obj) != {'judgments'} or not isinstance(obj['judgments'],list):
        raise ValueError('Wrong batch envelope')
    ids = [v.get('id') if isinstance(v,dict) else None for v in obj['judgments']]
    if len(ids) != len(set(ids)) or set(ids) != set(expected):
        raise ValueError('Batch IDs must match exactly, without duplicates')
    verdicts = {}
    for v in obj['judgments']:
        try:
            validate_vote(v,suite)
            verdicts[v['id']] = {'status':'ok','verdict':v,'error':''}
        except (ValueError,TypeError) as exc:
            verdicts[v['id']] = {'status':'invalid','verdict':v,'error':str(exc)}
    return verdicts

def redact(text):
    text = re.sub(r'(AIza[\w-]{20,}|sk-[\w-]{10,})','[REDACTED]',text)
    return re.sub(r'(?i)([?&](?:key|api_key)=)[^&\s\"]+',r'\1[REDACTED]',text)

def rows(folder):
    return [read(p) for p in sorted((ROOT/folder).glob('*.json'))]

def progress(phase):
    with LOCK:
        answers, judgments = rows('responses'), rows('judgments')
        write(ROOT/'progress.json',{'updated':now(),'phase':phase,'provider_calls_this_preflight':0 if not answers else None,
             'answer_target':144,'judgment_unit_target':216,'judge_call_target_if_complete':72,
             'answers':dict(collections.Counter(x['status'] for x in answers)), 'answer_rows':len(answers),
             'judgments':dict(collections.Counter(x['status'] for x in judgments)), 'judgment_rows':len(judgments)})

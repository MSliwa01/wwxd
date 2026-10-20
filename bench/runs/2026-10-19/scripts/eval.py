#!/usr/bin/env python3
"""Reproducible phases. Only answers and judge can invoke a provider, after approval."""
from __future__ import annotations
import argparse
import threading
import concurrent.futures as cf
import fcntl
import json
from pathlib import Path
import common as c
import adapters
import integrity
import prepare

def save_result(path, obj):
    c.immutable(path,c.encoded(obj))

def orphan(unit):
    return any((c.ROOT/'logs').glob(unit+'--attempt*')) or any((c.ROOT/'logs/work').glob(unit+'--attempt*'))

def interrupted(family,prompt):
    return {'status':'failed','answer':'','requested_model':c.MODELS[family],'effort':c.EFFORT[family],
            'prompt_sha256':c.sha(prompt),'attempts':[],
            'error':'Interrupted invocation artifacts already exist. Not regenerated. Inspect logs manually.',
            'finished':c.now()}

def run_tasks(one, tasks, family_of):
    slots={f:threading.BoundedSemaphore(n) for f,n in c.CONCURRENCY.items()}
    def limited(task):
        with slots[family_of(task)]:
            return one(task)
    with cf.ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(limited,tasks))

def answers():
    integrity.approved()
    qs=c.read(c.ROOT/'frozen/questions.json')
    tasks=[(q,f,a) for q in qs for f in c.MODELS for a in c.ARMS
           if not (c.ROOT/'responses'/f'{c.answer_id(q,f,a)}.json').exists()]
    def one(task):
        q,f,a=task; ident=c.answer_id(q,f,a)
        prompt=(c.ROOT/'frozen/prompts'/f'{c.qkey(q)}--{a}.txt').read_bytes().decode('utf-8')
        result=interrupted(f,prompt) if orphan(ident) else adapters.invoke(ident,f,prompt)
        text=result.get('answer','')
        deviations=c.output_deviations(text,result['status'])
        result.update({'id':ident,'question_key':c.qkey(q),'suite':q['suite'],'family':f,'arm':a,
                       'words':len(text.split()),'format_deviations':deviations})
        save_result(c.ROOT/'responses'/f'{ident}.json',result)
        c.progress('answers')
        print(ident,result['status'],flush=True)
    run_tasks(one,tasks,lambda task:task[1])
    c.progress('answers_complete')

def expected_answers(qs):
    return {c.answer_id(q,f,a) for q in qs for f in c.MODELS for a in c.ARMS}

def make_pairs():
    integrity.verify()
    if (c.ROOT/'results/pairs-manifest.json').exists():
        integrity.verify_pairs()
        return
    qs=c.read(c.ROOT/'frozen/questions.json'); mapping=c.read(c.ROOT/'frozen/mapping.json')
    responses={r['id']:r for r in c.rows('responses')}
    if set(responses)!=expected_answers(qs):
        raise ValueError('Pairs require all 144 terminal response rows, including failures')
    qmap={c.qkey(q):q for q in qs}; refs=c.read(c.ROOT/'frozen/references.json')
    estimates={(e['question_key'],e['family']):e['expected_context_token_delta']
               for e in c.read(c.ROOT/'frozen/manifest.json')['prompt_estimates'] if e['arm']=='grounded'}
    pairs=[]
    for m in mapping:
        q=qmap[m['question_key']]; family=m['answer_family']; order=m['order']
        rows=[responses[c.answer_id(q,family,a)] for a in order]
        usage=c.pair_context_usage(responses[c.answer_id(q,family,'raw')],responses[c.answer_id(q,family,'grounded')],
                                   estimates[(c.qkey(q),family)])
        pairs.append({**m,'question':q['question'],'eligible':usage['eligible'],'context_usage':usage,
                      'A':rows[0]['answer'],'B':rows[1]['answer'],
                      **({'reference':refs[c.qkey(q)]} if q['suite']=='diagnostic12' else {})})
    files={}
    def freeze(path, data):
        files[path.relative_to(c.ROOT).as_posix()]=c.immutable(path,data)
    freeze(c.ROOT/'results/pairs.json',c.encoded(pairs))
    pairmap={(p['pair_id'],p['judge_family']):p for p in pairs}
    active_batches=[]
    for b in c.read(c.ROOT/'frozen/batches.json'):
        selected=[pairmap[(ident,b['judge_family'])] for ident in b['pair_ids']]
        valid=[p for p in selected if p['eligible']]
        public=[{'id':p['pair_id'],**{k:p[k] for k in ('question','A','B')},
                 **({'reference':p['reference']} if b['suite']=='diagnostic12' else {})} for p in valid]
        prompt=c.judge_prompt(b['suite'],public)
        path=c.ROOT/'results/judge-prompts'/f"{b['id']}.txt"
        freeze(path,prompt)
        active_batches.append({**b,'eligible_pair_ids':[p['pair_id'] for p in valid],
                               'blocked_pair_ids':[p['pair_id'] for p in selected if not p['eligible']],
                               'prompt_sha256':c.sha(prompt),'prompt_bytes':len(prompt.encode('utf-8')),
                               'estimated_input_tokens':c.estimate_tokens(prompt,b['judge_family']),
                               'chars_per_token':c.CHARS_PER_TOKEN[b['judge_family']]})
    freeze(c.ROOT/'results/judge-batches.json',c.encoded(active_batches))
    for p in sorted((c.ROOT/'responses').glob('*.json')):
        files[p.relative_to(c.ROOT).as_posix()]=c.digest(p)
    manifest={'input_manifest_sha256':c.digest(c.ROOT/'frozen/manifest.json'),'files':files}
    c.immutable(c.ROOT/'results/pairs-manifest.json',c.encoded(manifest))
    c.immutable(c.ROOT/'results/PAIRS.sha256',c.digest(c.ROOT/'results/pairs-manifest.json')+'\n')
    integrity.verify_pairs(); c.progress('pairs_complete')

def judge():
    integrity.approved(); integrity.verify_pairs()
    pairs={(p['pair_id'],p['judge_family']):p for p in c.read(c.ROOT/'results/pairs.json')}
    tasks=[]
    for batch in c.read(c.ROOT/'results/judge-batches.json'):
        f=batch['judge_family']; path=c.ROOT/'results/batch-calls'/f"{batch['id']}.json"
        if not path.exists():
            tasks.append((batch,f,path))
    def one(task):
        b,f,path=task
        prompt=(c.ROOT/'results/judge-prompts'/f"{b['id']}.txt").read_bytes().decode('utf-8')
        unit='judge--'+b['id']
        if b['eligible_pair_ids']:
            result=interrupted(f,prompt) if orphan(unit) else adapters.invoke(unit,f,prompt)
        else:
            result={'status':'blocked','answer':'','attempts':[],'error':'All pairs blocked by failed answers','prompt_sha256':c.sha(prompt)}
        verdicts={}; parse_error=''
        if result['status']=='ok':
            try:
                verdicts=c.decode_votes(result['answer'],b['suite'],b['eligible_pair_ids'])
            except (ValueError,TypeError,KeyError) as exc:
                parse_error=f'{type(exc).__name__}: {exc}'
        # Persist original raw model output and batch errors even when JSON is malformed.
        call={**result,'batch':b,'parse_error':parse_error,'decoded':verdicts}
        save_result(path,call)
        materialize_batch(call,pairs)
        c.progress('judging'); print(b['id'],result['status'],parse_error,flush=True)
    run_tasks(one,tasks,lambda task:task[1])
    # Recover rows from persisted batches after a crash without calling a judge again.
    for path in sorted((c.ROOT/'results/batch-calls').glob('*.json')):
        materialize_batch(c.read(path),pairs)
    c.progress('judging_complete')

def materialize_batch(call,pairs):
    b=call['batch']; f=b['judge_family']
    for ident in b['pair_ids']:
        p=pairs[(ident,f)]; decoded=call['decoded'].get(ident)
        v=decoded['verdict'] if decoded else None
        blocked=ident in b['blocked_pair_ids']
        status='blocked' if blocked else decoded['status'] if decoded else 'failed'
        winner=None
        if status=='ok':
            winner='tie' if v['winner']=='tie' else p['order'][('A','B').index(v['winner'])]
        row={'id':f'{ident}--judge-{f}','pair_id':ident,'suite':p['suite'],'question_key':p['question_key'],
             'answer_family':p['answer_family'],'judge_family':f,'primary_eligible':f!=p['answer_family'] and p['eligible'],
             'order':p['order'],'batch_id':b['id'],'status':status,'winner':winner,'verdict':v,
             'error':'Answer pair ineligible: '+', '.join(p['context_usage']['flags']) if blocked else decoded['error'] if decoded else call['parse_error'] or call['error'],
             'prompt_sha256':call['prompt_sha256']}
        save_result(c.ROOT/'judgments'/f"{row['id']}.json",row)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('phase',choices=['prepare','freeze','answers','pairs','judge','validate','report','smoke'])
    args=ap.parse_args()
    with (c.ROOT/'.run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if args.phase in ('prepare','freeze'):
            print(json.dumps(prepare.prepare(),indent=2))
        elif args.phase=='answers':
            answers()
        elif args.phase=='pairs':
            make_pairs()
        elif args.phase=='judge':
            judge()
        else:
            import report
            import smoke
            {'validate':report.validate,'report':report.report,'smoke':smoke.main}[args.phase]()

if __name__=='__main__':
    main()

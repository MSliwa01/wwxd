"""Validation and descriptive, suite-separated reporting. Never changes original rows."""
from __future__ import annotations
import collections
import itertools
import json
import statistics
import common as c
import adapters
import integrity

def check_artifacts():
    integrity.verify()
    checks=[]; warnings=[]
    def check(name,ok):
        checks.append({'check':name,'passed':bool(ok)})
    qs=c.read(c.ROOT/'frozen/questions.json'); manifest=c.read(c.ROOT/'frozen/manifest.json')
    check('24 unique suite/question keys',len(qs)==len({c.qkey(q) for q in qs})==24)
    for suite in c.SUITES:
        check(suite+' has 12 questions',sum(q['suite']==suite for q in qs)==12)
    for vault,ctx in manifest['contexts'].items():
        data=(c.ROOT/'frozen/context'/f'{vault}.txt').read_bytes()
        for page in ctx['pages']:
            start=page['context_byte_offset']; segment=data[start:start+page['bytes']]
            check('unchanged full page '+vault+'/'+page['relative_path'],c.sha(segment)==page['sha256']==page['included_sha256'] and not page['truncated'])
        check('all source bytes included '+vault,sum(p['bytes'] for p in ctx['pages'])==ctx['source_bytes'])
    for q in qs:
        raw=(c.ROOT/'frozen/prompts'/f'{c.qkey(q)}--raw.txt').read_bytes()
        grounded=(c.ROOT/'frozen/prompts'/f'{c.qkey(q)}--grounded.txt').read_bytes()
        ctx=(c.ROOT/'frozen/context'/f"{q['vault']}.txt").read_bytes()
        check('exact arm prompt difference '+c.qkey(q),raw==c.answer_prompt(q).encode() and grounded==raw+c.CONTEXT_PREFIX.encode()+ctx+c.CONTEXT_TRAILER.encode())
    mapping=c.read(c.ROOT/'frozen/mapping.json')
    check('216 frozen mappings',len(mapping)==216)
    for suite in c.SUITES:
        for family in c.MODELS:
            signatures=[]
            for judge in c.MODELS:
                selected=sorted((m for m in mapping if (m['suite'],m['answer_family'],m['judge_family'])==(suite,family,judge)),key=lambda x:x['question_key'])
                check(f'6/6 order balance {suite}/{family}/{judge}',len(selected)==12 and sum(m['order'][0]=='grounded' for m in selected)==6)
                signatures.append(tuple(m['order'][0] for m in selected))
            check(f'distinct judge-family orders {suite}/{family}',len(set(signatures))==3)
    answers=c.rows('responses'); judgments=c.rows('judgments')
    expected={c.answer_id(q,f,a) for q in qs for f in c.MODELS for a in c.ARMS}
    check('all 144 terminal response rows',len(answers)==144 and {r['id'] for r in answers}==expected)
    expected_j={m['pair_id']+'--judge-'+m['judge_family'] for m in mapping}
    check('all 216 terminal judgment rows',len(judgments)==216 and {j['id'] for j in judgments}==expected_j)
    usage=[]
    for row in answers:
        name=f"{row['question_key']}--{row['arm']}.txt"
        prompt=(c.ROOT/'frozen/prompts'/name).read_bytes()
        check('answer prompt '+row['id'],row['prompt_sha256']==c.sha(prompt))
        check('answer configuration '+row['id'],row['requested_model']==c.MODELS[row['family']] and row['effort']==c.EFFORT[row['family']])
        check('word count '+row['id'],row['words']==len(row['answer'].split()))
        check('output deviations retained '+row['id'],row['format_deviations']==c.output_deviations(row['answer'],row['status']))
        for attempt in row['attempts']:
            unit=f"{row['id']}--attempt{attempt['attempt']}"
            for suffix,key in (('.stdout.jsonl','stdout_sha256'),('.stderr.txt','stderr_sha256')):
                check('log hash '+unit+suffix,c.digest(c.ROOT/'logs'/f'{unit}{suffix}')==attempt[key])
        if row['status']=='ok':
            log=c.ROOT/'logs'/f"{row['id']}--attempt{len(row['attempts'])}.stdout.jsonl"
            try:
                parsed=adapters.parse_output(row['family'],log.read_text())
                okay=parsed['answer']==row['answer'] and parsed['actual_input_tokens']==row.get('actual_input_tokens')
            except (ValueError,KeyError):
                okay=False
            check('no tools, matching answer and usage '+row['id'],okay)
            if row.get('actual_input_tokens') is None:
                warnings.append('Accepted input usage missing: '+row['id'])
        usage.append({k:row.get(k) for k in ('id','suite','family','arm','status','actual_input_tokens','usage_events','finish_reasons')})
    responsemap={r['id']:r for r in answers}
    estimates={(e['question_key'],e['family']):e['expected_context_token_delta']
               for e in manifest['prompt_estimates'] if e['arm']=='grounded'}
    context_checks={}
    for q in qs:
        for family in c.MODELS:
            raw=responsemap.get(c.answer_id(q,family,'raw')); grounded=responsemap.get(c.answer_id(q,family,'grounded'))
            if raw is None or grounded is None:
                continue
            assessment=c.pair_context_usage(raw,grounded,estimates[(c.qkey(q),family)])
            context_checks[(c.qkey(q),family)]=assessment
            usage.append({'kind':'context_usage_pair','question_key':c.qkey(q),'family':family,**assessment})
            if assessment['flags']:
                warnings.append('Pair ineligible '+c.qkey(q)+'/'+family+': '+', '.join(assessment['flags']))
    if (c.ROOT/'results/pairs-manifest.json').exists():
        integrity.verify_pairs()
        pairs={(p['pair_id'],p['judge_family']):p for p in c.read(c.ROOT/'results/pairs.json')}
        original_votes={}
        check('216 judge-specific pair views',len(pairs)==216)
        frozenmap={(m['pair_id'],m['judge_family']):m for m in mapping}
        qmap={c.qkey(q):q for q in qs}; responsemap={r['id']:r for r in answers}
        for key,p in pairs.items():
            m=frozenmap[key]; q=qmap[m['question_key']]
            assessment=context_checks[(c.qkey(q),m['answer_family'])]
            check('pair context usage and eligibility '+str(key),p['context_usage']==assessment and p['eligible']==assessment['eligible'])
            check('pair mapping '+str(key),all(p[k]==m[k] for k in m))
            check('pair original answer roundtrip '+str(key),all(p[label]==responsemap[c.answer_id(q,m['answer_family'],arm)]['answer'] for label,arm in zip(('A','B'),m['order'])))
        for b in c.read(c.ROOT/'results/judge-batches.json'):
            prompt=(c.ROOT/'results/judge-prompts'/f"{b['id']}.txt").read_text()
            check('bounded batch '+b['id'],len(b['pair_ids'])<=3 and len(b['eligible_pair_ids'])<=3)
            check('judge prompt hash '+b['id'],c.sha(prompt)==b['prompt_sha256'])
            payload=json.loads(prompt.split('\nPairs:\n',1)[1])
            allowed={'id','question','A','B'} | ({'reference'} if b['suite']=='diagnostic12' else set())
            check('minimal blind payload '+b['id'],all(set(p)==allowed and p['id'].startswith('p-') for p in payload))
            callpath=c.ROOT/'results/batch-calls'/f"{b['id']}.json"
            check('terminal judge batch '+b['id'],callpath.exists())
            if callpath.exists():
                call=c.read(callpath)
                check('judge used frozen prompt '+b['id'],call['prompt_sha256']==b['prompt_sha256'])
                decoded={}; decode_error=''
                if call['status']=='ok':
                    try:
                        decoded=c.decode_votes(call['answer'],b['suite'],b['eligible_pair_ids'])
                    except (ValueError,TypeError,KeyError) as exc:
                        decode_error=f'{type(exc).__name__}: {exc}'
                check('batch decoded votes match original output '+b['id'],decoded==call['decoded'] and decode_error==call['parse_error'])
                for ident in b['pair_ids']:
                    original_votes[(ident,b['judge_family'])]=decoded.get(ident)
                for attempt in call['attempts']:
                    unit=f"judge--{b['id']}--attempt{attempt['attempt']}"
                    for suffix,key in (('.stdout.jsonl','stdout_sha256'),('.stderr.txt','stderr_sha256')):
                        check('judge log hash '+unit+suffix,c.digest(c.ROOT/'logs'/f'{unit}{suffix}')==attempt[key])
                if call['status']=='ok':
                    log=c.ROOT/'logs'/f"judge--{b['id']}--attempt{len(call['attempts'])}.stdout.jsonl"
                    try:
                        parsed=adapters.parse_output(b['judge_family'],log.read_text())
                        okay=parsed['answer']==call['answer']
                    except (ValueError,KeyError):
                        okay=False
                    check('no judge tools and original output '+b['id'],okay)
                usage.append({'batch_id':b['id'],'suite':b['suite'],'judge_family':b['judge_family'],
                              **{k:call.get(k) for k in ('status','actual_input_tokens','usage_events','finish_reasons')}})
        for j in judgments:
            p=pairs[(j['pair_id'],j['judge_family'])]
            original=original_votes.get((j['pair_id'],j['judge_family']))
            check('individual verdict preserved from raw batch '+j['id'],j['verdict']==(original['verdict'] if original else None))
            check('judgment order and exclusion '+j['id'],j['order']==p['order'] and j['primary_eligible']==(j['answer_family']!=j['judge_family'] and p['eligible']))
            check('ineligible pair has blocked vote '+j['id'],p['eligible'] or j['status']=='blocked')
            if j['status']=='ok':
                try:
                    c.validate_vote(j['verdict'],j['suite']); valid=True
                except (ValueError,TypeError):
                    valid=False
                check('valid vote '+j['id'],valid)
                if valid:
                    v=j['verdict']; winner='tie' if v['winner']=='tie' else p['order'][('A','B').index(v['winner'])]
                    check('winner mapping roundtrip '+j['id'],j['winner']==winner)
    check('invocation work directories remain empty',not any(p.is_file() for p in (c.ROOT/'logs/work').rglob('*')))
    return checks,warnings,usage

def validate():
    checks,warnings,usage=check_artifacts()
    result={'passed':all(x['passed'] for x in checks),'checks':checks,'warnings':warnings}
    c.write(c.ROOT/'results/validation.json',result)
    c.write(c.ROOT/'results/accepted-input-usage.json',usage)
    print(json.dumps({'passed':result['passed'],'checks':len(checks),'failed':[x for x in checks if not x['passed']],'warnings':warnings},indent=2))
    if not result['passed']:
        raise SystemExit(1)
    return result

def counts(rows):
    return {'valid_ratings':len(rows),**{arm:sum(j['winner']==arm for j in rows) for arm in ('raw','grounded','tie')}}

def scores(rows,suite):
    result={}
    for arm in c.ARMS:
        result[arm]={}
        for dim in c.DIMS[suite]:
            values=[j['verdict'][('A','B')[j['order'].index(arm)]][dim] for j in rows]
            result[arm][dim]={'mean':round(statistics.mean(values),3) if values else None,'ratings':len(values)}
    return result

def suite_summary(suite,questions,answers,judgments):
    allrows=[j for j in judgments if j['suite']==suite and j['status']=='ok']
    primary=[j for j in allrows if j['primary_eligible']]
    matrix={a:{f:{'votes':counts([j for j in allrows if j['answer_family']==a and j['judge_family']==f]),
                  'scores':scores([j for j in allrows if j['answer_family']==a and j['judge_family']==f],suite),
                  'primary_eligible':a!=f,'target_ratings':12} for f in c.MODELS} for a in c.MODELS}
    consensus=[]
    for q in questions:
        if q['suite']!=suite:
            continue
        for f in c.MODELS:
            votes=[j for j in primary if j['pair_id']==c.pair_id(q,f)]
            label='missing' if len(votes)!=2 else votes[0]['winner'] if votes[0]['winner']==votes[1]['winner'] else 'disagreement'
            consensus.append({'question_key':c.qkey(q),'answer_family':f,'label':label,
                              'external_votes':[{k:j[k] for k in ('judge_family','winner','verdict')} for j in votes]})
    return {'questions':12,'answer_target':72,'judgment_unit_target':108,
            'answer_statuses':dict(collections.Counter(r['status'] for r in answers if r['suite']==suite)),
            'judgment_statuses':dict(collections.Counter(j['status'] for j in judgments if j['suite']==suite)),
            'primary_votes':counts(primary),'all_votes':counts(allrows),
            'same_family_votes':counts([j for j in allrows if not j['primary_eligible']]),
            'primary_scores':scores(primary,suite),'all_scores':scores(allrows,suite),'answer_judge_matrix':matrix,
            'primary_by_answer':{f:{'votes':counts([j for j in primary if j['answer_family']==f]),'scores':scores([j for j in primary if j['answer_family']==f],suite),
                                    'consensus_counts':dict(collections.Counter(cn['label'] for cn in consensus if cn['answer_family']==f))} for f in c.MODELS},
            'question_consensus':consensus,
            'judge_agreement':{f'{a}/{b}':agreement(allrows,a,b) for a,b in itertools.combinations(c.MODELS,2)}}

def agreement(rows,a,b):
    left={j['pair_id']:j['winner'] for j in rows if j['judge_family']==a}
    right={j['pair_id']:j['winner'] for j in rows if j['judge_family']==b}
    common=set(left)&set(right)
    return {'agree':sum(left[k]==right[k] for k in common),'common_pairs':len(common)}

def export_reviews(questions,answers,judgments,summaries):
    practical=[]; private=[]; objections=[]; diagnostic=[]
    qmap={c.qkey(q):q for q in questions}
    for r in answers:
        if r['suite']!='newadvice12':
            continue
        ident='review-'+c.sha('factual-review:'+r['id'])[:16]
        practical.append({'id':ident,'question':qmap[r['question_key']]['question'],'answer':r['answer'],'status':r['status']})
        private.append({'id':ident,'response_id':r['id'],'question_key':r['question_key']})
    practical.sort(key=lambda x:x['id'])
    refs=c.read(c.ROOT/'frozen/references.json')
    for cn in summaries['diagnostic12']['question_consensus']:
        p=c.pair_id(qmap[cn['question_key']],cn['answer_family'])
        votes=[j for j in judgments if j['suite']=='diagnostic12' and j['pair_id']==p]
        if cn['label'] in ('disagreement','missing') or any(j.get('winner') in ('raw','tie') for j in votes):
            rs=[r for r in answers if r['question_key']==cn['question_key'] and r['family']==cn['answer_family']]
            rs.sort(key=lambda r:c.sha('diagnostic-review:'+r['id']))
            diagnostic.append({'id':p,'question':qmap[cn['question_key']]['question'],
                               'answers':[{'id':'review-'+c.sha(r['id'])[:16],'answer':r['answer'],'status':r['status']} for r in rs],
                               'reference':refs[cn['question_key']]})
    for j in judgments:
        if j.get('verdict') and isinstance(j['verdict'].get('factual_objections'),list):
            for index,obj in enumerate(j['verdict']['factual_objections']):
                objections.append({'judgment_id':j['id'],'ordinal':index,'original_objection':obj,'vote_status':j['status']})
    target=c.ROOT/'results/review-export'
    for name,obj in [('practical-all-answers.json',practical),('private-answer-map.json',private),
                     ('diagnostic-selected.json',diagnostic),('original-factual-objections.json',objections)]:
        c.immutable(target/name,c.encoded(obj))
    return {'practical_answer_slots':len(practical),'diagnostic_pairs':len(diagnostic),'original_objections':len(objections),
            'status':'Independent post-run reviews pending. These exports cannot change original votes.'}

def report():
    validation=validate()
    questions=c.read(c.ROOT/'frozen/questions.json'); answers=c.rows('responses'); judgments=c.rows('judgments')
    calls=c.rows('results/batch-calls')
    suites={s:suite_summary(s,questions,answers,judgments) for s in c.SUITES}
    reviews=export_reviews(questions,answers,judgments,suites)
    failures=[{'id':r['id'],'status':r['status'],'error':r.get('error','')} for r in answers+judgments if r['status']!='ok']
    summary={'suites':suites,'answer_calls':dict(collections.Counter(r['status'] for r in answers)),
             'judge_batch_calls':dict(collections.Counter(r['status'] for r in calls)),
             'judge_batch_decode_failures':sum(bool(r.get('parse_error')) for r in calls),
             'context_usage_checks':[u for u in c.read(c.ROOT/'results/accepted-input-usage.json') if u.get('kind')=='context_usage_pair'],
             'attempts':sum(len(r['attempts']) for r in answers+calls),'failures':failures,'post_run_reviews':reviews,
             'word_counts':[{k:r[k] for k in ('id','suite','family','arm','words','format_deviations')} for r in answers],
             'validation_passed':validation['passed'],'usage_gaps':validation['warnings']}
    c.write(c.ROOT/'results/summary.json',summary)
    lines=['# Private evaluation report','',f'Evaluation date: {c.DATE}.',
           '',f"Answer calls: {summary['answer_calls']}, target 144. Judge batch calls: {summary['judge_batch_calls']}, target 72 if all pairs are eligible. Judgment units target 216. Total logged outer attempts: {summary['attempts']}.",
           '',f"A completed provider call does not imply a correct answer or a valid judgment. Judge batch JSON-envelope failures: {summary['judge_batch_decode_failures']}. Individual invalid votes and failed/blocked units remain in the status counts and denominators.",
           '', 'Each suite has 12 selected questions. Repeated judge ratings and answer families do not increase the number of independent questions. Results are descriptive and support no global model ranking or universal success-rate claim.']
    for suite,ss in suites.items():
        lines += ['',f'## {suite}','',f"Answer statuses: {ss['answer_statuses']}, target 72. Judgment statuses: {ss['judgment_statuses']}, target 108.",
                  '',f"External-judge votes: {ss['primary_votes']}. Same-family votes, excluded from primary: {ss['same_family_votes']}.",
                  '', '| Answer family | Judge family | Raw | Grounded | Tie | Valid / target | Primary |',
                  '| --- | --- | ---: | ---: | ---: | --- | --- |']
        for a,judges in ss['answer_judge_matrix'].items():
            for f,cell in judges.items():
                v=cell['votes']; lines.append(f"| {a} | {f} | {v['raw']} | {v['grounded']} | {v['tie']} | {v['valid_ratings']} / 12 | {cell['primary_eligible']} |")
        lines += ['', '| Dimension | Raw mean | Grounded mean | External ratings per arm |','| --- | ---: | ---: | ---: |']
        for dim in c.DIMS[suite]:
            r=ss['primary_scores']['raw'][dim]; g=ss['primary_scores']['grounded'][dim]
            lines.append(f"| {dim} | {r['mean']} | {g['mean']} | {r['ratings']} |")
        for f,cell in ss['primary_by_answer'].items():
            lines += ['',f"{f} external consensus across 12 question slots: {cell['consensus_counts']}."]
        lines += ['', 'All scores, every answer/judge combination, original question-level votes, disagreements and agreement denominators are in `results/summary.json`.']
    lines += ['', '## Review and limitations','',
              f"Post-run factual review exports: {reviews}. Original votes remain unchanged, including schema failures and factual errors.",
              '', 'Full wiki pages were frozen before fixture parsing. Every routed page is supplied unchanged, with provenance and hashes. Prompt estimates did not resize context. Actual input usage, including missing provider fields and raw usage records, is in `results/accepted-input-usage.json`.',
              '', f"Context-usage diagnostics: {sum('context_usage_inconsistent' in u['flags'] for u in summary['context_usage_checks'])} pairs flagged context_usage_inconsistent and excluded as ineligible. The pre-run tolerance is 50% through 200% of the frozen per-family estimate. Actual raw and grounded token counts and deltas are retained. This diagnostic does not prove attention to every page.",
              '', 'Sol native logs do not independently attest the serving model. Opus and Gemini observed model identifiers are checked when supplied. Provider CLI wrappers differ across families. CLI backends may retry transport internally; outer attempts and all provider streams are retained.',
              '',f"Validation passed. Usage and eligibility warnings: {len(validation['warnings'])}. Failed/blocked/invalid rows: {len(failures)}. Word counts and formatting deviations are retained without regenerating or truncating answers.",
              '', 'Diagnostic regression uses known cases and repaired raw references. Practical advice uses new raw-only scenarios and judges receive only questions and anonymous answers. Advice scores are not observed business outcomes. Independent factual reviews are required before interpretation is complete. No public site or CV metric is changed.']
    (c.ROOT/'REPORT.md').write_text('\n'.join(lines)+'\n')
    c.progress('reported_pending_post_run_factual_review')

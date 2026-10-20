"""Offline regression checks using local stubs only, isolated beneath run/results."""
from __future__ import annotations
import contextlib
import concurrent.futures as cf
import copy
import io
import json
from pathlib import Path
import shutil
import tempfile
import threading
import time
from unittest.mock import patch
import common as c
import adapters
import integrity
import prepare
import report

def events(family,answer,tokens=123):
    if family=='sol':
        return [{'type':'item.completed','item':{'type':'agent_message','text':answer}},
                {'type':'turn.completed','usage':{'input_tokens':tokens,'output_tokens':45}}]
    if family=='opus':
        return [{'type':'system','subtype':'init','tools':[]},
                {'type':'assistant','message':{'model':c.MODELS[family],'content':[]}},
                {'type':'result','subtype':'success','stop_reason':'end_turn','terminal_reason':'completed',
                 'result':answer,'is_error':False,'usage':{'input_tokens':tokens-23 if tokens is not None else None,'cache_read_input_tokens':23}}]
    return [{'modelVersion':c.MODELS[family],'candidates':[{'content':{'parts':[{'text':answer}]},'finishReason':'STOP'}],
             'usageMetadata':{'promptTokenCount':tokens,'candidatesTokenCount':45}}]

def valid_vote(ident,suite):
    return {'id':ident,'A':dict.fromkeys(c.DIMS[suite],3),'B':dict.fromkeys(c.DIMS[suite],4),
            'winner':'A','reason':'Offline stub deliberately prefers A despite the numeric scores; keep the original vote.',
            'factual_objections':[{'answer':'B','claim':'Offline synthetic claim','label':'unverified','evidence':'No confirming evidence in this synthetic test.'}]}

def main():
    original_root=c.ROOT
    checks=[]
    def check(name,condition):
        if not condition:
            raise AssertionError(name)
        checks.append({'check':name,'passed':True})
    def rejects(name,fn):
        try:
            fn()
        except (ValueError,PermissionError,FileNotFoundError,TypeError):
            check(name,True)
        else:
            check(name,False)
    for family in c.MODELS:
        parsed=adapters.parse_output(family,'\n'.join(json.dumps(e) for e in events(family,'offline text')))
        check('parse provider stub and actual usage '+family,parsed['answer']=='offline text' and parsed['actual_input_tokens']==123)
        bad=events(family,'offline text')
        if family=='sol':
            bad.insert(0,{'type':'item.completed','item':{'type':'command_execution'}})
        elif family=='opus':
            bad[0]['tools']=['Bash']
        else:
            bad[0]['candidates'][0]['content']['parts'].append({'functionCall':{'name':'read'}})
        rejects('reject tools '+family,lambda:adapters.parse_output(family,'\n'.join(json.dumps(e) for e in bad)))
    for family in ('opus','gemini'):
        bad=events(family,'offline text')
        if family=='opus':
            bad[1]['message']['model']='wrong-model'
        else:
            bad[0]['modelVersion']='wrong-model'
        rejects('reject wrong observed model '+family,lambda:adapters.parse_output(family,'\n'.join(json.dumps(e) for e in bad)))
    incomplete=events('gemini','cut off answer')
    incomplete[0]['candidates'][0]['finishReason']='MAX_TOKENS'
    rejects('reject truncated provider answer',lambda:adapters.parse_output('gemini','\n'.join(json.dumps(e) for e in incomplete)))
    reduced=[{'type':'context_reduced'},*events('sol','partial context answer')]
    rejects('reject context reduction event',lambda:adapters.parse_output('sol','\n'.join(json.dumps(e) for e in reduced)))
    sol_limit=events('sol','cut off answer')
    sol_limit[-1]['finish_reason']='length'
    rejects('reject Sol length termination',lambda:adapters.parse_output('sol','\n'.join(json.dumps(e) for e in sol_limit)))
    rejects('reject Sol missing terminal metadata',lambda:adapters.parse_output('sol',json.dumps(events('sol','partial answer')[0])))
    def parse(family, stream):
        return adapters.parse_output(family,'\n'.join(json.dumps(e) for e in stream))
    for stop in (None,'max_tokens','tool_use','pause_turn','refusal','STOP'):
        bad=events('opus','partial answer'); bad[-1]['stop_reason']=stop
        rejects('Opus rejects non-end_turn '+str(stop),lambda:parse('opus',bad))
    for terminal in ('max_tokens','incomplete','failed','error_max_turns'):
        bad=events('opus','partial answer'); bad[-1]['terminal_reason']=terminal
        rejects('Opus rejects bad terminal_reason '+terminal,lambda:parse('opus',bad))
    bad=events('opus','partial answer'); bad[-1]['subtype']='error_max_turns'
    rejects('Opus rejects unsuccessful result subtype',lambda:parse('opus',bad))
    rejects('Opus requires result event',lambda:parse('opus',events('opus','partial')[:-1]))
    for terminal in ('completed','end_turn',None):
        good=events('opus','complete answer'); good[-1]['terminal_reason']=terminal
        check('Opus accepts end_turn '+str(terminal),parse('opus',good)['answer']=='complete answer')
    check('Opus records both terminal fields',parse('opus',events('opus','complete'))['finish_reasons']==['success','end_turn','completed'])
    for stop in (None,'MAX_TOKENS','SAFETY','RECITATION','OTHER','BLOCKLIST','PROHIBITED_CONTENT','MALFORMED_FUNCTION_CALL','stop'):
        bad=events('gemini','partial answer'); bad[0]['candidates'][0]['finishReason']=stop
        rejects('Gemini rejects non-STOP '+str(stop),lambda:parse('gemini',bad))
    for family in c.MODELS:
        for reduction in ({'type':'context_truncated'}, {'type':'system','subtype':'compact_boundary'},
                          {'type':'item.completed','item':{'type':'context_compaction'}},
                          {'type':'system','subtype':'context_reduced'}):
            rejects('reject reduction fields '+family+'/'+repr(reduction),lambda:parse(family,[reduction,*events(family,'partial')]))
    for kind in ('browser_use','computer_use','image_generation','web_search','command_execution','file_change','tool_call','unknown',''):
        for event in ('item.started','item.updated','item.completed'):
            bad=[{'type':event,'item':{'type':kind}},*events('sol','partial')]
            rejects('Sol rejects unapproved item '+event+'/'+kind,lambda:parse('sol',bad))
    good=[{'type':'item.completed','item':{'type':'reasoning','text':'offline reasoning'}},*events('sol','complete')]
    check('Sol accepts reasoning and agent_message only',parse('sol',good)['answer']=='complete')
    rejects('Sol rejects failed turn even with final text',lambda:parse('sol',events('sol','partial')+[{'type':'turn.failed','error':'offline'}]))
    raw={'status':'ok','actual_input_tokens':100}
    for delta in (500,1000,2000):
        got=c.pair_context_usage(raw,{'status':'ok','actual_input_tokens':100+delta},1000)
        check('inclusive context delta accepted '+str(delta),got['eligible'] and got['input_token_delta']==delta)
    for delta in (-50,0,499,2001):
        got=c.pair_context_usage(raw,{'status':'ok','actual_input_tokens':100+delta},1000)
        check('inconsistent delta ineligible '+str(delta),not got['eligible'] and got['flags']==['context_usage_inconsistent'])
    for count in (None,0,-1,True,1.5,'100'):
        got=c.pair_context_usage(raw,{'status':'ok','actual_input_tokens':count},1000)
        check('missing/invalid usage ineligible '+str(count),not got['eligible'] and 'context_usage_missing' in got['flags'])
    got=c.pair_context_usage(raw,{'status':'failed','actual_input_tokens':1100},1000)
    check('failed arm ineligible despite plausible usage',got['flags']==['answer_incomplete'])
    for family,ratio in c.CHARS_PER_TOKEN.items():
        check('pilot ratio estimate '+family,c.estimate_tokens('x'*10000,family)==__import__('math').ceil(10000/ratio))
    for text in ('[[page]]','yt-8d-cApFHjeY','web-example_123','supplied context','WIKI','knowledge base','knowledge\nbase'):
        check('output leak flagged without rewriting '+repr(text),any('blinding leak' in flag for flag in c.output_deviations(text,'failed')))
    check('ordinary output has no leak flag',not any('blinding leak' in flag for flag in c.output_deviations('Use a ten dollar budget and test demand.','failed')))
    for error,delay in [('HTTP 429',60),('HTTP 429 {"retryDelay":"30s"}',60),
                        ('HTTP 429 {"retryDelay":"90s"}',90),('HTTP 429 {"retryDelay":"300s"}',120),
                        ('HTTP 503 {"retryDelay":"75s"}',75),('HTTP 503',10)]:
        check('Gemini retry delay '+error,adapters.retry_delay('gemini',error)==delay)
    for suite in c.SUITES:
        vote=valid_vote('p-stub',suite)
        decoded=c.decode_votes(json.dumps({'judgments':[vote]}),suite,['p-stub'])
        check('valid schema and wrong substantive vote preserved '+suite,decoded['p-stub']['verdict']==vote)
        for badscore in (0,6,True,2.5,'3'):
            bad=copy.deepcopy(vote); bad['A'][c.DIMS[suite][0]]=badscore
            got=c.decode_votes(json.dumps({'judgments':[bad]}),suite,['p-stub'])
            check('invalid score retained '+suite+'/'+str(badscore),got['p-stub']['status']=='invalid' and got['p-stub']['verdict']==bad)
        bad=copy.deepcopy(vote); bad['factual_objections'][0]['label']='hallucination'
        check('uncertain factual label rejected '+suite,c.decode_votes(json.dumps({'judgments':[bad]}),suite,['p-stub'])['p-stub']['status']=='invalid')
        rejects('no fenced JSON repair '+suite,lambda:c.decode_votes('```json\n{}\n```',suite,['p-stub']))
        rejects('no duplicate/missing IDs '+suite,lambda:c.decode_votes(json.dumps({'judgments':[vote,vote]}),suite,['p-stub']))
    check('transport retry classification',all(adapters.transport_failure(s) for s in ('HTTP 429','HTTP 503','stream disconnected','timeout')))
    check('no context/content/auth/model retries',not any(adapters.transport_failure(s) for s in ('context limit HTTP 503','No final answer HTTP 500','Actual model mismatch timeout','credential failed network','schema parse timeout','SAFETY HTTP 503','incomplete HTTP 429','STOP termination network')))
    with patch.dict('os.environ',{'OPENAI_API_KEY':'synthetic-secret','T3_FAKE':'synthetic-token','CLAUDECODE':'1'},clear=False):
        check('child env strips credentials and orchestrator session',not any(k in adapters.clean_env() for k in ('OPENAI_API_KEY','T3_FAKE','CLAUDECODE')))
    check('no OpenAI API adapter and exact models',adapters.command('sol')[0:2]==['codex','exec'] and c.MODELS=={'sol':'gpt-6.1-sol','opus':'claude-opus-5-5','gemini':'gemini-3.5-flash-lite'})
    # A complete synthetic run verifies all phases without credential loading or subprocesses.
    sandbox=Path(tempfile.mkdtemp(prefix='offline-smoke-',dir=original_root/'results'))
    root=sandbox/'run'; base=sandbox; vaults=sandbox/'vaults'; helper=sandbox/'helper.py'
    root.mkdir(); helper.write_text('raise RuntimeError("Offline test must never load this helper")\n')
    shutil.copytree(original_root/'scripts',root/'scripts',ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copyfile(original_root/'README.md',root/'README.md')
    (base/'PROTOCOL.md').write_text('Offline synthetic protocol only.\n')
    inventory=[]
    for suite in c.SUITES:
        questions=[]; packets=[]
        for i in range(12):
            vault='hormozi' if i<6 else 'yc'
            raw=vaults/vault/'raw/source.md'; raw.parent.mkdir(parents=True,exist_ok=True)
            raw.write_text('Synthetic raw evidence for offline validation.\n')
            question={'id':f'q{i:02}','vault':vault,'question':f'Synthetic decision {i}: choose a useful action with a budget of 10.','category':'synthetic'}
            questions.append(question)
            ev={'source_path':str(raw),'source_sha256':c.digest(raw),'quote':'Synthetic raw evidence for offline validation.','timestamp':None}
            packets.append({**question,('evidence' if suite=='diagnostic12' else 'source_support'):[ev]})
            inventory.append({'vault':vault,'source_path':str(raw),'source_sha256':c.digest(raw)})
        (base/'fixtures').mkdir(exist_ok=True)
        c.write(base/'fixtures'/('diagnostic-questions.json' if suite=='diagnostic12' else 'advice-questions.json'),questions)
        c.write(base/'fixtures'/('diagnostic-reference.json' if suite=='diagnostic12' else 'advice-evidence.json'),
                {('items' if suite=='diagnostic12' else 'cases'):packets})
    c.write(base/'fixtures/source-inventory.json',{'sources':inventory})
    (base/'fixtures/AUDIT.md').write_text('Synthetic offline audit, not real fixture provenance.\n')
    for vault in ('hormozi','yc'):
        wiki=vaults/vault/'wiki'; (wiki/'nested').mkdir(parents=True)
        # Larger than the historical pilot cap, includes Unicode and exact CRLF bytes.
        (wiki/'profile.md').write_bytes(b'---\nsource_refs: [raw/source.md]\n---\n'+b'unchanged page\r\n'*5000)
        (wiki/'nested/page.md').write_bytes(('all text including Unicode: żółć\n'*4000).encode())
    try:
        with patch.multiple(c,ROOT=root,BASE=base,VAULTS=vaults,HELPER=helper):
            # Regression for a progress reader observing an unfinished immutable JSON file.
            atomic_dir=root/'results/atomic-check'; atomic_dir.mkdir(parents=True)
            finished=threading.Event()
            def publish():
                try:
                    for i in range(32):
                        c.immutable(atomic_dir/f'{i}.json',c.encoded({'payload':'x'*65536}))
                finally:
                    finished.set()
            def observe():
                while not finished.is_set():
                    for p in atomic_dir.glob('*.json'):
                        c.read(p)
            with cf.ThreadPoolExecutor(max_workers=2) as pool:
                writer=pool.submit(publish); reader=pool.submit(observe)
                writer.result(); reader.result()
            check('immutable JSON publication is atomic during concurrent progress reads',len(list(atomic_dir.glob('*.json')))==32)
            frozen=prepare.prepare()
            check('synthetic complete freeze',frozen['status']=='frozen_awaiting_review')
            manifest=integrity.verify()
            check('large complete contexts not truncated',all(ctx['source_bytes']>56000 and all(not p['truncated'] for p in ctx['pages']) for ctx in manifest['contexts'].values()))
            rejects('approval absent blocks actual adapter before subprocess',lambda:adapters.invoke('blocked-test','sol','offline'))
            for q in c.read(root/'frozen/questions.json'):
                raw=(root/'frozen/prompts'/f'{c.qkey(q)}--raw.txt').read_bytes()
                ground=(root/'frozen/prompts'/f'{c.qkey(q)}--grounded.txt').read_bytes()
                check('exact prompt difference '+c.qkey(q),ground==raw+c.CONTEXT_PREFIX.encode()+(root/'frozen/context'/f"{q['vault']}.txt").read_bytes()+c.CONTEXT_TRAILER.encode())
            check('frozen per-family ratios',manifest['context_token_estimation']['chars_per_token_by_family']==c.CHARS_PER_TOKEN)
            for estimate in manifest['prompt_estimates']:
                text=(root/'frozen/prompts'/f"{estimate['question_key']}--{estimate['arm']}.txt").read_bytes().decode()
                check('frozen prompt estimate '+estimate['family']+'/'+estimate['arm'],
                      estimate['estimated_input_tokens']==c.estimate_tokens(text,estimate['family']) and estimate['chars_per_token']==c.CHARS_PER_TOKEN[estimate['family']])
                if estimate['arm']=='grounded':
                    raw=(root/'frozen/prompts'/f"{estimate['question_key']}--raw.txt").read_bytes().decode()
                    check('frozen added context estimate '+estimate['family'],estimate['expected_context_token_delta']==c.estimate_tokens(text[len(raw):],estimate['family']))
            mapping=c.read(root/'frozen/mapping.json'); grouping=c.read(root/'frozen/batches.json')
            check('144 answer and 216 judgment targets',manifest['counts']['answers']==144 and len(mapping)==216)
            check('72 batches of at most 3 units and exact coverage',len(grouping)==72 and all(len(b['pair_ids'])<=3 for b in grouping) and sum(len(b['pair_ids']) for b in grouping)==216)
            for suite in c.SUITES:
                for family in c.MODELS:
                    sigs=[]
                    for judge in c.MODELS:
                        selected=sorted([m for m in mapping if (m['suite'],m['answer_family'],m['judge_family'])==(suite,family,judge)],key=lambda m:m['question_key'])
                        check(f'exact 6/6 {suite}/{family}/{judge}',sum(m['order'][0]=='grounded' for m in selected)==6 and len(selected)==12)
                        sigs.append(tuple(m['order'][0] for m in selected))
                        for m in selected:
                            for arm in c.ARMS:
                                check('A/B mapping roundtrip',m['order'][('A','B').index(('A','B')[m['order'].index(arm)])]==arm)
                    check(f'distinct order {suite}/{family}',len(set(sigs))==3)
            protocol=base/'PROTOCOL.md'; original=protocol.read_bytes(); protocol.write_bytes(original+b'changed')
            rejects('source drift invalidates manifest',integrity.verify); protocol.write_bytes(original)
            extra=root/'frozen/unexpected.txt'; extra.write_text('extra')
            rejects('extra frozen file rejected',integrity.verify); extra.unlink()
            review_path=root/'results/reviewer.json'
            c.write(review_path,{'passed':True,'manifest_sha256':frozen['manifest_sha256'],
                               'checks':dict.fromkeys(('harness','fixture_provenance','reference_coverage','wiki_coverage','prompt_equivalence','model_settings'),True)})
            approval={'approved':True,'approved_by':'offline-parent','manifest_sha256':frozen['manifest_sha256'],
                      'context_capacity_acknowledged':True,'independent_review':{'passed':True,'reviewer':'offline-independent',
                      'path':str(review_path),'sha256':c.digest(review_path)}}
            c.write(root/'results/smoke.json',{'passed':True,'synthetic':True,'script_files':manifest['script_files'],
                                            'manifest_sha256':frozen['manifest_sha256']})
            c.write(root/'APPROVED.json',approval)
            check('exact manifest review approval accepted',bool(integrity.approved()))
            # Exercise the real outer adapter with a fake Popen. No child process or helper runs.
            class FakeProcess:
                outcomes=[]
                calls=0
                def __init__(self,*args,**kwargs):
                    type(self).calls+=1
                    self.returncode,self.output,self.stderr=type(self).outcomes.pop(0)
                def communicate(self,*args,**kwargs):
                    return self.output,self.stderr
            sol_output='\n'.join(json.dumps(e) for e in events('sol','offline transport stub'))+'\n'
            FakeProcess.outcomes=[(1,'','HTTP 503 network unavailable'),(0,sol_output,'')]
            with patch.object(adapters.subprocess,'Popen',FakeProcess),patch.object(adapters.time,'sleep'):
                got=adapters.invoke('offline-transport','sol','synthetic prompt')
            check('bounded transport retry retains both attempts',got['status']=='ok' and len(got['attempts'])==2 and FakeProcess.calls==2)
            FakeProcess.calls=0; FakeProcess.outcomes=[(1,'','HTTP 503 network unavailable')]*2
            with patch.object(adapters.subprocess,'Popen',FakeProcess),patch.object(adapters.time,'sleep'):
                got=adapters.invoke('offline-transport-failure','sol','synthetic prompt')
            check('transport retry stops after two attempts',got['status']=='failed' and len(got['attempts'])==2 and FakeProcess.calls==2)
            FakeProcess.calls=0; FakeProcess.outcomes=[(0,'{}\n','')]
            with patch.object(adapters.subprocess,'Popen',FakeProcess),patch.object(adapters.time,'sleep'):
                got=adapters.invoke('offline-content-failure','sol','synthetic prompt')
            check('content failure retained without retry',got['status']=='failed' and len(got['attempts'])==1 and FakeProcess.calls==1)
            for error in ('HTTP 429','HTTP 429 {"retryDelay":"90s"}','HTTP 429 {"retryDelay":"500s"}'):
                FakeProcess.calls=0
                output='\n'.join(json.dumps(e) for e in events('gemini','offline complete'))+'\n'
                FakeProcess.outcomes=[(1,'',error),(0,output,'')]
                unit='offline-gemini-'+str(int(adapters.retry_delay('gemini',error)))
                with patch.object(adapters.subprocess,'Popen',FakeProcess),patch.object(adapters.time,'sleep') as sleep:
                    got=adapters.invoke(unit,'gemini','synthetic prompt')
                check('Gemini delayed transport attempts retained '+unit,got['status']=='ok' and len(got['attempts'])==2 and got['attempts'][0]['retry_delay_seconds']==adapters.retry_delay('gemini',error))
                sleep.assert_called_once_with(adapters.retry_delay('gemini',error))
            for family in c.MODELS:
                bad=events(family,'network timeout text with incomplete termination')
                if family=='sol':
                    bad.pop()
                elif family=='opus':
                    bad[-1]['stop_reason']='max_tokens'
                else:
                    bad[0]['candidates'][0]['finishReason']='SAFETY'
                FakeProcess.calls=0; FakeProcess.outcomes=[(0,'\n'.join(json.dumps(e) for e in bad),'')]
                with patch.object(adapters.subprocess,'Popen',FakeProcess),patch.object(adapters.time,'sleep') as sleep:
                    got=adapters.invoke('offline-terminal-failure-'+family,family,'synthetic prompt')
                check('terminal content failures never retry '+family,got['status']=='failed' and len(got['attempts'])==1 and FakeProcess.calls==1 and not sleep.called)
            bad={**approval,'manifest_sha256':'wrong'}; c.write(root/'APPROVED.json',bad)
            rejects('wrong manifest approval rejected',integrity.approved)
            c.write(root/'APPROVED.json',{**approval,'model_context_limits':{'sol':1}})
            rejects('capacity estimate fails without shrinking',integrity.approved)
            opus_estimates=[e['estimated_input_tokens'] for e in manifest['prompt_estimates'] if e['family']=='opus']
            opus_limit=max(opus_estimates)+8191
            c.write(root/'APPROVED.json',{**approval,'model_context_limits':{'opus':opus_limit}})
            rejects('Opus family estimate gates capacity',integrity.approved)
            c.write(root/'APPROVED.json',approval)
            import eval as runner
            active=dict.fromkeys(c.MODELS,0); peak=active.copy(); seen=[]; guard=threading.Lock()
            def concurrent_stub(task):
                family,index=task
                with guard:
                    active[family]+=1; peak[family]=max(peak[family],active[family]); seen.append(index)
                time.sleep(0.01)
                with guard:
                    active[family]-=1
            tasks=[('gemini',0),('sol',1),('sol',2),('gemini',3),('opus',4),('gemini',5)]
            runner.run_tasks(concurrent_stub,tasks,lambda task:task[0])
            check('per-family concurrency serializes Gemini while other families overlap',peak['gemini']==1 and peak['sol']==2 and sorted(seen)==list(range(6)))
            def stub(unit,family,prompt):
                if '\nPairs:\n' in prompt:
                    pairs=json.loads(prompt.split('\nPairs:\n',1)[1]); suite='newadvice12' if 'Evaluate decision_quality' in prompt else 'diagnostic12'
                    answer=json.dumps({'judgments':[valid_vote(p['id'],suite) for p in pairs]})
                else:
                    answer=' '.join(['offline-stub']*180)
                tokens=123
                if '\nPairs:\n' not in prompt and '\nSupplied context:\n' in prompt:
                    added=c.CONTEXT_PREFIX+prompt.split(c.CONTEXT_PREFIX,1)[1]
                    delta=c.estimate_tokens(added,family)
                    tokens+=delta
                    if unit.startswith('diagnostic12--q00--sol--'):
                        tokens=123
                    elif unit.startswith('diagnostic12--q01--sol--'):
                        tokens=123+3*delta
                    elif unit.startswith('diagnostic12--q02--sol--'):
                        tokens=None
                output='\n'.join(json.dumps(e) for e in events(family,answer,tokens))+'\n'
                logbase=root/'logs'/f'{unit}--attempt1'
                c.immutable(logbase.with_suffix('.stdout.jsonl'),output)
                c.immutable(logbase.with_suffix('.stderr.txt'),'')
                return {'status':'failed' if unit=='diagnostic12--q03--sol--grounded' else 'ok',**adapters.parse_output(family,output),'requested_model':c.MODELS[family],
                        'effort':c.EFFORT[family],'prompt_sha256':c.sha(prompt),'error':'',
                        'attempts':[{'attempt':1,'stdout_sha256':c.sha(output),'stderr_sha256':c.sha('')}],
                        'finished':'offline-stub'}
            import eval as runner
            with patch.object(adapters,'invoke',stub), contextlib.redirect_stdout(io.StringIO()):
                runner.answers(); runner.make_pairs(); runner.judge(); report.report()
            check('complete offline pipeline 144/216',len(c.rows('responses'))==144 and len(c.rows('judgments'))==216)
            validation=c.read(root/'results/validation.json')
            check('end-to-end artifact validation',validation['passed'])
            check('all usage extracted from synthetic provider logs',all(r['actual_input_tokens']==adapters.parse_output(r['family'],(root/'logs'/f"{r['id']}--attempt1.stdout.jsonl").read_text())['actual_input_tokens'] for r in c.rows('responses')))
            pairs=c.read(root/'results/pairs.json')
            blocked=[p for p in pairs if not p['eligible']]
            check('context checks exclude pairs for all judges with denominator preserved',len(pairs)==216 and len(blocked)==12 and sum(j['status']=='blocked' for j in c.rows('judgments'))==12)
            check('both inconsistent delta directions retained',sum('context_usage_inconsistent' in p['context_usage']['flags'] for p in blocked)==6)
            summary=c.read(root/'results/summary.json')
            check('primary excludes same family in each suite',all(summary['suites'][s]['primary_votes']['valid_ratings']==(64 if s=='diagnostic12' else 72) and summary['suites'][s]['same_family_votes']['valid_ratings']==(32 if s=='diagnostic12' else 36) for s in c.SUITES))
            check('ineligible slots remain missing in primary consensus',summary['suites']['diagnostic12']['primary_by_answer']['sol']['consensus_counts']['missing']==4)
            check('usage diagnostics preserve actual counts and all 72 pairs',len(summary['context_usage_checks'])==72 and sum('context_usage_inconsistent' in u['flags'] for u in summary['context_usage_checks'])==2)
            check('all practical answers exported for blinded factual review',len(c.read(root/'results/review-export/practical-all-answers.json'))==72)
            check('wrong votes and all factual objections preserved',len(c.read(root/'results/review-export/original-factual-objections.json'))==204 and all(j['verdict']['winner']=='A' for j in c.rows('judgments') if j['status']=='ok'))
            for b in c.read(root/'results/judge-batches.json'):
                text=(root/'results/judge-prompts'/f"{b['id']}.txt").read_text()
                payload=json.loads(text.split('\nPairs:\n',1)[1])
                check('no family/arm in judge payload '+b['id'],all(set(p)==({'id','question','A','B'} if b['suite']=='newadvice12' else {'id','question','A','B','reference'}) for p in payload) and not any(x in text for x in ('--sol','--opus','--gemini','"grounded"','"raw"')))
            before={p:c.digest(p) for p in (root/'judgments').glob('*.json')}
            with patch.object(adapters,'invoke',side_effect=AssertionError('Must not rerun completed calls')),contextlib.redirect_stdout(io.StringIO()):
                runner.answers(); runner.make_pairs(); runner.judge()
            check('resume never regenerates completed or wrong votes',before=={p:c.digest(p) for p in (root/'judgments').glob('*.json')})
            check('manifest still valid after derived phases',bool(integrity.verify()) and bool(integrity.verify_pairs()))
            inner_count=len(validation['checks'])
    finally:
        # Only generated synthetic files inside this task's run/ are removed.
        for p in sandbox.rglob('*'):
            if p.is_file():
                p.chmod(0o600)
        shutil.rmtree(sandbox)
    # Mechanically check the real wiki contexts if prepare has produced them.
    real_inventory=original_root/'frozen/wiki-inventory.json'
    if real_inventory.exists():
        for vault,ctx in c.read(real_inventory).items():
            data=(original_root/'frozen/context'/f'{vault}.txt').read_bytes()
            live=sorted(p.relative_to(c.VAULTS/vault/'wiki').as_posix() for p in (c.VAULTS/vault/'wiki').rglob('*') if p.is_file())
            check('real complete wiki file coverage '+vault,live==[p['relative_path'] for p in ctx['pages']])
            check('real context hash '+vault,c.sha(data)==ctx['sha256'])
            for page in ctx['pages']:
                start=page['context_byte_offset']; segment=data[start:start+page['bytes']]
                check('real page unchanged '+vault+'/'+page['relative_path'],c.sha(segment)==page['sha256']==c.digest(page['path']) and segment==(original_root/'frozen/wiki'/vault/page['relative_path']).read_bytes())
    if (original_root/'frozen/manifest.json').exists():
        integrity.verify()
    result={'passed':True,'provider_calls':0,'credential_loader_calls':0,'checks':checks,
            'checks_count':len(checks),'synthetic_pipeline_validation_checks':inner_count,
            'script_files':integrity.local_inventory(original_root/'scripts'),
            'manifest_sha256':c.digest(original_root/'frozen/manifest.json') if (original_root/'frozen/manifest.json').exists() else None,
            'real_fixtures':'verified by prepare/manifest' if (original_root/'frozen/manifest.json').exists() else 'pending',
            'real_contexts_checked':real_inventory.exists()}
    c.write(original_root/'results/smoke.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('checks','script_files')},indent=2))

if __name__=='__main__':
    main()

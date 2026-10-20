"""Freeze complete wiki contexts first, then independent audited fixtures and protocol."""
from __future__ import annotations
import json
import math
from pathlib import Path
import re
import common as c
import adapters
import integrity

def freeze_contexts():
    contexts={}
    for vault in ('hormozi','yc'):
        wiki=c.VAULTS/vault/'wiki'
        pages=[]; blocks=[]; offset=0
        sources=sorted((p for p in wiki.rglob('*') if p.is_file()),key=lambda p:p.relative_to(wiki).as_posix())
        if not sources:
            raise ValueError('Wiki is empty: '+str(wiki))
        for p in sources:
            if p.is_symlink():
                raise ValueError('Wiki symlink requires explicit review: '+str(p))
            data=p.read_bytes(); data.decode('utf-8')
            rel=p.relative_to(wiki).as_posix()
            header=f'\n=== wiki/{rel} | sha256={c.sha(data)} | bytes={len(data)} ===\n'.encode()
            blocks.append(header); offset+=len(header)
            pages.append({'path':str(p),'relative_path':rel,'sha256':c.sha(data),'included_sha256':c.sha(data),
                          'bytes':len(data),'context_byte_offset':offset,'truncated':False})
            blocks.extend([data,b'\n']); offset+=len(data)+1
            c.immutable(c.ROOT/'frozen/wiki'/vault/rel,data)
        context=b''.join(blocks)
        c.immutable(c.ROOT/'frozen/context'/f'{vault}.txt',context)
        contexts[vault]={'sha256':c.sha(context),'bytes':len(context),'source_bytes':sum(p['bytes'] for p in pages),
                         'characters':len(context.decode('utf-8')),
                         'estimated_tokens_by_family':{f:c.estimate_tokens(context.decode('utf-8'),f) for f in c.MODELS},
                         'utf8_bytes_conservative_token_bound':len(context),'pages':pages,
                         'selection':'Every file below wiki, in POSIX relative-path lexical order; unchanged bytes; no question or gold access.'}
    c.immutable(c.ROOT/'frozen/wiki-inventory.json',c.encoded(contexts))
    return contexts

def raw_ref(ref,vault):
    if not isinstance(ref,dict) or not isinstance(ref.get('path'),str):
        raise ValueError('Each source_ref needs path and sha256')
    path=Path(ref['path'])
    if not path.is_absolute():
        path=c.VAULTS/vault/path
    path=path.resolve()
    if not path.is_relative_to((c.VAULTS/vault/'raw').resolve()) or not path.is_file():
        raise ValueError('Fixture sources must be existing routed raw documents: '+str(path))
    if ref.get('sha256')!=c.digest(path):
        raise ValueError('Raw source hash mismatch: '+str(path))
    return {'path':str(path),'sha256':ref['sha256']}

def load_fixtures():
    questions=[]; references={}; sources=[]
    folder=c.BASE/'fixtures'
    names=['diagnostic-questions.json','diagnostic-reference.json','advice-questions.json','advice-evidence.json','source-inventory.json']
    missing=[name for name in names if not (folder/name).exists()]
    audit=folder/'AUDIT.md'
    if missing or not audit.exists():
        return None,['Missing fixture: '+name for name in missing]+([] if audit.exists() else ['Raw-only author AUDIT.md is not available'])
    packets={'diagnostic12':c.read(folder/'diagnostic-reference.json')['items'],
             'newadvice12':c.read(folder/'advice-evidence.json')['cases']}
    for suite,filename in [('diagnostic12','diagnostic-questions.json'),('newadvice12','advice-questions.json')]:
        items=c.read(folder/filename)
        if not isinstance(items,list) or len(items)!=12:
            raise ValueError('Each suite needs exactly 12 standalone questions')
        refs={r['id']:r for r in packets[suite]}
        if len(refs)!=12 or set(refs)!={q['id'] for q in items}:
            raise ValueError('Reference/evidence coverage differs from question IDs: '+suite)
        for q in items:
            ident=c.safe_id(q.get('id'))
            vault=q.get('vault')
            if vault not in ('hormozi','yc') or not isinstance(q.get('question'),str) or not q['question'].strip():
                raise ValueError('Question needs routed vault and nonempty question')
            packet=refs[ident]
            if packet.get('vault')!=vault or (suite=='diagnostic12' and packet.get('question')!=q['question']):
                raise ValueError('Question and evidence packet differ: '+ident)
            evidence=packet.get('evidence' if suite=='diagnostic12' else 'source_support')
            if not isinstance(evidence,list) or not evidence:
                raise ValueError('Complete evidence packet missing: '+ident)
            for ev in evidence:
                sources.append(raw_ref({'path':ev['source_path'],'sha256':ev['source_sha256']},vault))
                source=Path(ev['source_path'])
                if not source.is_absolute():
                    source=c.VAULTS/vault/source
                text=source.read_text(encoding='utf-8')
                parts=text.split('\n---\n',1)
                body=parts[1] if len(parts)==2 else text
                quote=ev.get('quote')
                if not isinstance(quote,str) or not quote.strip():
                    raise ValueError('Nonempty evidence quote required: '+ident)
                timestamp=ev.get('timestamp')
                if timestamp:
                    segment=[]
                    for line in body.splitlines():
                        match=re.match(r'^\[(\d+(?::\d+){1,2})\]\s?(.*)$',line)
                        if match and match.group(1)==timestamp:
                            segment.append(match.group(2))
                    body=' '.join(segment)
                if ' '.join(quote.split()) not in ' '.join(body.split()):
                    raise ValueError('Evidence quote/timestamp not found in hashed raw source: '+ident)
            public={'suite':suite,'id':ident,'vault':vault,'question':q['question']}
            questions.append(public)
            if suite=='diagnostic12':
                references[c.qkey(public)]=packet
            elif re.search(r'\b(hormozi|graham|seibel|caldwell|altman|livingston|y combinator|acquisition\.com|skool)\b',q['question'],re.I):
                raise ValueError('Practical scenario names an expert or expert organisation: '+ident)
            # Keep every source author's original field in the frozen fixture, but never expose
            # advice gold, provenance, or raw-source metadata to answer/practical judge prompts.
    if len({c.qkey(q) for q in questions})!=24:
        raise ValueError('Question IDs must be unique within each suite')
    inventory=c.read(folder/'source-inventory.json')
    for item in inventory['sources']:
        sources.append(raw_ref({'path':item['source_path'],'sha256':item['source_sha256']},item['vault']))
    # Include ancillary files and the author's verifier, preserving their relative paths.
    fixture_paths=sorted(p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    return {'questions':questions,'references':references,'sources':sources,'paths':fixture_paths+[audit]},[]

def prepare():
    if (c.ROOT/'frozen/manifest.json').exists():
        integrity.verify()
        c.progress('frozen_awaiting_independent_review_and_parent_approval')
        return {'status':'already_frozen','manifest_sha256':c.digest(c.ROOT/'frozen/manifest.json')}
    # This order is intentional: no questions, keys, raw text or prior outcomes influence context.
    contexts=freeze_contexts()
    fixture,issues=load_fixtures()
    if fixture is None:
        result={'status':'pending_fixtures','issues':issues,'context_frozen':True,'contexts':{
          v:{k:d[k] for k in ('source_bytes','bytes','estimated_tokens_by_family')} for v,d in contexts.items()},
          'answer_target':144,'judgment_unit_target':216,'provider_calls':0}
        c.write(c.ROOT/'results/preflight.json',result)
        c.progress('pending_fixtures')
        return result
    questions=fixture['questions']
    c.immutable(c.ROOT/'frozen/questions.json',c.encoded(questions))
    c.immutable(c.ROOT/'frozen/references.json',c.encoded(fixture['references']))
    protocol=c.BASE/'PROTOCOL.md'
    c.immutable(c.ROOT/'frozen/PROTOCOL.md',protocol.read_bytes())
    for path in fixture['paths']:
        rel=path.relative_to(c.BASE/'fixtures') if path.is_relative_to(c.BASE/'fixtures') else Path(path.name)
        c.immutable(c.ROOT/'frozen/fixtures'/rel,path.read_bytes())
    c.immutable(c.ROOT/'frozen/answer-instructions.json',c.encoded({'common':c.ANSWER_BASE,'suite':c.ANSWER_EXTRA,'context_prefix':c.CONTEXT_PREFIX,'context_trailer':c.CONTEXT_TRAILER}))
    c.immutable(c.ROOT/'frozen/judge-instructions.json',c.encoded({'common':c.JUDGE_BASE,'suite':c.JUDGE_EXTRA,'dimensions':c.DIMS}))
    c.immutable(c.ROOT/'frozen/aggregation.json',c.encoded(c.AGGREGATION))
    mapping=c.mappings(questions)
    c.immutable(c.ROOT/'frozen/mapping.json',c.encoded(mapping))
    c.immutable(c.ROOT/'frozen/batches.json',c.encoded(c.batches(mapping)))
    estimates=[]
    for q in questions:
        base=c.answer_prompt(q)
        for arm in c.ARMS:
            prompt=base if arm=='raw' else base+c.CONTEXT_PREFIX+(c.ROOT/'frozen/context'/f"{q['vault']}.txt").read_bytes().decode('utf-8')+c.CONTEXT_TRAILER
            path=c.ROOT/'frozen/prompts'/f'{c.qkey(q)}--{arm}.txt'
            c.immutable(path,prompt)
            for family in c.MODELS:
                estimates.append({'question_key':c.qkey(q),'family':family,'arm':arm,'prompt_sha256':c.sha(prompt),
                                  'prompt_bytes':len(prompt.encode()),'estimated_input_tokens':c.estimate_tokens(prompt,family),
                                  'chars_per_token':c.CHARS_PER_TOKEN[family],
                                  'expected_context_token_delta':c.estimate_tokens(prompt[len(base):],family) if arm=='grounded' else 0,
                                  'utf8_bytes_conservative_token_bound':len(prompt.encode()),
                                  'provider_context_limit_tokens':None,'limit_check':'Unknown provider capacity/tokenizer; parent acknowledgment required. No pack resizing.'})
    external={str(p):c.digest(p) for p in [protocol,c.HELPER,*fixture['paths']]}
    external.update({r['path']:r['sha256'] for r in fixture['sources']})
    external.update({p['path']:p['sha256'] for ctx in contexts.values() for p in ctx['pages']})
    manifest={'schema_version':2,'date':c.DATE,'created':c.now(),'models':c.MODELS,'effort':c.EFFORT,
              'commands':{f:adapters.command(f) for f in c.MODELS},'contexts':contexts,
              'counts':{'questions':24,'answers':144,'pairs':72,'judgment_units':216,'judge_calls_if_complete':72},
              'concurrency':3,'concurrency_by_family':c.CONCURRENCY,
              'context_token_estimation':{'chars_per_token_by_family':c.CHARS_PER_TOKEN,
                  'delta_min_ratio':c.CONTEXT_DELTA_MIN,'delta_max_ratio':c.CONTEXT_DELTA_MAX,
                  'policy':'Pre-run diagnostic only; inconsistent pairs are ineligible. Actual counts retained; no proof of attention.'},
              'judge_batch_size':3,'seeds':c.SEEDS,'prompt_estimates':estimates,
              'retry':'At most two outer attempts, only bounded transport failures; Gemini serial, 429 delay at least 60s, provider retryDelay capped at 120s. No content retries, repair, truncation or model changes. CLI internal retries remain in logs.',
              'isolation':'Native subscription CLIs for Sol/Opus, fresh empty cwd, no tools; Gemini existing loader/call only; no OpenAI API; credentials never copied.',
              'actual_input_tokens':'Pending provider logs; estimates are not actual usage.',
              'frozen_files':integrity.local_inventory(c.ROOT/'frozen'),
              'script_files':integrity.local_inventory(c.ROOT/'scripts'),
              'readme_sha256':c.digest(c.ROOT/'README.md'),
              'external_inputs':[{'path':p,'sha256':h} for p,h in sorted(external.items())]}
    c.immutable(c.ROOT/'frozen/manifest.json',c.encoded(manifest))
    c.immutable(c.ROOT/'frozen/MANIFEST.sha256',c.digest(c.ROOT/'frozen/manifest.json')+'\n')
    integrity.verify()
    result={'status':'frozen_awaiting_review','manifest_sha256':c.digest(c.ROOT/'frozen/manifest.json'),
            'issues':['Independent review and parent approval have not been supplied.',
                      'Actual provider token counts are pending; full-context capacity requires parent acknowledgment.'],
            'answer_target':144,'judgment_unit_target':216,'provider_calls':0}
    c.write(c.ROOT/'results/preflight.json',result)
    c.progress('frozen_awaiting_independent_review_and_parent_approval')
    return result

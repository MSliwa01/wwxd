"""No-tools CLI adapters adapted from the historical pilot; never called by prepare."""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
import common as c

def clean_env():
    env = dict(os.environ)
    for key in list(env):
        if any(t in key.upper() for t in ('API_KEY','AUTH_TOKEN','ACCESS_TOKEN')) or key.startswith(('T3_','CODEX_THREAD','CLAUDECODE','CLAUDE_CODE_SESSION')):
            env.pop(key,None)
    env['CLAUDE_CODE_DISABLE_AUTO_MEMORY']='1'
    return env

def command(family):
    if family == 'sol':
        cmd = ['codex','exec','--ignore-user-config','--ignore-rules','--ephemeral','--skip-git-repo-check','--sandbox','read-only','--model',c.MODELS[family],'--json','--color','never']
        for flag in ('shell_tool','unified_exec','multi_agent','apps','plugins','view_image','shell_snapshot','skill_search','skill_mcp_dependency_install','request_permissions_tool','sleep_tool'):
            cmd += ['--disable',flag]
        for config in ('model_reasoning_effort="high"','project_doc_max_bytes=0','web_search="disabled"','mcp_servers={}','developer_instructions="Answer the supplied task using only its text. Do not use tools or commands."'):
            cmd += ['-c',config]
        return cmd + ['-']
    if family == 'opus':
        return ['claude','-p','--model',c.MODELS[family],'--effort','high','--output-format','stream-json','--verbose','--tools','','--strict-mcp-config','--settings','{"disableAllHooks":true}','--safe-mode','--restricted','--disable-slash-commands','--no-session-persistence','--no-chrome','--permission-prompts','none']
    if family == 'gemini':
        return [sys.executable,str(c.ROOT/'scripts/gemini_once.py'),c.MODELS[family]]
    raise ValueError('Unknown family')

def parse_output(family, output):
    events=[]; violations=[]; answer=''; actual=[]; usage=[]; finish=[]; opus_results=[]
    for line in output.splitlines():
        try:
            e=json.loads(line)
        except ValueError:
            continue
        if not isinstance(e,dict):
            continue
        events.append(e)
        item=e.get('item',{})
        if not isinstance(item,dict):
            raise ValueError('Malformed provider item')
        kinds=[str(e.get('type','')),str(e.get('subtype','')),str(item.get('type',''))]
        if any(marker in kind.lower() for kind in kinds for marker in ('compact','context_reduc','context_trunc')):
            raise ValueError('Context reduction event: '+repr(kinds))
        if family=='sol':
            item=e.get('item',{}); typ=item.get('type','')
            if ('item' in e or str(e.get('type','')).startswith('item.')) and typ not in ('reasoning','agent_message'):
                violations.append(typ or 'missing_item_type')
            if e.get('type')=='item.completed' and typ=='agent_message':
                answer=item.get('text','')
            if e.get('type')=='turn.completed':
                usage.append(e.get('usage',{}))
                finish.append('turn.completed')
                finish.extend(e[key] for key in ('finish_reason','stop_reason','status') if e.get(key))
            if e.get('type')=='item.completed' and typ=='agent_message':
                finish.extend(item[key] for key in ('finish_reason','stop_reason','status') if item.get(key))
            if e.get('type')=='turn.failed':
                raise ValueError('Provider turn failed: '+str(e.get('error','')))
        elif family=='opus':
            if e.get('type')=='assistant':
                msg=e.get('message',{}); actual.append(msg.get('model',''))
                if msg.get('usage'):
                    usage.append(msg['usage'])
                for block in msg.get('content',[]):
                    if block.get('type')=='tool_use':
                        violations.append(block.get('name','tool_use'))
            if e.get('type')=='system' and e.get('subtype')=='init' and e.get('tools'):
                violations.append('nonempty_tool_inventory')
            if e.get('type')=='result':
                answer=e.get('result','')
                if e.get('usage'):
                    # The result is the provider's aggregate; do not sum streaming duplicates.
                    usage=[e['usage']]
                opus_results.append(e)
                finish.extend(e[key] for key in ('subtype','stop_reason','terminal_reason') if e.get(key))
                if e.get('is_error'):
                    raise ValueError('Provider error: '+str(e.get('result') or e.get('errors')))
        elif family=='gemini':
            actual.append(e.get('modelVersion',''))
            if e.get('error'):
                raise ValueError('Provider error: '+str(e['error']))
            if e.get('usageMetadata'):
                usage.append(e['usageMetadata'])
            candidates=e.get('candidates',[])
            if candidates:
                parts=candidates[0].get('content',{}).get('parts',[])
                finish.append(candidates[0].get('finishReason'))
                for part in parts:
                    if 'functionCall' in part:
                        violations.append('functionCall')
                answer=''.join(p.get('text','') for p in parts if not p.get('thought'))
        else:
            raise ValueError('Unknown family')
    if violations:
        raise ValueError('Tool isolation violation: '+repr(violations))
    if not isinstance(answer,str) or not answer.strip():
        raise ValueError('No final answer in provider events')
    if family=='sol' and 'turn.completed' not in finish:
        raise ValueError('Missing successful terminal turn metadata')
    if family=='opus' and (not opus_results or any(
            e.get('subtype')!='success' or e.get('stop_reason')!='end_turn' or
            e.get('terminal_reason') not in (None,'completed','end_turn') for e in opus_results)):
        raise ValueError('Opus requires successful end_turn termination: '+repr(finish))
    if family=='gemini' and (not finish or any(reason!='STOP' for reason in finish)):
        raise ValueError('Gemini requires STOP termination: '+repr(finish))
    if any(str(reason).lower() in ('max_tokens','length','max_output_tokens','incomplete','error_max_turns','error_max_budget_usd') for reason in finish):
        raise ValueError('Truncated or incomplete provider response: '+repr(finish))
    if family in ('opus','gemini') and any(model and model!=c.MODELS[family] for model in actual):
        raise ValueError('Actual model mismatch: '+repr(actual))
    tokens=None
    if usage:
        u=usage[-1]
        if family=='sol':
            tokens=u.get('input_tokens')
        elif family=='opus':
            tokens=sum(u.get(k,0) for k in ('input_tokens','cache_read_input_tokens','cache_creation_input_tokens')) if 'input_tokens' in u else None
        else:
            tokens=u.get('promptTokenCount')
    return {'answer':answer,'observed_models':sorted(set(filter(None,actual))),
            'usage_events':usage,'actual_input_tokens':tokens,'finish_reasons':finish,'event_count':len(events),
            'serving_model_attested':bool(actual) and family!='sol'}

def transport_failure(error):
    # Context/size, auth, schema, tool and content failures never cause retry.
    if re.search(r'context|too (?:long|large)|token limit|maximum.*tokens|auth|credential|permission|schema|isolation|model mismatch|No final answer|SAFETY|RECITATION|truncat|incomplete|end_turn|STOP termination',error,re.I):
        return False
    return bool(re.search(r'\b(?:429|500|502|503|504)\b|timed?\s*out|timeout|connection reset|connection refused|transport|network|stream disconnected|overloaded',error,re.I))

def retry_delay(family, error):
    if family != 'gemini':
        return 10
    match=re.search(r"[\"']retryDelay[\"']\s*:\s*[\"'](\d+(?:\.\d+)?)s[\"']",error)
    hint=float(match.group(1)) if match else 0
    return min(120,max(60 if re.search(r'\b429\b',error) else 10,hint))

def invoke(unit, family, prompt):
    # Defense in depth even if a caller bypasses eval.py.
    import integrity
    integrity.approved()
    c.safe_id(unit,max_length=200)
    approval=c.read(c.ROOT/'APPROVED.json')
    limit=approval.get('model_context_limits',{}).get(family)
    estimate=c.estimate_tokens(prompt,family)
    if limit and estimate+8192>limit:
        return {'status':'failed','answer':'','requested_model':c.MODELS[family],'effort':c.EFFORT[family],
                'prompt_sha256':c.sha(prompt),'attempts':[],'estimated_input_tokens':estimate,'chars_per_token':c.CHARS_PER_TOKEN[family],
                'error':'Predicted context exceeds acknowledged capacity. No provider call, model change or context resizing.',
                'finished':c.now()}
    attempts=[]; parsed={}; status='failed'
    for attempt in (1,2):
        work=c.ROOT/'logs/work'/f'{unit}--attempt{attempt}'
        work.mkdir(parents=True,exist_ok=False)
        start=time.monotonic(); output=''; stderr=''; error=''; code=None; retryable=False
        try:
            proc=subprocess.Popen(command(family),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                                  text=True,encoding='utf-8',cwd=work,env=clean_env(),start_new_session=True)
            try:
                output,stderr=proc.communicate(prompt,timeout=600)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid,signal.SIGTERM)
                try:
                    output,stderr=proc.communicate(timeout=15)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid,signal.SIGKILL)
                    output,stderr=proc.communicate(timeout=10)
                retryable=True
                raise TimeoutError('Invocation timed out after 600 seconds')
            code=proc.returncode
            if code:
                # Full streams are retained below. Error summaries cannot expose credentials.
                detail=stderr or output
                retryable=transport_failure(detail)
                raise RuntimeError(f'CLI exited {code}: '+detail[-3000:])
            parsed=parse_output(family,output); status='ok'
        except (ConnectionError, OSError) as exc:
            retryable=transport_failure(str(exc))
            error=c.redact(f'{type(exc).__name__}: {exc}')
        except Exception as exc:
            error=c.redact(f'{type(exc).__name__}: {exc}')
        logbase=c.ROOT/'logs'/f'{unit}--attempt{attempt}'
        output=c.redact(output); stderr=c.redact(stderr)
        c.immutable(logbase.with_suffix('.stdout.jsonl'),output)
        c.immutable(logbase.with_suffix('.stderr.txt'),stderr)
        delay=retry_delay(family,stderr or output or error) if status!='ok' and attempt<2 and retryable else None
        record={'attempt':attempt,'seconds':round(time.monotonic()-start,3),'exit_code':code,
                'error':error,'retry_delay_seconds':delay,'stdout_sha256':c.sha(output),'stderr_sha256':c.sha(stderr)}
        attempts.append(record)
        # Journal every completed attempt before a possible transport retry or process crash.
        c.immutable(logbase.with_suffix('.attempt.json'),c.encoded(record))
        if delay is None:
            break
        time.sleep(delay)
    return {'status':status,**parsed,'answer':parsed.get('answer',''), 'requested_model':c.MODELS[family],
            'effort':c.EFFORT[family],'command':command(family),'prompt_sha256':c.sha(prompt),
            'estimated_input_tokens':estimate,'chars_per_token':c.CHARS_PER_TOKEN[family],
            'attempts':attempts,'error':attempts[-1]['error'],'finished':c.now()}

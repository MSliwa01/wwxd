#!/usr/bin/env python3
"""Use only the existing helper's loader and request function; no rotation-state writes."""
import importlib.util
import json
import sys
import urllib.error
from pathlib import Path

def main():
    import common as c
    import integrity
    integrity.approved()
    if len(sys.argv)!=2 or sys.argv[1]!=c.MODELS['gemini']:
        raise ValueError('Exact frozen Gemini model required')
    spec=importlib.util.spec_from_file_location('existing_gemini',c.HELPER)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.HERE=c.HELPER.parent
    keys=mod.load_keys()
    if not keys:
        raise ValueError('Existing Gemini loader returned no credentials')
    index=sum(Path.cwd().name.encode()) % len(keys)
    body={'contents':[{'role':'user','parts':[{'text':sys.stdin.read()}]}]}
    try:
        response=mod.call(f'models/{sys.argv[1]}:generateContent',keys[index],body,timeout=300)
        print(c.redact(json.dumps(response,ensure_ascii=False)))
    except urllib.error.HTTPError as exc:
        # Avoid helper URLs, header dumps, or credential values in exception representations.
        print(c.redact(f'HTTP {exc.code}: '+exc.read().decode(errors='replace')),file=sys.stderr)
        return 1
    except Exception as exc:
        print('Existing Gemini helper failed: '+type(exc).__name__,file=sys.stderr)
        return 1
    return 0

if __name__=='__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""Immutable input inventory, derived-pair seal, and parent-owned approval gate."""
from __future__ import annotations
import argparse
from pathlib import Path
import common as c

def local_inventory(folder):
    return {p.relative_to(c.ROOT).as_posix():c.digest(p) for p in sorted(folder.rglob('*'))
            if p.is_file() and '__pycache__' not in p.parts and p.name not in ('manifest.json','MANIFEST.sha256')}

def verify():
    path=c.ROOT/'frozen/manifest.json'
    if not path.exists():
        raise ValueError('Final manifest absent. Complete prepare after fixtures are ready.')
    manifest=c.read(path)
    anchor=(c.ROOT/'frozen/MANIFEST.sha256').read_text().strip()
    if c.digest(path)!=anchor:
        raise ValueError('Manifest hash anchor mismatch')
    actual=local_inventory(c.ROOT/'frozen')
    if actual!=manifest['frozen_files']:
        raise ValueError('Frozen inventory missing, changed, or contains unexpected files')
    scripts=local_inventory(c.ROOT/'scripts')
    if scripts!=manifest['script_files']:
        raise ValueError('Harness scripts changed since freeze')
    if c.digest(c.ROOT/'README.md')!=manifest['readme_sha256']:
        raise ValueError('Harness instructions changed since freeze')
    for item in manifest['external_inputs']:
        if c.digest(item['path'])!=item['sha256']:
            raise ValueError('External input changed: '+item['path'])
    for vault,inventory in manifest['contexts'].items():
        wiki=c.VAULTS/vault/'wiki'
        live=sorted(p.relative_to(wiki).as_posix() for p in wiki.rglob('*') if p.is_file())
        if live!=[p['relative_path'] for p in inventory['pages']]:
            raise ValueError('Wiki file set changed: '+vault)
    return manifest

def approved():
    manifest=verify()
    path=c.ROOT/'APPROVED.json'
    if not path.exists():
        raise PermissionError('Parent approval absent: run/APPROVED.json')
    obj=c.read(path)
    if obj.get('approved') is not True or obj.get('manifest_sha256')!=c.digest(c.ROOT/'frozen/manifest.json'):
        raise PermissionError('Parent approval must match the exact manifest hash')
    if not isinstance(obj.get('approved_by'),str) or not obj['approved_by'].strip():
        raise PermissionError('Missing parent approver identity')
    review=obj.get('independent_review',{})
    if review.get('passed') is not True or not review.get('reviewer') or review['reviewer']==obj['approved_by']:
        raise PermissionError('Independent reviewer must be identified and distinct from approver')
    review_path=Path(review.get('path','')).resolve()
    if not review_path.is_relative_to((c.ROOT/'results').resolve()) or not review_path.is_file():
        raise PermissionError('Review artifact must exist under run/results')
    if c.digest(review_path)!=review.get('sha256'):
        raise PermissionError('Independent review artifact hash mismatch')
    report=c.read(review_path)
    if report.get('manifest_sha256')!=obj['manifest_sha256'] or report.get('passed') is not True:
        raise PermissionError('Review must explicitly pass this manifest')
    required=('harness','fixture_provenance','reference_coverage','wiki_coverage','prompt_equivalence','model_settings')
    if any(report.get('checks',{}).get(name) is not True for name in required):
        raise PermissionError('Independent review must explicitly verify harness, provenance, evidence coverage, context, prompts and model settings')
    if obj.get('context_capacity_acknowledged') is not True:
        raise PermissionError('Parent must acknowledge the full-context estimates and unknown tokenization/limits')
    if not (c.ROOT/'results/smoke.json').exists() or c.read(c.ROOT/'results/smoke.json').get('passed') is not True:
        raise PermissionError('Offline smoke checks must pass')
    smoke=c.read(c.ROOT/'results/smoke.json')
    if smoke.get('script_files')!=manifest['script_files'] or smoke.get('manifest_sha256')!=obj['manifest_sha256']:
        raise PermissionError('Offline smoke checks must cover the frozen scripts and exact final manifest')
    # Estimates never silently change packs or models. Optional documented capacities can reject a call.
    capacities=obj.get('model_context_limits',{})
    for family,limit in capacities.items():
        if family not in c.MODELS or type(limit) is not int or limit<=0:
            raise PermissionError('Invalid acknowledged model context capacity')
        if max(x['estimated_input_tokens'] for x in manifest['prompt_estimates'] if x['family']==family)+8192>limit:
            raise PermissionError('Full prompt estimate plus output allowance exceeds acknowledged capacity: '+family)
    return manifest

def verify_pairs():
    path=c.ROOT/'results/pairs-manifest.json'
    obj=c.read(path)
    if c.digest(path)!=(c.ROOT/'results/PAIRS.sha256').read_text().strip():
        raise ValueError('Pair manifest anchor mismatch')
    if obj['input_manifest_sha256']!=c.digest(c.ROOT/'frozen/manifest.json'):
        raise ValueError('Pairs refer to another input manifest')
    for name,digest in obj['files'].items():
        if c.digest(c.ROOT/name)!=digest:
            raise ValueError('Pair artifact changed: '+name)
    return obj

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('phase',choices=['verify','approval','pairs'])
    args=ap.parse_args()
    obj={'verify':verify,'approval':approved,'pairs':verify_pairs}[args.phase]()
    print(args.phase+': passed')

if __name__=='__main__':
    main()

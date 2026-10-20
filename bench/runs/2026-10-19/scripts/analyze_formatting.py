"""Separate post-hoc analysis of original judge outputs; never changes runner artifacts."""
from pathlib import Path
import collections
import json
import re
import sys

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE / 'run'
sys.path.insert(0, str(ROOT / 'scripts'))
import common as c
import integrity
import report


def unwrap(text):
    match = re.fullmatch(r'```(?:json)?[ \t]*\r?\n([\s\S]*)\r?\n```[ \t]*', text.strip())
    return (match.group(1), True) if match else (text, False)


def main():
    integrity.verify()
    integrity.verify_pairs()
    batches = c.read(ROOT / 'results/judge-batches.json')
    calls = c.rows('results/batch-calls')
    assert len(calls) == len(batches) == 72, 'Wait for every original terminal batch'
    assert {x['batch']['id'] for x in calls} == {x['id'] for x in batches}
    pairs = {(x['pair_id'], x['judge_family']): x for x in c.read(ROOT / 'results/pairs.json')}
    rows = []
    decoding = []
    for call in calls:
        batch = call['batch']
        decoded = {}
        error = ''
        changed = False
        if call['status'] == 'ok':
            payload, changed = unwrap(call['answer'])
            try:
                decoded = c.decode_votes(payload, batch['suite'], batch['eligible_pair_ids'])
            except (ValueError, TypeError, KeyError) as exc:
                error = f'{type(exc).__name__}: {exc}'
        decoding.append({'batch_id': batch['id'], 'outer_fence_removed': changed,
                         'call_status': call['status'], 'decode_error': error,
                         'valid_votes': sum(x['status'] == 'ok' for x in decoded.values())})
        for ident in batch['pair_ids']:
            pair = pairs[(ident, batch['judge_family'])]
            vote = decoded.get(ident)
            verdict = vote['verdict'] if vote else None
            blocked = ident in batch['blocked_pair_ids']
            status = 'blocked' if blocked else vote['status'] if vote else 'failed'
            winner = None
            if status == 'ok':
                winner = 'tie' if verdict['winner'] == 'tie' else pair['order'][('A', 'B').index(verdict['winner'])]
            rows.append({'id': f"{ident}--judge-{batch['judge_family']}", 'pair_id': ident,
                         'suite': pair['suite'], 'question_key': pair['question_key'],
                         'answer_family': pair['answer_family'], 'judge_family': pair['judge_family'],
                         'primary_eligible': pair['eligible'] and pair['answer_family'] != pair['judge_family'],
                         'order': pair['order'], 'batch_id': batch['id'], 'status': status,
                         'winner': winner, 'verdict': verdict, 'outer_fence_removed': changed,
                         'error': error or call.get('error', '')})
    original = c.rows('judgments')
    assert len(rows) == len(original) == 216
    byid = {x['id']: x for x in rows}
    for old in original:
        if old['status'] == 'ok':
            new = byid[old['id']]
            assert all(old[k] == new[k] for k in ('status', 'winner', 'verdict', 'order', 'primary_eligible'))
    questions = c.read(ROOT / 'frozen/questions.json')
    answers = c.rows('responses')
    result = {'analysis': 'post-hoc mechanical outer-fence removal; original strict result unchanged',
              'manifest_sha256': c.digest(ROOT / 'frozen/manifest.json'),
              'original_statuses': dict(collections.Counter(x['status'] for x in original)),
              'mechanical_statuses': dict(collections.Counter(x['status'] for x in rows)),
              'batches': decoding,
              'suites': {s: report.suite_summary(s, questions, answers, rows) for s in c.SUITES}}
    paths = [ROOT / 'frozen/manifest.json', ROOT / 'results/pairs-manifest.json',
             *sorted((ROOT / 'results/batch-calls').glob('*.json')),
             *sorted((ROOT / 'judgments').glob('*.json')),
             Path(__file__), BASE / 'post-run/FORMATTING-ANALYSIS.md']
    result['input_hashes'] = {str(p): c.digest(p) for p in paths}
    c.immutable(BASE / 'post-run/mechanical-votes.json', c.encoded(rows))
    c.immutable(BASE / 'post-run/mechanical-summary.json', c.encoded(result))
    print(json.dumps({k: result[k] for k in ('original_statuses', 'mechanical_statuses')}, indent=2))
    for suite, data in result['suites'].items():
        print(suite, {f: x['consensus_counts'] for f, x in data['primary_by_answer'].items()})


if __name__ == '__main__':
    main()

"""Record split-specific QA runs; answer correctness requires separate review."""
import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from app import ROOT, ask


def summarize(rows):
    positives = [r for r in rows if r['case']['category'] == 'answerable']
    negatives = [r for r in rows if r['case']['category'] != 'answerable']
    # Operational errors count as misses in the all-case retrieval denominator.
    recalls = []
    for row in positives:
        expected = set(row['case']['relevant'])
        found = {s['paragraph'] for s in row.get('result', {}).get('sources', [])
                 if s['source'] == 'intro.md'}
        recalls.append(len(expected & found) / len(expected))
    completed_negatives = [r for r in negatives if 'result' in r]
    return {
        'cases': len(rows), 'errors': sum('error' in r for r in rows),
        'answerable_cases': len(positives),
        'answerable_recall_at_3': sum(recalls) / len(recalls) if recalls else None,
        'completed_negative_cases': len(completed_negatives),
        'negative_cases_with_hits': sum(bool(r['result']['sources']) for r in completed_negatives),
        'semantic_quality_evaluated': False,
    }


def run(cases, generate, output):
    if not cases:
        raise ValueError('No cases selected')
    report = {'timestamp': datetime.now(timezone.utc).isoformat(),
              'generate': generate, 'model': os.environ.get('OLLAMA_MODEL') if generate else None,
              'corpus_sha256': hashlib.sha256((ROOT / 'docs/intro.md').read_bytes()).hexdigest(),
              'cases_sha256': hashlib.sha256(json.dumps(cases, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
              'results': []}
    output.parent.mkdir(parents=True, exist_ok=True)
    for case in cases:
        row = {'case': case}
        try:
            row['result'] = ask(case['question'], generate=generate)
        except Exception as error:
            row['error'] = f'{type(error).__name__}: {error}'
        report['results'].append(row)
        report['summary'] = summarize(report['results'])
        report['complete'] = len(report['results']) == len(cases)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f'{case["id"]}: {"error" if "error" in row else row["result"]["mode"]}', flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--split', choices=['dev', 'test'], required=True)
    parser.add_argument('--generate', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.generate and not os.environ.get('OLLAMA_MODEL'):
        parser.error('Set OLLAMA_MODEL for real generation')
    cases = json.loads((ROOT / 'evaluation/qa_cases.json').read_text(encoding='utf-8'))
    report = run([c for c in cases if c['split'] == args.split], args.generate, args.output)
    return int(report['summary']['errors'] > 0)


if __name__ == '__main__':
    raise SystemExit(main())

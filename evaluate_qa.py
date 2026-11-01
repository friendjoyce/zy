"""Record split-specific QA runs; answer correctness requires separate review."""
import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from app import ROOT, ask


def corpus_manifest(docs):
    docs = Path(docs)
    if not docs.is_dir():
        raise ValueError('Document directory must exist')
    return {p.relative_to(docs).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(docs.rglob('*'))
            if p.is_file() and p.suffix.lower() in {'.md', '.txt'}}


def summarize(rows):
    positives = [r for r in rows if r['case']['category'] == 'answerable']
    negatives = [r for r in rows if r['case']['category'] != 'answerable']
    # Operational errors count as misses in the all-case retrieval denominator.
    recalls = []
    ranks = []
    top_one = []
    for row in positives:
        expected = {(s['source'], s['paragraph']) if isinstance(s, dict) else ('intro.md', s)
                    for s in row['case']['relevant']}
        if not expected:
            raise ValueError('Answerable cases require relevant passages')
        found = {(s['source'], s['paragraph']) for s in row.get('result', {}).get('sources', [])}
        recalls.append(len(expected & found) / len(expected))
        ordered = [(s['source'], s['paragraph']) for s in row.get('result', {}).get('sources', [])][:3]
        ranks.append(next((1 / i for i, key in enumerate(ordered, 1) if key in expected), 0))
        top_one.append(int(bool(ordered) and ordered[0] in expected))
    completed_negatives = [r for r in negatives if 'result' in r]
    return {
        'cases': len(rows), 'errors': sum('error' in r for r in rows),
        'answerable_cases': len(positives),
        'answerable_recall_at_3': sum(recalls) / len(recalls) if recalls else None,
        'answerable_mrr_at_3': sum(ranks) / len(ranks) if ranks else None,
        'answerable_hit_at_1': sum(top_one) / len(top_one) if top_one else None,
        'completed_negative_cases': len(completed_negatives),
        'negative_cases_with_hits': sum(bool(r['result']['sources']) for r in completed_negatives),
        'semantic_quality_evaluated': False,
    }


def run(cases, generate, output, docs=None, rerank='none', chunking='paragraph'):
    if not cases:
        raise ValueError('No cases selected')
    docs = ROOT / 'docs' if docs is None else Path(docs)
    manifest = corpus_manifest(docs)
    report = {'timestamp': datetime.now(timezone.utc).isoformat(),
              'generate': generate, 'model': os.environ.get('OLLAMA_MODEL') if generate else None,
              'rerank': rerank, 'chunking': chunking,
              'corpus_manifest': manifest,
              'corpus_hash_format': 'sorted-json-path-to-sha256-v1',
              'corpus_sha256': hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest(),
              'cases_sha256': hashlib.sha256(json.dumps(cases, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
              'results': []}
    output.parent.mkdir(parents=True, exist_ok=True)
    for case in cases:
        row = {'case': case}
        try:
            row['result'] = ask(case['question'], generate=generate, docs=docs, rerank=rerank, chunking=chunking)
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
    parser.add_argument('--docs', type=Path, default=ROOT / 'docs')
    parser.add_argument('--cases', type=Path, default=ROOT / 'evaluation/qa_cases.json')
    parser.add_argument('--rerank', choices=['none', 'title'], default='none')
    parser.add_argument('--chunking', choices=['paragraph', 'heading_context'], default='paragraph')
    args = parser.parse_args()
    if args.generate and not os.environ.get('OLLAMA_MODEL'):
        parser.error('Set OLLAMA_MODEL for real generation')
    cases = json.loads(args.cases.read_text(encoding='utf-8'))
    report = run([c for c in cases if c['split'] == args.split], args.generate, args.output, args.docs, args.rerank, args.chunking)
    return int(report['summary']['errors'] > 0)


if __name__ == '__main__':
    raise SystemExit(main())

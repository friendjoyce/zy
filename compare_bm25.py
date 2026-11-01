"""Fixed-parameter TF-IDF/BM25 retrieval comparison; no generation."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from evaluate_qa import ROOT, corpus_manifest, summarize
from validate_cases import validate_cases
from search import search


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--split', choices=['dev', 'test'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = {'timestamp': datetime.now(timezone.utc).isoformat(), 'split': args.split,
              'configuration': {'k': 3, 'min_score': 0, 'rerank': 'none', 'chunking': 'paragraph',
                                'bm25_k1': 1.2, 'bm25_b': 0.75}, 'runs': []}
    for suite, docs, case_path in [
        ('intro', ROOT / 'docs', ROOT / 'evaluation/qa_cases.json'),
        ('multidoc', ROOT / 'evaluation/multidoc/docs', ROOT / 'evaluation/multidoc/cases.json')]:
        all_cases = json.loads(case_path.read_text(encoding='utf-8'))
        validate_cases(all_cases, docs)
        cases = [c for c in all_cases if c['split'] == args.split]
        for method in ['tfidf', 'bm25']:
            rows = []
            for case in cases:
                hits = search(docs, case['question'], 3, method=method)
                rows.append({'case': case, 'result': {'sources': [
                    {'score': score, 'source': source.replace('\\', '/'), 'paragraph': paragraph, 'text': text}
                    for score, source, paragraph, text in hits]}})
            report['runs'].append({'suite': suite, 'method': method,
                                   'corpus_manifest': corpus_manifest(docs),
                                   'cases_sha256': hashlib.sha256(case_path.read_bytes()).hexdigest(),
                                   'summary': summarize(rows), 'results': rows})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for run in report['runs']:
        print(run['suite'], run['method'], json.dumps(run['summary']))


if __name__ == '__main__':
    main()

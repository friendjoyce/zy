"""Compare paragraph and heading-context chunking with fixed title reranking."""
import argparse
import json
import re
from pathlib import Path
from evaluate_qa import ROOT, run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--split', choices=['dev', 'test'], required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    summaries = []
    for name, docs, case_path in [
        ('intro', ROOT / 'docs', ROOT / 'evaluation/qa_cases.json'),
        ('multidoc', ROOT / 'evaluation/multidoc/docs', ROOT / 'evaluation/multidoc/cases.json')]:
        cases = [c for c in json.loads(case_path.read_text(encoding='utf-8')) if c['split'] == args.split]
        for mode in ['paragraph', 'heading_context']:
            report = run(cases, False, args.output_dir / f'{name}_{args.split}_{mode}.json', docs, 'title', mode)
            sources = [s for row in report['results'] for s in row.get('result', {}).get('sources', [])]
            heading_only = sum(bool(s['text'].strip()) and all(
                re.match(r'^#{1,6}\s+', line) for line in s['text'].splitlines() if line.strip()) for s in sources)
            summaries.append({'suite': name, 'split': args.split, 'chunking': mode,
                              'rerank': 'title', 'retrieved_passages': len(sources),
                              'heading_only_passages': heading_only, **report['summary']})
    (args.output_dir / f'{args.split}_summary.json').write_text(json.dumps(summaries, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return int(any(r['errors'] for r in summaries))


if __name__ == '__main__':
    raise SystemExit(main())

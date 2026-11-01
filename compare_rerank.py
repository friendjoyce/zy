"""Compare fixed lexical ranking variants on existing synthetic dev/test suites."""
import argparse
import json
from pathlib import Path
from evaluate_qa import ROOT, run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--split', choices=['dev', 'test'], required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    summaries = []
    suites = [('intro', ROOT / 'docs', ROOT / 'evaluation/qa_cases.json'),
              ('multidoc', ROOT / 'evaluation/multidoc/docs', ROOT / 'evaluation/multidoc/cases.json')]
    for name, docs, case_file in suites:
        cases = [c for c in json.loads(case_file.read_text(encoding='utf-8')) if c['split'] == args.split]
        for mode in ['none', 'title']:
            report = run(cases, False, args.output_dir / f'{name}_{args.split}_{mode}.json', docs, mode)
            summaries.append({'suite': name, 'split': args.split, 'rerank': mode, **report['summary']})
    (args.output_dir / f'{args.split}_summary.json').write_text(
        json.dumps(summaries, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return int(any(row['errors'] for row in summaries))


if __name__ == '__main__':
    raise SystemExit(main())

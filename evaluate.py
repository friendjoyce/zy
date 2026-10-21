"""Evaluate passage retrieval on a small, fixed labelled dataset."""
import argparse
import json
from pathlib import Path
from search import search


def recall_at_k(retrieved, relevant, k):
    if k < 1 or not relevant:
        raise ValueError('k must be positive and relevant passages non-empty')
    return len(set(retrieved[:k]) & set(relevant)) / len(set(relevant))


def evaluate(docs, cases, k):
    if not cases or k < 1:
        raise ValueError('At least one case and positive k are required')
    rows = []
    for case in cases:
        relevant = [(item['source'], item['paragraph']) for item in case['relevant']]
        hits = search(docs, case['query'], k)
        retrieved = [(source.replace('\\', '/'), paragraph) for _, source, paragraph, _ in hits]
        rows.append({'query': case['query'], 'recall': recall_at_k(retrieved, relevant, k)})
    return {'k': k, 'queries': len(rows), 'mean_recall': sum(row['recall'] for row in rows) / len(rows), 'results': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--docs', default='docs')
    parser.add_argument('--cases', default='evaluation/cases.json')
    parser.add_argument('--top-k', type=int, default=3)
    args = parser.parse_args()
    try:
        cases = json.loads(Path(args.cases).read_text(encoding='utf-8-sig'))
        report = evaluate(args.docs, cases, args.top_k)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.error(str(error))
    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()

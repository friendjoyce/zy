import argparse
import json
import re
from pathlib import Path


def tokens(text):
    return set(re.findall(r'[a-z0-9_]+|[\u4e00-\u9fff]', text.lower()))


def search(root, query, limit=3):
    root = Path(root)
    if not root.is_dir() or limit < 1:
        raise ValueError('Document directory must exist and limit must be positive')
    query = tokens(query)
    hits = []
    for path in sorted(root.rglob('*')):
        if path.is_file() and path.suffix.lower() in {'.md', '.txt'}:
            for number, text in enumerate(re.split(r'\n\s*\n', path.read_text(encoding='utf-8')), 1):
                words = tokens(text)
                overlap = len(query & words)
                if overlap:
                    score = overlap / len(query | words)
                    hits.append((score, str(path.relative_to(root)), number, text.strip()))
    return sorted(hits, key=lambda hit: (-hit[0], hit[1], hit[2]))[:limit]


def main():
    parser = argparse.ArgumentParser(description='Source-linked local document search')
    parser.add_argument('query')
    parser.add_argument('--docs', default='docs')
    parser.add_argument('--top-k', type=int, default=3)
    parser.add_argument('--json', action='store_true', help='Emit structured results for other programs')
    args = parser.parse_args()
    try:
        hits = search(args.docs, args.query, args.top_k)
    except (ValueError, OSError, UnicodeError) as error:
        parser.error(str(error))
    if args.json:
        print(json.dumps([
            {'score': score, 'source': source.replace('\\', '/'),
             'paragraph': paragraph, 'text': text}
            for score, source, paragraph, text in hits
        ], ensure_ascii=True))
        return
    for score, source, paragraph, text in hits:
        print(f'[{source}, paragraph {paragraph}] score={score:.3f}\n{text}\n')
    if not hits:
        print('No matching passages.')


if __name__ == '__main__':
    main()

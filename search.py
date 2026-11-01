import argparse
import json
import re
from collections import Counter
from math import log, sqrt
from pathlib import Path
from functools import lru_cache


def tokens(text):
    return set(re.findall(r'[a-z0-9_]+|[\u4e00-\u9fff]', text.lower()))


@lru_cache(maxsize=128)
def cached_passages(path, modified, size):
    """Cache immutable parsed passages; metadata changes invalidate the entry."""
    text = Path(path).read_text(encoding='utf-8-sig')
    return tuple((n, part.strip(), frozenset(tokens(part)))
                 for n, part in enumerate(re.split(r'\n\s*\n', text), 1))


def contextual_passages(passages):
    """Attach standalone ATX headings to bodies without changing paragraph IDs."""
    headings = []
    fence = None
    for number, text, words in passages:
        lines = text.splitlines()
        matches = [re.fullmatch(r'(#{1,6})\s+(.+?)\s*#*\s*', line) for line in lines]
        if fence is None and lines and all(matches):
            for match in matches:
                level = len(match[1])
                headings = [(n, title) for n, title in headings if n < level]
                headings.append((level, match[2]))
            continue
        for line in lines:
            marker = re.match(r'^\s{0,3}(`{3,}|~{3,})(.*)$', line)
            if marker:
                run, rest = marker.groups()
                if fence is None:
                    fence = (run[0], len(run))
                elif run[0] == fence[0] and len(run) >= fence[1] and not rest.strip():
                    fence = None
        if text:
            context = '\n'.join('#' * level + ' ' + title for level, title in headings)
            combined = context + '\n\n' + text if context else text
            yield number, combined, frozenset(tokens(combined))


def search(root, query, limit=3, min_score=0.0, method='jaccard', *, rerank='none', chunking='paragraph'):
    root = Path(root)
    if not root.is_dir() or limit < 1:
        raise ValueError('Document directory must exist and limit must be positive')
    if not 0 <= min_score <= 1:
        raise ValueError('min_score must be between 0 and 1')
    if method not in {'jaccard', 'tfidf'}:
        raise ValueError("method must be 'jaccard' or 'tfidf'")
    if rerank not in {'none', 'title'}:
        raise ValueError("rerank must be 'none' or 'title'")
    if chunking not in {'paragraph', 'heading_context'}:
        raise ValueError("chunking must be 'paragraph' or 'heading_context'")
    query_counts = Counter(re.findall(r"[a-z0-9_]+|[\u4e00-\u9fff]", query.lower()))
    query = set(query_counts)
    documents = []
    title_terms = {}
    for path in sorted(root.rglob('*')):
        if path.is_file() and path.suffix.lower() in {'.md', '.txt'}:
            stat = path.stat()
            passages = cached_passages(str(path.resolve()), stat.st_mtime_ns, stat.st_size)
            first_line = next((text.splitlines()[0] for _, text, _ in passages if text), '')
            title_terms[str(path.relative_to(root))] = (
                set(re.findall(r'[a-z][a-z0-9_]*', first_line.lower()))
                if re.match(r'^#{1,6}\s+', first_line) else set())
            if chunking == 'heading_context' and path.suffix.lower() == '.md':
                passages = contextual_passages(passages)
            for number, text, words in passages:
                documents.append((path, number, text, words))
    document_frequency = Counter(token for _, _, _, words in documents for token in set(words))
    total_documents = len(documents)
    hits = []
    for path, number, text, words in documents:
        overlap = query & words
        if not overlap:
            continue
        if method == 'tfidf':
            word_counts = Counter(re.findall(r'[a-z0-9_]+|[\u4e00-\u9fff]', text.lower()))
            def weight(token):
                return 1 + log((total_documents + 1) / (document_frequency[token] + 1))
            q = {token: count * weight(token) for token, count in query_counts.items()}
            d = {token: count * weight(token) for token, count in word_counts.items()}
            score = sum(q[token] * d[token] for token in overlap)
            score /= sqrt(sum(v*v for v in q.values())) * sqrt(sum(v*v for v in d.values()))
            score = min(1.0, score)
        else:
            score = len(overlap) / len(query | words)
        if score >= min_score:
            hits.append((score, str(path.relative_to(root)), number, text.strip()))
    # Reorder all matching candidates before truncation; scores remain lexical similarity.
    return sorted(hits, key=lambda hit: (
        -len(query & title_terms[hit[1]]) if rerank == 'title' else 0,
        -hit[0], hit[1], hit[2]))[:limit]


def main():
    parser = argparse.ArgumentParser(description='Source-linked local document search')
    parser.add_argument('query')
    parser.add_argument('--docs', default='docs')
    parser.add_argument('--top-k', type=int, default=3)
    parser.add_argument('--method', choices=['jaccard', 'tfidf'], default='jaccard',
                        help='Scoring method (default: jaccard)')
    parser.add_argument('--min-score', type=float, default=0.0,
                        help='Minimum similarity, from 0 to 1 (default: 0)')
    parser.add_argument('--json', action='store_true', help='Emit structured results for other programs')
    parser.add_argument('--rerank', choices=['none', 'title'], default='none')
    parser.add_argument('--chunking', choices=['paragraph', 'heading_context'], default='paragraph')
    args = parser.parse_args()
    try:
        hits = search(args.docs, args.query, args.top_k, args.min_score, args.method, rerank=args.rerank, chunking=args.chunking)
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

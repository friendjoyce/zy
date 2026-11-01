"""Structural QA label validation, not semantic answer grading."""
from pathlib import Path, PurePosixPath
from search import cached_passages, contextual_passages


def validate_cases(cases, docs, chunking='paragraph'):
    if not isinstance(cases, list) or not cases:
        raise ValueError('Cases must be a nonempty list')
    if chunking not in ('paragraph', 'heading_context'):
        raise ValueError('Invalid chunking mode')
    root = Path(docs).resolve()
    if not root.is_dir():
        raise ValueError('Document directory must exist')
    ids, questions, available = set(), set(), {}
    for index, case in enumerate(cases, 1):
        prefix = f'Case {index}'
        if not isinstance(case, dict):
            raise ValueError(f'{prefix}: expected object')
        identifier, question = case.get('id'), case.get('question')
        if not isinstance(identifier, str) or not identifier.strip() or identifier in ids:
            raise ValueError(f'{prefix}: missing or duplicate id')
        ids.add(identifier)
        prefix = f'Case {identifier}'
        if not isinstance(question, str) or not 1 <= len(question.strip()) <= 2000:
            raise ValueError(f'{prefix}: question must contain 1-2000 characters')
        normalized = ' '.join(question.split()).casefold()
        if normalized in questions:
            raise ValueError(f'{prefix}: duplicate question (including across splits)')
        questions.add(normalized)
        if case.get('split') not in ('dev', 'test'):
            raise ValueError(f'{prefix}: split must be dev or test')
        category = case.get('category')
        if category not in ('answerable', 'hard_negative', 'no_match'):
            raise ValueError(f'{prefix}: invalid category')
        labels = case.get('relevant')
        if not isinstance(labels, list) or bool(labels) != (category == 'answerable'):
            raise ValueError(f'{prefix}: only answerable cases require nonempty relevant labels')
        seen = set()
        for label in labels:
            if type(label) is int:
                source, number = 'intro.md', label
            elif isinstance(label, dict):
                source, number = label.get('source'), label.get('paragraph')
            else:
                raise ValueError(f'{prefix}: invalid relevant label')
            if not isinstance(source, str) or not source or '\\' in source or ':' in source:
                raise ValueError(f'{prefix}: source must be a relative POSIX path')
            relative = PurePosixPath(source)
            if relative.is_absolute() or '..' in relative.parts or relative.as_posix() != source:
                raise ValueError(f'{prefix}: invalid source path')
            path = (root / source).resolve()
            if not path.is_relative_to(root) or path.suffix.lower() not in ('.md', '.txt') or not path.is_file():
                raise ValueError(f'{prefix}: source missing or outside corpus: {source}')
            if type(number) is not int or number < 1:
                raise ValueError(f'{prefix}: paragraph must be a positive integer')
            key = (source, number)
            if key in seen:
                raise ValueError(f'{prefix}: duplicate relevant label')
            seen.add(key)
            if source not in available:
                stat = path.stat()
                passages = cached_passages(str(path), stat.st_mtime_ns, stat.st_size)
                if chunking == 'heading_context' and path.suffix.lower() == '.md':
                    passages = contextual_passages(passages)
                available[source] = {n for n, text, _ in passages if text.strip()}
            if number not in available[source]:
                raise ValueError(f'{prefix}: paragraph {source}:{number} missing, empty or excluded by chunking')
    return len(cases)

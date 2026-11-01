"""Record real local-model responses; this is a smoke check, not a quality score."""
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

from app import ask


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    model = os.environ.get('OLLAMA_MODEL')
    if not model:
        parser.error('Set OLLAMA_MODEL to an installed local model')
    report = {'timestamp': datetime.now(timezone.utc).isoformat(),
              'model': model, 'quality_evaluated': False, 'cases': []}
    failed = False
    try:
        with urlopen('http://127.0.0.1:11434/api/tags', timeout=10) as response:
            report['installed_models'] = json.load(response)['models']
    except Exception as error:
        report['service_error'] = f'{type(error).__name__}: {error}'
        failed = True
    for question in ['RAG', 'Git', '火星基地的食堂菜单是什么？', 'zzzzzzzz']:
        case = {'question': question}
        try:
            case['result'] = ask(question, generate=True)
        except Exception as error:
            case['error'] = f'{type(error).__name__}: {error}'
            failed = True
        report['cases'].append(case)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Recorded {len(report["cases"])} cases in {args.output}; errors={failed}')
    return int(failed)


if __name__ == '__main__':
    raise SystemExit(main())

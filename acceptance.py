"""Real HTTP/model acceptance recording. Requires running local Ollama."""
import argparse
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen
from app import Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    os.environ['OLLAMA_MODEL'] = args.model
    report = {'timestamp': datetime.now(timezone.utc).isoformat(), 'model': args.model,
              'semantic_quality_evaluated': False, 'results': []}
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    url = f'http://127.0.0.1:{server.server_port}/api/ask'
    cases = [('rules', 'Orion 当前文档上传上限是多少？旧规则是否仍然适用？', 'generated'),
             ('conflict', 'Vega 文档保留期限是多少天？记录是否一致？', 'generated'),
             ('unknown', 'Orion 文档系统最多支持多少并发用户？', 'generated'),
             ('no_match', 'zzzzzzzz', 'no_evidence')]
    try:
        for identifier, question, expected_mode in cases:
            payload = {'question': question, 'generate': True, 'corpus': 'multidoc',
                       'method': 'bm25', 'rerank': 'none', 'chunking': 'heading_context'}
            row = {'id': identifier, 'request': payload}
            try:
                request = Request(url, json.dumps(payload).encode(), {'Content-Type': 'application/json'})
                with urlopen(request, timeout=150) as response:
                    row['response'] = json.load(response)
                row['transport_pass'] = (row['response']['mode'] == expected_mode
                                         and row['response']['settings']['method'] == 'bm25')
            except Exception as error:
                row['error'] = f'{type(error).__name__}: {error}'
                row['transport_pass'] = False
            report['results'].append(row)
            report['complete'] = len(report['results']) == len(cases)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            print(identifier, row['transport_pass'], flush=True)
    finally:
        server.shutdown()
        server.server_close()
        worker.join()
    return int(not all(row['transport_pass'] for row in report['results']))


if __name__ == '__main__':
    raise SystemExit(main())

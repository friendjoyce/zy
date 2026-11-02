"""Start the local demo after preflight: python run.py [--model qwen3:4b]."""
import argparse
import os
from http.server import ThreadingHTTPServer
from app import Handler, CORPORA
from doctor import diagnose


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', help='Enable generation using an installed Ollama model')
    args = parser.parse_args()
    if args.model is not None:
        if not args.model.strip():
            parser.error('--model must not be empty')
        os.environ['OLLAMA_MODEL'] = args.model.strip()
    model = os.environ.get('OLLAMA_MODEL')
    for name, docs in CORPORA.items():
        report = diagnose(docs, generate=bool(model) and name == 'intro', model=model)
        for check in report['checks']:
            print(f'{name}/{check["check"]}: {"PASS" if check["ok"] else "FAIL"}', flush=True)
            if not check['ok']:
                print(check['message'])
        if not report['ok']:
            return 1
    try:
        server = ThreadingHTTPServer(('127.0.0.1', 8080), Handler)
    except OSError:
        print('Cannot bind 127.0.0.1:8080. Check whether an existing demo is already running.')
        return 1
    print('Open http://127.0.0.1:8080 ; Ctrl+C stops this server.', flush=True)
    print('Generation enabled.' if model else 'Retrieval mode. Use --model to enable generation.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

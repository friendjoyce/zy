"""Read-only preflight checks; never downloads models or sends documents."""
import argparse
import json
import os
import sys
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent


def diagnose(docs, generate=False, model=None):
    checks = []

    def record(name, ok, message):
        checks.append({'check': name, 'ok': ok, 'message': message})

    record('python', sys.version_info >= (3, 10), '需要 Python 3.10 或以上。')
    try:
        root = Path(docs)
        if not root.is_dir():
            raise ValueError('知识库目录不存在，请检查 --docs。')
        files = [p for p in root.rglob('*') if p.is_file() and p.suffix.lower() in {'.md', '.txt'}]
        if not files:
            raise ValueError('知识库没有 Markdown/TXT 文件，请添加 UTF-8 文档。')
        nonempty = 0
        for path in files:
            nonempty += bool(path.read_text(encoding='utf-8-sig').strip())
        record('documents', nonempty > 0, f'读取 {len(files)} 个 UTF-8 文档，其中 {nonempty} 个非空。')
    except UnicodeError:
        record('documents', False, '存在无法按 UTF-8 读取的文档，请转换编码后重试。')
    except OSError:
        record('documents', False, '无法读取知识库，请检查文件权限和路径。')
    except ValueError as error:
        record('documents', False, str(error))

    if generate:
        model = model if model is not None else os.environ.get('OLLAMA_MODEL', '')
        model = model.strip()
        record('model_config', bool(model), '已指定模型。' if model else '请设置 OLLAMA_MODEL 或传入 --model。')
        try:
            with urlopen('http://127.0.0.1:11434/api/tags', timeout=5) as response:
                data = json.load(response)
            if not isinstance(data, dict) or not isinstance(data.get('models'), list):
                raise ValueError('Invalid model list')
            names = set()
            for entry in data['models']:
                if not isinstance(entry, dict) or not isinstance(entry.get('name'), str):
                    raise ValueError('Invalid model entry')
                names.add(entry['name'])
            record('ollama', True, '本机 Ollama 模型列表接口可用。')
            if model:
                # A name without a tag uses Ollama's latest tag convention.
                canonical = model if ':' in model.rsplit('/', 1)[-1] else model + ':latest'
                installed = model in names or canonical in names
                record('model_installed', installed, '指定模型已安装。' if installed else
                       '指定模型不在本机列表中，请确认模型名，或自行使用 ollama pull 下载。')
        except (OSError, ValueError):
            record('ollama', False, '本机 11434 服务不可用或响应无效，请启动 Ollama 并检查其日志。')
    return {'ok': all(c['ok'] for c in checks), 'mode': 'generation' if generate else 'retrieval',
            'inference_tested': False, 'checks': checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--docs', type=Path, default=ROOT / 'docs')
    parser.add_argument('--generate', action='store_true')
    parser.add_argument('--model', help='Check a model without changing OLLAMA_MODEL')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    if args.model and not args.generate:
        parser.error('--model requires --generate')
    report = diagnose(args.docs, args.generate, args.model)
    if args.json:
        print(json.dumps(report, ensure_ascii=True, indent=2))
    else:
        for check in report['checks']:
            print(f'{"PASS" if check["ok"] else "FAIL"} {check["check"]}: {check["message"]}')
        print('自检不运行推理，不证明回答质量、显存充足或网页端口可用。')
    return int(not report['ok'])


if __name__ == '__main__':
    raise SystemExit(main())

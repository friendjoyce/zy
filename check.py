"""Run the same model-free checks locally and in GitHub Actions."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    commands = [['-m', 'unittest', 'discover', '-v']]
    for docs, cases in [('docs', 'evaluation/qa_cases.json'),
                        ('evaluation/multidoc/docs', 'evaluation/multidoc/cases.json')]:
        commands.append(['doctor.py', '--docs', docs, '--json'])
        for chunking in ['paragraph', 'heading_context']:
            commands.append(['evaluate_qa.py', '--validate-only', '--docs', docs,
                             '--cases', cases, '--chunking', chunking])
    for command in commands:
        print('CHECK: python ' + ' '.join(command), flush=True)
        result = subprocess.run([sys.executable, *command], cwd=ROOT, check=False)
        if result.returncode:
            print('FAILED: python ' + ' '.join(command), file=sys.stderr)
            return 1
    print('All model-free checks passed. Real inference and browser behavior are not checked.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

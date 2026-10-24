import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from evaluate import evaluate


class ThresholdEvaluationTests(unittest.TestCase):
    def test_threshold_changes_recall_and_preserves_boundary(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, 'note.txt').write_text('git commits', encoding='utf-8')
            cases = [{'query': 'git', 'relevant': [{'source': 'note.txt', 'paragraph': 1}]}]
            self.assertEqual(evaluate(folder, cases, 1)['mean_recall'], 1)
            boundary = evaluate(folder, cases, 1, min_score=0.5)
            self.assertEqual(boundary['mean_recall'], 1)
            self.assertEqual(boundary['min_score'], 0.5)
            self.assertEqual(evaluate(folder, cases, 1, min_score=0.6)['mean_recall'], 0)
            for score in [-0.1, 1.1, float('nan'), float('inf')]:
                with self.subTest(score=score), self.assertRaises(ValueError):
                    evaluate(folder, cases, 1, min_score=score)

    def test_cli_reports_threshold_and_rejects_invalid_value(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, 'note.txt').write_text('git commits', encoding='utf-8')
            cases = Path(folder, 'cases.json')
            cases.write_text(json.dumps([{'query': 'git', 'relevant': [
                {'source': 'note.txt', 'paragraph': 1}]}]), encoding='utf-8')
            command = [sys.executable, str(Path(__file__).with_name('evaluate.py')),
                       '--docs', folder, '--cases', str(cases), '--min-score']
            result = subprocess.run(command + ['0.6'], capture_output=True, text=True, check=True)
            report = json.loads(result.stdout)
            self.assertEqual(report['min_score'], 0.6)
            self.assertEqual(report['mean_recall'], 0)
            invalid = subprocess.run(command + ['1.1'], capture_output=True, text=True)
            self.assertNotEqual(invalid.returncode, 0)
            self.assertEqual(invalid.stdout, '')
            self.assertIn('min_score must be between 0 and 1', invalid.stderr)

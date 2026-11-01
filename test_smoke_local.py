import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import smoke_local


class SmokeRecorderTests(unittest.TestCase):
    def run_recorder(self, directory, answers):
        output = Path(directory) / 'report.json'
        with patch.dict('os.environ', {'OLLAMA_MODEL': 'test-model'}), \
             patch('sys.argv', ['smoke_local.py', '--output', str(output)]), \
             patch('smoke_local.urlopen') as request, \
             patch('smoke_local.ask', side_effect=answers), \
             patch('builtins.print'):
            request.return_value.__enter__.return_value.read.return_value = b'{"models": []}'
            status = smoke_local.main()
        return status, json.loads(output.read_text(encoding='utf-8'))

    def test_partial_failure_keeps_all_cases(self):
        with tempfile.TemporaryDirectory() as directory:
            status, report = self.run_recorder(directory, [
                {'answer': 'first'}, TimeoutError('timed out'),
                {'answer': 'third'}, {'mode': 'no_evidence'}])
        self.assertEqual(status, 1)
        self.assertEqual(len(report['cases']), 4)
        self.assertIn('TimeoutError', report['cases'][1]['error'])
        self.assertEqual(report['cases'][2]['result']['answer'], 'third')
        self.assertFalse(report['quality_evaluated'])

    def test_success_records_model_without_claiming_quality(self):
        with tempfile.TemporaryDirectory() as directory:
            status, report = self.run_recorder(directory, [{'answer': 'mock'}] * 4)
        self.assertEqual(status, 0)
        self.assertEqual(report['model'], 'test-model')
        self.assertFalse(report['quality_evaluated'])


if __name__ == '__main__':
    unittest.main()

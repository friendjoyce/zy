import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from evaluate_qa import ROOT, run, summarize
from qa import answer


class QAEvaluationTests(unittest.TestCase):
    def test_negatives_do_not_inflate_answerable_recall(self):
        rows = [
            {'case': {'category': 'answerable', 'relevant': [2]},
             'result': {'sources': [{'source': 'intro.md', 'paragraph': 2}]}},
            {'case': {'category': 'answerable', 'relevant': [3]}, 'error': 'timeout'},
            {'case': {'category': 'hard_negative', 'relevant': []},
             'result': {'sources': [{'source': 'intro.md', 'paragraph': 3}]}}
        ]
        report = summarize(rows)
        self.assertEqual(report['answerable_recall_at_3'], 0.5)
        self.assertEqual(report['negative_cases_with_hits'], 1)
        self.assertEqual(report['errors'], 1)
        self.assertFalse(report['semantic_quality_evaluated'])
        self.assertIsNone(summarize(rows[2:])['answerable_recall_at_3'])

    def test_partial_failure_is_saved_and_following_case_runs(self):
        cases = [{'id': str(i), 'question': 'q', 'category': 'hard_negative', 'relevant': []}
                 for i in range(2)]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'report.json'
            with patch('evaluate_qa.ask', side_effect=[TimeoutError(), {'mode': 'no_evidence', 'sources': []}]), patch('builtins.print'):
                run(cases, True, output)
            report = json.loads(output.read_text(encoding='utf-8'))
        self.assertTrue(report['complete'])
        self.assertEqual(report['summary']['errors'], 1)
        self.assertEqual(len(report['results']), 2)

    def test_dataset_has_real_hard_negatives_and_disjoint_questions(self):
        cases = json.loads((ROOT / 'evaluation/qa_cases.json').read_text(encoding='utf-8'))
        self.assertEqual(len({c['id'] for c in cases}), len(cases))
        self.assertEqual(len({c['question'] for c in cases}), len(cases))
        for split in ['dev', 'test']:
            selected = [c for c in cases if c['split'] == split]
            self.assertEqual(len(selected), 6)
            for case in selected:
                result = answer(ROOT / 'docs', case['question'])
                if case['category'] == 'hard_negative':
                    self.assertTrue(result['sources'], case['id'])
                    self.assertEqual(case['relevant'], [])
                elif case['category'] == 'no_match':
                    self.assertEqual(result['sources'], [])
                else:
                    self.assertTrue(case['relevant'])


if __name__ == '__main__':
    unittest.main()

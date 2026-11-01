import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from validate_cases import validate_cases
from evaluate_qa import run


class CaseValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'intro.md').write_text('# Title\n\nEvidence', encoding='utf-8')
        self.case = {'id': 'one', 'split': 'dev', 'question': 'Question',
                     'category': 'answerable', 'relevant': [2]}

    def test_valid_legacy_and_multidoc_labels(self):
        self.assertEqual(validate_cases([self.case], self.root, 'heading_context'), 1)
        self.case['relevant'] = [{'source': 'intro.md', 'paragraph': 2}]
        self.assertEqual(validate_cases([self.case], self.root), 1)

    def test_duplicate_questions_across_splits(self):
        second = {**self.case, 'id': 'two', 'split': 'test', 'question': '  QUESTION  '}
        with self.assertRaisesRegex(ValueError, 'duplicate question'):
            validate_cases([self.case, second], self.root)
        second.update(question='other', id='one')
        with self.assertRaisesRegex(ValueError, 'duplicate id'):
            validate_cases([self.case, second], self.root)

    def test_bad_schema_labels_and_paths(self):
        for change in [{'split': 'typo'}, {'category': 'typo'}, {'question': ''},
                       {'relevant': []}, {'relevant': [True]}, {'relevant': [0]},
                       {'relevant': [2, 2]}, {'relevant': [99]},
                       {'category': 'hard_negative'},
                       {'relevant': [{'source': '../outside.md', 'paragraph': 1}]},
                       {'relevant': [{'source': 'missing.md', 'paragraph': 1}]}]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_cases([{**self.case, **change}], self.root)

    def test_heading_label_invalid_under_context_mode(self):
        self.case['relevant'] = [1]
        validate_cases([self.case], self.root)
        with self.assertRaisesRegex(ValueError, 'excluded by chunking'):
            validate_cases([self.case], self.root, 'heading_context')

    @patch('evaluate_qa.ask')
    def test_fail_before_model_call_or_existing_report_overwrite(self, ask):
        output = self.root / 'report.json'
        output.write_text('previous evidence', encoding='utf-8')
        self.case['relevant'] = [99]
        with self.assertRaises(ValueError):
            run([self.case], True, output, self.root)
        ask.assert_not_called()
        self.assertEqual(output.read_text(encoding='utf-8'), 'previous evidence')


if __name__ == '__main__':
    unittest.main()

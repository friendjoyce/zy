import tempfile
import unittest
from pathlib import Path
from evaluate import evaluate

class EvaluationMethodTests(unittest.TestCase):
    def test_report_records_method(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, "note.txt").write_text("retrieval rare", encoding="utf-8")
            cases = [{"query": "rare", "relevant": [{"source": "note.txt", "paragraph": 1}]}]
            report = evaluate(folder, cases, 1, method="tfidf")
            self.assertEqual(report["method"], "tfidf")
            self.assertEqual(report["mean_recall"], 1)

    def test_invalid_method_is_rejected(self):
        with self.assertRaises(ValueError):
            evaluate(".", [{"query": "x", "relevant": [{"source": "x", "paragraph": 1}]}], 1, method="bm25")

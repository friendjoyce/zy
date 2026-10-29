import tempfile
import unittest
from pathlib import Path
from search import search

class TfidfTests(unittest.TestCase):
    def test_tfidf_prefers_term_specific_passage(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, "docs.txt").write_text("retrieval retrieval common\n\nretrieval rare", encoding="utf-8")
            hits = search(folder, "rare", method="tfidf")
            self.assertEqual(hits[0][2], 2)
            self.assertGreater(hits[0][0], 0)

    def test_invalid_method(self):
        with self.assertRaises(ValueError):
            search(".", "query", method="bm25")

class TfidfRegressionTests(unittest.TestCase):
    def test_single_document_has_positive_score(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, 'a.txt').write_text('git', encoding='utf-8')
            self.assertAlmostEqual(search(folder, 'git', method='tfidf', min_score=1)[0][0], 1)

    def test_frequency_affects_ranking(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, 'a.txt').write_text('git other other other\n\ngit git git other', encoding='utf-8')
            hits = search(folder, 'git', method='tfidf')
            self.assertEqual(hits[0][2], 2)
            self.assertGreater(hits[0][0], hits[1][0])
            self.assertEqual(search(folder, 'unknown', method='tfidf'), [])

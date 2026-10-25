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

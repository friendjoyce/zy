import math
import tempfile
import unittest
from pathlib import Path
from search import search


class BM25Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_hand_calculated_score_and_duplicate_query_terms(self):
        (self.root / 'a.txt').write_text('cat cat dog\n\ndog', encoding='utf-8')
        hits = search(self.root, 'cat', method='bm25')
        expected = math.log(2) * 2 * 2.2 / (2 + 1.2 * (0.25 + 0.75 * 3 / 2))
        self.assertAlmostEqual(hits[0][0], expected)
        self.assertEqual(hits, search(self.root, 'cat cat', method='bm25'))
        self.assertEqual(search(self.root, 'cat', method='bm25', min_score=expected), hits)
        self.assertEqual(search(self.root, 'cat', method='bm25', min_score=expected + 0.01), [])

    def test_length_normalization_and_empty_corpus(self):
        self.assertEqual(search(self.root, 'cat', method='bm25'), [])
        (self.root / 'a.txt').write_text('cat dog dog dog dog\n\ncat\n\n', encoding='utf-8')
        self.assertEqual(search(self.root, 'cat', method='bm25')[0][2], 2)
        self.assertEqual(search(self.root, 'unknown', method='bm25'), [])
        self.assertEqual(search(self.root, '', method='bm25'), [])

    def test_raw_scores_and_threshold_validation(self):
        (self.root / 'a.txt').write_text('one two three\n\nfour\n\nfive', encoding='utf-8')
        hit = search(self.root, 'one two three', method='bm25')[0]
        self.assertGreater(hit[0], 1)
        self.assertEqual(search(self.root, 'one two three', method='bm25', min_score=1.1)[0], hit)
        for value in [-1, float('nan'), float('inf')]:
            with self.assertRaises(ValueError):
                search(self.root, 'one', method='bm25', min_score=value)


if __name__ == '__main__':
    unittest.main()

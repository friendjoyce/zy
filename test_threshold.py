import tempfile
import unittest
from pathlib import Path
from search import search


class ThresholdTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'notes.txt').write_text('alpha beta\n\nalpha beta gamma delta', encoding='utf-8')

    def test_threshold_filters_weak_match_and_keeps_boundary(self):
        self.assertEqual(len(search(self.root, 'alpha')), 2)
        hits = search(self.root, 'alpha', min_score=0.5)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0][2], 1)
        self.assertEqual(hits[0][0], 0.5)

    def test_no_matches_and_exact_match(self):
        self.assertEqual(search(self.root, 'alpha', min_score=1), [])
        self.assertEqual(len(search(self.root, 'alpha beta', min_score=1)), 1)
        self.assertEqual(search(self.root, 'unknown', min_score=0), [])

    def test_invalid_threshold(self):
        for value in (-0.1, 1.1, float('nan'), float('inf')):
            with self.subTest(value=value), self.assertRaises(ValueError):
                search(self.root, 'alpha', min_score=value)

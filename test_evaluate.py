import unittest
from evaluate import recall_at_k, evaluate


class RecallTests(unittest.TestCase):
    def test_partial_and_cutoff(self):
        self.assertEqual(recall_at_k(['a', 'b'], ['a', 'b'], 1), 0.5)
        self.assertEqual(recall_at_k(['a', 'b'], ['a', 'b'], 2), 1)

    def test_duplicates_do_not_inflate_recall(self):
        self.assertEqual(recall_at_k(['a', 'a'], ['a', 'b'], 2), 0.5)

    def test_no_hits(self):
        self.assertEqual(recall_at_k([], ['a'], 3), 0)

    def test_invalid_inputs(self):
        for hits, relevant, k in [([], [], 1), ([], ['a'], 0)]:
            with self.assertRaises(ValueError):
                recall_at_k(hits, relevant, k)
        with self.assertRaises(ValueError):
            evaluate('docs', [], 3)

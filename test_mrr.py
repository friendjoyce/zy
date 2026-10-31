import unittest
from unittest.mock import patch
from evaluate import reciprocal_rank_at_k, evaluate

class MrrTests(unittest.TestCase):
    def test_rank_cutoff_and_no_hits(self):
        self.assertEqual(reciprocal_rank_at_k(['x', 'a', 'b'], ['a', 'b'], 3), 0.5)
        self.assertEqual(reciprocal_rank_at_k(['x', 'a'], ['a'], 1), 0)
        self.assertEqual(reciprocal_rank_at_k([], ['a'], 3), 0)
        self.assertEqual(reciprocal_rank_at_k(['a', 'a'], ['a'], 2), 1)

    def test_invalid(self):
        for relevant, k in [([], 1), (['a'], 0)]:
            with self.assertRaises(ValueError):
                reciprocal_rank_at_k([], relevant, k)

    @patch('evaluate.search')
    def test_macro_average_includes_unanswered_queries(self, search):
        search.side_effect = [[(1, 'x', 1, ''), (0.5, 'a', 1, '')], []]
        cases = [{'query': q, 'relevant': [{'source': 'a', 'paragraph': 1}]} for q in ['one', 'two']]
        report = evaluate('.', cases, 2)
        self.assertEqual(report['mrr'], 0.25)
        self.assertEqual(report['mean_recall'], 0.5)
        self.assertEqual(report['results'][0]['reciprocal_rank'], 0.5)

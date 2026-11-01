import tempfile
import unittest
from pathlib import Path
from search import search
from evaluate_qa import summarize


class TitleRerankTests(unittest.TestCase):
    def test_title_match_precedes_body_mention_before_cutoff(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'a.md').write_text('# Atlas\n\nAtlas upload limit current policy value extra words', encoding='utf-8')
            (root / 'b.md').write_text('# Boreal\n\nAtlas upload limit', encoding='utf-8')
            baseline = search(root, 'Atlas upload limit', 1, method='tfidf')
            ranked = search(root, 'Atlas upload limit', 1, method='tfidf', rerank='title')
            self.assertEqual(baseline[0][1], 'b.md')
            self.assertEqual(ranked[0][1], 'a.md')
            original = search(root, 'Atlas upload limit', 20, method='tfidf')
            self.assertIn(ranked[0], original)  # Reordering never fabricates a similarity score.
            self.assertEqual(search(root, 'zzzz', rerank='title'), [])
            for query in ['upload limit', '上传限制']:
                self.assertEqual(search(root, query, method='tfidf'),
                                 search(root, query, method='tfidf', rerank='title'))

    def test_plain_text_and_unknown_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, 'a.txt').write_text('Atlas\n\nupload limit', encoding='utf-8')
            self.assertEqual(search(directory, 'Atlas'), search(directory, 'Atlas', rerank='title'))
            with self.assertRaises(ValueError):
                search(directory, 'Atlas', rerank='invalid')

    def test_rank_metrics_distinguish_recall_from_first_hit(self):
        row = {'case': {'category': 'answerable', 'relevant': [
            {'source': 'right.md', 'paragraph': 2}]},
            'result': {'sources': [{'source': 'wrong.md', 'paragraph': 2},
                                   {'source': 'right.md', 'paragraph': 2}]}}
        result = summarize([row])
        self.assertEqual(result['answerable_recall_at_3'], 1)
        self.assertEqual(result['answerable_mrr_at_3'], 0.5)
        self.assertEqual(result['answerable_hit_at_1'], 0)


if __name__ == '__main__':
    unittest.main()

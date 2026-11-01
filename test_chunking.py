import tempfile
import unittest
from pathlib import Path
from search import search
from qa import answer


class HeadingContextTests(unittest.TestCase):
    def write(self, folder, text, suffix='md'):
        Path(folder, 'a.' + suffix).write_text(text, encoding='utf-8')

    def test_heading_attaches_to_body_and_keeps_original_id(self):
        with tempfile.TemporaryDirectory() as folder:
            self.write(folder, '# Atlas\n\n## Upload\n\nLimit is 20 MB.\n\n## Retention\n\nKeep for 7 days.')
            hits = search(folder, 'Atlas', 10, chunking='heading_context')
            self.assertEqual({h[2] for h in hits}, {3, 5})
            texts = {h[2]: h[3] for h in hits}
            self.assertIn('# Atlas\n## Upload', texts[3])
            self.assertIn('## Retention', texts[5])
            self.assertNotIn('## Upload', texts[5])
            result = answer(folder, '20 MB', chunking='heading_context')
            self.assertEqual(result['sources'][0]['paragraph'], 3)

    def test_heading_only_empty_and_plain_text(self):
        with tempfile.TemporaryDirectory() as folder:
            self.write(folder, '# Atlas\n\n## Upload')
            self.assertEqual(search(folder, 'Atlas', chunking='heading_context'), [])
            self.write(folder, '# Atlas\n\nbody', suffix='txt')
            hits = search(folder, 'Atlas', chunking='heading_context')
            self.assertEqual([(h[1], h[2]) for h in hits], [('a.txt', 1)])
            with self.assertRaises(ValueError):
                search(folder, 'Atlas', chunking='bad')

    def test_fenced_heading_is_preserved_as_code(self):
        with tempfile.TemporaryDirectory() as folder:
            self.write(folder, '# Guide\n\n```python\n\n# example\n\n```\n\nAfter code.')
            hits = search(folder, 'example', chunking='heading_context')
            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0][2], 3)
            self.assertIn('# example', hits[0][3])
            after = search(folder, 'After', chunking='heading_context')[0][3]
            self.assertNotIn('# example', after)

    def test_default_unchanged_and_cache_reflects_new_heading(self):
        with tempfile.TemporaryDirectory() as folder:
            self.write(folder, '# Atlas\n\nbody')
            self.assertEqual(search(folder, 'Atlas')[0][2], 1)
            self.assertEqual(search(folder, 'Atlas', chunking='heading_context')[0][2], 2)
            self.write(folder, '# Borealis\n\nbody')
            self.assertEqual(search(folder, 'Atlas', chunking='heading_context'), [])


if __name__ == '__main__':
    unittest.main()

import tempfile
import unittest
from pathlib import Path
from search import search


class SearchTests(unittest.TestCase):
    def test_search(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, 'a.md').write_text('向量检索查找文档。\n\nGit records commits.', encoding='utf-8')
            self.assertEqual(search(folder, '向量检索')[0][1:3], ('a.md', 1))
            self.assertEqual(search(folder, 'GIT')[0][2], 2)
            self.assertEqual(search(folder, 'unknown'), [])
            self.assertEqual(search(folder, ''), [])
            self.assertEqual(len(search(folder, 'Git 向量', 1)), 1)
            with self.assertRaises(ValueError):
                search(folder, 'Git', 0)
            with self.assertRaises(ValueError):
                search(Path(folder, 'missing'), 'Git')


if __name__ == '__main__':
    unittest.main()

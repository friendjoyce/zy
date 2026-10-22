import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class JsonCliTests(unittest.TestCase):
    def run_search(self, query):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, 'note.txt').write_text('Git records commits.', encoding='utf-8')
            result = subprocess.run(
                [sys.executable, str(Path(__file__).with_name('search.py')),
                 query, '--docs', folder, '--json'],
                capture_output=True, text=True, check=True)
            return json.loads(result.stdout)

    def test_structured_hit(self):
        hit = self.run_search('Git')[0]
        self.assertEqual(hit['source'], 'note.txt')
        self.assertEqual(hit['paragraph'], 1)
        self.assertEqual(hit['text'], 'Git records commits.')
        self.assertGreater(hit['score'], 0)

    def test_no_matches_is_empty_array(self):
        self.assertEqual(self.run_search('missingword'), [])

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
from search import search, cached_passages
from qa import answer

class ApplicationTests(unittest.TestCase):
    def test_cache_reuse_and_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder, 'a.txt'); p.write_text('git')
            cached_passages.cache_clear()
            search(folder, 'git'); search(folder, 'git')
            self.assertEqual(cached_passages.cache_info().hits, 1)
            p.write_text('python code')
            self.assertEqual(search(folder, 'git'), [])
            p.unlink()
            self.assertEqual(search(folder, 'python'), [])

    def test_qa_modes_and_model_contract(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, 'a.txt').write_text('git commits')
            self.assertEqual(answer(folder, 'git')['mode'], 'extractive')
            with patch('qa.subprocess.run', return_value=SimpleNamespace(stdout='Git [1]')) as run:
                self.assertEqual(answer(folder, 'unknown', ['model'])['mode'], 'no_evidence')
                run.assert_not_called()
                result = answer(folder, 'git', ['model'])
                self.assertEqual(result['answer'], 'Git [1]')
                self.assertEqual(result['sources'][0]['paragraph'], 1)
                self.assertFalse(run.call_args.kwargs['shell'])
            with self.assertRaises(ValueError):
                answer(folder, ' ')

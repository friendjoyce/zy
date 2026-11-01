import unittest
from types import SimpleNamespace
from unittest.mock import patch
from check import main, ROOT


class CheckRunnerTests(unittest.TestCase):
    @patch('builtins.print')
    @patch('check.subprocess.run')
    def test_first_failure_stops_later_checks(self, run, _print):
        run.side_effect = [SimpleNamespace(returncode=0), SimpleNamespace(returncode=2)]
        self.assertEqual(main(), 1)
        self.assertEqual(run.call_count, 2)

    @patch('builtins.print')
    @patch('check.subprocess.run', return_value=SimpleNamespace(returncode=0))
    def test_success_uses_repo_directory_and_no_generation(self, run, _print):
        self.assertEqual(main(), 0)
        self.assertEqual(run.call_count, 7)
        for call in run.call_args_list:
            self.assertEqual(call.kwargs['cwd'], ROOT)
            self.assertNotIn('--generate', call.args[0])


if __name__ == '__main__':
    unittest.main()

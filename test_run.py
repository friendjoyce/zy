import unittest
from unittest.mock import patch
import run


class LauncherTests(unittest.TestCase):
    @patch('sys.argv', ['run.py'])
    @patch.dict('os.environ', {}, clear=True)
    @patch('builtins.print')
    @patch('run.ThreadingHTTPServer')
    @patch('run.diagnose', return_value={'ok': False, 'checks': []})
    def test_failed_preflight_does_not_start_server(self, diagnose, server, _print):
        self.assertEqual(run.main(), 1)
        server.assert_not_called()

    @patch('sys.argv', ['run.py', '--model', 'demo'])
    @patch.dict('os.environ', {}, clear=True)
    @patch('builtins.print')
    @patch('run.ThreadingHTTPServer')
    @patch('run.diagnose', return_value={'ok': True, 'checks': []})
    def test_keyboard_interrupt_closes_server(self, diagnose, server, _print):
        server.return_value.serve_forever.side_effect = KeyboardInterrupt
        self.assertEqual(run.main(), 0)
        self.assertEqual(diagnose.call_args_list[0].kwargs['model'], 'demo')
        server.return_value.server_close.assert_called_once()

    @patch('sys.argv', ['run.py'])
    @patch.dict('os.environ', {}, clear=True)
    @patch('builtins.print')
    @patch('run.ThreadingHTTPServer', side_effect=OSError('port busy'))
    @patch('run.diagnose', return_value={'ok': True, 'checks': []})
    def test_busy_port_returns_failure(self, diagnose, server, _print):
        self.assertEqual(run.main(), 1)


if __name__ == '__main__':
    unittest.main()

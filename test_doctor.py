import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError
from doctor import diagnose


class DoctorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'a.md').write_text('sample', encoding='utf-8')

    @patch('doctor.urlopen')
    def test_retrieval_does_not_contact_model(self, request):
        self.assertTrue(diagnose(self.root)['ok'])
        request.assert_not_called()

    def test_missing_empty_and_invalid_utf8(self):
        self.assertFalse(diagnose(self.root / 'missing')['ok'])
        (self.root / 'a.md').write_text('', encoding='utf-8')
        self.assertFalse(diagnose(self.root)['ok'])
        (self.root / 'a.md').write_bytes(b'\xff')
        self.assertFalse(diagnose(self.root)['ok'])

    @patch('doctor.urlopen')
    def test_installed_missing_and_default_tag(self, request):
        request.return_value.__enter__.return_value.read.return_value = b'{"models":[{"name":"demo:latest"}]}'
        self.assertTrue(diagnose(self.root, True, 'demo')['ok'])
        self.assertFalse(diagnose(self.root, True, 'demo:other')['ok'])
        self.assertFalse(diagnose(self.root, True, '')['ok'])
        self.assertFalse(diagnose(self.root, True, 'demo')['inference_tested'])
        request.assert_called_with('http://127.0.0.1:11434/api/tags', timeout=5)

    @patch('doctor.urlopen')
    def test_unavailable_and_malformed_service(self, request):
        request.side_effect = URLError('offline')
        self.assertFalse(diagnose(self.root, True, 'demo')['ok'])
        request.side_effect = None
        for body in [b'bad json', b'[]', b'{"models":[{}]}']:
            request.return_value.__enter__.return_value.read.return_value = body
            self.assertFalse(diagnose(self.root, True, 'demo')['ok'])


if __name__ == '__main__':
    unittest.main()

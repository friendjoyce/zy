import unittest
from unittest.mock import patch, MagicMock
from app import ask

class AppTests(unittest.TestCase):
    def test_invalid_question(self):
        for q in [None, '', 'x'*2001]:
            with self.assertRaises(ValueError): ask(q)
    def test_extractive(self):
        result=ask('RAG')
        self.assertEqual(result['mode'], 'extractive')
        self.assertTrue(result['sources'])
    @patch.dict('os.environ', {'OLLAMA_MODEL':'test'})
    @patch('app.urlopen')
    def test_generation_and_invalid_citation(self, request):
        request.return_value.__enter__.return_value.read.return_value=b'{"message":{"content":"answer [99]"}}'
        result=ask('RAG', True)
        self.assertEqual(result['citation_check']['unknown_ids'], [99])
        self.assertEqual(result['mode'], 'generated')

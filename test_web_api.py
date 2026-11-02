import json
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from app import Handler


class WebAPITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def post(self, payload, origin=None):
        connection = HTTPConnection(*self.server.server_address, timeout=5)
        headers = {'Content-Type': 'application/json'}
        if origin:
            headers['Origin'] = origin
        connection.request('POST', '/api/ask', json.dumps(payload), headers)
        response = connection.getresponse()
        status, body = response.status, json.loads(response.read())
        connection.close()
        return status, body

    def test_selected_corpus_and_original_paragraph(self):
        status, body = self.post({'question': 'Orion 当前上传上限', 'corpus': 'multidoc',
                                  'rerank': 'title', 'chunking': 'heading_context'})
        self.assertEqual(status, 200)
        self.assertEqual(body['settings']['chunking'], 'heading_context')
        first = body['sources'][0]
        self.assertEqual(first['source'], 'orion_current.md')
        self.assertIn('# 虚构测试资料', first['text'])
        self.assertNotIn('# 虚构测试资料', first['original_text'])
        self.assertIn('20 MB', first['original_text'])

    def test_bm25_sources_match_search(self):
        from search import search
        from app import CORPORA
        query = 'Orion 当前文档上传上限是多少？旧规则是否仍然适用？'
        status, body = self.post({'question': query, 'corpus': 'multidoc', 'method': 'bm25'})
        self.assertEqual(status, 200)
        self.assertEqual(body['settings']['method'], 'bm25')
        expected = search(CORPORA['multidoc'], query, method='bm25')
        self.assertEqual([(s['score'], s['source'], s['paragraph']) for s in body['sources']],
                         [(score, source.replace('\\', '/'), paragraph) for score, source, paragraph, _ in expected])

    def test_invalid_options_rejected(self):
        for key in ['corpus', 'rerank', 'chunking', 'method']:
            for value in ['../../private', [], None]:
                self.assertEqual(self.post({'question': 'RAG', key: value})[0], 400)
        self.assertEqual(self.post({'question': 'RAG', 'generate': 'yes'})[0], 400)
        self.assertEqual(self.post({'question': 'RAG'}, 'https://example.com')[0], 403)

    def test_defaults_and_no_evidence(self):
        status, body = self.post({'question': 'zzzzzzzz'})
        self.assertEqual(status, 200)
        self.assertEqual(body['mode'], 'no_evidence')
        self.assertEqual(body['sources'], [])
        self.assertEqual(body['settings'], {'corpus': 'intro', 'rerank': 'none', 'chunking': 'paragraph', 'method': 'tfidf'})


if __name__ == '__main__':
    unittest.main()

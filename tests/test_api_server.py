import unittest
from unittest import mock
import types
import sys
import asyncio

# Provide minimal Flask stub
fake_flask = types.ModuleType('flask')

class _Request:
    json_data = None
    def get_json(self, force=False):
        return self.json_data

request = _Request()

class _Response:
    def __init__(self, json, status=200):
        self._json = json
        self.status_code = status
    def get_json(self):
        return self._json

def jsonify(obj):
    return obj

class Flask:
    def __init__(self, name):
        self.routes = {}
    def post(self, path):
        def decorator(func):
            self.routes[path] = func
            return func
        return decorator
    def test_client(self):
        app = self
        class Client:
            def post(self, path, json=None):
                request.json_data = json
                result = app.routes[path]()
                if asyncio.iscoroutine(result):
                    rv = asyncio.run(result)
                else:
                    rv = result
                if isinstance(rv, tuple):
                    data, status = rv
                else:
                    data, status = rv, 200
                if isinstance(data, _Response):
                    return data
                return _Response(data, status)
        return Client()

fake_flask.Flask = Flask
fake_flask.jsonify = jsonify
fake_flask.request = request
sys.modules['flask'] = fake_flask

import assembler
import importlib
server = importlib.import_module('server')


class APIServerTest(unittest.TestCase):
    def setUp(self):
        self.client = server.create_app().test_client()

    def test_assemble(self):
        asm = "PUSH 1\nPRINT"
        resp = self.client.post('/assemble', json={'text': asm})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json(), {'chunks': assembler.assemble(asm)})

    def test_run_text(self):
        asm = "PUSH 2\nPRINT"
        resp = self.client.post('/run', json={'text': asm})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json(), {'output': '2'})

    def test_run_chunks(self):
        asm = "PUSH 3\nPRINT"
        chunks_list = assembler.assemble(asm)
        resp = self.client.post('/run', json={'chunks': chunks_list})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json(), {'output': '3'})

    def test_generate(self):
        with mock.patch('uor.async_llm_client.async_call_model', new=mock.AsyncMock(return_value='PUSH 1\nPRINT')) as call, \
             mock.patch('uor.ipfs_storage.async_add_data', new=mock.AsyncMock(return_value='CID')) as add:
            resp = self.client.post('/generate', json={'prompt': 'hi', 'provider': 'openai'})
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.get_json(), {'cid': 'CID'})
            call.assert_called_with('openai', 'hi')
            add.assert_called()


if __name__ == '__main__':
    unittest.main()

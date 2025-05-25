import unittest
from unittest import mock

import assembler
from uor import api_server
try:
    import flask  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    flask = None

create_app = api_server.create_app


class APIServerTest(unittest.TestCase):
    def setUp(self):
        if flask is None:
            self.skipTest('flask not installed')
        self.app = create_app().test_client()

    def test_generate_endpoint(self):
        program_text = "PUSH 1\nPRINT"
        encoded = "\n".join(str(x) for x in assembler.assemble(program_text)).encode("utf-8")
        with mock.patch('uor.llm_client.call_model', return_value=program_text) as call_model, \
             mock.patch('uor.ipfs_storage.add_data', return_value='CID') as add_data:
            resp = self.app.post('/generate', json={'provider': 'openai', 'prompt': 'hi'})
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.get_json(), {'cid': 'CID'})
            call_model.assert_called_with('openai', 'hi')
            add_data.assert_called_with(encoded)

    def test_run_endpoint(self):
        program_text = "PUSH 5\nPRINT"
        encoded = "\n".join(str(x) for x in assembler.assemble(program_text)).encode("utf-8")
        with mock.patch('uor.ipfs_storage.get_data', return_value=encoded) as get_data:
            resp = self.app.get('/run/XYZ')
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.get_json(), {'output': '5'})
            get_data.assert_called_with('XYZ')


if __name__ == '__main__':
    unittest.main()

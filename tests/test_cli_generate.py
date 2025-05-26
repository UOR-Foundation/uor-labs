import io
import contextlib
import unittest
from unittest import mock

import uor_cli


class CLIGenerateTest(unittest.TestCase):
    def test_generate_calls_llm_and_ipfs(self):
        asm = "PUSH 1\nPRINT"
        with mock.patch('uor.llm_client.call_model', return_value=asm) as call, \
             mock.patch('uor.ipfs_storage.add_data', return_value='CID') as add:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = uor_cli.main(['generate', '--provider', 'openai', 'hi'])
            self.assertEqual(rc, 0)
            self.assertEqual(buf.getvalue().strip(), 'CID')
            call.assert_called_with('openai', 'hi')
            add.assert_called()


if __name__ == '__main__':
    unittest.main()

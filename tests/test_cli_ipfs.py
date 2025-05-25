import io
import os
import contextlib
import importlib.util
import unittest
from unittest import mock

# Load the CLI module since its filename contains a dash
spec = importlib.util.spec_from_file_location('uor_cli', os.path.join(os.path.dirname(__file__), '..', 'uor-cli.py'))
uor_cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(uor_cli)

import assembler

class CLIIpfsTest(unittest.TestCase):
    def test_ipfs_add_prints_cid(self):
        with mock.patch('uor.ipfs_storage.add_data', return_value='CID') as add:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = uor_cli.main(['ipfs-add', 'examples/countdown.asm'])
            self.assertEqual(rc, 0)
            self.assertEqual(buf.getvalue().strip(), 'CID')
            add.assert_called()

    def test_ipfs_run_executes_program(self):
        program = assembler.assemble_file('examples/countdown.asm')
        data = '\n'.join(str(x) for x in program).encode('utf-8')
        with mock.patch('uor.ipfs_storage.get_data', return_value=data) as get:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = uor_cli.main(['ipfs-run', 'fakecid'])
            self.assertEqual(rc, 0)
            self.assertEqual(buf.getvalue().strip(), '321')
            get.assert_called_with('fakecid')


if __name__ == '__main__':
    unittest.main()

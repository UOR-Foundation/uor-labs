import importlib
import os
import sys
import tempfile
import unittest
from unittest import mock

import chunks
from decoder import decode
from vm import VM
import uor.vm.checkpoint as cp


class CheckpointFileTest(unittest.TestCase):
    def test_round_trip(self):
        stack = [1, 2]
        mem = {0: 5}
        ip = 3
        data = cp.serialize_state(stack, mem, ip)
        with tempfile.TemporaryDirectory() as td:
            backend = cp.FileBackend(td)
            ident = backend.save("state", data)
            loaded = backend.load(ident)
        s, m, i = cp.deserialize_state(loaded)
        self.assertEqual(s, stack)
        self.assertEqual(m, mem)
        self.assertEqual(i, ip)


class CheckpointIPFSTest(unittest.TestCase):
    def setUp(self):
        self.fake_mod = mock.MagicMock()
        self.patcher = mock.patch.dict(sys.modules, {'ipfshttpclient': self.fake_mod})
        self.patcher.start()
        import uor.ipfs_storage as ipfs_storage
        importlib.reload(ipfs_storage)
        importlib.reload(cp)

    def tearDown(self):
        self.patcher.stop()

    def test_ipfs_backend(self):
        self.fake_mod.connect.return_value.__enter__.return_value = self.fake_mod
        self.fake_mod.add_bytes.return_value = 'cid'
        self.fake_mod.cat.return_value = b'data'
        backend = cp.IPFSBackend()
        cid = backend.save('x', b'data')
        self.assertEqual(cid, 'cid')
        data = backend.load(cid)
        self.fake_mod.add_bytes.assert_called_with(b'data')
        self.fake_mod.cat.assert_called_with('cid')
        self.assertEqual(data, b'data')


class AutoCheckpointTest(unittest.TestCase):
    def test_instruction_policy(self):
        prog = [chunks.chunk_push(1), chunks.chunk_push(2), chunks.chunk_add()]
        with tempfile.TemporaryDirectory() as td:
            vm = VM()
            vm.checkpoint_backend = cp.FileBackend(td)
            vm.checkpoint_policy = cp.InstructionCountPolicy(2)
            list(vm.execute(decode(prog)))
            files = os.listdir(td)
            self.assertTrue(files)


if __name__ == '__main__':
    unittest.main()

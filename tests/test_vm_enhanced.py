import unittest
from unittest import mock

import chunks
from decoder import decode
from vm import VM


class VMEnhancedTest(unittest.TestCase):
    def test_call_and_ret(self):
        prog = [
            chunks.chunk_push(5),
            chunks.chunk_ret(),
            chunks.chunk_push(2),
            chunks.chunk_call(-4),
            chunks.chunk_add(),
            chunks.chunk_print(),
        ]
        out = ''.join(VM().execute(decode(prog)))
        self.assertEqual(out, '7')

    def test_checkpoint_opcode(self):
        class Backend:
            def __init__(self):
                self.called = False
            def save(self, name, data):
                self.called = True
                return 'id'
        vm = VM()
        vm.checkpoint_backend = Backend()
        prog = [chunks.chunk_checkpoint()]
        list(vm.execute(decode(prog)))
        self.assertTrue(vm.checkpoint_backend.called)

    def test_jit_path(self):
        vm = VM()
        vm.jit_threshold = 1
        vm._jit.available = True
        with mock.patch.object(vm._jit, 'compile_block', wraps=vm._jit._compile_py) as comp:
            prog = decode([chunks.chunk_push(1), chunks.chunk_print()])
            ''.join(vm.execute(prog))
            self.assertTrue(comp.called)
            out = ''.join(vm.execute(prog))
            self.assertEqual(out, '1')


if __name__ == '__main__':
    unittest.main()

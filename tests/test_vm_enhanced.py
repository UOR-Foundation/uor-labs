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

    def test_comparison_and_not_ops(self):
        prog = [
            chunks.chunk_push(5),
            chunks.chunk_not(),
            chunks.chunk_print(),
            chunks.chunk_push(3),
            chunks.chunk_push(2),
            chunks.chunk_gt(),
            chunks.chunk_print(),
            chunks.chunk_push(2),
            chunks.chunk_push(3),
            chunks.chunk_lt(),
            chunks.chunk_print(),
            chunks.chunk_push(5),
            chunks.chunk_push(5),
            chunks.chunk_eq(),
            chunks.chunk_print(),
            chunks.chunk_push(4),
            chunks.chunk_push(5),
            chunks.chunk_neq(),
            chunks.chunk_print(),
            chunks.chunk_push(3),
            chunks.chunk_push(2),
            chunks.chunk_gte(),
            chunks.chunk_print(),
            chunks.chunk_push(3),
            chunks.chunk_push(3),
            chunks.chunk_lte(),
            chunks.chunk_print(),
        ]
        out = ''.join(VM().execute(decode(prog)))
        self.assertEqual(out, '-6111111')

    def test_stack_manipulation_ops(self):
        prog = [
            chunks.chunk_push(1),
            chunks.chunk_dup(),
            chunks.chunk_add(),
            chunks.chunk_print(),
            chunks.chunk_push(2),
            chunks.chunk_push(3),
            chunks.chunk_swap(),
            chunks.chunk_sub(),
            chunks.chunk_print(),
            chunks.chunk_push(4),
            chunks.chunk_push(5),
            chunks.chunk_push(6),
            chunks.chunk_rot(),
            chunks.chunk_drop(),
            chunks.chunk_print(),
            chunks.chunk_drop(),
            chunks.chunk_push(7),
            chunks.chunk_push(8),
            chunks.chunk_over(),
            chunks.chunk_sub(),
            chunks.chunk_print(),
            chunks.chunk_drop(),
            chunks.chunk_push(9),
            chunks.chunk_push(10),
            chunks.chunk_push(11),
            chunks.chunk_push(12),
            chunks.chunk_push(2),
            chunks.chunk_pick(),
            chunks.chunk_print(),
            chunks.chunk_drop(),
            chunks.chunk_drop(),
            chunks.chunk_drop(),
            chunks.chunk_drop(),
        ]
        out = ''.join(VM().execute(decode(prog)))
        self.assertEqual(out, '216110')


if __name__ == '__main__':
    unittest.main()

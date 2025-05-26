import unittest
import assembler
import chunks
from decoder import decode
from vm import VM

class ExtendedRuntimeTest(unittest.TestCase):
    def test_call_and_ret_program(self):
        src = """
        PUSH 5
        RET
        PUSH 2
        CALL -4
        ADD
        PRINT
        """
        prog = assembler.assemble(src)
        expected = [
            chunks.chunk_push(5),
            chunks.chunk_ret(),
            chunks.chunk_push(2),
            chunks.chunk_call(-4),
            chunks.chunk_add(),
            chunks.chunk_print(),
        ]
        self.assertEqual(prog, expected)
        vm = VM()
        out = ''.join(vm.execute(decode(prog)))
        self.assertEqual(out, '7')
        self.assertEqual(vm.call_stack, [])

    def test_alloc_and_free_program(self):
        src = """
        ALLOC 8
        FREE 4096
        """
        prog = assembler.assemble(src)
        expected = [
            chunks.chunk_alloc(8),
            chunks.chunk_free(4096),
        ]
        self.assertEqual(prog, expected)
        vm = VM()
        list(vm.execute(decode(prog)))
        self.assertEqual(len(vm.mem._allocations), 0)

    def test_input_and_output_program(self):
        src = """
        INPUT
        OUTPUT
        """
        prog = assembler.assemble(src)
        expected = [
            chunks.chunk_input(),
            chunks.chunk_output(),
        ]
        self.assertEqual(prog, expected)
        vm = VM()
        vm.io_in.append(42)
        out = ''.join(vm.execute(decode(prog)))
        self.assertEqual(out, '42')
        self.assertEqual(vm.io_out, [42])

    def test_network_program(self):
        src = """
        NET_RECV
        NET_SEND
        """
        prog = assembler.assemble(src)
        expected = [
            chunks.chunk_net_recv(),
            chunks.chunk_net_send(),
        ]
        self.assertEqual(prog, expected)
        vm = VM()
        list(vm.execute(decode(prog)))
        self.assertEqual(vm.stack, [0])

    def test_thread_program(self):
        src = """
        THREAD_START
        THREAD_JOIN
        """
        prog = assembler.assemble(src)
        expected = [
            chunks.chunk_thread_start(),
            chunks.chunk_thread_join(),
        ]
        self.assertEqual(prog, expected)
        vm = VM()
        list(vm.execute(decode(prog)))


if __name__ == '__main__':
    unittest.main()

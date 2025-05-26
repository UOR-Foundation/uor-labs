import unittest

import chunks
from vm import VM
from decoder import decode, DecodedInstruction
from uor.memory import SegmentedMemory
from uor.exceptions import (
    DivisionByZeroError,
    MemoryAccessError,
    InvalidOpcodeError,
    StackOverflowError,
    StackUnderflowError,
    SegmentationFaultError,
)


class VMTest(unittest.TestCase):
    def test_add(self):
        prog = [
            chunks.chunk_push(2),
            chunks.chunk_push(3),
            chunks.chunk_add(),
            chunks.chunk_print(),
        ]
        out = ''.join(VM().execute(decode(prog)))
        self.assertEqual(out, '5')

    def test_memory(self):
        prog = [
            chunks.chunk_push(7),
            chunks.chunk_store(0),
            chunks.chunk_load(0),
            chunks.chunk_print(),
        ]
        out = ''.join(VM().execute(decode(prog)))
        self.assertEqual(out, '7')

    def test_division_by_zero(self):
        prog = [
            chunks.chunk_push(1),
            chunks.chunk_push(1),
            chunks.chunk_push(1),
            chunks.chunk_sub(),
            chunks.chunk_div(),
        ]
        with self.assertRaises(DivisionByZeroError) as cm:
            list(VM().execute(decode(prog)))
        self.assertEqual(cm.exception.ip, 4)
        self.assertIn('Division by zero', str(cm.exception))

    def test_memory_access_error(self):
        addr = SegmentedMemory.STACK_START + SegmentedMemory.STACK_SIZE + 10
        prog = [chunks.chunk_load(addr)]
        with self.assertRaises(MemoryAccessError) as cm:
            list(VM().execute(decode(prog)))
        self.assertEqual(cm.exception.ip, 0)
        self.assertTrue('Address out of range' in str(cm.exception))

    def test_invalid_opcode(self):
        from primes import get_prime
        instr = DecodedInstruction(data=[(get_prime(5000), 4)])
        with self.assertRaises(InvalidOpcodeError) as cm:
            list(VM().execute([instr]))
        self.assertEqual(cm.exception.ip, 0)
        self.assertIn('Unknown opcode', str(cm.exception))

    def test_stack_overflow(self):
        old = SegmentedMemory.STACK_SIZE
        SegmentedMemory.STACK_SIZE = 1
        try:
            prog = [chunks.chunk_push(1), chunks.chunk_push(2)]
            with self.assertRaises(StackOverflowError):
                list(VM().execute(decode(prog)))
        finally:
            SegmentedMemory.STACK_SIZE = old

    def test_stack_underflow(self):
        prog = [chunks.chunk_add()]
        with self.assertRaises(StackUnderflowError) as cm:
            list(VM().execute(decode(prog)))
        self.assertEqual(cm.exception.ip, 0)

    def test_segmentation_fault(self):
        prog = [chunks.chunk_jmp(-2)]
        with self.assertRaises(SegmentationFaultError) as cm:
            list(VM().execute(decode(prog)))
        self.assertEqual(cm.exception.ip, -1)


if __name__ == '__main__':
    unittest.main()


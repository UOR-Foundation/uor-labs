import unittest

import assembler
from decoder import decode
from vm import VM
from uor.exceptions import DivisionByZeroError
from uor.memory import SegmentedMemory


class IntegrationProgramsTest(unittest.TestCase):
    def run_prog(self, text: str) -> str:
        prog = assembler.assemble(text)
        return "".join(VM().execute(decode(prog)))

    def test_fibonacci(self):
        src = """
        PUSH 10
        STORE 2
        PUSH 1
        PUSH 1
        SUB
        STORE 0
        PUSH 1
        STORE 1
        loop:
        LOAD 2
        JZ end
        LOAD 0
        PRINT
        LOAD 0
        LOAD 1
        ADD
        STORE 3
        LOAD 1
        STORE 0
        LOAD 3
        STORE 1
        LOAD 2
        PUSH 1
        SUB
        STORE 2
        JMP loop
        end:
        NOP
        """
        out = self.run_prog(src)
        self.assertEqual(out, "0112358132134")

    def test_crypto_roundtrip(self):
        src = """
        PUSH 10
        HASH
        PRINT
        PUSH 5
        SIGN
        PUSH 5
        VERIFY
        PRINT
        """
        out = self.run_prog(src)
        import hashlib
        h = hashlib.sha256(b"10").digest()
        hv = int.from_bytes(h[:4], "big")
        self.assertEqual(out, f"{hv}1")

    def test_memory_stress(self):
        mem = SegmentedMemory()
        pages = mem.HEAP_SIZE // mem.PAGE_SIZE + 5
        for _ in range(pages):
            mem.allocate(mem.PAGE_SIZE)
        self.assertLessEqual(len(mem._allocations), mem.HEAP_SIZE // mem.PAGE_SIZE)

    def test_exception_handling(self):
        src = """
        PUSH 1
        PUSH 1
        PUSH 1
        SUB
        DIV
        """
        prog = assembler.assemble(src)
        with self.assertRaises(DivisionByZeroError):
            list(VM().execute(decode(prog)))


if __name__ == "__main__":
    unittest.main()

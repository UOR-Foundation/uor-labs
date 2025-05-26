import unittest
import assembler
from decoder import decode
from vm import VM

class NewInstructionsTest(unittest.TestCase):
    def run_prog(self, text: str) -> str:
        prog = assembler.assemble(text)
        return ''.join(VM().execute(decode(prog)))

    def test_arithmetic_and_logic(self):
        src = """
        PUSH 7
        PUSH 3
        DIV
        PRINT
        PUSH 7
        PUSH 3
        MOD
        PRINT
        PUSH 6
        PUSH 3
        AND
        PRINT
        PUSH 2
        PUSH 1
        SHL
        PRINT
        PUSH 5
        NEG
        PRINT
        """
        out = self.run_prog(src)
        self.assertEqual(out, '2124-5')

    def test_float_ops(self):
        src = """
        PUSH 3
        I2F
        PUSH 2
        I2F
        FMUL
        F2I
        PRINT
        PUSH 5
        I2F
        PUSH 2
        I2F
        FDIV
        F2I
        PRINT
        """
        out = self.run_prog(src)
        self.assertEqual(out, '62')

    def test_system_and_crypto(self):
        src = """
        SYSCALL
        PRINT
        PUSH 10
        HASH
        PRINT
        PUSH 5
        SIGN
        PUSH 5
        VERIFY
        PRINT
        RNG
        PRINT
        BRK
        PUSH 9
        TRACE
        NOP
        INT
        PRINT
        """
        out = self.run_prog(src)
        import hashlib
        h = hashlib.sha256(b"10").digest()
        hv = int.from_bytes(h[:4], 'big')
        self.assertEqual(out, f"0{hv}14BRK90")

    def test_halt(self):
        src = """
        PUSH 1
        HALT
        PUSH 2
        PRINT
        """
        out = self.run_prog(src)
        self.assertEqual(out, '')

if __name__ == '__main__':
    unittest.main()

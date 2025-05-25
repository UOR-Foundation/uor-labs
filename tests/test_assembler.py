import unittest

import assembler
import chunks
from vm import VM
from decoder import decode


class AssemblerTest(unittest.TestCase):
    def test_loop(self):
        src = """
        PUSH 3
        STORE 0
        start:
        LOAD 0
        JZ end
        LOAD 0
        PRINT
        LOAD 0
        PUSH 1
        SUB
        STORE 0
        JMP start
        end:
        """
        prog = assembler.assemble(src)
        out = ''.join(VM().execute(decode(prog)))
        self.assertEqual(out, '321')

    def test_numeric_negative_jump(self):
        src = """
        PUSH 3
        STORE 0
        LOAD 0
        PRINT
        LOAD 0
        PUSH 1
        SUB
        STORE 0
        LOAD 0
        JNZ -8
        """
        prog = assembler.assemble(src)
        out = ''.join(VM().execute(decode(prog)))
        self.assertEqual(out, '321')

    def test_label_resolution_forward(self):
        src = """
        JMP end
        PUSH 1
        end:
        PUSH 2
        PRINT
        """
        prog = assembler.assemble(src)
        out = ''.join(VM().execute(decode(prog)))
        self.assertEqual(out, '2')

    def test_unknown_label_error(self):
        with self.assertRaises(ValueError):
            assembler.assemble("JMP nowhere")

    def test_invalid_instruction_error(self):
        with self.assertRaises(ValueError):
            assembler.assemble("FOO 1")


if __name__ == '__main__':
    unittest.main()


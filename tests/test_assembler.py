import unittest

import assembler
import chunks
from vm import VM


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
        out = ''.join(VM().execute(prog))
        self.assertEqual(out, '321')


if __name__ == '__main__':
    unittest.main()


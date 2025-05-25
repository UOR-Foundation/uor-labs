import unittest
import assembler
from vm import VM

class BlockOpcodeTest(unittest.TestCase):
    def test_block_executes_sub_vm(self):
        src = """
        BLOCK 4
        PUSH 1
        PUSH 2
        ADD
        PRINT
        """
        prog = assembler.assemble(src)
        out = ''.join(VM().execute(prog))
        self.assertEqual(out, '3')

if __name__ == '__main__':
    unittest.main()

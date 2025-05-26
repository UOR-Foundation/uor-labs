import unittest
import assembler
from decoder import decode
from vm import VM


class DebugAtomicInstructionsTest(unittest.TestCase):
    def run_prog(self, text: str, vm: VM | None = None) -> tuple[str, VM]:
        prog = assembler.assemble(text)
        vm = vm or VM()
        out = ''.join(vm.execute(decode(prog)))
        return out, vm

    def test_debug_output(self):
        src = """
        DEBUG
        PUSH 1
        PRINT
        """
        out, _ = self.run_prog(src)
        self.assertEqual(out, 'DEBUG1')

    def test_atomic_toggle(self):
        src = """
        ATOMIC
        ATOMIC
        """
        vm = VM()
        out, vm = self.run_prog(src, vm)
        self.assertEqual(out, '')
        self.assertFalse(vm.atomic)
        out2, vm2 = self.run_prog("ATOMIC")
        self.assertEqual(out2, '')
        self.assertTrue(vm2.atomic)


if __name__ == '__main__':
    unittest.main()

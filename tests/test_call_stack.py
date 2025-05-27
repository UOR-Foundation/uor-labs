import unittest
import assembler
from decoder import decode
from uor.debug import DebugVM


class CallStackTrackerTest(unittest.TestCase):
    def test_nested_calls(self) -> None:
        src = """
        CALL f1
        HALT
        f1:
        CALL f2
        RET
        f2:
        RET
        """
        prog = decode(assembler.assemble(src))
        vm = DebugVM()
        vm.add_breakpoint(2)
        vm.add_breakpoint(4)
        states = []
        for out in vm.execute(prog):
            frames = [(f.call_site, f.return_ip) for f in vm.call_stack_tracker.frames]
            states.append((out, vm.ip, frames))
        self.assertEqual(states[0], ("BREAK:2", 2, [(0, 1)]))
        self.assertEqual(states[1], ("BREAK:4", 4, [(0, 1), (2, 3)]))
        self.assertEqual(len(vm.call_stack_tracker.frames), 0)


if __name__ == "__main__":
    unittest.main()

import unittest

import chunks
from decoder import decode
from uor.debug import DebugVM


class DebugVMTest(unittest.TestCase):
    def test_breakpoint(self):
        prog = [chunks.chunk_push(1), chunks.chunk_print()]
        vm = DebugVM()
        vm.add_breakpoint(0)
        out = list(vm.execute(decode(prog)))
        self.assertEqual(out[0], 'BREAK:0')
        self.assertEqual(out[-1], '1')

    def test_watchpoint(self):
        prog = [
            chunks.chunk_push(7),
            chunks.chunk_store(0),
            chunks.chunk_load(0),
            chunks.chunk_print(),
        ]
        vm = DebugVM()
        vm.add_watchpoint(0)
        out = list(vm.execute(decode(prog)))
        self.assertIn('WATCH:0:write', out)
        self.assertIn('WATCH:0:read', out)
        self.assertEqual(out[-1], '7')

    def test_tracing(self):
        prog = [chunks.chunk_push(2), chunks.chunk_print()]
        vm = DebugVM()
        vm.enable_tracing()
        out = list(vm.execute(decode(prog)))
        self.assertTrue(out[0].startswith('TRACE:'))
        self.assertGreater(len(out), 0)
        self.assertEqual(out[-1], '2')


if __name__ == '__main__':
    unittest.main()

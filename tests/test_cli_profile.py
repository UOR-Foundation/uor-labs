import io
import contextlib
import unittest
from unittest import mock

import uor_cli


class CLIProfileTest(unittest.TestCase):
    def test_profile_prints_report(self):
        with mock.patch.object(uor_cli.assembler, 'assemble_file', return_value=[1]) as asm, \
             mock.patch.object(uor_cli, 'decode', return_value='decoded') as dec, \
             mock.patch.object(uor_cli, 'VM') as MockVM, \
             mock.patch.object(uor_cli, 'VMProfiler') as MockProfiler:
            vm_inst = MockVM.return_value
            vm_inst.execute.return_value = iter('')
            prof_inst = MockProfiler.return_value
            prof_inst.export_report.return_value = '{"ok":1}'
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = uor_cli.main(['profile', 'prog.asm'])
            self.assertEqual(rc, 0)
            MockVM.assert_called_with(profiler=prof_inst)
            vm_inst.execute.assert_called_with('decoded')
            self.assertEqual(buf.getvalue().strip(), '{"ok":1}')

    def test_flamegraph_prints_output(self):
        with mock.patch.object(uor_cli.assembler, 'assemble_file', return_value=[1]) as asm, \
             mock.patch.object(uor_cli, 'decode', return_value='decoded') as dec, \
             mock.patch.object(uor_cli, 'VM') as MockVM, \
             mock.patch.object(uor_cli, 'VMProfiler') as MockProfiler:
            vm_inst = MockVM.return_value
            vm_inst.execute.return_value = iter('')
            prof_inst = MockProfiler.return_value
            prof_inst.export_flamegraph.return_value = 'ip_0 0.1\n'
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = uor_cli.main(['flamegraph', 'prog.asm'])
            self.assertEqual(rc, 0)
            MockVM.assert_called_with(profiler=prof_inst)
            vm_inst.execute.assert_called_with('decoded')
            self.assertEqual(buf.getvalue(), 'ip_0 0.1\n')


if __name__ == '__main__':
    unittest.main()

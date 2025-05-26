import io
import contextlib
import unittest
from unittest import mock

import uor_cli
import chunks


class CLIUniversalTest(unittest.TestCase):
    def test_create_builds_program(self):
        expected = [chunks.chunk_un_create(4), chunks.chunk_print()]
        decoded = object()

        def fake_decode(prog):
            self.assertEqual(prog, expected)
            return decoded

        with mock.patch.object(uor_cli, 'decode', side_effect=fake_decode), \
             mock.patch.object(uor_cli, 'VM') as MockVM:
            inst = MockVM.return_value
            inst.execute.return_value = iter('X')
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = uor_cli.main(['universal', 'create', '4'])
            self.assertEqual(rc, 0)
            inst.execute.assert_called_with(decoded)
            self.assertEqual(buf.getvalue().strip(), 'X')

    def test_dwt_reads_signal(self):
        expected = [
            chunks.chunk_push(1),
            chunks.chunk_push(2),
            chunks.chunk_un_dwt(),
            chunks.chunk_print(),
        ]
        decoded = object()

        def fake_decode(prog):
            self.assertEqual(prog, expected)
            return decoded

        mopen = mock.mock_open(read_data='1 2')
        with mock.patch('builtins.open', mopen), \
             mock.patch.object(uor_cli, 'decode', side_effect=fake_decode), \
             mock.patch.object(uor_cli, 'VM') as MockVM:
            inst = MockVM.return_value
            inst.execute.return_value = iter('Y')
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = uor_cli.main(['universal', 'dwt', 'sig.txt'])
            self.assertEqual(rc, 0)
            inst.execute.assert_called_with(decoded)
            self.assertEqual(buf.getvalue().strip(), 'Y')

    def test_denoise_image(self):
        expected = [
            chunks.chunk_push(3),
            chunks.chunk_un_dwt(),
            chunks.chunk_un_trans(),
            chunks.chunk_print(),
        ]
        decoded = object()

        def fake_decode(prog):
            self.assertEqual(prog, expected)
            return decoded

        mopen = mock.mock_open(read_data='3')
        with mock.patch('builtins.open', mopen), \
             mock.patch.object(uor_cli, 'decode', side_effect=fake_decode), \
             mock.patch.object(uor_cli, 'VM') as MockVM:
            inst = MockVM.return_value
            inst.execute.return_value = iter('Z')
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = uor_cli.main(['universal', 'denoise', 'img.raw'])
            self.assertEqual(rc, 0)
            inst.execute.assert_called_with(decoded)
            self.assertEqual(buf.getvalue().strip(), 'Z')

    def test_benchmark(self):
        expected = [chunks.chunk_un_create(1)]
        decoded = object()

        def fake_decode(prog):
            self.assertEqual(prog, expected)
            return decoded

        with mock.patch.object(uor_cli, 'decode', side_effect=fake_decode), \
             mock.patch.object(uor_cli, 'VM') as MockVM, \
             mock.patch('uor_cli.time.time', side_effect=[0.0, 1.0]):
            inst = MockVM.return_value
            inst.execute.return_value = iter('')
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = uor_cli.main(['universal', 'benchmark'])
            self.assertEqual(rc, 0)
            inst.execute.assert_called_with(decoded)
            self.assertEqual(buf.getvalue().strip(), '1.000000')


if __name__ == '__main__':
    unittest.main()

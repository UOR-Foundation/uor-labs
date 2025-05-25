import unittest

from base import chunks
from base.vm import VM


class VMTest(unittest.TestCase):
    def test_add(self):
        prog = [
            chunks.chunk_push(2),
            chunks.chunk_push(3),
            chunks.chunk_add(),
            chunks.chunk_print(),
        ]
        out = ''.join(VM().execute(prog))
        self.assertEqual(out, '5')

    def test_memory(self):
        prog = [
            chunks.chunk_push(7),
            chunks.chunk_store(0),
            chunks.chunk_load(0),
            chunks.chunk_print(),
        ]
        out = ''.join(VM().execute(prog))
        self.assertEqual(out, '7')


if __name__ == '__main__':
    unittest.main()


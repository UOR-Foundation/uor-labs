import unittest
import assembler
import chunks
from vm import VM
from decoder import decode

class NTTTest(unittest.TestCase):
    def test_ntt_roundtrip(self):
        prog = assembler.assemble("NTT 3")
        prog += [chunks.chunk_data(i, ord(c)) for i, c in enumerate("XYZ")]
        out = ''.join(VM().execute(decode(prog)))
        self.assertEqual(out, 'XYZ')

if __name__ == '__main__':
    unittest.main()

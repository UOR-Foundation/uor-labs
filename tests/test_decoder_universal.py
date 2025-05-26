import unittest

import chunks
from decoder import decode
from primes import get_prime, _PRIME_IDX


class DecoderUniversalTest(unittest.TestCase):
    def _encode(self, data):
        xor = 0
        prod = 1
        for p, e in data:
            xor ^= _PRIME_IDX[p] * e
            prod *= p ** e
        chk = get_prime(xor)
        return prod * (chk ** 6)

    def _roundtrip(self, chunk, expected_pairs):
        inst = decode([chunk])[0]
        self.assertEqual(set(inst.data), set(expected_pairs))
        self.assertEqual(self._encode(inst.data), chunk)

    def test_un_create(self):
        chunk = chunks.chunk_un_create(4)
        self._roundtrip(chunk, [(chunks.OP_UN_CREATE, 4), (get_prime(4), 5)])

    def test_un_grade(self):
        chunk = chunks.chunk_un_grade(2)
        self._roundtrip(chunk, [(chunks.OP_UN_GRADE, 4), (get_prime(2), 5)])

    def test_un_inner(self):
        chunk = chunks.chunk_un_inner()
        self._roundtrip(chunk, [(chunks.OP_UN_INNER, 4)])

    def test_un_norm(self):
        chunk = chunks.chunk_un_norm()
        self._roundtrip(chunk, [(chunks.OP_UN_NORM, 4)])

    def test_un_trans(self):
        chunk = chunks.chunk_un_trans()
        self._roundtrip(chunk, [(chunks.OP_UN_TRANS, 4)])

    def test_un_dwt(self):
        chunk = chunks.chunk_un_dwt()
        self._roundtrip(chunk, [(chunks.OP_UN_DWT, 4)])


if __name__ == "__main__":
    unittest.main()

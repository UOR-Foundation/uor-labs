import time
import unittest

from primes import get_prime


def naive_get_prime(idx: int) -> int:
    primes = [2]
    candidate = 3
    while len(primes) <= idx:
        for p in primes:
            if candidate % p == 0:
                break
        else:
            primes.append(candidate)
        candidate += 1
    return primes[idx]


class PrimeBenchTest(unittest.TestCase):
    def test_sieve_faster_than_naive(self):
        idx = 2000
        start = time.time()
        naive_get_prime(idx)
        naive_time = time.time() - start
        start = time.time()
        get_prime(idx)
        sieve_time = time.time() - start
        self.assertLess(sieve_time, naive_time)


if __name__ == "__main__":
    unittest.main()

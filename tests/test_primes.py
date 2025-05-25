import time
import unittest

from primes import get_prime, factor, _FACTOR_CACHE


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


class FactorRegressionTest(unittest.TestCase):
    def test_factor_cache_original_input(self):
        _FACTOR_CACHE.clear()
        result = factor(12)
        self.assertEqual(result, [(2, 2), (3, 1)])
        self.assertIn(12, _FACTOR_CACHE)
        self.assertEqual(_FACTOR_CACHE[12], result)


if __name__ == "__main__":
    unittest.main()

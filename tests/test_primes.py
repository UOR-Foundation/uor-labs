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

    def test_factor_cache_returns_copy(self):
        _FACTOR_CACHE.clear()
        result1 = factor(12)
        result1.append((5, 1))
        self.assertIn(12, _FACTOR_CACHE)
        self.assertEqual(_FACTOR_CACHE[12], [(2, 2), (3, 1)])
        result2 = factor(12)
        self.assertEqual(result2, [(2, 2), (3, 1)])
        self.assertIsNot(result2, _FACTOR_CACHE[12])

    def test_factor_cache_reused(self):
        _FACTOR_CACHE.clear()
        factor(18)
        cache_snapshot = dict(_FACTOR_CACHE)
        factor(18)
        self.assertEqual(_FACTOR_CACHE, cache_snapshot)


class SegmentedSieveTest(unittest.TestCase):
    def setUp(self):
        import primes
        self.orig_primes = list(primes._PRIMES)
        self.orig_idx = dict(primes._PRIME_IDX)
        self.orig_limit = primes._sieve_limit
        primes._PRIMES[:] = [2]
        primes._PRIME_IDX.clear()
        primes._PRIME_IDX[2] = 0
        primes._sieve_limit = 2

    def tearDown(self):
        import primes
        primes._PRIMES[:] = self.orig_primes
        primes._PRIME_IDX.clear()
        primes._PRIME_IDX.update(self.orig_idx)
        primes._sieve_limit = self.orig_limit

    def test_generator_yields_primes(self):
        import primes
        result = list(primes.segmented_sieve(20, segment_size=10))
        self.assertEqual(result, [3, 5, 7, 11, 13, 17, 19])
        self.assertEqual(primes._PRIMES, [2, 3, 5, 7, 11, 13, 17, 19])


if __name__ == "__main__":
    unittest.main()

import time
import unittest

from primes import (
    miller_rabin,
    pollard_rho,
    optimized_factorize,
    factor,
    _FACTOR_CACHE,
)


class PrimalityTest(unittest.TestCase):
    def test_miller_rabin_basic(self):
        self.assertTrue(miller_rabin(101))
        self.assertFalse(miller_rabin(102))

    def test_pollard_rho_factor(self):
        n = 1000003 * 1000033
        f = pollard_rho(n)
        self.assertNotEqual(f, 1)
        self.assertNotEqual(f, n)
        self.assertEqual(n % f, 0)


class OptimizedFactorTest(unittest.TestCase):
    def test_factor_correctness(self):
        nums = [12, 12345, 1000003 * 1000033]
        for n in nums:
            self.assertEqual(sorted(optimized_factorize(n)), sorted(factor(n)))

    def test_optimized_faster_than_standard(self):
        n = 1000003 * 1000033
        start = time.time()
        factor(n)
        normal = time.time() - start

        start = time.time()
        optimized_factorize(n)
        opt = time.time() - start

        self.assertLess(opt, normal)

    def test_cache_reused(self):
        _FACTOR_CACHE.clear()
        optimized_factorize(18)
        cache_snapshot = dict(_FACTOR_CACHE)
        optimized_factorize(18)
        self.assertEqual(_FACTOR_CACHE, cache_snapshot)


if __name__ == "__main__":
    unittest.main()

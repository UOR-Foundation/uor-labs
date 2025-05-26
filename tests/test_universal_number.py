import unittest

from uor.universal_number import UniversalNumber


class UniversalNumberTest(unittest.TestCase):
    def test_prime_factorization_cache(self):
        UniversalNumber._prime_cache.clear()
        num1 = UniversalNumber(12)
        self.assertEqual(num1.prime_coords, {2: 2, 3: 1})
        self.assertIn(12, UniversalNumber._prime_cache)
        # modify result and ensure cache not affected
        num1.prime_coords[5] = 1
        num2 = UniversalNumber(12)
        self.assertEqual(num2.prime_coords, {2: 2, 3: 1})
        self.assertEqual(UniversalNumber._prime_cache[12], {2: 2, 3: 1})

    def test_reference_frame(self):
        num = UniversalNumber(1)
        frame = num.reference_frame
        self.assertIn("e1", frame)
        self.assertIn("e12", frame)
        self.assertIn("e123", frame)

    def test_get_graded_components(self):
        num = UniversalNumber(123)
        self.assertEqual(num.getGradedComponents([10, 10, 10]), [3, 2, 1])

    def test_inner_product_and_norm(self):
        num1 = UniversalNumber(12)
        num2 = UniversalNumber(18)
        self.assertEqual(num1.innerProduct(num2), 4)
        self.assertAlmostEqual(num1.coherenceNorm(), (5) ** 0.5)


if __name__ == "__main__":
    unittest.main()

import unittest

from uor.uor_object import UORObject


class UORObjectTest(unittest.TestCase):
    def test_coherence_norm_zero(self):
        obj = UORObject(30)
        self.assertAlmostEqual(obj.coherence_norm(), 0.0)

    def test_serialization_roundtrip(self):
        obj = UORObject(42)
        enc = obj.to_prime_encoding()
        obj2 = UORObject.from_prime_encoding(enc)
        self.assertEqual(obj, obj2)

    def test_transform_preserves_coherence(self):
        obj = UORObject(7)
        obj2 = obj.transform(lambda x: x * 2)
        self.assertAlmostEqual(obj2.coherence_norm(), 0.0)
        self.assertEqual(obj2.content_num.value, 14)

    def test_observer_transformation(self):
        obj = UORObject(15)
        obj2 = obj.transform_observer((4, 1))
        self.assertAlmostEqual(obj2.coherence_norm(), 0.0)


if __name__ == "__main__":
    unittest.main()

import threading
import unittest

from uor.cache import InstructionCache


class InstructionCacheTest(unittest.TestCase):
    def test_eviction(self):
        cache = InstructionCache(max_size=2)
        cache.put(1, 'a')
        cache.put(2, 'b')
        cache.get(1)  # mark 1 as recently used
        cache.put(3, 'c')  # should evict key 2
        self.assertIsNone(cache.get(2))
        self.assertEqual(cache.get(1), 'a')
        self.assertEqual(cache.get(3), 'c')
        stats = cache.get_stats()
        self.assertEqual(stats['size'], 2)
        self.assertEqual(stats['hits'], 3)
        self.assertEqual(stats['misses'], 1)
        self.assertAlmostEqual(stats['hit_rate'], 0.75)
        self.assertEqual(stats['avg_decode_time_saved'], 0.0)

    def test_thread_safety(self):
        cache = InstructionCache(max_size=1000)

        def worker(start):
            for i in range(100):
                cache.put(start + i, i)
                self.assertIsNotNone(cache.get(start + i))

        threads = [threading.Thread(target=worker, args=(j * 1000,)) for j in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        stats = cache.get_stats()
        self.assertEqual(stats['misses'], 0)
        self.assertEqual(stats['hits'], 5 * 100)
        self.assertEqual(stats['size'], 5 * 100)
        self.assertEqual(stats['hit_rate'], 1.0)
        self.assertEqual(stats['avg_decode_time_saved'], 0.0)

    def test_time_saved_metric(self):
        cache = InstructionCache(max_size=2)
        cache.put(1, 'a', decode_time=1.0)
        cache.put(2, 'b', decode_time=0.5)
        self.assertEqual(cache.get(1), 'a')
        self.assertEqual(cache.get(2), 'b')

        stats = cache.get_stats()
        self.assertEqual(stats['hits'], 2)
        self.assertEqual(stats['misses'], 0)
        self.assertEqual(stats['size'], 2)
        self.assertEqual(stats['hit_rate'], 1.0)
        self.assertAlmostEqual(stats['avg_decode_time_saved'], 0.75)


if __name__ == '__main__':
    unittest.main()

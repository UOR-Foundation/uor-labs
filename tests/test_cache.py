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


if __name__ == '__main__':
    unittest.main()

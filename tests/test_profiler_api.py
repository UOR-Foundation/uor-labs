import unittest

import chunks
from decoder import decode, _CACHE
from vm import VM
from uor.profiler import VMProfiler


class VMProfilerTest(unittest.TestCase):
    def test_basic_metrics(self):
        prog = [
            chunks.chunk_push(7),
            chunks.chunk_store(0),
            chunks.chunk_load(0),
            chunks.chunk_print(),
        ]
        _CACHE.clear()
        profiler = VMProfiler()
        vm = VM(profiler=profiler)
        out = ''.join(vm.execute(decode(prog)))
        self.assertEqual(out, '7')
        metrics = profiler.metrics()
        self.assertEqual(metrics['instruction_count'], len(prog))
        self.assertEqual(metrics['memory_access'][0]['write'], 1)
        self.assertEqual(metrics['memory_access'][0]['read'], 1)
        self.assertIn('cache_stats', metrics)

    def test_flamegraph_export(self):
        _CACHE.clear()
        prog = [chunks.chunk_push(1), chunks.chunk_print()]
        profiler = VMProfiler()
        vm = VM(profiler=profiler)
        list(vm.execute(decode(prog)))
        flame = profiler.export_flamegraph()
        self.assertTrue(flame.strip().startswith('ip_'))


if __name__ == '__main__':
    unittest.main()

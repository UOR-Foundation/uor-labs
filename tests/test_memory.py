import unittest

from uor.memory import SegmentedMemory
from vm import VM


class SegmentedMemoryTest(unittest.TestCase):
    def test_segment_bounds(self):
        mem = SegmentedMemory()
        mem.store(SegmentedMemory.DATA_START, 1)
        self.assertEqual(mem.load(SegmentedMemory.DATA_START), 1)
        with self.assertRaises(MemoryError):
            mem.load(SegmentedMemory.STACK_START + SegmentedMemory.STACK_SIZE + 10)

    def test_gc(self):
        mem = SegmentedMemory()
        a1 = mem.allocate(10)
        a2 = mem.allocate(10)
        mem.store(a1, a2)
        # remove reference so second block becomes unreachable
        mem.store(a1, 0)
        class Dummy:
            pass
        vm = Dummy()
        vm.stack = [a1]
        vm.call_stack = []
        mem.collect(vm)
        self.assertIn(a1, mem._allocations)
        self.assertNotIn(a2, mem._allocations)

    def test_memory_mapped_io(self):
        vm = VM()
        vm.io_in.append(42)
        val = vm.mem.load(SegmentedMemory.MMIO_IN)
        self.assertEqual(val, 42)
        vm.mem.store(SegmentedMemory.MMIO_OUT, 99)
        self.assertIn(99, vm.io_out)

    def test_code_segment_protection(self):
        mem = SegmentedMemory()
        mem.load_code([1, 2, 3])
        self.assertEqual(mem.load(mem.CODE_START), 1)
        with self.assertRaises(MemoryError):
            mem.store(mem.CODE_START, 5)

    def test_memory_map_visualization(self):
        mem = SegmentedMemory()
        mapping = mem.memory_map()
        self.assertIn("CODE", mapping)
        self.assertIn("DATA", mapping)


if __name__ == "__main__":
    unittest.main()

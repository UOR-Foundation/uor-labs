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

    def test_permission_enforcement(self):
        mem = SegmentedMemory()
        mem.load_code([1])
        with self.assertRaises(MemoryError):
            mem.store(mem.CODE_START, 3)
        with self.assertRaises(MemoryError):
            mem.load(mem.MMIO_OUT)
        with self.assertRaises(MemoryError):
            mem.store(mem.MMIO_IN, 1)

    def test_allocate_helpers(self):
        mem = SegmentedMemory()
        sp = mem.stack_pointer
        addr_s = mem.allocate_stack(4)
        self.assertEqual(addr_s, sp)
        self.assertEqual(mem.stack_pointer, sp + 4)
        hp = mem.heap_pointer
        addr_h = mem.allocate_heap(8)
        self.assertEqual(addr_h, hp)
        self.assertEqual(mem.heap_pointer, hp + 8)
        mem.store(addr_s, 1)
        mem.store(addr_h, 2)
        self.assertEqual(mem.load(addr_s), 1)
        self.assertEqual(mem.load(addr_h), 2)

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

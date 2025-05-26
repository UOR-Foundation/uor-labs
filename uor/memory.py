"""Segmented memory model for the UOR VM."""
from __future__ import annotations

import math
from typing import Dict, List, Optional


class SegmentedMemory:
    """Simple segmented memory with heap allocation and GC."""

    PAGE_SIZE = 256
    DATA_SIZE = 0x1000
    HEAP_SIZE = 0x1000
    STACK_SIZE = 0x1000

    DATA_START = 0x0000
    HEAP_START = DATA_START + DATA_SIZE
    STACK_START = HEAP_START + HEAP_SIZE

    MMIO_IN = STACK_START + STACK_SIZE
    MMIO_OUT = MMIO_IN + 1

    def __init__(self, vm=None) -> None:
        self.vm = vm
        self.storage: Dict[int, int] = {}
        self._free_pages = set(range(self.HEAP_SIZE // self.PAGE_SIZE))
        self._allocations: Dict[int, Dict[str, object]] = {}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _segment(self, addr: int) -> str:
        if self.DATA_START <= addr < self.HEAP_START:
            return "data"
        if self.HEAP_START <= addr < self.STACK_START:
            return "heap"
        if self.STACK_START <= addr < self.STACK_START + self.STACK_SIZE:
            return "stack"
        if addr in (self.MMIO_IN, self.MMIO_OUT):
            return "mmio"
        raise MemoryError("Address out of range")

    def _page_for(self, addr: int) -> int:
        return (addr - self.HEAP_START) // self.PAGE_SIZE

    def _alloc_for_addr(self, addr: int) -> Optional[int]:
        for start, info in self._allocations.items():
            pages = info["pages"]  # type: ignore
            size = info["size"]  # type: ignore
            start_page = self._page_for(start)
            if start <= addr < start + size:
                return start
            if any(start_page + i == self._page_for(addr) for i in pages):
                return start
        return None

    # ------------------------------------------------------------------
    # Basic load/store with MMIO
    # ------------------------------------------------------------------
    def load(self, addr: int) -> int:
        seg = self._segment(addr)
        if seg == "mmio":
            if addr == self.MMIO_IN:
                if self.vm and self.vm.io_in:
                    return self.vm.io_in.pop(0)
                return 0
            raise MemoryError("Cannot load from MMIO address")
        return self.storage.get(addr, 0)

    def store(self, addr: int, value: int) -> None:
        seg = self._segment(addr)
        if seg == "mmio":
            if addr == self.MMIO_OUT:
                if self.vm is not None:
                    self.vm.io_out.append(value)
                return
            raise MemoryError("Cannot store to MMIO_IN")
        self.storage[addr] = value

    # ------------------------------------------------------------------
    # Allocation helpers
    # ------------------------------------------------------------------
    def allocate(self, size: int, vm=None) -> int:
        addr = self._try_allocate(size)
        if addr is None:
            self.collect(vm or self.vm)
            addr = self._try_allocate(size)
            if addr is None:
                raise MemoryError("Out of memory")
        return addr

    def _try_allocate(self, size: int) -> Optional[int]:
        pages_needed = math.ceil(size / self.PAGE_SIZE)
        pages = sorted(self._free_pages)
        for i in range(len(pages) - pages_needed + 1):
            run = pages[i : i + pages_needed]
            if run == list(range(pages[i], pages[i] + pages_needed)):
                for p in run:
                    self._free_pages.remove(p)
                start = self.HEAP_START + run[0] * self.PAGE_SIZE
                self._allocations[start] = {"pages": run, "size": size, "marked": False}
                for o in range(size):
                    self.storage[start + o] = 0
                return start
        return None

    def free(self, addr: int) -> None:
        info = self._allocations.pop(addr, None)
        if not info:
            return
        for p in info["pages"]:  # type: ignore
            self._free_pages.add(p)
            base = self.HEAP_START + p * self.PAGE_SIZE
            for o in range(self.PAGE_SIZE):
                self.storage.pop(base + o, None)

    # ------------------------------------------------------------------
    # Mark and sweep GC
    # ------------------------------------------------------------------
    def collect(self, vm=None) -> None:
        roots: List[int] = []
        if vm is not None:
            roots.extend(v for v in getattr(vm, "stack", []) if isinstance(v, int))
            roots.extend(v for v in getattr(vm, "call_stack", []) if isinstance(v, int))
        roots.extend(v for v in self.storage.values() if isinstance(v, int))
        work = [r for r in roots if self.HEAP_START <= r < self.STACK_START]
        marked = set()
        while work:
            ptr = work.pop()
            start = self._alloc_for_addr(ptr)
            if start is None or start in marked:
                continue
            marked.add(start)
            info = self._allocations.get(start)
            if not info:
                continue
            size = info["size"]  # type: ignore
            for o in range(size):
                val = self.storage.get(start + o)
                if (
                    isinstance(val, int)
                    and self.HEAP_START <= val < self.STACK_START
                    and self._alloc_for_addr(val) not in marked
                ):
                    work.append(val)
        for start, info in list(self._allocations.items()):
            if start not in marked:
                self.free(start)
            else:
                info["marked"] = False

    # ------------------------------------------------------------------
    # Helpers for checkpointing
    # ------------------------------------------------------------------
    def dump(self) -> Dict[int, int]:
        return dict(self.storage)

    def load_dump(self, data: Dict[int, int]) -> None:
        self.storage = dict(data)

    def __len__(self) -> int:
        return len(self.storage)


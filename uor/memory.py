"""Segmented memory model for the UOR VM."""
from __future__ import annotations

import math
from typing import Dict, List, Optional
from enum import Enum, auto


class MemorySegment(Enum):
    """Logical memory segments."""

    CODE = auto()
    DATA = auto()
    HEAP = auto()
    STACK = auto()
    MMIO_IN = auto()
    MMIO_OUT = auto()


class SegmentedMemory:
    """Simple segmented memory with heap allocation and GC."""

    # default segment sizes
    CODE_SIZE = 0x1000
    DATA_SIZE = 0x1000
    HEAP_SIZE = 0x1000
    STACK_SIZE = 0x1000

    PAGE_SIZE = 256

    # default starts (data begins at 0 for backward compat)
    CODE_START = -CODE_SIZE
    DATA_START = 0x0000
    HEAP_START = DATA_START + DATA_SIZE
    STACK_START = HEAP_START + HEAP_SIZE

    MMIO_IN = STACK_START + STACK_SIZE
    MMIO_OUT = MMIO_IN + 1

    def __init__(
        self,
        vm=None,
        *,
        code: Optional[List[int]] = None,
        code_size: int | None = None,
        data_size: int | None = None,
        heap_size: int | None = None,
        stack_size: int | None = None,
    ) -> None:
        self.vm = vm

        self.CODE_SIZE = code_size or self.CODE_SIZE
        self.DATA_SIZE = data_size or self.DATA_SIZE
        self.HEAP_SIZE = heap_size or self.HEAP_SIZE
        self.STACK_SIZE = stack_size or self.STACK_SIZE

        self.CODE_START = -self.CODE_SIZE
        self.DATA_START = 0
        self.HEAP_START = self.DATA_START + self.DATA_SIZE
        self.STACK_START = self.HEAP_START + self.HEAP_SIZE
        self.MMIO_IN = self.STACK_START + self.STACK_SIZE
        self.MMIO_OUT = self.MMIO_IN + 1

        self.segments: Dict[MemorySegment, Dict[int, int]] = {
            MemorySegment.DATA: {},
            MemorySegment.HEAP: {},
            MemorySegment.STACK: {},
        }
        self.permissions = {
            MemorySegment.CODE: {"read": True, "write": False, "execute": True},
            MemorySegment.DATA: {"read": True, "write": True, "execute": False},
            MemorySegment.HEAP: {"read": True, "write": True, "execute": False},
            MemorySegment.STACK: {"read": True, "write": True, "execute": False},
            MemorySegment.MMIO_IN: {"read": True, "write": False, "execute": False},
            MemorySegment.MMIO_OUT: {"read": False, "write": True, "execute": False},
        }

        self.heap_pointer = self.HEAP_START
        self.stack_pointer = self.STACK_START

        self._free_pages = set(range(self.HEAP_SIZE // self.PAGE_SIZE))
        self._allocations: Dict[int, Dict[str, object]] = {}

        self.code: List[int] = []
        if code:
            self.load_code(code)

    def load_code(self, code: List[int]) -> None:
        """Load prime-encoded instructions into the code segment."""
        if len(code) > self.CODE_SIZE:
            raise MemoryError("Program too large for code segment")
        self.code = list(code)

    def memory_map(self) -> str:
        """Return a simple textual map of all memory segments."""
        segs = [
            ("CODE", self.CODE_START, self.CODE_START + self.CODE_SIZE - 1),
            ("DATA", self.DATA_START, self.DATA_START + self.DATA_SIZE - 1),
            ("HEAP", self.HEAP_START, self.HEAP_START + self.HEAP_SIZE - 1),
            ("STACK", self.STACK_START, self.STACK_START + self.STACK_SIZE - 1),
            ("MMIO_IN", self.MMIO_IN, self.MMIO_IN),
            ("MMIO_OUT", self.MMIO_OUT, self.MMIO_OUT),
        ]
        lines = [f"{name:8s}: {start:#06x}-{end:#06x}" for name, start, end in segs]
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _segment(self, addr: int) -> MemorySegment:
        if self.CODE_START <= addr < self.CODE_START + self.CODE_SIZE:
            return MemorySegment.CODE
        if self.DATA_START <= addr < self.HEAP_START:
            return MemorySegment.DATA
        if self.HEAP_START <= addr < self.STACK_START:
            return MemorySegment.HEAP
        if self.STACK_START <= addr < self.STACK_START + self.STACK_SIZE:
            return MemorySegment.STACK
        if addr == self.MMIO_IN:
            return MemorySegment.MMIO_IN
        if addr == self.MMIO_OUT:
            return MemorySegment.MMIO_OUT
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
        if not self.permissions[seg]["read"]:
            if seg == MemorySegment.MMIO_OUT:
                raise MemoryError("Cannot load from MMIO address")
            raise MemoryError("Read permission denied")

        if seg == MemorySegment.CODE:
            idx = addr - self.CODE_START
            if 0 <= idx < len(self.code):
                return self.code[idx]
            raise MemoryError("Code address out of range")

        if seg == MemorySegment.MMIO_IN:
            if self.vm and self.vm.io_in:
                return self.vm.io_in.pop(0)
            return 0

        return self.segments[seg].get(addr, 0)

    def store(self, addr: int, value: int) -> None:
        seg = self._segment(addr)
        if not self.permissions[seg]["write"]:
            if seg == MemorySegment.CODE:
                raise MemoryError("Cannot write to code segment")
            if seg == MemorySegment.MMIO_IN:
                raise MemoryError("Cannot store to MMIO_IN")
            raise MemoryError("Write permission denied")

        if seg == MemorySegment.MMIO_OUT:
            if self.vm is not None:
                self.vm.io_out.append(value)
            return

        self.segments[seg][addr] = value

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

    def allocate_heap(self, size: int) -> int:
        if self.heap_pointer + size > self.STACK_START:
            raise MemoryError("Out of heap memory")
        addr = self.heap_pointer
        for o in range(size):
            self.segments[MemorySegment.HEAP][addr + o] = 0
        self.heap_pointer += size
        return addr

    def allocate_stack(self, size: int) -> int:
        if self.stack_pointer + size > self.STACK_START + self.STACK_SIZE:
            raise MemoryError("Out of stack memory")
        addr = self.stack_pointer
        for o in range(size):
            self.segments[MemorySegment.STACK][addr + o] = 0
        self.stack_pointer += size
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
                    self.segments[MemorySegment.HEAP][start + o] = 0
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
                self.segments[MemorySegment.HEAP].pop(base + o, None)

    # ------------------------------------------------------------------
    # Mark and sweep GC
    # ------------------------------------------------------------------
    def collect(self, vm=None) -> None:
        roots: List[int] = []
        if vm is not None:
            roots.extend(v for v in getattr(vm, "stack", []) if isinstance(v, int))
            roots.extend(v for v in getattr(vm, "call_stack", []) if isinstance(v, int))
        all_vals = []
        for store in self.segments.values():
            all_vals.extend(store.values())
        roots.extend(v for v in all_vals if isinstance(v, int))
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
                val = self.segments[MemorySegment.HEAP].get(start + o)
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
        data: Dict[int, int] = {}
        for store in self.segments.values():
            data.update(store)
        return data

    def load_dump(self, data: Dict[int, int]) -> None:
        for seg in self.segments.values():
            seg.clear()
        for addr, val in data.items():
            seg = self._segment(addr)
            if seg in (MemorySegment.MMIO_IN, MemorySegment.MMIO_OUT, MemorySegment.CODE):
                continue
            self.segments[seg][addr] = val

    def __len__(self) -> int:
        return sum(len(seg) for seg in self.segments.values())


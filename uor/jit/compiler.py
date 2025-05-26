from __future__ import annotations

import ctypes
import os
import platform
import subprocess
import tempfile
import time
from typing import Callable, Dict, Iterable, List, Optional, Tuple

from decoder import DecodedInstruction
from primes import _PRIME_IDX
from chunks import (
    OP_PUSH,
    OP_ADD,
    OP_SUB,
    OP_MUL,
    OP_DIV,
    OP_MOD,
    OP_NEG,
)


class JITBlock:
    """Callable wrapper for compiled blocks."""

    def __init__(self, func: Callable[["VM"], Iterable[str]], end_ip: int) -> None:
        self.func = func
        self.end_ip = end_ip

    def __call__(self, vm: "VM") -> Iterable[str]:
        return self.func(vm)


class JITCompiler:
    """JIT compiler using a tiny C backend with caching."""

    def __init__(self, ttl: float = 60.0) -> None:
        self.arch = platform.machine().lower()
        self.available = self.arch in {"x86_64", "amd64", "aarch64", "arm64"}
        self.ttl = ttl
        self._cache: Dict[Tuple[Tuple[Tuple[int, int], ...], ...], Tuple[JITBlock, float]] = {}
        self.blocks_compiled = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.trace: Dict[int, int] = {}

    # ------------------------------------------------------------------
    def compile_block(self, instructions: List[DecodedInstruction]) -> Optional[JITBlock]:
        """Compile ``instructions`` and return a ``JITBlock``."""
        key = tuple(tuple(instr.data) for instr in instructions)
        self._prune()
        entry = self._cache.get(key)
        if entry is not None:
            self.cache_hits += 1
            return entry[0]
        self.cache_misses += 1
        block = self._compile_native(instructions) if self.available else None
        if block is None:
            block = self._compile_py(instructions)
        self._cache[key] = (block, time.time() + self.ttl)
        self.blocks_compiled += 1
        return block

    # ------------------------------------------------------------------
    def _prune(self) -> None:
        now = time.time()
        for k, (_, exp) in list(self._cache.items()):
            if exp < now:
                self._cache.pop(k, None)

    # ------------------------------------------------------------------
    def _compile_py(self, instructions: List[DecodedInstruction]) -> JITBlock:
        """Fallback: execute instructions via regular handlers."""

        def block(vm: "VM") -> Iterable[str]:
            for instr in instructions:
                op = next(p for p, e in instr.data if e == 4)
                handler = vm._dispatch[op]
                yield from handler(instr.data)
            vm.ip += len(instructions)
            return iter(())

        return JITBlock(block, end_ip=0)

    # ------------------------------------------------------------------
    def _compile_native(self, instructions: List[DecodedInstruction]) -> Optional[JITBlock]:
        supported = {OP_PUSH, OP_ADD, OP_SUB, OP_MUL, OP_DIV, OP_MOD, OP_NEG}
        lines: List[str] = []
        for instr in instructions:
            op = next((p for p, e in instr.data if e == 4), None)
            if op not in supported:
                return None
            if op == OP_PUSH:
                vp = next(p for p, e in instr.data if e == 5)
                val = _PRIME_IDX[vp]
                lines.append(f"stack[++sp] = {val};")
            elif op == OP_ADD:
                lines.append("sp--; stack[sp] = stack[sp] + stack[sp+1];")
            elif op == OP_SUB:
                lines.append("sp--; stack[sp] = stack[sp] - stack[sp+1];")
            elif op == OP_MUL:
                lines.append("sp--; stack[sp] = stack[sp] * stack[sp+1];")
            elif op == OP_DIV:
                lines.append("sp--; if(stack[sp+1]==0) return; stack[sp]=stack[sp]/stack[sp+1];")
            elif op == OP_MOD:
                lines.append("sp--; if(stack[sp+1]==0) return; stack[sp]=stack[sp]%stack[sp+1];")
            elif op == OP_NEG:
                lines.append("stack[sp] = -stack[sp];")

        c_src = "\n".join(
            [
                "#include <stdint.h>",
                "void block(long *stack, long *sp_ptr){",
                "    long sp = *sp_ptr;",
                *(f"    {ln}" for ln in lines),
                "    *sp_ptr = sp;",
                "}",
            ]
        )

        td = tempfile.mkdtemp()
        c_file = os.path.join(td, "block.c")
        so_file = os.path.join(td, "block.so")
        with open(c_file, "w") as f:
            f.write(c_src)
        try:
            subprocess.run([
                "gcc",
                "-shared",
                "-O2",
                "-fPIC",
                c_file,
                "-o",
                so_file,
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            return None
        lib = ctypes.CDLL(so_file)
        func = lib.block
        func.argtypes = [ctypes.POINTER(ctypes.c_long), ctypes.POINTER(ctypes.c_long)]
        func.restype = None

        def block(vm: "VM") -> Iterable[str]:  # pragma: no cover - runtime
            size = len(vm.stack) + 32
            arr_type = ctypes.c_long * size
            arr = arr_type(*vm.stack, *([0] * (size - len(vm.stack))))
            sp = ctypes.c_long(len(vm.stack) - 1)
            func(arr, ctypes.byref(sp))
            vm.stack = list(arr)[: sp.value + 1]
            vm.ip += len(instructions)
            return iter(())

        return JITBlock(block, end_ip=0)


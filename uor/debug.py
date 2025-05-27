"""Debugging utilities for the UOR VM."""
from __future__ import annotations

from typing import Dict, List, Iterator, Optional, Set, Tuple
import time

from vm import VM
from uor.debugger import CallStackTracker
from decoder import DecodedInstruction
from chunks import (
    OP_LOAD,
    OP_STORE,
    BLOCK_TAG,
    NTT_TAG,
    T_MOD,
    NTT_ROOT,
)
from primes import _PRIME_IDX
from uor.exceptions import InvalidOpcodeError


class DebugVM(VM):
    """VM subclass with interactive debugging helpers."""

    def __init__(self, profiler: Optional[object] = None) -> None:
        super().__init__(profiler=profiler)
        self.call_stack_tracker = CallStackTracker()
        self.breakpoints: Set[int] = set()
        self.watchpoints: Dict[int, str] = {}
        self.tracing: bool = False
        self._step_mode: bool = False

        # override dispatch for load/store to watch memory
        self._dispatch[OP_LOAD] = self._op_load
        self._dispatch[OP_STORE] = self._op_store

    # ------------------------------------------------------------------
    # Breakpoints / watchpoints setup
    # ------------------------------------------------------------------
    def add_breakpoint(self, ip: int) -> None:
        self.breakpoints.add(ip)

    def remove_breakpoint(self, ip: int) -> None:
        self.breakpoints.discard(ip)

    def clear_breakpoints(self) -> None:
        self.breakpoints.clear()

    def add_watchpoint(self, addr: int, mode: str = "rw") -> None:
        self.watchpoints[addr] = mode

    def remove_watchpoint(self, addr: int) -> None:
        self.watchpoints.pop(addr, None)

    def enable_tracing(self) -> None:
        self.tracing = True

    def disable_tracing(self) -> None:
        self.tracing = False

    def step(self) -> None:
        """Pause after the next instruction."""
        self._step_mode = True

    def backtrace(self) -> str:
        """Return a formatted backtrace of call frames."""
        if self.call_stack_tracker is None:
            return ""
        lines = []
        for idx, frame in enumerate(self.call_stack_tracker.backtrace()):
            lines.append(f"#{idx} call@{frame.call_site} -> {frame.return_ip}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------
    def execute(
        self, program: List[DecodedInstruction], resume: bool = False
    ) -> Iterator[str]:
        if not resume:
            self.ip = 0
        self._program_len = len(program)
        if self.profiler:
            self.profiler.reset()
        while self.ip < len(program):
            if self.ip in self.breakpoints or self._step_mode:
                bp = self.ip
                self._step_mode = False
                self.remove_breakpoint(bp)
                yield f"BREAK:{bp}"
                continue

            if self.tracing:
                yield f"TRACE:{self.ip}"

            ip_before = self.ip
            if self._jit.available and self.ip in self._compiled:
                block, exp = self._compiled[self.ip]
                if exp < time.time():
                    self._compiled.pop(self.ip, None)
                else:
                    start_t = time.perf_counter()
                    yield from block(self)
                    duration = time.perf_counter() - start_t
                    self.executed_instructions += 1
                    if self.profiler:
                        self.profiler.record_instruction(ip_before, None, duration, cache_hit=True)
                    if self.checkpoint_policy and self.checkpoint_policy.should_checkpoint(self):
                        self.checkpoint()
                    continue

            instr = program[self.ip]
            self._counter[self.ip] = self._counter.get(self.ip, 0) + 1
            if (
                self._jit.available
                and self._counter[self.ip] >= self.jit_threshold
                and self.ip not in self._compiled
            ):
                block = self._jit.compile_block([instr])
                if block is not None:
                    self._compiled[self.ip] = (block, time.time() + self._jit.ttl)

            self.ip += 1
            data = instr.data

            if any(p == BLOCK_TAG and e == 7 for p, e in data):
                start_t = time.perf_counter()
                yield from DebugVM().execute(instr.inner or [])
                duration = time.perf_counter() - start_t
                self.executed_instructions += 1
                if self.profiler:
                    self.profiler.record_instruction(ip_before, None, duration)
                if self.checkpoint_policy and self.checkpoint_policy.should_checkpoint(self):
                    self.checkpoint()
                continue

            if any(p == NTT_TAG and e == 4 for p, e in data):
                inner = instr.inner or []
                vec = [next((e2 for _, e2 in i.data if e2 > 0), 0) for i in inner]
                n = len(vec)
                if n:
                    root = pow(NTT_ROOT, (T_MOD - 1) // n, T_MOD)

                    def _ntt(values: List[int]) -> List[int]:
                        res = []
                        for i in range(n):
                            acc = 0
                            for j, v in enumerate(values):
                                acc = (acc + v * pow(root, (i * j) % n, T_MOD)) % T_MOD
                            res.append(acc)
                        return res

                    def _intt(values: List[int]) -> List[int]:
                        inv_root = pow(root, T_MOD - 2, T_MOD)
                        inv_n = pow(n, T_MOD - 2, T_MOD)
                        res = []
                        for i in range(n):
                            acc = 0
                            for j, v in enumerate(values):
                                acc = (acc + v * pow(inv_root, (i * j) % n, T_MOD)) % T_MOD
                            res.append((acc * inv_n) % T_MOD)
                        return res

                    vec = _intt(_ntt(vec))
                start_t = time.perf_counter()
                yield from DebugVM().execute(inner)
                duration = time.perf_counter() - start_t
                self.executed_instructions += 1
                if self.profiler:
                    self.profiler.record_instruction(ip_before, None, duration)
                if self.checkpoint_policy and self.checkpoint_policy.should_checkpoint(self):
                    self.checkpoint()
                continue

            exps = {e for _, e in data}
            if 4 in exps:
                op = next(p for p, e in data if e == 4)
                handler = self._dispatch.get(op)
                if handler is None:
                    raise InvalidOpcodeError("Unknown opcode", self.ip - 1)
                start_t = time.perf_counter()
                yield from handler(data)
                duration = time.perf_counter() - start_t
                self.executed_instructions += 1
                if self.profiler:
                    self.profiler.record_instruction(ip_before, op, duration)
                if self.checkpoint_policy and self.checkpoint_policy.should_checkpoint(self):
                    self.checkpoint()
            else:
                p_chr = next((p for p, e in data if e in (2, 3)), None)
                if p_chr is None:
                    raise ValueError("Bad data")
                start_t = time.perf_counter()
                yield chr(_PRIME_IDX[p_chr])
                duration = time.perf_counter() - start_t
                self.executed_instructions += 1
                if self.profiler:
                    self.profiler.record_instruction(ip_before, None, duration)
                if self.checkpoint_policy and self.checkpoint_policy.should_checkpoint(self):
                    self.checkpoint()

    # ------------------------------------------------------------------
    # Watchpoint-aware opcode handlers
    # ------------------------------------------------------------------
    def _op_load(self, data):
        addr_p = next(p for p, e in data if e == 5)
        addr = _PRIME_IDX[addr_p]
        if addr in self.watchpoints and "r" in self.watchpoints[addr]:
            yield f"WATCH:{addr}:read"
        yield from super()._op_load(data)

    def _op_store(self, data):
        addr_p = next(p for p, e in data if e == 5)
        addr = _PRIME_IDX[addr_p]
        if addr in self.watchpoints and "w" in self.watchpoints[addr]:
            yield f"WATCH:{addr}:write"
        yield from super()._op_store(data)


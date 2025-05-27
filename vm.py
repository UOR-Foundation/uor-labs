"""Virtual machine implementation."""
from __future__ import annotations

from typing import List, Iterator, Tuple, Optional, Dict
import time

from uor.jit import JITCompiler, JITBlock
from uor.profiler import VMProfiler
from uor.memory import SegmentedMemory
from uor.vm.coherence import CoherenceValidator
from uor.debugger import CallStackTracker
from uor.exceptions import (
    DivisionByZeroError,
    MemoryAccessError,
    StackOverflowError,
    StackUnderflowError,
    SegmentationFaultError,
    InvalidOpcodeError,
)

from decoder import DecodedInstruction

from primes import _PRIME_IDX
from chunks import (
    OP_PUSH, OP_ADD, OP_PRINT,
    OP_SUB, OP_MUL,
    OP_LOAD, OP_STORE,
    OP_JMP, OP_JZ, OP_JNZ,
    OP_CALL, OP_RET,
    OP_ALLOC, OP_FREE,
    OP_INPUT, OP_OUTPUT,
    OP_NET_SEND, OP_NET_RECV,
    OP_THREAD_START, OP_THREAD_JOIN,
    OP_CHECKPOINT,
    OP_DIV, OP_MOD, OP_AND, OP_OR, OP_XOR, OP_SHL, OP_SHR, OP_NEG,
    OP_FMUL, OP_FDIV, OP_F2I, OP_I2F,
    OP_SYSCALL, OP_INT, OP_HALT, OP_NOP,
    OP_HASH, OP_SIGN, OP_VERIFY, OP_RNG, OP_BRK, OP_TRACE, OP_DEBUG, OP_ATOMIC,
    OP_NOT, OP_GT, OP_LT, OP_EQ, OP_NEQ, OP_GTE, OP_LTE,
    OP_DUP, OP_SWAP, OP_ROT, OP_DROP, OP_OVER, OP_PICK,
    NEG_FLAG,
    BLOCK_TAG, NTT_TAG, T_MOD,
    NTT_ROOT,
)


class VM:
    def __init__(self, profiler: Optional[VMProfiler] = None, coherence_validator: CoherenceValidator | None = None) -> None:
        self.stack: List[int] = []
        self.mem = SegmentedMemory(self)
        self.cs = self.mem.CODE_START
        self.ds = self.mem.DATA_START
        self.hs = self.mem.HEAP_START
        self.ss = self.mem.STACK_START
        self.hp = self.mem.heap_pointer
        self.sp = self.mem.stack_pointer
        self.ip: int = 0
        self.call_stack: List[int] = []
        self.call_stack_tracker: CallStackTracker | None = None
        self.io_in: List[int] = []
        self.io_out: List[int] = []
        self.atomic: bool = False
        self._counter: Dict[int, int] = {}
        self._compiled: Dict[int, Tuple[JITBlock, float]] = {}
        self.jit_threshold: int = 1000
        self._jit = JITCompiler()
        self.profiler = profiler
        self.executed_instructions: int = 0
        self.checkpoint_backend = None
        self.checkpoint_policy = None
        self.last_checkpoint_id: str | None = None
        self.coherence_validator = coherence_validator
        self._program_len: int = 0
        self._dispatch = {
            OP_PUSH: self._op_push,
            OP_ADD: self._op_add,
            OP_SUB: self._op_sub,
            OP_MUL: self._op_mul,
            OP_LOAD: self._op_load,
            OP_STORE: self._op_store,
            OP_JMP: self._op_jmp,
            OP_JZ: self._op_jz,
            OP_JNZ: self._op_jnz,
            OP_PRINT: self._op_print,
            OP_CALL: self._op_call,
            OP_RET: self._op_ret,
            OP_ALLOC: self._op_alloc,
            OP_FREE: self._op_free,
            OP_DIV: self._op_div,
            OP_MOD: self._op_mod,
            OP_AND: self._op_and,
            OP_OR: self._op_or,
            OP_XOR: self._op_xor,
            OP_SHL: self._op_shl,
            OP_SHR: self._op_shr,
            OP_NEG: self._op_neg,
            OP_FMUL: self._op_fmul,
            OP_FDIV: self._op_fdiv,
            OP_F2I: self._op_f2i,
            OP_I2F: self._op_i2f,
            OP_SYSCALL: self._op_syscall,
            OP_INT: self._op_int,
            OP_HALT: self._op_halt,
            OP_NOP: self._op_nop,
            OP_HASH: self._op_hash,
            OP_SIGN: self._op_sign,
            OP_VERIFY: self._op_verify,
            OP_RNG: self._op_rng,
            OP_BRK: self._op_brk,
            OP_TRACE: self._op_trace,
            OP_DEBUG: self._op_debug,
            OP_ATOMIC: self._op_atomic,
            OP_INPUT: self._op_input,
            OP_OUTPUT: self._op_output,
            OP_NET_SEND: self._op_net_send,
            OP_NET_RECV: self._op_net_recv,
            OP_THREAD_START: self._op_thread_start,
            OP_THREAD_JOIN: self._op_thread_join,
            OP_CHECKPOINT: self._op_checkpoint,
            OP_NOT: self._op_not,
            OP_GT: self._op_gt,
            OP_LT: self._op_lt,
            OP_EQ: self._op_eq,
            OP_NEQ: self._op_neq,
            OP_GTE: self._op_gte,
            OP_LTE: self._op_lte,
            OP_DUP: self._op_dup,
            OP_SWAP: self._op_swap,
            OP_ROT: self._op_rot,
            OP_DROP: self._op_drop,
            OP_OVER: self._op_over,
            OP_PICK: self._op_pick,
        }

    def _pop(self) -> int:
        """Pop a single value from the stack with underflow check."""
        if not self.stack:
            raise StackUnderflowError("Stack underflow", self.ip - 1)
        return self.stack.pop()

    def _pop_two(self) -> Tuple[int, int]:
        """Pop two values from the stack with underflow check."""
        if len(self.stack) < 2:
            raise StackUnderflowError("Stack underflow", self.ip - 1)
        b = self.stack.pop()
        a = self.stack.pop()
        return a, b

    def checkpoint(self) -> None:
        if self.checkpoint_backend is not None:
            import uor.vm.checkpoint as cp
            payload = cp.serialize_state(self.stack, self.mem.dump(), self.ip)
            name = f"cp_{int(time.time()*1000)}"
            self.last_checkpoint_id = self.checkpoint_backend.save(name, payload)

    def _check_coherence(self) -> None:
        if self.coherence_validator:
            self.coherence_validator.check(self)

    def execute(self, program: List[DecodedInstruction], resume: bool = False) -> Iterator[str]:
        if not resume:
            self.ip = 0
        self._program_len = len(program)
        if self.coherence_validator:
            self.coherence_validator.start(self)
        if self.profiler:
            self.profiler.reset()
        while True:
            if self.ip == len(program):
                break
            if self.ip < 0 or self.ip > len(program):
                raise SegmentationFaultError("Instruction pointer out of range", self.ip)
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
                    self._check_coherence()
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
                yield from VM().execute(instr.inner or [])
                duration = time.perf_counter() - start_t
                self.executed_instructions += 1
                if self.profiler:
                    self.profiler.record_instruction(ip_before, None, duration)
                if self.checkpoint_policy and self.checkpoint_policy.should_checkpoint(self):
                    self.checkpoint()
                self._check_coherence()
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
                yield from VM().execute(inner)
                duration = time.perf_counter() - start_t
                self.executed_instructions += 1
                if self.profiler:
                    self.profiler.record_instruction(ip_before, None, duration)
                if self.checkpoint_policy and self.checkpoint_policy.should_checkpoint(self):
                    self.checkpoint()
                self._check_coherence()
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
                self._check_coherence()
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
            self._check_coherence()

    # ──────────────────────────────────────────────────────────────────
    # Opcode handlers
    # ──────────────────────────────────────────────────────────────────

    def _op_push(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        v = next(p for p, e in data if e == 5)
        self.stack.append(_PRIME_IDX[v])
        if len(self.stack) > SegmentedMemory.STACK_SIZE:
            raise StackOverflowError("Stack overflow", self.ip - 1)
        return iter(())

    def _binary_op(self, func) -> None:
        a, b = self._pop_two()
        self.stack.append(func(a, b))

    def _op_add(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        self._binary_op(lambda a, b: a + b)
        return iter(())

    def _op_sub(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        self._binary_op(lambda a, b: a - b)
        return iter(())

    def _op_mul(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        self._binary_op(lambda a, b: a * b)
        return iter(())

    def _op_load(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        addr_p = next(p for p, e in data if e == 5)
        addr = _PRIME_IDX[addr_p]
        try:
            self.stack.append(self.mem.load(addr))
        except MemoryError as exc:
            raise MemoryAccessError(str(exc), self.ip - 1) from None
        if self.profiler:
            self.profiler.record_memory_access(addr, "read")
        return iter(())

    def _op_store(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        addr_p = next(p for p, e in data if e == 5)
        addr = _PRIME_IDX[addr_p]
        val = self._pop()
        try:
            self.mem.store(addr, val)
        except MemoryError as exc:
            raise MemoryAccessError(str(exc), self.ip - 1) from None
        if self.profiler:
            self.profiler.record_memory_access(addr, "write")
        return iter(())

    def _op_jmp(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        sign = -1 if any(p == NEG_FLAG and e == 5 for p, e in data) else 1
        off = next(p for p, e in data if e == 5 and p != NEG_FLAG)
        self.ip += sign * _PRIME_IDX[off]
        return iter(())

    def _op_jz(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        sign = -1 if any(p == NEG_FLAG and e == 5 for p, e in data) else 1
        off = next(p for p, e in data if e == 5 and p != NEG_FLAG)
        val = self._pop()
        if val == 0:
            self.ip += sign * _PRIME_IDX[off]
        return iter(())

    def _op_jnz(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        sign = -1 if any(p == NEG_FLAG and e == 5 for p, e in data) else 1
        off = next(p for p, e in data if e == 5 and p != NEG_FLAG)
        val = self._pop()
        if val != 0:
            self.ip += sign * _PRIME_IDX[off]
        return iter(())

    def _op_print(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        yield str(self._pop())

    # ------------------------------------------------------------------
    # Extended opcode handlers
    # ------------------------------------------------------------------

    def _op_call(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        sign = -1 if any(p == NEG_FLAG and e == 5 for p, e in data) else 1
        off = next(p for p, e in data if e == 5 and p != NEG_FLAG)
        self.call_stack.append(self.ip)
        if self.call_stack_tracker is not None:
            self.call_stack_tracker.push(self.ip - 1, self.ip)
        self.ip += sign * _PRIME_IDX[off]
        return iter(())

    def _op_ret(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        if self.call_stack:
            self.ip = self.call_stack.pop()
            if self.call_stack_tracker is not None:
                self.call_stack_tracker.pop()
        return iter(())

    def _op_alloc(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        size_p = next(p for p, e in data if e == 5)
        size = _PRIME_IDX[size_p]
        try:
            addr = self.mem.allocate(size)
        except MemoryError as exc:
            raise MemoryAccessError(str(exc), self.ip - 1) from None
        self.stack.append(addr)
        return iter(())

    def _op_free(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        addr_p = next(p for p, e in data if e == 5)
        addr = _PRIME_IDX[addr_p]
        self.mem.free(addr)
        return iter(())

    def _op_input(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        val = self.io_in.pop(0) if self.io_in else 0
        self.stack.append(val)
        if self.profiler:
            self.profiler.record_io()
        return iter(())

    def _op_output(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        if self.profiler:
            self.profiler.record_io()
        val = self._pop()
        self.io_out.append(val)
        yield str(val)

    def _op_net_send(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        start = time.time()
        # network operation would occur here
        if self.profiler:
            self.profiler.record_network_latency(time.time() - start)
        return iter(())

    def _op_net_recv(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        start = time.time()
        self.stack.append(0)
        if self.profiler:
            self.profiler.record_network_latency(time.time() - start)
        return iter(())

    def _op_thread_start(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        return iter(())

    def _op_thread_join(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        return iter(())

    def _op_checkpoint(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        self.checkpoint()
        return iter(())

    # ------------------------------------------------------------------
    # New opcode handlers
    # ------------------------------------------------------------------

    def _op_div(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        a, b = self._pop_two()
        if b == 0:
            raise DivisionByZeroError("Division by zero", self.ip - 1)
        self.stack.append(a // b)
        return iter(())

    def _op_mod(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        a, b = self._pop_two()
        if b == 0:
            raise DivisionByZeroError("Modulo by zero", self.ip - 1)
        self.stack.append(a % b)
        return iter(())

    def _op_and(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        self._binary_op(lambda a, b: a & b)
        return iter(())

    def _op_or(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        self._binary_op(lambda a, b: a | b)
        return iter(())

    def _op_xor(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        self._binary_op(lambda a, b: a ^ b)
        return iter(())

    def _op_shl(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        self._binary_op(lambda a, b: a << b)
        return iter(())

    def _op_shr(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        self._binary_op(lambda a, b: a >> b)
        return iter(())

    def _op_neg(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        v = self._pop()
        self.stack.append(-v)
        return iter(())

    def _op_fmul(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        a, b = self._pop_two()
        a = float(a)
        b = float(b)
        self.stack.append(a * b)
        return iter(())

    def _op_fdiv(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        a, b = self._pop_two()
        a = float(a)
        b = float(b)
        if b == 0:
            raise DivisionByZeroError("Float division by zero", self.ip - 1)
        self.stack.append(a / b)
        return iter(())

    def _op_f2i(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        self.stack.append(int(self._pop()))
        return iter(())

    def _op_i2f(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        self.stack.append(float(self._pop()))
        return iter(())

    def _op_syscall(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        self.stack.append(0)
        return iter(())

    def _op_int(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        self.stack.append(0)
        return iter(())

    def _op_halt(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        self.ip = self._program_len
        return iter(())

    def _op_nop(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        return iter(())

    def _op_hash(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        import hashlib

        v = self._pop()
        h = hashlib.sha256(str(v).encode()).digest()
        self.stack.append(int.from_bytes(h[:4], "big"))
        return iter(())

    def _op_sign(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        v = self._pop()
        self.stack.append(v + 1)
        return iter(())

    def _op_verify(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        v = self._pop()
        sig = self._pop()
        self.stack.append(1 if sig == v + 1 else 0)
        return iter(())

    def _op_rng(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        self.stack.append(4)
        return iter(())

    def _op_brk(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        yield "BRK"

    def _op_trace(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        yield str(self.stack[-1] if self.stack else 0)

    def _op_debug(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        yield "DEBUG"

    def _op_atomic(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        self.atomic = not self.atomic
        return iter(())

    def _op_not(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        v = self._pop()
        self.stack.append(~v)
        return iter(())

    def _op_gt(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        a, b = self._pop_two()
        self.stack.append(1 if a > b else 0)
        return iter(())

    def _op_lt(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        a, b = self._pop_two()
        self.stack.append(1 if a < b else 0)
        return iter(())

    def _op_eq(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        a, b = self._pop_two()
        self.stack.append(1 if a == b else 0)
        return iter(())

    def _op_neq(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        a, b = self._pop_two()
        self.stack.append(1 if a != b else 0)
        return iter(())

    def _op_gte(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        a, b = self._pop_two()
        self.stack.append(1 if a >= b else 0)
        return iter(())

    def _op_lte(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        a, b = self._pop_two()
        self.stack.append(1 if a <= b else 0)
        return iter(())

    def _op_dup(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        if not self.stack:
            raise StackUnderflowError("Stack underflow", self.ip - 1)
        self.stack.append(self.stack[-1])
        return iter(())

    def _op_swap(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        a, b = self._pop_two()
        self.stack.extend([b, a])
        return iter(())

    def _op_rot(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        if len(self.stack) < 3:
            raise StackUnderflowError("Stack underflow", self.ip - 1)
        c = self.stack.pop()
        b = self.stack.pop()
        a = self.stack.pop()
        self.stack.extend([b, c, a])
        return iter(())

    def _op_drop(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        self._pop()
        return iter(())

    def _op_over(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        if len(self.stack) < 2:
            raise StackUnderflowError("Stack underflow", self.ip - 1)
        self.stack.append(self.stack[-2])
        return iter(())

    def _op_pick(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        idx = self._pop()
        if idx < 0 or idx >= len(self.stack):
            raise StackUnderflowError("Stack underflow", self.ip - 1)
        self.stack.append(self.stack[-idx - 1])
        return iter(())


"""Virtual machine implementation."""
from __future__ import annotations

from typing import List, Dict, Iterator, Tuple, Optional
import time

from uor.jit import JITCompiler, JITBlock
from uor.vm import Profiler

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
    OP_HASH, OP_SIGN, OP_VERIFY, OP_RNG, OP_BRK, OP_TRACE,
    NEG_FLAG,
    BLOCK_TAG, NTT_TAG, T_MOD,
    NTT_ROOT,
)


class VM:
    def __init__(self, profiler: Optional[Profiler] = None) -> None:
        self.stack: List[int] = []
        self.mem: Dict[int, int] = {}
        self.ip: int = 0
        self.call_stack: List[int] = []
        self.heap_ptr: int = 0
        self.io_in: List[int] = []
        self._counter: Dict[int, int] = {}
        self._compiled: Dict[int, JITBlock] = {}
        self.jit_threshold: int = 100
        self._jit = JITCompiler()
        self.profiler = profiler
        self.executed_instructions: int = 0
        self.checkpoint_backend = None
        self.checkpoint_policy = None
        self.last_checkpoint_id: str | None = None
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
            OP_INPUT: self._op_input,
            OP_OUTPUT: self._op_output,
            OP_NET_SEND: self._op_net_send,
            OP_NET_RECV: self._op_net_recv,
            OP_THREAD_START: self._op_thread_start,
            OP_THREAD_JOIN: self._op_thread_join,
            OP_CHECKPOINT: self._op_checkpoint,
        }

    def checkpoint(self) -> None:
        if self.checkpoint_backend is not None:
            import uor.vm.checkpoint as cp
            payload = cp.serialize_state(self.stack, self.mem, self.ip)
            name = f"cp_{int(time.time()*1000)}"
            self.last_checkpoint_id = self.checkpoint_backend.save(name, payload)

    def execute(self, program: List[DecodedInstruction], resume: bool = False) -> Iterator[str]:
        if not resume:
            self.ip = 0
        self._program_len = len(program)
        while self.ip < len(program):
            if self._jit.available and self.ip in self._compiled:
                yield from self._compiled[self.ip](self)
                self.executed_instructions += 1
                if self.profiler:
                    self.profiler.record_instruction(self, cache_hit=True)
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
                    self._compiled[self.ip] = block

            self.ip += 1
            data = instr.data

            if any(p == BLOCK_TAG and e == 7 for p, e in data):
                yield from VM().execute(instr.inner or [])
                self.executed_instructions += 1
                if self.profiler:
                    self.profiler.record_instruction(self)
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
                yield from VM().execute(inner)
                self.executed_instructions += 1
                if self.profiler:
                    self.profiler.record_instruction(self)
                if self.checkpoint_policy and self.checkpoint_policy.should_checkpoint(self):
                    self.checkpoint()
                continue

            exps = {e for _, e in data}
            if 4 in exps:
                op = next(p for p, e in data if e == 4)
                handler = self._dispatch.get(op)
                if handler is None:
                    raise ValueError("Unknown opcode")
                yield from handler(data)
                self.executed_instructions += 1
                if self.profiler:
                    self.profiler.record_instruction(self)
                if self.checkpoint_policy and self.checkpoint_policy.should_checkpoint(self):
                    self.checkpoint()
            else:
                p_chr = next((p for p, e in data if e in (2, 3)), None)
                if p_chr is None:
                    raise ValueError("Bad data")
                yield chr(_PRIME_IDX[p_chr])
                self.executed_instructions += 1
                if self.profiler:
                    self.profiler.record_instruction(self)
                if self.checkpoint_policy and self.checkpoint_policy.should_checkpoint(self):
                    self.checkpoint()

    # ──────────────────────────────────────────────────────────────────
    # Opcode handlers
    # ──────────────────────────────────────────────────────────────────

    def _op_push(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        v = next(p for p, e in data if e == 5)
        self.stack.append(_PRIME_IDX[v])
        return iter(())

    def _binary_op(self, func) -> None:
        b, a = self.stack.pop(), self.stack.pop()
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
        addr = next(p for p, e in data if e == 5)
        self.stack.append(self.mem.get(_PRIME_IDX[addr], 0))
        return iter(())

    def _op_store(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        addr = next(p for p, e in data if e == 5)
        val = self.stack.pop()
        self.mem[_PRIME_IDX[addr]] = val
        return iter(())

    def _op_jmp(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        sign = -1 if any(p == NEG_FLAG and e == 5 for p, e in data) else 1
        off = next(p for p, e in data if e == 5 and p != NEG_FLAG)
        self.ip += sign * _PRIME_IDX[off]
        return iter(())

    def _op_jz(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        sign = -1 if any(p == NEG_FLAG and e == 5 for p, e in data) else 1
        off = next(p for p, e in data if e == 5 and p != NEG_FLAG)
        val = self.stack.pop()
        if val == 0:
            self.ip += sign * _PRIME_IDX[off]
        return iter(())

    def _op_jnz(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        sign = -1 if any(p == NEG_FLAG and e == 5 for p, e in data) else 1
        off = next(p for p, e in data if e == 5 and p != NEG_FLAG)
        val = self.stack.pop()
        if val != 0:
            self.ip += sign * _PRIME_IDX[off]
        return iter(())

    def _op_print(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        yield str(self.stack.pop())

    # ------------------------------------------------------------------
    # Extended opcode handlers
    # ------------------------------------------------------------------

    def _op_call(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        sign = -1 if any(p == NEG_FLAG and e == 5 for p, e in data) else 1
        off = next(p for p, e in data if e == 5 and p != NEG_FLAG)
        self.call_stack.append(self.ip)
        self.ip += sign * _PRIME_IDX[off]
        return iter(())

    def _op_ret(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        if self.call_stack:
            self.ip = self.call_stack.pop()
        return iter(())

    def _op_alloc(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        size_p = next(p for p, e in data if e == 5)
        size = _PRIME_IDX[size_p]
        addr = self.heap_ptr
        self.heap_ptr += size
        for i in range(size):
            self.mem[addr + i] = 0
        self.stack.append(addr)
        return iter(())

    def _op_free(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        addr_p = next(p for p, e in data if e == 5)
        addr = _PRIME_IDX[addr_p]
        self.mem.pop(addr, None)
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
        yield str(self.stack.pop())

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
        self._binary_op(lambda a, b: a // b)
        return iter(())

    def _op_mod(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        self._binary_op(lambda a, b: a % b)
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
        v = self.stack.pop()
        self.stack.append(-v)
        return iter(())

    def _op_fmul(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        b, a = float(self.stack.pop()), float(self.stack.pop())
        self.stack.append(a * b)
        return iter(())

    def _op_fdiv(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        b, a = float(self.stack.pop()), float(self.stack.pop())
        self.stack.append(a / b)
        return iter(())

    def _op_f2i(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        self.stack.append(int(self.stack.pop()))
        return iter(())

    def _op_i2f(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        self.stack.append(float(self.stack.pop()))
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

        v = self.stack.pop()
        h = hashlib.sha256(str(v).encode()).digest()
        self.stack.append(int.from_bytes(h[:4], "big"))
        return iter(())

    def _op_sign(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        v = self.stack.pop()
        self.stack.append(v + 1)
        return iter(())

    def _op_verify(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        v = self.stack.pop()
        sig = self.stack.pop()
        self.stack.append(1 if sig == v + 1 else 0)
        return iter(())

    def _op_rng(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        self.stack.append(4)
        return iter(())

    def _op_brk(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        yield "BRK"

    def _op_trace(self, data: List[Tuple[int, int]]) -> Iterator[str]:
        yield str(self.stack[-1] if self.stack else 0)


"""Virtual machine implementation."""
from __future__ import annotations

from typing import List, Dict, Iterator, Tuple

from decoder import DecodedInstruction

from primes import _PRIME_IDX
from chunks import (
    OP_PUSH, OP_ADD, OP_PRINT,
    OP_SUB, OP_MUL,
    OP_LOAD, OP_STORE,
    OP_JMP, OP_JZ, OP_JNZ,
    NEG_FLAG,
    BLOCK_TAG, NTT_TAG, T_MOD,
    NTT_ROOT,
)


class VM:
    def __init__(self) -> None:
        self.stack: List[int] = []
        self.mem: Dict[int, int] = {}
        self.ip: int = 0
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
        }

    def execute(self, program: List[DecodedInstruction]) -> Iterator[str]:
        self.ip = 0
        while self.ip < len(program):
            instr = program[self.ip]
            self.ip += 1
            data = instr.data

            if any(p == BLOCK_TAG and e == 7 for p, e in data):
                yield from VM().execute(instr.inner or [])
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
                continue

            exps = {e for _, e in data}
            if 4 in exps:
                op = next(p for p, e in data if e == 4)
                handler = self._dispatch.get(op)
                if handler is None:
                    raise ValueError("Unknown opcode")
                yield from handler(data)
            else:
                p_chr = next((p for p, e in data if e in (2, 3)), None)
                if p_chr is None:
                    raise ValueError("Bad data")
                yield chr(_PRIME_IDX[p_chr])

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

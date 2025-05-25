"""Virtual machine implementation."""
from __future__ import annotations

from typing import List, Dict, Iterator, Tuple

from .primes import get_prime, _PRIME_IDX, factor
from .chunks import (
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

    def execute(self, chunks: List[int]) -> Iterator[str]:
        self.ip = 0
        while self.ip < len(chunks):
            ck = chunks[self.ip]
            self.ip += 1
            fac = factor(ck)
            chk = None
            data: List[Tuple[int, int]] = []
            for p, e in fac:
                if e >= 6 and chk is None:
                    chk = p
                    e -= 6
                elif e >= 6:
                    raise ValueError("Duplicate checksum")
                if e:
                    data.append((p, e))
            if chk is None:
                raise ValueError("Checksum missing")
            xor = 0
            for p, e in data:
                xor ^= _PRIME_IDX[p] * e
            if chk != get_prime(xor):
                raise ValueError("Checksum mismatch")

            if any(p == BLOCK_TAG and e == 7 for p, e in data):
                lp = next(p for p, e in data if p != BLOCK_TAG and e == 5)
                cnt = _PRIME_IDX[lp]
                inner = chunks[self.ip:self.ip + cnt]
                self.ip += cnt
                yield from VM().execute(inner)
                continue

            if any(p == NTT_TAG and e == 4 for p, e in data):
                lp = next(p for p, e in data if p != NTT_TAG and e == 5)
                cnt = _PRIME_IDX[lp]
                inner = chunks[self.ip:self.ip + cnt]
                self.ip += cnt
                vec = []
                for c in inner:
                    f = factor(c)
                    sub = []
                    cchk = None
                    for p2, e2 in f:
                        if e2 >= 6 and cchk is None:
                            e2 -= 6
                            cchk = p2
                        sub.append((p2, e2))
                    vec.append(next((e2 for _, e2 in sub if e2 > 0), 0))
                _ = vec  # placeholder for NTT roundtrip
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

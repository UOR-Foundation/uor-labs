"""Virtual machine implementation."""
from __future__ import annotations

from typing import List, Dict, Iterator, Tuple

from .primes import get_prime, _PRIME_IDX, factor
from .chunks import (
    OP_PUSH, OP_ADD, OP_PRINT,
    OP_SUB, OP_MUL,
    OP_LOAD, OP_STORE,
    OP_JMP, OP_JZ, OP_JNZ,
    NEG_FLAG, DATA_OFFSET,
    BLOCK_TAG, NTT_TAG, T_MOD,
    NTT_ROOT,
)


class VM:
    def __init__(self) -> None:
        self.stack: List[int] = []
        self.mem: Dict[int, int] = {}
        self.ip: int = 0

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
                cnt = _PRIME_IDX[lp] - DATA_OFFSET
                inner = chunks[self.ip:self.ip + cnt]
                self.ip += cnt
                yield from VM().execute(inner)
                continue

            if any(p == NTT_TAG and e == 4 for p, e in data):
                lp = next(p for p, e in data if p != NTT_TAG and e == 5)
                cnt = _PRIME_IDX[lp] - DATA_OFFSET
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
                if op == OP_PUSH:
                    v = next(p for p, e in data if e == 5 and p != NEG_FLAG)
                    self.stack.append(_PRIME_IDX[v] - DATA_OFFSET)
                elif op == OP_ADD:
                    if len(self.stack) < 2:
                        raise IndexError("Stack underflow")
                    b, a = self.stack.pop(), self.stack.pop()
                    self.stack.append(a + b)
                elif op == OP_SUB:
                    if len(self.stack) < 2:
                        raise IndexError("Stack underflow")
                    b, a = self.stack.pop(), self.stack.pop()
                    self.stack.append(a - b)
                elif op == OP_MUL:
                    if len(self.stack) < 2:
                        raise IndexError("Stack underflow")
                    b, a = self.stack.pop(), self.stack.pop()
                    self.stack.append(a * b)
                elif op == OP_LOAD:
                    addr = next(p for p, e in data if e == 5)
                    self.stack.append(self.mem.get(_PRIME_IDX[addr] - DATA_OFFSET, 0))
                elif op == OP_STORE:
                    addr = next(p for p, e in data if e == 5)
                    if not self.stack:
                        raise IndexError("Stack underflow")
                    val = self.stack.pop()
                    self.mem[_PRIME_IDX[addr] - DATA_OFFSET] = val
                elif op == OP_JMP:
                    neg = any(p == NEG_FLAG and e == 5 for p, e in data)
                    off_p = next(p for p, e in data if e == 5 and p != NEG_FLAG)
                    off = _PRIME_IDX[off_p] - DATA_OFFSET
                    if neg:
                        off = -off
                    self.ip += off
                elif op == OP_JZ:
                    neg = any(p == NEG_FLAG and e == 5 for p, e in data)
                    off_p = next(p for p, e in data if e == 5 and p != NEG_FLAG)
                    if not self.stack:
                        raise IndexError("Stack underflow")
                    val = self.stack.pop()
                    off = _PRIME_IDX[off_p] - DATA_OFFSET
                    if neg:
                        off = -off
                    if val == 0:
                        self.ip += off
                elif op == OP_JNZ:
                    neg = any(p == NEG_FLAG and e == 5 for p, e in data)
                    off_p = next(p for p, e in data if e == 5 and p != NEG_FLAG)
                    if not self.stack:
                        raise IndexError("Stack underflow")
                    val = self.stack.pop()
                    off = _PRIME_IDX[off_p] - DATA_OFFSET
                    if neg:
                        off = -off
                    if val != 0:
                        self.ip += off
                elif op == OP_PRINT:
                    if not self.stack:
                        raise IndexError("Stack underflow")
                    yield str(self.stack.pop())
                else:
                    raise ValueError("Unknown opcode")
            else:
                p_chr = next((p for p, e in data if e in (2, 3)), None)
                if p_chr is None:
                    raise ValueError("Bad data")
                yield chr(_PRIME_IDX[p_chr])

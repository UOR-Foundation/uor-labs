from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import time
from primes import get_prime, _PRIME_IDX, factor
from chunks import (
    BLOCK_TAG,
    NTT_TAG,
    OP_CALL,
    OP_RET,
    OP_ALLOC,
    OP_FREE,
    OP_INPUT,
    OP_OUTPUT,
    OP_NET_SEND,
    OP_NET_RECV,
    OP_THREAD_START,
    OP_THREAD_JOIN,
)


@dataclass
class DecodedInstruction:
    data: List[Tuple[int, int]]
    inner: List["DecodedInstruction"] | None = None


def _decode_single(chunk: int) -> List[Tuple[int, int]]:
    time.sleep(0.0001)
    fac = factor(chunk)
    chk = None
    data: List[Tuple[int, int]] = []
    for p, e in fac:
        if e >= 6 and chk is None:
            chk = p
            e -= 6
        elif e >= 6:
            if p == BLOCK_TAG and e == 7:
                pass
            else:
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
    return data


def decode(chunks: List[int]) -> List[DecodedInstruction]:
    result: List[DecodedInstruction] = []
    ip = 0
    while ip < len(chunks):
        ck = chunks[ip]
        ip += 1
        data = _decode_single(ck)
        inner: List[DecodedInstruction] | None = None
        if any(p == BLOCK_TAG and e == 7 for p, e in data):
            lp = next(p for p, e in data if p != BLOCK_TAG and e == 5)
            cnt = _PRIME_IDX[lp]
            inner = decode(chunks[ip : ip + cnt])
            ip += cnt
        elif any(p == NTT_TAG and e == 4 for p, e in data):
            lp = next(p for p, e in data if p != NTT_TAG and e == 5)
            cnt = _PRIME_IDX[lp]
            inner = decode(chunks[ip : ip + cnt])
            ip += cnt
        result.append(DecodedInstruction(data=data, inner=inner))
    return result

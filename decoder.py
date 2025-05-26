from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from uor.cache import InstructionCache
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


_CACHE = InstructionCache()


@dataclass
class DecodedInstruction:
    data: List[Tuple[int, int]]
    inner: List["DecodedInstruction"] | None = None


def _decode_single(chunk: int) -> DecodedInstruction:
    """Decode a single chunk into a ``DecodedInstruction`` object."""
    cached = _CACHE.get(chunk)
    if cached is not None:
        return DecodedInstruction(data=cached.data)
    fac = factor(chunk)
    chk = None
    data: List[Tuple[int, int]] = []
    for p, e in fac:
        if e >= 6 and chk is None:
            chk = p
            e -= 6
        elif e >= 6:
            # ``BLOCK`` uses exponent 7 in addition to the checksum. Allow it
            # as a special case instead of treating it as a duplicate checksum.
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

    instr = DecodedInstruction(data=data)
    _CACHE.put(chunk, instr)
    return DecodedInstruction(data=instr.data)


def decode(chunks: List[int]) -> List[DecodedInstruction]:
    """Decode a list of numeric chunks into ``DecodedInstruction`` objects."""
    result: List[DecodedInstruction] = []
    ip = 0
    while ip < len(chunks):
        ck = chunks[ip]
        ip += 1
        instr = _decode_single(ck)
        data = instr.data
        if any(p == BLOCK_TAG and e == 7 for p, e in data):
            lp = next(p for p, e in data if p != BLOCK_TAG and e == 5)
            cnt = _PRIME_IDX[lp]
            instr.inner = decode(chunks[ip : ip + cnt])
            ip += cnt
        elif any(p == NTT_TAG and e == 4 for p, e in data):
            lp = next(p for p, e in data if p != NTT_TAG and e == 5)
            cnt = _PRIME_IDX[lp]
            instr.inner = decode(chunks[ip : ip + cnt])
            ip += cnt
        result.append(instr)
    return result

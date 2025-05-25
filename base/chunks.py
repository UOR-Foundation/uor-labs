"""Chunk construction utilities."""
from __future__ import annotations

from typing import List, Tuple

from .primes import get_prime, _PRIME_IDX

# Opcode prime indices
from .primes import _PRIMES
from .primes import _extend_primes_to

DATA_OFFSET = 50

_extend_primes_to(max(12, DATA_OFFSET + 10))
OP_PUSH, OP_ADD, OP_PRINT = _PRIMES[0], _PRIMES[1], _PRIMES[2]
OP_SUB, OP_MUL = _PRIMES[6], _PRIMES[7]
OP_LOAD, OP_STORE = _PRIMES[8], _PRIMES[9]
OP_JMP, OP_JZ, OP_JNZ = _PRIMES[10], _PRIMES[11], _PRIMES[12]
NEG_FLAG = _PRIMES[13]
BLOCK_TAG, NTT_TAG, T_MOD = _PRIMES[3], _PRIMES[4], _PRIMES[5]
NTT_ROOT = 2


def _attach_checksum(raw: int, fac: List[Tuple[int, int]]) -> int:
    xor = 0
    for p, e in fac:
        xor ^= _PRIME_IDX[p] * e
    chk = get_prime(xor)
    return raw * (chk ** 6)


# Data and opcode chunks

def chunk_data(pos: int, cp: int) -> int:
    p1, p2 = get_prime(pos), get_prime(cp)
    if p1 == p2:
        raw, fac = p1 ** 3, [(p1, 3)]
    else:
        raw, fac = p1 * (p2 ** 2), [(p1, 1), (p2, 2)]
    return _attach_checksum(raw, fac)


def chunk_push(v: int) -> int:
    p = get_prime(DATA_OFFSET + v)
    return _attach_checksum(OP_PUSH ** 4 * p ** 5, [(OP_PUSH, 4), (p, 5)])


def chunk_add() -> int:
    return _attach_checksum(OP_ADD ** 4, [(OP_ADD, 4)])


def chunk_sub() -> int:
    return _attach_checksum(OP_SUB ** 4, [(OP_SUB, 4)])


def chunk_mul() -> int:
    return _attach_checksum(OP_MUL ** 4, [(OP_MUL, 4)])


def chunk_print() -> int:
    return _attach_checksum(OP_PRINT ** 4, [(OP_PRINT, 4)])


def chunk_load(addr: int) -> int:
    p = get_prime(DATA_OFFSET + addr)
    return _attach_checksum(OP_LOAD ** 4 * p ** 5, [(OP_LOAD, 4), (p, 5)])


def chunk_store(addr: int) -> int:
    p = get_prime(DATA_OFFSET + addr)
    return _attach_checksum(OP_STORE ** 4 * p ** 5, [(OP_STORE, 4), (p, 5)])


def chunk_jmp(offset: int) -> int:
    p = get_prime(DATA_OFFSET + abs(offset))
    fac = [(OP_JMP, 4), (p, 5)]
    if offset < 0:
        fac.append((NEG_FLAG, 1))
    return _attach_checksum(OP_JMP ** 4 * p ** 5 * (NEG_FLAG ** 1 if offset < 0 else 1), fac)


def chunk_jz(offset: int) -> int:
    p = get_prime(DATA_OFFSET + abs(offset))
    fac = [(OP_JZ, 4), (p, 5)]
    if offset < 0:
        fac.append((NEG_FLAG, 1))
    return _attach_checksum(OP_JZ ** 4 * p ** 5 * (NEG_FLAG ** 1 if offset < 0 else 1), fac)


def chunk_jnz(offset: int) -> int:
    p = get_prime(DATA_OFFSET + abs(offset))
    fac = [(OP_JNZ, 4), (p, 5)]
    if offset < 0:
        fac.append((NEG_FLAG, 1))
    return _attach_checksum(OP_JNZ ** 4 * p ** 5 * (NEG_FLAG ** 1 if offset < 0 else 1), fac)


def chunk_block_start(n: int) -> int:
    lp = get_prime(n)
    return _attach_checksum(BLOCK_TAG ** 7 * lp ** 5, [(BLOCK_TAG, 7), (lp, 5)])


def chunk_ntt(n: int) -> int:
    lp = get_prime(n)
    return _attach_checksum(NTT_TAG ** 4 * lp ** 5, [(NTT_TAG, 4), (lp, 5)])

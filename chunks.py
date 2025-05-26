"""Chunk construction utilities."""
from __future__ import annotations

from typing import List, Tuple

from primes import get_prime, _PRIME_IDX

# Opcode prime indices
from primes import _PRIMES
from primes import _extend_primes_to

_extend_primes_to(24)
OP_PUSH, OP_ADD, OP_PRINT = _PRIMES[0], _PRIMES[1], _PRIMES[2]
OP_SUB, OP_MUL = _PRIMES[6], _PRIMES[7]
OP_LOAD, OP_STORE = _PRIMES[8], _PRIMES[9]
OP_JMP, OP_JZ, OP_JNZ = _PRIMES[10], _PRIMES[11], _PRIMES[12]
NEG_FLAG = _PRIMES[13]
OP_CALL, OP_RET = _PRIMES[14], _PRIMES[15]
OP_ALLOC, OP_FREE = _PRIMES[16], _PRIMES[17]
OP_INPUT, OP_OUTPUT = _PRIMES[18], _PRIMES[19]
OP_NET_SEND, OP_NET_RECV = _PRIMES[20], _PRIMES[21]
OP_THREAD_START, OP_THREAD_JOIN = _PRIMES[22], _PRIMES[23]
OP_CHECKPOINT = _PRIMES[24]
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
    p = get_prime(v)
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
    p = get_prime(addr)
    return _attach_checksum(OP_LOAD ** 4 * p ** 5, [(OP_LOAD, 4), (p, 5)])


def chunk_store(addr: int) -> int:
    p = get_prime(addr)
    return _attach_checksum(OP_STORE ** 4 * p ** 5, [(OP_STORE, 4), (p, 5)])


def chunk_jmp(offset: int) -> int:
    sign = 1
    if offset < 0:
        sign = -1
        offset = -offset
    p = get_prime(offset)
    fac = [(OP_JMP, 4), (p, 5)]
    raw = OP_JMP ** 4 * p ** 5
    if sign < 0:
        raw *= NEG_FLAG ** 5
        fac.append((NEG_FLAG, 5))
    return _attach_checksum(raw, fac)


def chunk_jz(offset: int) -> int:
    sign = 1
    if offset < 0:
        sign = -1
        offset = -offset
    p = get_prime(offset)
    fac = [(OP_JZ, 4), (p, 5)]
    raw = OP_JZ ** 4 * p ** 5
    if sign < 0:
        raw *= NEG_FLAG ** 5
        fac.append((NEG_FLAG, 5))
    return _attach_checksum(raw, fac)


def chunk_jnz(offset: int) -> int:
    sign = 1
    if offset < 0:
        sign = -1
        offset = -offset
    p = get_prime(offset)
    fac = [(OP_JNZ, 4), (p, 5)]
    raw = OP_JNZ ** 4 * p ** 5
    if sign < 0:
        raw *= NEG_FLAG ** 5
        fac.append((NEG_FLAG, 5))
    return _attach_checksum(raw, fac)


def chunk_block_start(n: int) -> int:
    lp = get_prime(n)
    return _attach_checksum(BLOCK_TAG ** 7 * lp ** 5, [(BLOCK_TAG, 7), (lp, 5)])


def chunk_ntt(n: int) -> int:
    lp = get_prime(n)
    return _attach_checksum(NTT_TAG ** 4 * lp ** 5, [(NTT_TAG, 4), (lp, 5)])


def chunk_call(offset: int) -> int:
    sign = 1
    if offset < 0:
        sign = -1
        offset = -offset
    p = get_prime(offset)
    fac = [(OP_CALL, 4), (p, 5)]
    raw = OP_CALL ** 4 * p ** 5
    if sign < 0:
        raw *= NEG_FLAG ** 5
        fac.append((NEG_FLAG, 5))
    return _attach_checksum(raw, fac)


def chunk_ret() -> int:
    return _attach_checksum(OP_RET ** 4, [(OP_RET, 4)])


def chunk_alloc(size: int) -> int:
    p = get_prime(size)
    return _attach_checksum(OP_ALLOC ** 4 * p ** 5, [(OP_ALLOC, 4), (p, 5)])


def chunk_free(addr: int) -> int:
    p = get_prime(addr)
    return _attach_checksum(OP_FREE ** 4 * p ** 5, [(OP_FREE, 4), (p, 5)])


def chunk_input() -> int:
    return _attach_checksum(OP_INPUT ** 4, [(OP_INPUT, 4)])


def chunk_output() -> int:
    return _attach_checksum(OP_OUTPUT ** 4, [(OP_OUTPUT, 4)])


def chunk_net_send() -> int:
    return _attach_checksum(OP_NET_SEND ** 4, [(OP_NET_SEND, 4)])


def chunk_net_recv() -> int:
    return _attach_checksum(OP_NET_RECV ** 4, [(OP_NET_RECV, 4)])


def chunk_thread_start() -> int:
    return _attach_checksum(OP_THREAD_START ** 4, [(OP_THREAD_START, 4)])


def chunk_thread_join() -> int:
    return _attach_checksum(OP_THREAD_JOIN ** 4, [(OP_THREAD_JOIN, 4)])


def chunk_checkpoint() -> int:
    """Encode a CHECKPOINT instruction."""
    return _attach_checksum(OP_CHECKPOINT ** 4, [(OP_CHECKPOINT, 4)])

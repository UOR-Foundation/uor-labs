"""Prime generation and factorization utilities."""
from __future__ import annotations

from math import isqrt
from typing import List, Dict, Tuple

# cache for factorization results
_FACTOR_CACHE: Dict[int, List[Tuple[int, int]]] = {}

# Prime cache
_PRIMES: List[int] = [2]
_PRIME_IDX: Dict[int, int] = {2: 0}

# Simple sieve for faster prime generation
_sieve = bytearray(b"\x00\x00\x01")
_sieve_limit = 2

def _extend_sieve(limit: int) -> None:
    """Extend the sieve of Eratosthenes up to ``limit``."""
    global _sieve_limit, _sieve
    if limit <= _sieve_limit:
        return
    sieve = _sieve
    sieve.extend(b"\x01" * (limit - _sieve_limit))
    for p in range(2, isqrt(limit) + 1):
        if sieve[p]:
            start = max(p * p, ((_sieve_limit + 1 + p - 1) // p) * p)
            sieve[start:limit + 1:p] = b"\x00" * ((limit - start) // p + 1)
    _sieve = sieve
    _sieve_limit = limit

def _extend_primes_to(idx: int) -> None:
    """Ensure ``_PRIMES`` contains at least ``idx + 1`` primes."""
    limit = _sieve_limit
    while len(_PRIMES) <= idx:
        limit = max(limit * 2, 4)
        _extend_sieve(limit)
        start = _PRIMES[-1] + 1
        for n in range(start, _sieve_limit + 1):
            if _sieve[n]:
                _PRIME_IDX[n] = len(_PRIMES)
                _PRIMES.append(n)
        if len(_PRIMES) > idx:
            break


def get_prime(idx: int) -> int:
    _extend_primes_to(idx)
    return _PRIMES[idx]


def factor(x: int) -> List[Tuple[int, int]]:
    if x in _FACTOR_CACHE:
        return list(_FACTOR_CACHE[x])
    orig = x
    fac: List[Tuple[int, int]] = []
    i = 0
    while True:
        p = get_prime(i)
        if p * p > x:
            break
        if x % p == 0:
            cnt = 0
            while x % p == 0:
                x //= p
                cnt += 1
            fac.append((p, cnt))
        i += 1
    if x > 1:
        if x not in _PRIME_IDX:
            _PRIME_IDX[x] = len(_PRIMES)
            _PRIMES.append(x)
        fac.append((x, 1))
    _FACTOR_CACHE[orig] = list(fac)
    return fac

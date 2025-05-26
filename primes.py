"""Prime generation and factorization utilities."""
from __future__ import annotations

from math import isqrt, gcd
from typing import List, Dict, Tuple
from weakref import WeakValueDictionary
import random

class FactorList(list):
    """List subclass that supports weak references for caching."""
    pass

# cache for factorization results using weak references
_FACTOR_CACHE: WeakValueDictionary[int, FactorList] = WeakValueDictionary()
_FACTOR_STRONG: Dict[int, FactorList] = {}

# Prime cache
_PRIMES: List[int] = [2]
_PRIME_IDX: Dict[int, int] = {2: 0}

# Prime generation limit already processed
_sieve_limit = 2


def segmented_sieve(limit: int, segment_size: int = 32768) -> None:
    """Extend the prime list using a segmented sieve up to ``limit``."""
    global _sieve_limit
    if limit <= _sieve_limit:
        return

    # ensure we have primes up to sqrt(limit) for sieving
    root = isqrt(limit)
    if root > _sieve_limit:
        segmented_sieve(root, segment_size)

    start = _sieve_limit + 1
    while start <= limit:
        end = min(start + segment_size - 1, limit)
        seg = bytearray(b"\x01" * (end - start + 1))
        for p in _PRIMES:
            if p * p > end:
                break
            s = ((start + p - 1) // p) * p
            for j in range(s, end + 1, p):
                seg[j - start] = 0
        for i, val in enumerate(seg):
            if val:
                n = start + i
                _PRIME_IDX[n] = len(_PRIMES)
                _PRIMES.append(n)
        _sieve_limit = end
        start = end + 1

def _extend_primes_to(idx: int) -> None:
    """Ensure ``_PRIMES`` contains at least ``idx + 1`` primes."""
    limit = _sieve_limit
    while len(_PRIMES) <= idx:
        limit = max(limit * 2, 4)
        segmented_sieve(limit)


def get_prime(idx: int) -> int:
    _extend_primes_to(idx)
    return _PRIMES[idx]


def factor(x: int) -> List[Tuple[int, int]]:
    cached = _FACTOR_CACHE.get(x)
    if cached is not None:
        return list(cached)
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
    flist = FactorList(fac)
    _FACTOR_CACHE[orig] = flist
    _FACTOR_STRONG[orig] = flist
    return list(flist)


def miller_rabin(n: int, bases: List[int] | None = None) -> bool:
    """Probabilistic primality test using the Miller-Rabin method."""
    if n < 2:
        return False
    # small primes
    small_primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]
    for p in small_primes:
        if n % p == 0:
            return n == p

    if bases is None:
        bases = [2, 325, 9375, 28178, 450775, 9780504, 1795265022]

    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1

    for a in bases:
        if a % n == 0:
            continue
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def pollard_rho(n: int) -> int:
    """Return a non-trivial factor of ``n`` using Pollard's Rho method."""
    if n % 2 == 0:
        return 2
    while True:
        c = random.randrange(1, n)
        f = lambda x: (pow(x, 2, n) + c) % n
        x = random.randrange(0, n)
        y = x
        d = 1
        while d == 1:
            x = f(x)
            y = f(f(y))
            d = gcd(abs(x - y), n)
        if d != n:
            return d


def optimized_factorize(n: int) -> List[Tuple[int, int]]:
    """Factor ``n`` using Pollard Rho and Miller-Rabin with caching."""
    cached = _FACTOR_CACHE.get(n)
    if cached is not None:
        return list(cached)

    factors: List[int] = []

    def _factor(m: int) -> None:
        if m == 1:
            return
        if miller_rabin(m):
            factors.append(m)
            return
        d = pollard_rho(m)
        _factor(d)
        _factor(m // d)

    _factor(n)
    factors.sort()
    result: List[Tuple[int, int]] = []
    i = 0
    while i < len(factors):
        p = factors[i]
        cnt = 1
        i += 1
        while i < len(factors) and factors[i] == p:
            cnt += 1
            i += 1
        if p not in _PRIME_IDX:
            _PRIME_IDX[p] = len(_PRIMES)
            _PRIMES.append(p)
        result.append((p, cnt))

    flist = FactorList(result)
    _FACTOR_CACHE[n] = flist
    _FACTOR_STRONG[n] = flist
    return list(flist)

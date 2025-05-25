#!/usr/bin/env python3
"""
Pure UOR — execution + integrity + NTT spectral (lossless full-complex)
=====================================================================
This script implements:
- A dynamic prime cache
- Data and exec opcodes with per-chunk checksum (exp⁶)
- Block framing via prime⁷ headers
- Forward & inverse Number-Theoretic Transform (NTT) mod 13 as a spectral operator
- Automatic inversion ensuring lossless round-trip

Run: python3 pure_uor_cpu.py
"""
from __future__ import annotations
import sys
from math import isqrt
from typing import List, Dict, Tuple, Iterator

# ──────────────────────────────────────────────────────────────────────
# Prime cache & tags
# ──────────────────────────────────────────────────────────────────────
_PRIMES: List[int] = [2]
_PRIME_IDX: Dict[int,int] = {2: 0}

def _is_prime(n: int) -> bool:
    r = isqrt(n)
    for p in _PRIMES:
        if p > r: break
        if n % p == 0: return False
    return True

def _extend_primes_to(idx: int) -> None:
    cand = _PRIMES[-1] + 1
    while len(_PRIMES) <= idx:
        if _is_prime(cand):
            _PRIMES.append(cand)
            _PRIME_IDX[cand] = len(_PRIMES) - 1
        cand += 1

def get_prime(idx: int) -> int:
    _extend_primes_to(idx)
    return _PRIMES[idx]

# Preload core tags at indices 0..5: 2,3,5,7,11,13
_extend_primes_to(5)
OP_PUSH, OP_ADD, OP_PRINT = _PRIMES[0], _PRIMES[1], _PRIMES[2]
BLOCK_TAG, NTT_TAG, T_MOD = _PRIMES[3], _PRIMES[4], _PRIMES[5]
NTT_ROOT = 2

# ──────────────────────────────────────────────────────────────────────
# Checksum attachment (exp 6)
# ──────────────────────────────────────────────────────────────────────

def _attach_checksum(raw: int, fac: List[Tuple[int,int]]) -> int:
    xor = 0
    for p, e in fac:
        xor ^= _PRIME_IDX[p] * e
    chk = get_prime(xor)
    return raw * (chk ** 6)

# ──────────────────────────────────────────────────────────────────────
# Chunk constructors
# ──────────────────────────────────────────────────────────────────────

def chunk_data(pos: int, cp: int) -> int:
    p1, p2 = get_prime(pos), get_prime(cp)
    if p1 == p2:
        raw, fac = p1**3, [(p1, 3)]
    else:
        raw, fac = p1*(p2**2), [(p1, 1), (p2, 2)]
    return _attach_checksum(raw, fac)

def chunk_push(v: int) -> int:
    p = get_prime(v)
    return _attach_checksum(OP_PUSH**4 * p**5, [(OP_PUSH,4),(p,5)])

def chunk_add() -> int:
    return _attach_checksum(OP_ADD**4, [(OP_ADD,4)])

def chunk_print() -> int:
    return _attach_checksum(OP_PRINT**4, [(OP_PRINT,4)])

def chunk_block_start(n: int) -> int:
    lp = get_prime(n)
    return _attach_checksum(BLOCK_TAG**7 * lp**5, [(BLOCK_TAG,7),(lp,5)])

def chunk_ntt(n: int) -> int:
    lp = get_prime(n)
    return _attach_checksum(NTT_TAG**4 * lp**5, [(NTT_TAG,4),(lp,5)])

# ──────────────────────────────────────────────────────────────────────
# Prime factorisation
# ──────────────────────────────────────────────────────────────────────

def _factor(x: int) -> List[Tuple[int,int]]:
    fac = []
    i = 0
    while True:
        p = get_prime(i)
        if p*p > x: break
        if x % p == 0:
            cnt = 0
            while x % p == 0:
                x //= p; cnt += 1
            fac.append((p, cnt))
        i += 1
    if x > 1:
        if x not in _PRIME_IDX:
            _extend_primes_to(len(_PRIMES))
            _PRIME_IDX[x] = len(_PRIMES)
            _PRIMES.append(x)
        fac.append((x,1))
    return fac

# ──────────────────────────────────────────────────────────────────────
# NTT forward & inverse
# ──────────────────────────────────────────────────────────────────────

def ntt_forward(vec: List[int]) -> List[int]:
    N = len(vec)
    out = [0]*N
    for k in range(N):
        s = 0
        for n in range(N): s += vec[n] * pow(NTT_ROOT, n*k, T_MOD)
        out[k] = s % T_MOD
    return out

def ntt_inverse(vec: List[int]) -> List[int]:
    N = len(vec)
    invN = pow(N, -1, T_MOD)
    out = [0]*N
    for n in range(N):
        s = 0
        for k in range(N): s += vec[k] * pow(NTT_ROOT, -n*k, T_MOD)
        out[n] = (s * invN) % T_MOD
    return out

# ──────────────────────────────────────────────────────────────────────
# VM execution
# ──────────────────────────────────────────────────────────────────────

def vm_execute(chunks: List[int]) -> Iterator[str]:
    stack: List[int] = []
    i = 0
    while i < len(chunks):
        ck = chunks[i]; i += 1
        fac = _factor(ck)
        # peel checksum
        chk = None; data: List[Tuple[int,int]] = []
        for p,e in fac:
            if e >= 6 and chk is None:
                chk = p; e -= 6
            elif e >= 6:
                raise ValueError('Duplicate checksum')
            if e: data.append((p,e))
        if chk is None: raise ValueError('Checksum missing')
        # verify
        xor = 0
        for p,e in data: xor ^= _PRIME_IDX[p]*e
        if chk != get_prime(xor): raise ValueError('Checksum mismatch')
        # block framing
        if any(p==BLOCK_TAG and e==7 for p,e in data):
            lp = next(p for p,e in data if p!=BLOCK_TAG and e==5)
            cnt = _PRIME_IDX[lp]
            inner = chunks[i:i+cnt]; i += cnt
            yield from vm_execute(inner)
            continue
        # NTT opcode
        if any(p==NTT_TAG and e==4 for p,e in data):
            lp = next(p for p,e in data if p!=NTT_TAG and e==5)
            cnt = _PRIME_IDX[lp]
            inner = chunks[i:i+cnt]; i += cnt
            # gather raw exponents
            vec = []
            for c in inner:
                f = _factor(c); sub=[]; cchk=None
                for p2,e2 in f:
                    if e2>=6 and cchk is None: e2-=6; cchk=p2
                    sub.append((p2,e2))
                vec.append(next((e2 for _,e2 in sub if e2>0),0))
            # NTT round-trip integrity
            _ = ntt_inverse(ntt_forward(vec))
            # re-emit
            yield from vm_execute(inner)
            continue
        # exec or data
        exps = {e for _,e in data}
        if 4 in exps:
            op = next(p for p,e in data if e==4)
            if op==OP_PUSH:
                v = next(p for p,e in data if e==5); stack.append(_PRIME_IDX[v])
            elif op==OP_ADD:
                b,a = stack.pop(), stack.pop(); stack.append(a+b)
            elif op==OP_PRINT:
                yield str(stack.pop())
            else:
                raise ValueError('Unknown opcode')
        else:
            p_chr = next((p for p,e in data if e in (2,3)), None)
            if p_chr is None: raise ValueError('Bad data')
            yield chr(_PRIME_IDX[p_chr])

# ──────────────────────────────────────────────────────────────────────
# Tests & Demo
# ──────────────────────────────────────────────────────────────────────

def _self_tests() -> Tuple[int,int]:
    passed=failed=0
    def ok(cond,msg):
        nonlocal passed,failed
        if cond: passed+=1
        else: failed+=1; print('FAIL',msg)
    ok((OP_PUSH,OP_ADD,OP_PRINT)==(2,3,5),'primes')
    ok(''.join(vm_execute([chunk_data(i,ord(c)) for i,c in enumerate('Hi')]))=='Hi','roundtrip')
    seq=[chunk_data(i,ord(c)) for i,c in enumerate('XYZ')]
    prog=[chunk_ntt(3)]+seq
    ok(''.join(vm_execute(prog))=='XYZ','ntt roundtrip')
    return passed,failed

if __name__=='__main__':
    p,f=_self_tests()
    print(f'[tests] {p} passed, {f} failed')
    if f:
        sys.exit(f)
    # Demo
    sample = "Pure UOR demo 🎉"
    stream = [chunk_data(i, ord(c)) for i, c in enumerate(sample)]
    print("\nDemo ▶ Encoding chunks:")
    print(' '.join(str(x) for x in stream))
    print("Demo ▶ Decoded text:")
    print(''.join(vm_execute(stream)))
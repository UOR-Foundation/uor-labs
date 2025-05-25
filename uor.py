#!/usr/bin/env python3
"""Pure UOR virtual machine with extended opcodes."""
from __future__ import annotations

import sys
from typing import List, Tuple

import primes
import chunks
from vm import VM

# Opcode aliases for backwards compatibility
OP_PUSH = chunks.OP_PUSH
OP_ADD = chunks.OP_ADD
OP_SUB = chunks.OP_SUB
OP_MUL = chunks.OP_MUL
OP_PRINT = chunks.OP_PRINT
OP_LOAD = chunks.OP_LOAD
OP_STORE = chunks.OP_STORE
OP_JMP = chunks.OP_JMP
OP_JZ = chunks.OP_JZ
OP_JNZ = chunks.OP_JNZ

# Re-export for compatibility
get_prime = primes.get_prime
chunk_data = chunks.chunk_data
chunk_push = chunks.chunk_push
chunk_add = chunks.chunk_add
chunk_sub = chunks.chunk_sub
chunk_mul = chunks.chunk_mul
chunk_print = chunks.chunk_print
chunk_load = chunks.chunk_load
chunk_store = chunks.chunk_store
chunk_jmp = chunks.chunk_jmp
chunk_jz = chunks.chunk_jz
chunk_jnz = chunks.chunk_jnz
chunk_block_start = chunks.chunk_block_start
chunk_ntt = chunks.chunk_ntt


def vm_execute(prog: List[int]):
    """Execute program using the built-in VM."""
    return VM().execute(prog)


# ──────────────────────────────────────────────────────────────────────
# Tests & Demo
# ──────────────────────────────────────────────────────────────────────

def _self_tests() -> Tuple[int, int]:
    vm = VM()
    passed = failed = 0

    def ok(cond, msg):
        nonlocal passed, failed
        if cond:
            passed += 1
        else:
            failed += 1
            print("FAIL", msg)

    ok((chunks.OP_PUSH, chunks.OP_ADD, chunks.OP_PRINT) == (2, 3, 5), "primes")
    ok("".join(vm.execute([chunk_data(i, ord(c)) for i, c in enumerate("Hi")])) == "Hi", "roundtrip")
    seq = [chunk_data(i, ord(c)) for i, c in enumerate("XYZ")]
    prog = [chunk_ntt(3)] + seq
    ok("".join(VM().execute(prog)) == "XYZ", "ntt roundtrip")

    prog_mem = [
        chunk_push(10),
        chunk_store(0),
        chunk_load(0),
        chunk_print(),
    ]
    ok("".join(VM().execute(prog_mem)) == "10", "memory")

    prog_loop = [
        chunk_push(3),
        chunk_store(0),
        chunk_load(0),
        chunk_jz(7),
        chunk_load(0),
        chunk_print(),
        chunk_load(0),
        chunk_push(1),
        chunk_sub(),
        chunk_store(0),
        chunk_jmp(-9),
    ]
    ok("".join(VM().execute(prog_loop)) == "321", "loop")

    # Stress-test prime factorization with large numbers
    large = primes.get_prime(1000) * primes.get_prime(1100)
    fac = primes.factor(large)
    prod = 1
    for p_, e_ in fac:
        prod *= p_ ** e_
    ok(prod == large, "factor large")
    ok(primes.factor(large) == fac, "factor cache")

    return passed, failed


if __name__ == "__main__":
    p, f = _self_tests()
    print(f"[tests] {p} passed, {f} failed")
    if f:
        sys.exit(f)

    vm = VM()
    sample = "Pure UOR demo 🎉"
    stream = [chunk_data(i, ord(c)) for i, c in enumerate(sample)]
    print("\nDemo ▶ Encoding chunks:")
    print(" ".join(str(x) for x in stream))
    print("Demo ▶ Decoded text:")
    print("".join(vm.execute(stream)))

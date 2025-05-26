import time
import assembler
from decoder import decode, _CACHE
from primes import factor, optimized_factorize
from uor.memory import SegmentedMemory
from vm import VM
import chunks


def bench_prime_factorization(runs: int = 1000) -> tuple[float, float]:
    """Return baseline vs optimized times for factoring a large number."""
    n = 1000003 * 1000033
    start = time.perf_counter()
    for _ in range(runs):
        factor(n)
    baseline = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(runs):
        optimized_factorize(n)
    optimized = time.perf_counter() - start
    return baseline, optimized


def bench_decode_speed(runs: int = 200) -> tuple[float, float]:
    """Return decode times without cache and with cache."""
    src = """
    PUSH 1
    PUSH 2
    ADD
    PRINT
    """
    prog = assembler.assemble(src)
    # without cache
    total = 0.0
    for _ in range(runs):
        _CACHE.clear()
        start = time.perf_counter()
        decode(prog)
        total += time.perf_counter() - start
    no_cache = total

    # with cache
    _CACHE.clear()
    decode(prog)  # warm
    start = time.perf_counter()
    for _ in range(runs):
        decode(prog)
    with_cache = time.perf_counter() - start
    _CACHE.clear()
    return no_cache, with_cache


def bench_memory_allocation(runs: int = 1000) -> tuple[float, float]:
    """Return allocation times for manual free vs GC collect."""
    mem = SegmentedMemory()
    start = time.perf_counter()
    for _ in range(runs):
        addr = mem.allocate(32)
        mem.free(addr)
    manual = time.perf_counter() - start

    mem = SegmentedMemory()
    addrs = []
    start = time.perf_counter()
    for _ in range(runs):
        addrs.append(mem.allocate(32))
    mem.collect()
    gc_time = time.perf_counter() - start
    return manual, gc_time


def _build_arith_program(count: int) -> list[int]:
    prog = []
    for _ in range(count):
        prog.append(chunks.chunk_push(1))
        prog.append(chunks.chunk_push(2))
        prog.append(chunks.chunk_add())
        prog.append(chunks.chunk_print())  # print pops result
    return prog


def bench_arithmetic_throughput(count: int = 1000) -> tuple[float, float]:
    """Return execution time without JIT and with JIT for arithmetic ops."""
    prog = _build_arith_program(count)
    decoded = decode(prog)

    vm = VM()
    vm.jit_threshold = count + 1  # disable JIT
    start = time.perf_counter()
    "".join(vm.execute(decoded))
    baseline = time.perf_counter() - start

    vm_jit = VM()
    vm_jit.jit_threshold = 1
    vm_jit._jit.available = True
    start = time.perf_counter()
    "".join(vm_jit.execute(decoded))
    optimized = time.perf_counter() - start
    return baseline, optimized


def _build_crypto_program(count: int) -> list[int]:
    prog = []
    for _ in range(count):
        prog.append(chunks.chunk_push(10))
        prog.append(chunks.chunk_hash())
        prog.append(chunks.chunk_push(5))
        prog.append(chunks.chunk_sign())
        prog.append(chunks.chunk_push(5))
        prog.append(chunks.chunk_verify())
        prog.append(chunks.chunk_print())
    return prog


def bench_crypto_operations(count: int = 500) -> tuple[float, float]:
    """Return execution time without JIT and with JIT for crypto ops."""
    prog = _build_crypto_program(count)
    decoded = decode(prog)

    vm = VM()
    vm.jit_threshold = count + 1
    start = time.perf_counter()
    "".join(vm.execute(decoded))
    baseline = time.perf_counter() - start

    vm_jit = VM()
    vm_jit.jit_threshold = 1
    vm_jit._jit.available = True
    start = time.perf_counter()
    "".join(vm_jit.execute(decoded))
    optimized = time.perf_counter() - start
    return baseline, optimized


if __name__ == "__main__":
    pf_base, pf_opt = bench_prime_factorization()
    dec_base, dec_cache = bench_decode_speed()
    mem_manual, mem_gc = bench_memory_allocation()
    arith_base, arith_jit = bench_arithmetic_throughput()
    crypto_base, crypto_jit = bench_crypto_operations()

    print("Prime factorization:\t", pf_base, pf_opt)
    print("Decode speed:\t", dec_base, dec_cache)
    print("Memory allocation:\t", mem_manual, mem_gc)
    print("Arithmetic throughput:\t", arith_base, arith_jit)
    print("Crypto ops:\t", crypto_base, crypto_jit)

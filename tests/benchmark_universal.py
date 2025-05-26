"""Simple benchmarks for UniversalNumber helpers."""
import time
from uor.parallel_universal import fast_prime_factorization, discrete_wavelet_transform, CUDA_AVAILABLE


def bench_factorization(runs: int = 1000) -> float:
    n = 1234567891011
    start = time.time()
    for _ in range(runs):
        fast_prime_factorization(n)
    return time.time() - start


def bench_dwt(runs: int = 1000) -> float:
    data = list(range(64))
    if not CUDA_AVAILABLE:
        return 0.0
    start = time.time()
    for _ in range(runs):
        discrete_wavelet_transform(data)
    return time.time() - start


if __name__ == "__main__":
    fact_t = bench_factorization()
    print(f"factorization: {fact_t:.6f}s")
    if CUDA_AVAILABLE:
        dwt_t = bench_dwt()
        print(f"dwt (cuda): {dwt_t:.6f}s")
    else:
        print("CUDA not available - skipping DWT benchmark")


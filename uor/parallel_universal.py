"""Parallelized UniversalNumber helpers."""
from __future__ import annotations

from typing import Dict, List

import numpy as np

try:
    from numba import njit, cuda, int64
    from numba.typed import List as NumbaList
    from numba.types import UniTuple
    NUMBA_AVAILABLE = True
    CUDA_AVAILABLE = cuda.is_available()
except Exception:  # pragma: no cover - optional dependency may be missing
    NUMBA_AVAILABLE = False
    CUDA_AVAILABLE = False

    def njit(*args, **kwargs):  # type: ignore
        if args and callable(args[0]):
            return args[0]
        def wrapper(func):
            return func
        return wrapper

    class DummyCuda:
        def is_available(self) -> bool:
            return False
        def __getattr__(self, name):
            raise RuntimeError("CUDA not available")
    cuda = DummyCuda()  # type: ignore
    int64 = None  # type: ignore
    def NumbaList(*args, **kwargs):  # type: ignore
        raise RuntimeError("Numba not available")
    def UniTuple(*args, **kwargs):  # type: ignore
        raise RuntimeError("Numba not available")


@njit
def _factor_list(n: int):
    res = NumbaList.empty_list(UniTuple(int64, 2)) if NUMBA_AVAILABLE else []
    i = 2
    while i * i <= n:
        cnt = 0
        while n % i == 0:
            n //= i
            cnt += 1
        if cnt:
            if NUMBA_AVAILABLE:
                res.append((i, cnt))
            else:
                res.append((i, cnt))
        i += 1
    if n > 1:
        if NUMBA_AVAILABLE:
            res.append((n, 1))
        else:
            res.append((n, 1))
    return res


def fast_prime_factorization(value: int) -> Dict[int, int]:
    """Return prime factorization of ``value`` using Numba if available."""
    pairs = _factor_list(value)
    return {int(p): int(e) for p, e in pairs}


@njit
def _haar_cpu(arr: np.ndarray) -> np.ndarray:
    n = arr.shape[0] // 2
    out = np.empty_like(arr)
    for i in range(n):
        a = arr[2 * i]
        b = arr[2 * i + 1]
        out[i] = 0.5 * (a + b)
        out[n + i] = 0.5 * (a - b)
    return out

if CUDA_AVAILABLE:
    @cuda.jit
    def _haar_kernel(data, out):
        i = cuda.grid(1)
        n = data.shape[0] // 2
        if i < n:
            a = data[2 * i]
            b = data[2 * i + 1]
            out[i] = (a + b) / 2.0
            out[n + i] = (a - b) / 2.0
else:  # pragma: no cover - CUDA not available
    def _haar_kernel(data, out):
        raise RuntimeError("CUDA not available")


def discrete_wavelet_transform(signal: List[float]) -> List[float]:
    """Perform a single-level Haar DWT on ``signal``. Uses CUDA if available."""
    arr = np.asarray(signal, dtype=np.float64)
    if CUDA_AVAILABLE:
        d_in = cuda.to_device(arr)
        d_out = cuda.device_array_like(arr)
        threads = 32
        blocks = (arr.shape[0] // 2 + threads - 1) // threads
        _haar_kernel[blocks, threads](d_in, d_out)
        return d_out.copy_to_host().tolist()
    else:
        return _haar_cpu(arr).tolist()


__all__ = ["fast_prime_factorization", "discrete_wavelet_transform", "CUDA_AVAILABLE"]

"""Representation of integers with prime and geometric coordinates."""
from __future__ import annotations

from math import sqrt
from typing import Dict, Tuple, Iterable, List

from primes import factor


class UniversalNumber:
    """Integer wrapper exposing prime factors and a simple Clifford frame."""

    _prime_cache: Dict[int, Dict[int, int]] = {}
    _frame_cache: Dict[Tuple[int, int], Dict[str, Tuple[int, ...]]] = {}

    def __init__(self, value: int, cl_algebra: Tuple[int, int] = (3, 0)) -> None:
        self.value = int(value)
        self.cl_algebra = cl_algebra
        self.prime_coords = self._prime_factorization(self.value)
        self.reference_frame = self._init_reference_frame()

    # ------------------------------------------------------------------
    # Prime factorization helpers
    # ------------------------------------------------------------------
    @classmethod
    def _prime_factorization(cls, value: int) -> Dict[int, int]:
        if value in cls._prime_cache:
            return dict(cls._prime_cache[value])
        fac = {p: exp for p, exp in factor(value)}
        cls._prime_cache[value] = dict(fac)
        return fac

    # ------------------------------------------------------------------
    # Reference frame helpers
    # ------------------------------------------------------------------
    def _init_reference_frame(self) -> Dict[str, Tuple[int, ...]]:
        key = self.cl_algebra
        if key in self._frame_cache:
            return dict(self._frame_cache[key])

        # Only create a simple 3D euclidean frame for now
        frame = {
            "e1": (1,),
            "e2": (2,),
            "e3": (3,),
            "e12": (1, 2),
            "e23": (2, 3),
            "e31": (3, 1),
            "e123": (1, 2, 3),
        }

        self._frame_cache[key] = dict(frame)
        return frame

    # ------------------------------------------------------------------
    # Basic operations
    # ------------------------------------------------------------------
    def getGradedComponents(self, bases: Iterable[int]) -> List[int]:
        """Return the digits of ``value`` in the given ``bases``."""
        digits: List[int] = []
        n = self.value
        for base in bases:
            digits.append(n % base)
            n //= base
        return digits

    def innerProduct(self, other: "UniversalNumber") -> int:
        """Simple Clifford inner product using prime exponents."""
        result = 0
        primes = set(self.prime_coords) | set(other.prime_coords)
        for p in primes:
            result += self.prime_coords.get(p, 0) * other.prime_coords.get(p, 0)
        return result

    def coherenceNorm(self) -> float:
        """Euclidean norm based on prime exponents for coherence metrics."""
        return sqrt(self.innerProduct(self))

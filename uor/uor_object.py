from __future__ import annotations

"""Core UOR object model with trilateral coherence."""

from typing import Callable, Tuple

from .universal_number import UniversalNumber


class UORObject:
    """Represents an object in the UOR framework with trilateral coherence."""

    def __init__(
        self,
        content: int,
        *,
        representation: int | None = None,
        observer: Tuple[int, int] = (3, 0),
    ) -> None:
        self.observer = observer
        self.content_num = UniversalNumber(content, cl_algebra=observer)
        rep = representation if representation is not None else self._encode(content)
        self.representation_num = UniversalNumber(rep, cl_algebra=observer)
        self._validate_coherence()

    # ------------------------------------------------------------------
    # Encoding helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _encode(value: int) -> int:
        """Default prime encoding uses the value itself."""
        return value

    @staticmethod
    def _decode(value: int) -> int:
        return value

    # ------------------------------------------------------------------
    # Coherence utilities
    # ------------------------------------------------------------------
    def _coherence_vector(self) -> UniversalNumber:
        diff: dict[int, int] = {}
        primes = set(self.content_num.prime_coords) | set(
            self.representation_num.prime_coords
        )
        for p in primes:
            diff[p] = self.content_num.prime_coords.get(p, 0) - self.representation_num.prime_coords.get(p, 0)
        vec = UniversalNumber(1, cl_algebra=self.observer)
        vec.prime_coords = diff
        return vec

    def coherence_norm(self) -> float:
        return self._coherence_vector().coherenceNorm()

    def _validate_coherence(self) -> None:
        if abs(self.coherence_norm()) > 1e-9:
            raise ValueError("Object is incoherent")

    # ------------------------------------------------------------------
    # Transformations
    # ------------------------------------------------------------------
    def transform(self, func: Callable[[int], int]) -> "UORObject":
        new_content = func(self.content_num.value)
        new_rep = func(self.representation_num.value)
        return UORObject(new_content, representation=new_rep, observer=self.observer)

    def transform_observer(self, frame: Tuple[int, int]) -> "UORObject":
        return UORObject(
            self.content_num.value,
            representation=self.representation_num.value,
            observer=frame,
        )

    # ------------------------------------------------------------------
    # Serialization helpers
    # ------------------------------------------------------------------
    def to_prime_encoding(self) -> int:
        return self.representation_num.value

    @classmethod
    def from_prime_encoding(
        cls, encoding: int, *, observer: Tuple[int, int] = (3, 0)
    ) -> "UORObject":
        content = cls._decode(encoding)
        return cls(content, representation=encoding, observer=observer)

    # ------------------------------------------------------------------
    # Comparisons
    # ------------------------------------------------------------------
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, UORObject):
            return NotImplemented
        return self.to_prime_encoding() == other.to_prime_encoding()

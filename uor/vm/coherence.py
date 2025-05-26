"""Coherence validation helpers for the VM."""
from __future__ import annotations

from typing import Dict

from ..exceptions import CoherenceViolationError


class CoherenceMode:
    """Available coherence checking modes."""

    STRICT = "STRICT"
    TOLERANT = "TOLERANT"
    DISABLED = "DISABLED"


class CoherenceValidator:
    """Validate and restore VM coherence across instruction boundaries."""

    def __init__(self, *, tolerance: float = 1.0, mode: str = CoherenceMode.STRICT, runtime_check: bool = True) -> None:
        self.tolerance = tolerance
        self.mode = mode
        self.runtime_check = runtime_check
        self._last_checksum = 0.0
        self.max_drift = 0.0
        self.restorations = 0
        self.violations = 0

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _checksum(self, vm) -> float:
        return float(sum(vm.stack) + sum(vm.mem.storage.values()) + vm.ip)

    def start(self, vm) -> None:
        self._last_checksum = self._checksum(vm)
        self.max_drift = 0.0
        self.restorations = 0
        self.violations = 0

    def check(self, vm) -> None:
        if self.mode == CoherenceMode.DISABLED or not self.runtime_check:
            self._last_checksum = self._checksum(vm)
            return

        current = self._checksum(vm)
        drift = abs(current - self._last_checksum)
        self.max_drift = max(self.max_drift, drift)
        if drift <= self.tolerance:
            self._last_checksum = current
            return

        if self.mode == CoherenceMode.TOLERANT:
            self.restore(vm)
            self._last_checksum = self._checksum(vm)
            return

        self.violations += 1
        raise CoherenceViolationError(
            f"Coherence drift {drift:.2f} exceeds tolerance {self.tolerance}"
        )

    def restore(self, vm) -> None:
        self.restorations += 1
        self._last_checksum = self._checksum(vm)

    def metrics(self) -> Dict[str, float | int]:
        return {
            "max_drift": self.max_drift,
            "restorations": self.restorations,
            "violations": self.violations,
        }

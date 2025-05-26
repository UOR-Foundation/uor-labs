"""Runtime profiling utilities for the VM."""
from __future__ import annotations

import json
import time
from typing import Any, Dict, Optional


class Profiler:
    """Collect and export execution metrics."""

    def __init__(self, websocket: Optional[Any] = None) -> None:
        self.websocket = websocket
        self.reset()

    def reset(self) -> None:
        self.start = time.time()
        self.instruction_count = 0
        self.memory_usage = 0
        self.cache_hits = 0
        self.io_count = 0
        self.network_latency = 0.0

    # ------------------------------------------------------------------
    # Recording helpers
    # ------------------------------------------------------------------
    def record_instruction(self, vm, *, cache_hit: bool = False) -> None:
        """Record a single executed instruction."""
        self.instruction_count += 1
        if cache_hit:
            self.cache_hits += 1
        self.memory_usage = len(getattr(vm, "mem", {}))
        self._maybe_send()

    def record_io(self) -> None:
        self.io_count += 1
        self._maybe_send()

    def record_network_latency(self, latency: float) -> None:
        self.network_latency += latency
        self._maybe_send()

    # ------------------------------------------------------------------
    # Export helpers
    # ------------------------------------------------------------------
    def metrics(self) -> Dict[str, Any]:
        elapsed = time.time() - self.start
        ips = self.instruction_count / elapsed if elapsed > 0 else 0.0
        return {
            "instructions_per_second": ips,
            "memory_usage": self.memory_usage,
            "cache_hits": self.cache_hits,
            "io_count": self.io_count,
            "network_latency": self.network_latency,
        }

    def to_json(self) -> str:
        return json.dumps(self.metrics())

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    def _maybe_send(self) -> None:
        if self.websocket is None:
            return
        try:
            self.websocket.send(self.to_json())
        except Exception:
            pass

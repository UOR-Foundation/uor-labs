from __future__ import annotations

"""Advanced profiler for the UOR virtual machine."""

import json
import time
from collections import defaultdict
from typing import Any, Dict, Optional

from decoder import _CACHE


class VMProfiler:
    """Collect detailed execution metrics for a VM run."""

    def __init__(self) -> None:
        self.reset()

    # ------------------------------------------------------------------
    def reset(self) -> None:
        self.start_time = time.perf_counter()
        self.instruction_count = 0
        self.total_time = 0.0
        self.opcode_counts: Dict[int, int] = defaultdict(int)
        self.ip_counts: Dict[int, int] = defaultdict(int)
        self.instruction_times: Dict[int, float] = defaultdict(float)
        self.memory_access: Dict[int, Dict[str, int]] = defaultdict(lambda: {"read": 0, "write": 0})
        self.cache_hits = 0
        self.cache_misses = 0

    # ------------------------------------------------------------------
    def record_instruction(self, ip: int, opcode: Optional[int], duration: float, *, cache_hit: bool = False) -> None:
        """Record execution of a single instruction."""
        self.instruction_count += 1
        self.total_time += duration
        if opcode is not None:
            self.opcode_counts[opcode] += 1
        self.ip_counts[ip] += 1
        self.instruction_times[ip] += duration
        if cache_hit:
            self.cache_hits += 1

    def record_memory_access(self, addr: int, mode: str) -> None:
        if mode == "read":
            self.memory_access[addr]["read"] += 1
        elif mode == "write":
            self.memory_access[addr]["write"] += 1

    # ------------------------------------------------------------------
    def metrics(self) -> Dict[str, Any]:
        elapsed = time.perf_counter() - self.start_time
        cache_stats = _CACHE.get_stats()
        return {
            "instruction_count": self.instruction_count,
            "elapsed": elapsed,
            "opcode_counts": dict(self.opcode_counts),
            "ip_hotspots": dict(self.ip_counts),
            "memory_access": dict(self.memory_access),
            "cache_stats": {
                "hits": cache_stats.get("hits", 0) + self.cache_hits,
                "misses": cache_stats.get("misses", 0),
            },
        }

    def export_report(self) -> str:
        """Return collected metrics as a JSON string."""
        return json.dumps(self.metrics())

    def export_flamegraph(self) -> str:
        """Return execution timing data in folded stack format."""
        lines = []
        for ip, dur in self.instruction_times.items():
            lines.append(f"ip_{ip} {dur}\n")
        return "".join(lines)


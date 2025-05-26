from __future__ import annotations

from collections import OrderedDict
from threading import Lock
from typing import Any, Dict, Optional


class InstructionCache:
    """Thread-safe LRU cache for decoded instructions."""

    def __init__(self, max_size: int = 128) -> None:
        self.max_size = max_size
        self._data: "OrderedDict[int, Any]" = OrderedDict()
        self._lock = Lock()
        self._hits = 0
        self._misses = 0
        self._decode_times: Dict[int, float] = {}
        self._total_time_saved = 0.0
        self._time_saved_hits = 0

    def get(self, key: int) -> Optional[Any]:
        """Retrieve ``key`` from the cache."""
        with self._lock:
            if key in self._data:
                value = self._data.pop(key)
                self._data[key] = value  # mark as recently used
                self._hits += 1
                if key in self._decode_times:
                    self._total_time_saved += self._decode_times[key]
                    self._time_saved_hits += 1
                return value
            self._misses += 1
            return None

    def put(self, key: int, value: Any, *, decode_time: Optional[float] = None) -> None:
        """Insert ``value`` for ``key`` into the cache.

        If ``decode_time`` is provided it is used when calculating the average
        decode time saved for cache hits.
        """
        with self._lock:
            if key in self._data:
                self._data.pop(key)
            elif len(self._data) >= self.max_size:
                old_key, _ = self._data.popitem(last=False)
                self._decode_times.pop(old_key, None)
            self._data[key] = value
            if decode_time is not None:
                self._decode_times[key] = decode_time

    def clear(self) -> None:
        """Clear the cache and statistics."""
        with self._lock:
            self._data.clear()
            self._decode_times.clear()
            self._hits = 0
            self._misses = 0
            self._total_time_saved = 0.0
            self._time_saved_hits = 0

    def get_stats(self) -> Dict[str, float]:
        """Return cache statistics as a dictionary."""
        with self._lock:
            ops = self._hits + self._misses
            hit_rate = self._hits / ops if ops else 0.0
            avg_time = (
                self._total_time_saved / self._time_saved_hits
                if self._time_saved_hits
                else 0.0
            )
            return {
                "hits": self._hits,
                "misses": self._misses,
                "size": len(self._data),
                "hit_rate": hit_rate,
                "avg_decode_time_saved": avg_time,
            }

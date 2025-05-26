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

    def get(self, key: int) -> Optional[Any]:
        """Retrieve ``key`` from the cache."""
        with self._lock:
            if key in self._data:
                value = self._data.pop(key)
                self._data[key] = value  # mark as recently used
                self._hits += 1
                return value
            self._misses += 1
            return None

    def put(self, key: int, value: Any) -> None:
        """Insert ``value`` for ``key`` into the cache."""
        with self._lock:
            if key in self._data:
                self._data.pop(key)
            elif len(self._data) >= self.max_size:
                self._data.popitem(last=False)
            self._data[key] = value

    def clear(self) -> None:
        """Clear the cache and statistics."""
        with self._lock:
            self._data.clear()
            self._hits = 0
            self._misses = 0

    def get_stats(self) -> Dict[str, int]:
        """Return cache statistics as a dictionary."""
        with self._lock:
            return {"hits": self._hits, "misses": self._misses}

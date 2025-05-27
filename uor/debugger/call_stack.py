from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CallFrame:
    """Represents a single call frame."""
    call_site: int
    return_ip: int


class CallStackTracker:
    """Track call/return events for backtraces."""

    def __init__(self) -> None:
        self.frames: List[CallFrame] = []

    def push(self, call_site: int, return_ip: int) -> None:
        """Push a new frame onto the call stack."""
        self.frames.append(CallFrame(call_site, return_ip))

    def pop(self) -> Optional[CallFrame]:
        """Pop the most recent frame, if any."""
        if not self.frames:
            return None
        return self.frames.pop()

    def backtrace(self) -> List[CallFrame]:
        """Return the current backtrace (newest frame first)."""
        return list(reversed(self.frames))

    def clear(self) -> None:
        self.frames.clear()

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self.frames)

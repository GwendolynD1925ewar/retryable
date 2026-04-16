"""Sliding window attempt tracker for retry logic."""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field


@dataclass
class RetryWindow:
    """Tracks attempt timestamps within a rolling time window."""

    window_seconds: float
    max_attempts: int

    _timestamps: deque = field(default_factory=deque, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")

    def _evict(self, now: float) -> None:
        cutoff = now - self.window_seconds
        while self._timestamps and self._timestamps[0] <= cutoff:
            self._timestamps.popleft()

    def record(self, now: float | None = None) -> None:
        """Record an attempt at the current (or provided) time."""
        ts = now if now is not None else time.monotonic()
        self._evict(ts)
        self._timestamps.append(ts)

    def allowed(self, now: float | None = None) -> bool:
        """Return True if another attempt is permitted within the window."""
        ts = now if now is not None else time.monotonic()
        self._evict(ts)
        return len(self._timestamps) < self.max_attempts

    def attempt_count(self, now: float | None = None) -> int:
        """Return number of attempts recorded in the current window."""
        ts = now if now is not None else time.monotonic()
        self._evict(ts)
        return len(self._timestamps)

    def reset(self) -> None:
        """Clear all recorded attempts."""
        self._timestamps.clear()

"""RetryTide: tracks attempt volume over a sliding time window and detects surges."""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Deque


class TideSurge(Exception):
    """Raised when the attempt rate exceeds the surge threshold."""

    def __init__(self, count: int, window: float, threshold: int) -> None:
        self.count = count
        self.window = window
        self.threshold = threshold
        super().__init__(
            f"Retry tide surge: {count} attempts in {window}s window "
            f"(threshold={threshold})"
        )


@dataclass
class RetryTide:
    """Sliding-window attempt counter that can detect surge conditions."""

    window: float
    surge_threshold: int
    _clock: Callable[[], float] = field(default=time.monotonic, repr=False)
    _timestamps: Deque[float] = field(default_factory=deque, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.window <= 0:
            raise ValueError("window must be positive")
        if self.surge_threshold < 1:
            raise ValueError("surge_threshold must be >= 1")

    def _evict(self) -> None:
        cutoff = self._clock() - self.window
        while self._timestamps and self._timestamps[0] <= cutoff:
            self._timestamps.popleft()

    def record(self) -> None:
        """Record a new attempt timestamp."""
        self._evict()
        self._timestamps.append(self._clock())

    def count(self) -> int:
        """Return the number of attempts within the current window."""
        self._evict()
        return len(self._timestamps)

    def surging(self) -> bool:
        """Return True if the attempt count exceeds the surge threshold."""
        return self.count() >= self.surge_threshold

    def check(self) -> None:
        """Raise TideSurge if the attempt count exceeds the surge threshold."""
        n = self.count()
        if n >= self.surge_threshold:
            raise TideSurge(n, self.window, self.surge_threshold)

    def reset(self) -> None:
        """Clear all recorded timestamps."""
        self._timestamps.clear()

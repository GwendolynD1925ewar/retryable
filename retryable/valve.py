"""RetryValve — flow-control gate that pauses retries when throughput exceeds a threshold."""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Deque


class ValveThrottled(Exception):
    """Raised when the valve is closed and no wait budget remains."""

    def __init__(self, message: str = "Retry valve is closed") -> None:
        super().__init__(message)


@dataclass
class RetryValve:
    """Sliding-window throughput gate for retry flows.

    The valve allows at most *max_throughput* retries within any rolling
    *window_seconds* period.  Once the limit is reached the valve is
    considered *closed*; callers can check :meth:`open` before proceeding
    or call :meth:`acquire` which raises :class:`ValveThrottled` when closed.
    """

    max_throughput: int
    window_seconds: float
    _clock: Callable[[], float] = field(default=time.monotonic, repr=False)
    _timestamps: Deque[float] = field(default_factory=deque, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.max_throughput <= 0:
            raise ValueError("max_throughput must be a positive integer")
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be positive")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _evict(self, now: float) -> None:
        cutoff = now - self.window_seconds
        while self._timestamps and self._timestamps[0] <= cutoff:
            self._timestamps.popleft()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def open(self) -> bool:
        """Return ``True`` when the valve permits another retry."""
        now = self._clock()
        self._evict(now)
        return len(self._timestamps) < self.max_throughput

    def acquire(self) -> None:
        """Record a retry attempt or raise :class:`ValveThrottled`."""
        now = self._clock()
        self._evict(now)
        if len(self._timestamps) >= self.max_throughput:
            raise ValveThrottled(
                f"Retry valve closed: {self.max_throughput} retries already "
                f"recorded within the last {self.window_seconds}s"
            )
        self._timestamps.append(now)

    @property
    def current_count(self) -> int:
        """Number of retry attempts recorded in the current window."""
        now = self._clock()
        self._evict(now)
        return len(self._timestamps)

    @property
    def remaining(self) -> int:
        """Remaining retry slots in the current window."""
        return max(0, self.max_throughput - self.current_count)

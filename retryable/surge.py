"""RetrySurge: tracks burst attempt counts within a rolling window and
rejects retries when the burst limit is exceeded."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field


class SurgeLimitExceeded(Exception):
    """Raised when the burst retry limit within a window is exceeded."""

    def __init__(self, limit: int, window: float) -> None:
        self.limit = limit
        self.window = window
        super().__init__(
            f"Retry surge limit of {limit} attempts per {window}s exceeded."
        )


@dataclass
class RetrySurge:
    """Tracks retry attempts in a rolling time window and enforces a burst cap.

    Args:
        limit: Maximum number of retry attempts allowed within *window* seconds.
        window: Rolling time window in seconds.
        clock: Callable returning current time as a float (defaults to time.monotonic).
    """

    limit: int
    window: float
    clock: object = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self.limit <= 0:
            raise ValueError("limit must be a positive integer.")
        if self.window <= 0:
            raise ValueError("window must be a positive number.")
        if self.clock is None:
            self.clock = time.monotonic
        self._timestamps: deque[float] = deque()

    def _evict(self) -> None:
        now = self.clock()
        cutoff = now - self.window
        while self._timestamps and self._timestamps[0] <= cutoff:
            self._timestamps.popleft()

    def acquire(self) -> None:
        """Record an attempt, raising SurgeLimitExceeded if the burst cap is hit."""
        self._evict()
        if len(self._timestamps) >= self.limit:
            raise SurgeLimitExceeded(self.limit, self.window)
        self._timestamps.append(self.clock())

    @property
    def current_count(self) -> int:
        """Number of attempts recorded in the current window."""
        self._evict()
        return len(self._timestamps)

    @property
    def remaining(self) -> int:
        """Remaining attempts allowed before the burst cap is hit."""
        return max(0, self.limit - self.current_count)

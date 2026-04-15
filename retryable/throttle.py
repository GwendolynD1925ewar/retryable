"""Throttle support for retry logic — limits retry rate using a token bucket."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


class ThrottleExceeded(Exception):
    """Raised when a retry is rejected due to throttle limits."""

    def __init__(self, retry_after: float) -> None:
        self.retry_after = retry_after
        super().__init__(f"Throttle exceeded; retry after {retry_after:.3f}s")


@dataclass
class RetryThrottle:
    """Enforces a minimum interval between successive retry attempts.

    Args:
        min_interval: Minimum seconds required between retries.
        max_wait: If set, block up to this many seconds instead of raising.
    """

    min_interval: float
    max_wait: Optional[float] = None
    _last_retry_at: float = field(default=0.0, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.min_interval <= 0:
            raise ValueError("min_interval must be positive")
        if self.max_wait is not None and self.max_wait < 0:
            raise ValueError("max_wait must be non-negative")

    def acquire(self, *, _now: Optional[float] = None) -> float:
        """Acquire permission to retry.

        Returns the number of seconds waited (0 if no wait was needed).
        Raises ThrottleExceeded if the required wait exceeds max_wait.
        """
        now = _now if _now is not None else time.monotonic()
        elapsed = now - self._last_retry_at
        wait_needed = max(0.0, self.min_interval - elapsed)

        if wait_needed > 0:
            if self.max_wait is not None and wait_needed > self.max_wait:
                raise ThrottleExceeded(retry_after=wait_needed)
            time.sleep(wait_needed)

        self._last_retry_at = time.monotonic()
        return wait_needed

    @property
    def seconds_until_ready(self) -> float:
        """Estimate of how many seconds until the next retry is allowed."""
        elapsed = time.monotonic() - self._last_retry_at
        return max(0.0, self.min_interval - elapsed)

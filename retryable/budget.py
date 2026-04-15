"""Retry budget support for limiting total retry attempts across calls."""

import threading
import time
from typing import Optional


class RetryBudget:
    """Tracks and limits the total number of retries allowed within a time window.

    Useful for preventing retry storms in high-throughput systems by capping
    the total number of retries across multiple calls to retried functions.
    """

    def __init__(self, max_retries: int, window_seconds: float = 60.0):
        """Initialize the retry budget.

        Args:
            max_retries: Maximum number of retries allowed within the window.
            window_seconds: Duration of the sliding window in seconds.
        """
        if max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")

        self.max_retries = max_retries
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        self._retry_timestamps: list[float] = []

    def _evict_expired(self, now: float) -> None:
        """Remove timestamps outside the current window."""
        cutoff = now - self.window_seconds
        self._retry_timestamps = [
            ts for ts in self._retry_timestamps if ts > cutoff
        ]

    def acquire(self) -> bool:
        """Attempt to consume one retry from the budget.

        Returns:
            True if a retry is permitted, False if the budget is exhausted.
        """
        now = time.monotonic()
        with self._lock:
            self._evict_expired(now)
            if len(self._retry_timestamps) < self.max_retries:
                self._retry_timestamps.append(now)
                return True
            return False

    def remaining(self) -> int:
        """Return the number of retries remaining in the current window."""
        now = time.monotonic()
        with self._lock:
            self._evict_expired(now)
            return max(0, self.max_retries - len(self._retry_timestamps))

    def reset(self) -> None:
        """Clear all recorded retry timestamps, fully restoring the budget."""
        with self._lock:
            self._retry_timestamps.clear()

    def __repr__(self) -> str:
        return (
            f"RetryBudget(max_retries={self.max_retries}, "
            f"window_seconds={self.window_seconds})"
        )

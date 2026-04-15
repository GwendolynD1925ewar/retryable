"""Timeout support for retry operations."""

import time
from typing import Optional


class RetryTimeout:
    """Tracks an overall deadline across multiple retry attempts."""

    def __init__(self, total_seconds: float):
        """Create a timeout that expires after *total_seconds* seconds.

        Args:
            total_seconds: Maximum wall-clock time (in seconds) allowed for
                all retry attempts combined.  Must be a positive number.

        Raises:
            ValueError: If *total_seconds* is not positive.
        """
        if total_seconds <= 0:
            raise ValueError(
                f"total_seconds must be positive, got {total_seconds}"
            )
        self._total_seconds = total_seconds
        self._deadline: float = time.monotonic() + total_seconds

    @property
    def total_seconds(self) -> float:
        """The original timeout duration in seconds."""
        return self._total_seconds

    @property
    def remaining(self) -> float:
        """Seconds remaining before the deadline (never negative)."""
        return max(0.0, self._deadline - time.monotonic())

    @property
    def expired(self) -> bool:
        """True if the deadline has passed."""
        return time.monotonic() >= self._deadline

    def clamp_delay(self, delay: float) -> float:
        """Return *delay* clamped so it does not exceed the remaining time.

        Args:
            delay: Proposed sleep duration in seconds.

        Returns:
            The smaller of *delay* and :attr:`remaining`.
        """
        return min(delay, self.remaining)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"RetryTimeout(total_seconds={self._total_seconds}, "
            f"remaining={self.remaining:.3f})"
        )


def no_timeout() -> None:
    """Sentinel that signals no deadline should be enforced."""
    return None

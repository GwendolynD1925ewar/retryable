"""High-watermark tracking for retry attempt counts across calls."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RetryWatermark:
    """Tracks the maximum number of attempts ever seen across all calls.

    Useful for surfacing worst-case retry behaviour in production systems
    without requiring a full metrics pipeline.
    """

    _peak: int = field(default=0, init=False, repr=False)
    _total_calls: int = field(default=0, init=False, repr=False)
    _threshold: int = 1

    def __post_init__(self) -> None:
        if self._threshold < 1:
            raise ValueError("threshold must be >= 1")

    def record(self, attempts: int) -> None:
        """Record the number of attempts used by a single call.

        Args:
            attempts: Total attempts made (>= 1).

        Raises:
            ValueError: If *attempts* is less than 1.
        """
        if attempts < 1:
            raise ValueError("attempts must be >= 1")
        self._total_calls += 1
        if attempts > self._peak:
            self._peak = attempts

    @property
    def peak(self) -> int:
        """The highest attempt count recorded so far."""
        return self._peak

    @property
    def total_calls(self) -> int:
        """Total number of calls recorded."""
        return self._total_calls

    @property
    def threshold_breached(self) -> bool:
        """True when *peak* exceeds the configured threshold."""
        return self._peak > self._threshold

    def reset(self) -> None:
        """Reset all counters back to zero."""
        self._peak = 0
        self._total_calls = 0

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"RetryWatermark(peak={self._peak}, "
            f"total_calls={self._total_calls}, "
            f"threshold={self._threshold})"
        )


def watermark_hook(watermark: RetryWatermark):
    """Return an *on_retry* hook that records attempt counts into *watermark*.

    The hook increments the attempt counter on every retry so that when the
    decorated call eventually resolves the watermark reflects the total
    attempts used.
    """

    def hook(
        attempt: int,
        exception: Optional[BaseException] = None,
        result: object = None,
    ) -> None:
        # attempt is 1-based; record after each retry so the final attempt
        # count (including the eventual success/failure) is captured.
        watermark.record(attempt)

    return hook

"""RetryBand — clamps computed backoff delays into a [min_delay, max_delay] band."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


class BandViolation(Exception):
    def __init__(self, msg: str) -> None:
        super().__init__(msg)


@dataclass
class RetryBand:
    """Wraps a backoff callable and clamps its output to [min_delay, max_delay]."""

    min_delay: float
    max_delay: float
    backoff: Callable[[int], float]

    def __post_init__(self) -> None:
        if self.min_delay < 0:
            raise ValueError("min_delay must be >= 0")
        if self.max_delay <= 0:
            raise ValueError("max_delay must be > 0")
        if self.min_delay > self.max_delay:
            raise ValueError("min_delay must be <= max_delay")

    def delay(self, attempt: int) -> float:
        """Return the clamped delay for the given attempt number."""
        raw = self.backoff(attempt)
        return max(self.min_delay, min(self.max_delay, raw))

    def within_band(self, value: float) -> bool:
        """Return True if *value* falls within [min_delay, max_delay]."""
        return self.min_delay <= value <= self.max_delay

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"RetryBand(min_delay={self.min_delay}, max_delay={self.max_delay})"
        )

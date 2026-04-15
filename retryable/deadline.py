"""Per-attempt deadline enforcement for retry logic."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


class AttemptDeadlineExceeded(Exception):
    """Raised when a single attempt exceeds its allotted deadline."""

    def __init__(self, deadline_seconds: float, elapsed: float) -> None:
        self.deadline_seconds = deadline_seconds
        self.elapsed = elapsed
        super().__init__(
            f"Attempt exceeded deadline of {deadline_seconds}s (elapsed {elapsed:.3f}s)"
        )


@dataclass
class AttemptDeadline:
    """Tracks a per-attempt time budget.

    Args:
        seconds: Maximum seconds allowed for a single attempt.
    """

    seconds: float
    _start: float = field(default_factory=time.monotonic, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.seconds <= 0:
            raise ValueError(f"deadline seconds must be positive, got {self.seconds}")

    @property
    def elapsed(self) -> float:
        """Seconds elapsed since this deadline was created."""
        return time.monotonic() - self._start

    @property
    def remaining(self) -> float:
        """Seconds remaining before the deadline expires."""
        return max(0.0, self.seconds - self.elapsed)

    @property
    def expired(self) -> bool:
        """True if the deadline has been exceeded."""
        return self.elapsed >= self.seconds

    def check(self) -> None:
        """Raise AttemptDeadlineExceeded if the deadline has passed."""
        elapsed = self.elapsed
        if elapsed >= self.seconds:
            raise AttemptDeadlineExceeded(self.seconds, elapsed)


def make_attempt_deadline(seconds: Optional[float]) -> Optional[AttemptDeadline]:
    """Factory that returns an AttemptDeadline or None if seconds is None."""
    if seconds is None:
        return None
    return AttemptDeadline(seconds=seconds)

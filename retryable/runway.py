"""RetryRunway — tracks remaining attempt budget as a countdown.

A runway defines how many more attempts are permitted before the retry
loop is considered exhausted.  Unlike a hard cap enforced elsewhere, the
runway is *observable*: hooks and predicates can inspect how much room is
left and adjust behaviour accordingly (e.g. skip expensive fallbacks when
only one attempt remains).
"""

from __future__ import annotations

from dataclasses import dataclass, field


class RunwayExhausted(Exception):
    """Raised when an attempt is made after the runway is exhausted."""

    def __init__(self, max_attempts: int) -> None:
        self.max_attempts = max_attempts
        super().__init__(
            f"Runway exhausted: all {max_attempts} attempt(s) have been used."
        )


@dataclass
class RetryRunway:
    """Countdown tracker for remaining retry attempts.

    Parameters
    ----------
    max_attempts:
        Total number of attempts allowed (>= 1).
    """

    max_attempts: int
    _used: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError(
                f"max_attempts must be >= 1, got {self.max_attempts}"
            )

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    @property
    def used(self) -> int:
        """Number of attempts consumed so far."""
        return self._used

    @property
    def remaining(self) -> int:
        """Number of attempts still available (never negative)."""
        return max(0, self.max_attempts - self._used)

    @property
    def exhausted(self) -> bool:
        """True when no more attempts are available."""
        return self.remaining == 0

    @property
    def fraction_used(self) -> float:
        """Proportion of the runway consumed, in [0.0, 1.0]."""
        return self._used / self.max_attempts

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def consume(self) -> None:
        """Record one attempt.  Raises RunwayExhausted if already empty."""
        if self.exhausted:
            raise RunwayExhausted(self.max_attempts)
        self._used += 1

    def reset(self) -> None:
        """Reset the runway to its initial state."""
        self._used = 0

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"RetryRunway(max_attempts={self.max_attempts}, "
            f"used={self._used}, remaining={self.remaining})"
        )

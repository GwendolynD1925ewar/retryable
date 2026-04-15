"""Cooldown support: enforce a minimum wait period between retry attempts."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


class CooldownActive(Exception):
    """Raised when a retry is attempted before the cooldown period has elapsed."""

    def __init__(self, remaining: float) -> None:
        self.remaining = remaining
        super().__init__(f"Cooldown active: {remaining:.3f}s remaining")


@dataclass
class RetryCooldown:
    """Tracks per-key cooldown windows between retry attempts.

    Args:
        min_wait: Minimum seconds that must elapse before the next retry.
        max_wait: Optional cap on the cooldown duration (e.g. after backoff scaling).
    """

    min_wait: float
    max_wait: Optional[float] = None
    _last_attempt: Optional[float] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.min_wait <= 0:
            raise ValueError("min_wait must be positive")
        if self.max_wait is not None and self.max_wait < self.min_wait:
            raise ValueError("max_wait must be >= min_wait")

    def record(self, *, now: Optional[float] = None) -> None:
        """Record that an attempt just occurred."""
        self._last_attempt = now if now is not None else time.monotonic()

    def remaining(self, *, now: Optional[float] = None) -> float:
        """Return how many seconds remain in the current cooldown (0.0 if clear)."""
        if self._last_attempt is None:
            return 0.0
        current = now if now is not None else time.monotonic()
        elapsed = current - self._last_attempt
        wait = min(self.min_wait, self.max_wait) if self.max_wait is not None else self.min_wait
        remaining = wait - elapsed
        return max(0.0, remaining)

    def is_clear(self, *, now: Optional[float] = None) -> bool:
        """Return True if the cooldown period has elapsed."""
        return self.remaining(now=now) == 0.0

    def acquire(self, *, now: Optional[float] = None) -> None:
        """Raise CooldownActive if the cooldown has not yet elapsed."""
        rem = self.remaining(now=now)
        if rem > 0.0:
            raise CooldownActive(rem)

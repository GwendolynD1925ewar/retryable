"""Pluggable clock abstraction for retry timing."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, List


Clock = Callable[[], float]


def system_clock() -> float:
    """Return the current time in seconds since the epoch."""
    return time.monotonic()


@dataclass
class ManualClock:
    """A controllable clock for use in tests."""

    _now: float = field(default=0.0)
    _advances: List[float] = field(default_factory=list, repr=False)

    def __call__(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        """Move the clock forward by *seconds*."""
        if seconds < 0:
            raise ValueError(f"Cannot advance clock by negative value: {seconds}")
        self._now += seconds
        self._advances.append(seconds)

    def set(self, now: float) -> None:
        """Set the clock to an absolute value."""
        self._now = now

    @property
    def total_advances(self) -> int:
        return len(self._advances)


@dataclass
class OffsetClock:
    """Wraps a base clock and applies a fixed offset."""

    base: Clock
    offset: float

    def __post_init__(self) -> None:
        if not callable(self.base):
            raise TypeError("base must be callable")

    def __call__(self) -> float:
        return self.base() + self.offset


def make_clock(clock: Clock | None = None) -> Clock:
    """Return *clock* if provided, otherwise the system clock."""
    return clock if clock is not None else system_clock

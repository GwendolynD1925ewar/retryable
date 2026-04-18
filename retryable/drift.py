"""Retry drift tracking — measures how much actual retry delays deviate from scheduled delays."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class DriftEntry:
    attempt: int
    scheduled_delay: float
    actual_delay: float

    @property
    def drift(self) -> float:
        """Positive drift means the actual delay was longer than scheduled."""
        return self.actual_delay - self.scheduled_delay

    def __repr__(self) -> str:
        return (
            f"DriftEntry(attempt={self.attempt}, scheduled={self.scheduled_delay:.4f}, "
            f"actual={self.actual_delay:.4f}, drift={self.drift:.4f})"
        )


@dataclass
class RetryDriftTracker:
    """Tracks scheduled vs actual retry delays to surface timing drift."""
    _entries: List[DriftEntry] = field(default_factory=list, init=False)
    _last_scheduled: Optional[float] = field(default=None, init=False)
    _last_fired: Optional[float] = field(default=None, init=False)

    def schedule(self, delay: float) -> None:
        """Record that a delay of `delay` seconds was scheduled; capture the current time."""
        if delay < 0:
            raise ValueError("scheduled delay must be non-negative")
        self._last_scheduled = delay
        self._last_fired = time.monotonic()

    def record(self, attempt: int) -> Optional[DriftEntry]:
        """Call after the sleep completes to record the actual elapsed time."""
        if self._last_scheduled is None or self._last_fired is None:
            return None
        actual = time.monotonic() - self._last_fired
        entry = DriftEntry(
            attempt=attempt,
            scheduled_delay=self._last_scheduled,
            actual_delay=actual,
        )
        self._entries.append(entry)
        self._last_scheduled = None
        self._last_fired = None
        return entry

    @property
    def entries(self) -> List[DriftEntry]:
        return list(self._entries)

    @property
    def total_drift(self) -> float:
        return sum(e.drift for e in self._entries)

    @property
    def average_drift(self) -> float:
        if not self._entries:
            return 0.0
        return self.total_drift / len(self._entries)

    @property
    def max_drift(self) -> Optional[float]:
        if not self._entries:
            return None
        return max(e.drift for e in self._entries)

    def reset(self) -> None:
        self._entries.clear()
        self._last_scheduled = None
        self._last_fired = None

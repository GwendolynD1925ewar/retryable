"""Retry attempt snapshot — captures a point-in-time summary of retry state."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class RetrySnapshot:
    """Immutable record of a single retry attempt's outcome."""

    attempt: int
    """1-based attempt number."""

    timestamp: float
    """Unix timestamp when the snapshot was captured."""

    elapsed: float
    """Seconds elapsed since the first attempt (attempt 1)."""

    exception: Optional[BaseException]
    """Exception raised during this attempt, or *None* if it succeeded."""

    result: Any
    """Return value of this attempt, or *None* if it raised."""

    delay: float
    """Backoff delay (seconds) that will be applied *before* the next attempt."""

    @property
    def succeeded(self) -> bool:
        """Return *True* when the attempt did not raise an exception."""
        return self.exception is None

    @property
    def failed(self) -> bool:
        """Return *True* when the attempt raised an exception."""
        return self.exception is not None

    def __repr__(self) -> str:  # pragma: no cover
        exc_name = type(self.exception).__name__ if self.exception else "None"
        return (
            f"RetrySnapshot(attempt={self.attempt}, succeeded={self.succeeded}, "
            f"exception={exc_name}, delay={self.delay:.3f}s, elapsed={self.elapsed:.3f}s)"
        )


@dataclass
class SnapshotHistory:
    """Accumulates :class:`RetrySnapshot` objects across all attempts of one call."""

    _snapshots: list[RetrySnapshot] = field(default_factory=list, init=False)
    _start: float = field(default_factory=time.monotonic, init=False)

    def record(
        self,
        *,
        attempt: int,
        exception: Optional[BaseException] = None,
        result: Any = None,
        delay: float = 0.0,
    ) -> RetrySnapshot:
        """Create and store a snapshot for *attempt*."""
        now = time.monotonic()
        snapshot = RetrySnapshot(
            attempt=attempt,
            timestamp=time.time(),
            elapsed=now - self._start,
            exception=exception,
            result=result,
            delay=delay,
        )
        self._snapshots.append(snapshot)
        return snapshot

    @property
    def snapshots(self) -> list[RetrySnapshot]:
        """Return a shallow copy of all recorded snapshots."""
        return list(self._snapshots)

    @property
    def total_attempts(self) -> int:
        return len(self._snapshots)

    @property
    def last(self) -> Optional[RetrySnapshot]:
        """Return the most-recently recorded snapshot, or *None*."""
        return self._snapshots[-1] if self._snapshots else None

    def failures(self) -> list[RetrySnapshot]:
        """Return only the snapshots where the attempt failed."""
        return [s for s in self._snapshots if s.failed]

    def reset(self) -> None:
        """Clear all snapshots and restart the elapsed timer."""
        self._snapshots.clear()
        self._start = time.monotonic()

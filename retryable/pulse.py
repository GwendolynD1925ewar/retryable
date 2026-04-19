"""RetryPulse — periodic heartbeat tracker for retry loops.

Tracks whether a retry loop is still making progress by recording
'pulses' (successful partial progress signals). If no pulse is recorded
within a given interval, the loop is considered stalled.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Optional


class PulseStalled(Exception):
    """Raised when no pulse has been recorded within the expected interval."""

    def __init__(self, label: str, interval: float, since: float) -> None:
        self.label = label
        self.interval = interval
        self.since = since
        elapsed = time.monotonic() - since
        super().__init__(
            f"Pulse '{label}' stalled: no heartbeat for {elapsed:.2f}s "
            f"(interval={interval}s)"
        )


@dataclass
class RetryPulse:
    """Heartbeat tracker that detects stalled retry loops.

    Args:
        label: Human-readable name for this pulse tracker.
        interval: Maximum seconds allowed between pulses before stall.
        clock: Callable returning current time (defaults to time.monotonic).
    """

    label: str
    interval: float
    clock: Callable[[], float] = field(default=time.monotonic, repr=False)

    _last_pulse: Optional[float] = field(default=None, init=False, repr=False)
    _pulse_count: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.label or not self.label.strip():
            raise ValueError("label must be a non-empty string")
        if self.interval <= 0:
            raise ValueError("interval must be positive")
        self._last_pulse = self.clock()

    def beat(self) -> None:
        """Record a heartbeat, resetting the stall timer."""
        self._last_pulse = self.clock()
        self._pulse_count += 1

    def stalled(self) -> bool:
        """Return True if no pulse has been recorded within the interval."""
        if self._last_pulse is None:
            return True
        return (self.clock() - self._last_pulse) > self.interval

    def check(self) -> None:
        """Raise PulseStalled if the loop appears stalled."""
        if self.stalled():
            raise PulseStalled(
                label=self.label,
                interval=self.interval,
                since=self._last_pulse or 0.0,
            )

    def elapsed_since_last(self) -> float:
        """Return seconds elapsed since the last recorded pulse."""
        if self._last_pulse is None:
            return float("inf")
        return self.clock() - self._last_pulse

    @property
    def pulse_count(self) -> int:
        """Total number of pulses recorded (not counting initialization)."""
        return self._pulse_count

    def reset(self) -> None:
        """Reset the pulse tracker as if freshly initialized."""
        self._last_pulse = self.clock()
        self._pulse_count = 0

    def __repr__(self) -> str:
        return (
            f"RetryPulse(label={self.label!r}, interval={self.interval}, "
            f"pulse_count={self._pulse_count}, "
            f"elapsed={self.elapsed_since_last():.3f}s)"
        )

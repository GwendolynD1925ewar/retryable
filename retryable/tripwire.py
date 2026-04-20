"""RetryTripwire: trips after a threshold of consecutive failures."""
from __future__ import annotations

from dataclasses import dataclass, field


class TripwireTripped(Exception):
    def __init__(self, label: str, consecutive: int) -> None:
        self.label = label
        self.consecutive = consecutive
        super().__init__(
            f"Tripwire '{label}' tripped after {consecutive} consecutive failures"
        )


@dataclass
class RetryTripwire:
    """Trips after *threshold* consecutive failures; resets on any success."""

    threshold: int
    label: str = "default"
    _consecutive: int = field(default=0, init=False, repr=False)
    _tripped: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.threshold < 1:
            raise ValueError("threshold must be >= 1")
        if not self.label or not self.label.strip():
            raise ValueError("label must be a non-empty string")

    @property
    def tripped(self) -> bool:
        return self._tripped

    @property
    def consecutive(self) -> int:
        return self._consecutive

    def record_failure(self) -> None:
        """Record a failure; raises TripwireTripped if threshold is reached."""
        if self._tripped:
            raise TripwireTripped(self.label, self._consecutive)
        self._consecutive += 1
        if self._consecutive >= self.threshold:
            self._tripped = True
            raise TripwireTripped(self.label, self._consecutive)

    def record_success(self) -> None:
        """Reset consecutive failure count and clear tripped state."""
        self._consecutive = 0
        self._tripped = False

    def reset(self) -> None:
        """Unconditionally reset the tripwire."""
        self._consecutive = 0
        self._tripped = False

    def __repr__(self) -> str:
        return (
            f"RetryTripwire(label={self.label!r}, threshold={self.threshold}, "
            f"consecutive={self._consecutive}, tripped={self._tripped})"
        )

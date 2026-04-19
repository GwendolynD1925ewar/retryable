"""RetryLatch — a one-shot gate that blocks retries once tripped."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


class LatchTripped(Exception):
    """Raised when an operation is attempted on a tripped latch."""

    def __init__(self, reason: str = "") -> None:
        self.reason = reason
        super().__init__(f"Latch tripped: {reason}" if reason else "Latch tripped")


@dataclass
class RetryLatch:
    """A one-shot gate that, once tripped, prevents further retries.

    Args:
        label: Optional human-readable name for this latch.
    """

    label: str = "default"
    _tripped: bool = field(default=False, init=False, repr=False)
    _reason: str = field(default="", init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.label or not self.label.strip():
            raise ValueError("label must be a non-empty string")

    @property
    def tripped(self) -> bool:
        """Return True if this latch has been tripped."""
        return self._tripped

    @property
    def reason(self) -> str:
        """Return the reason the latch was tripped, or empty string."""
        return self._reason

    def trip(self, reason: str = "") -> None:
        """Trip the latch, optionally recording a reason."""
        self._tripped = True
        self._reason = reason

    def reset(self) -> None:
        """Reset the latch to its un-tripped state."""
        self._tripped = False
        self._reason = ""

    def check(self) -> None:
        """Raise LatchTripped if the latch has been tripped."""
        if self._tripped:
            raise LatchTripped(self._reason)

    def __repr__(self) -> str:
        state = f"tripped={self._tripped!r}"
        if self._reason:
            state += f", reason={self._reason!r}"
        return f"RetryLatch(label={self.label!r}, {state})"

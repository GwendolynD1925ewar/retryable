"""RetrySlot — a fixed-capacity slot pool that gates concurrent retry attempts."""
from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Optional


class SlotUnavailable(Exception):
    """Raised when no slot is available in the pool."""

    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        super().__init__(f"All {capacity} retry slot(s) are occupied")


@dataclass
class RetrySlot:
    """A thread-safe fixed-capacity slot pool for bounding concurrent retries."""

    capacity: int
    _lock: Lock = field(default_factory=Lock, init=False, repr=False)
    _occupied: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.capacity <= 0:
            raise ValueError(f"capacity must be >= 1, got {self.capacity}")

    # ------------------------------------------------------------------
    def acquire(self) -> None:
        """Occupy one slot.  Raises SlotUnavailable if the pool is full."""
        with self._lock:
            if self._occupied >= self.capacity:
                raise SlotUnavailable(self.capacity)
            self._occupied += 1

    def release(self) -> None:
        """Return a previously acquired slot to the pool."""
        with self._lock:
            if self._occupied > 0:
                self._occupied -= 1

    @property
    def available(self) -> int:
        """Number of free slots."""
        with self._lock:
            return self.capacity - self._occupied

    @property
    def occupied(self) -> int:
        """Number of occupied slots."""
        with self._lock:
            return self._occupied

    def reset(self) -> None:
        """Release all slots (useful for testing)."""
        with self._lock:
            self._occupied = 0

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"RetrySlot(capacity={self.capacity}, "
            f"occupied={self._occupied}, available={self.available})"
        )

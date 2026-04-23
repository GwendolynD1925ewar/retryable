"""RetryBarrier — pause retries until a shared condition is cleared."""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional


class BarrierBlocked(Exception):
    """Raised when a retry is attempted while the barrier is raised."""

    def __init__(self, label: str) -> None:
        self.label = label
        super().__init__(f"RetryBarrier '{label}' is currently blocking retries")


@dataclass
class RetryBarrier:
    """A thread-safe gate that can block or allow retry attempts.

    When *raised* the barrier prevents further retries by raising
    ``BarrierBlocked``.  Call :meth:`lower` to re-open the gate.
    """

    label: str
    auto_lower_after: Optional[float] = None  # seconds; None means manual only
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    _raised: bool = field(default=False, init=False)
    _raised_at: Optional[float] = field(default=None, init=False)

    def __post_init__(self) -> None:
        if not self.label or not self.label.strip():
            raise ValueError("label must be a non-empty string")
        if self.auto_lower_after is not None and self.auto_lower_after <= 0:
            raise ValueError("auto_lower_after must be a positive number")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def raise_barrier(self) -> None:
        """Raise the barrier, blocking future retry attempts."""
        with self._lock:
            self._raised = True
            self._raised_at = time.monotonic()

    def lower(self) -> None:
        """Lower the barrier, allowing retry attempts to proceed."""
        with self._lock:
            self._raised = False
            self._raised_at = None

    @property
    def is_raised(self) -> bool:
        """Return True if the barrier is currently blocking retries."""
        with self._lock:
            if not self._raised:
                return False
            if self.auto_lower_after is not None and self._raised_at is not None:
                if time.monotonic() - self._raised_at >= self.auto_lower_after:
                    self._raised = False
                    self._raised_at = None
                    return False
            return True

    def check(self) -> None:
        """Raise ``BarrierBlocked`` if the barrier is currently raised."""
        if self.is_raised:
            raise BarrierBlocked(self.label)

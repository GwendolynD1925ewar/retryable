"""RetryDrain — gradually reduces retry allowance as a resource drains.

Models a draining reservoir: each retry consumes a unit; the reservoir
refills at a fixed rate over time.  When the reservoir is empty retries
are blocked until enough capacity has been restored.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable


class DrainExhausted(Exception):
    """Raised when the drain reservoir has no remaining capacity."""

    def __init__(self, available: float, required: float = 1.0) -> None:
        self.available = available
        self.required = required
        super().__init__(
            f"Drain exhausted: {available:.3f} available, {required:.3f} required"
        )


@dataclass
class RetryDrain:
    """Token-bucket style drain that refills at *refill_rate* units per second.

    Args:
        capacity:     Maximum number of tokens the reservoir can hold.
        refill_rate:  Tokens added per second (must be > 0).
        clock:        Callable returning the current time in seconds.
    """

    capacity: float
    refill_rate: float
    clock: Callable[[], float] = field(default=time.monotonic, repr=False)

    def __post_init__(self) -> None:
        if self.capacity <= 0:
            raise ValueError("capacity must be greater than zero")
        if self.refill_rate <= 0:
            raise ValueError("refill_rate must be greater than zero")
        self._tokens: float = float(self.capacity)
        self._last_refill: float = self.clock()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _refill(self) -> None:
        now = self.clock()
        elapsed = now - self._last_refill
        if elapsed > 0:
            self._tokens = min(
                self.capacity, self._tokens + elapsed * self.refill_rate
            )
            self._last_refill = now

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def available(self) -> float:
        """Current token level after applying any pending refill."""
        self._refill()
        return self._tokens

    def acquire(self, tokens: float = 1.0) -> None:
        """Consume *tokens* from the reservoir or raise :exc:`DrainExhausted`."""
        if tokens <= 0:
            raise ValueError("tokens must be greater than zero")
        self._refill()
        if self._tokens < tokens:
            raise DrainExhausted(available=self._tokens, required=tokens)
        self._tokens -= tokens

    def reset(self) -> None:
        """Restore the reservoir to full capacity."""
        self._tokens = float(self.capacity)
        self._last_refill = self.clock()

"""Leaky bucket rate limiter for retry flow control."""
from __future__ import annotations
from dataclasses import dataclass, field
from time import monotonic


class BucketOverflow(Exception):
    """Raised when the leaky bucket is full and cannot accept new tokens."""

    def __init__(self, capacity: int) -> None:
        super().__init__(f"Leaky bucket is full (capacity={capacity})")
        self.capacity = capacity


@dataclass
class LeakyBucket:
    """Token-based leaky bucket that drains at a fixed rate."""

    rate: float  # tokens drained per second
    capacity: int  # max tokens in bucket
    _level: float = field(default=0.0, init=False, repr=False)
    _last_check: float = field(default_factory=monotonic, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.rate <= 0:
            raise ValueError("rate must be positive")
        if self.capacity <= 0:
            raise ValueError("capacity must be positive")

    def _drain(self) -> None:
        now = monotonic()
        elapsed = now - self._last_check
        self._level = max(0.0, self._level - elapsed * self.rate)
        self._last_check = now

    def acquire(self, tokens: int = 1) -> None:
        """Add tokens to the bucket, raising BucketOverflow if full."""
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        self._drain()
        if self._level + tokens > self.capacity:
            raise BucketOverflow(self.capacity)
        self._level += tokens

    @property
    def level(self) -> float:
        self._drain()
        return self._level

    @property
    def available(self) -> float:
        return max(0.0, self.capacity - self.level)

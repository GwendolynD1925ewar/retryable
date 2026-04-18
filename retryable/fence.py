"""RetryFence: limits concurrent retry attempts across threads."""
from __future__ import annotations

import threading
from dataclasses import dataclass, field


class FenceExhausted(Exception):
    def __init__(self, limit: int) -> None:
        super().__init__(f"Retry fence exhausted: max {limit} concurrent retries allowed")
        self.limit = limit


@dataclass
class RetryFence:
    """Limits the number of concurrent in-flight retry attempts."""

    max_concurrent: int
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    _active: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.max_concurrent <= 0:
            raise ValueError("max_concurrent must be a positive integer")

    def acquire(self) -> None:
        """Acquire a slot. Raises FenceExhausted if limit is reached."""
        with self._lock:
            if self._active >= self.max_concurrent:
                raise FenceExhausted(self.max_concurrent)
            self._active += 1

    def release(self) -> None:
        """Release a previously acquired slot."""
        with self._lock:
            if self._active > 0:
                self._active -= 1

    @property
    def active(self) -> int:
        with self._lock:
            return self._active

    @property
    def available(self) -> int:
        with self._lock:
            return max(0, self.max_concurrent - self._active)

    def __repr__(self) -> str:
        return (
            f"RetryFence(max_concurrent={self.max_concurrent}, "
            f"active={self.active}, available={self.available})"
        )

"""Token-bucket rate limiter for controlling retry attempt frequency."""

import time
import threading
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RateLimiter:
    """Token-bucket rate limiter that caps the number of attempts per second."""

    rate: float  # tokens per second
    capacity: float  # maximum burst size
    _tokens: float = field(init=False)
    _last_refill: float = field(init=False)
    _lock: threading.Lock = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.rate <= 0:
            raise ValueError("rate must be positive")
        if self.capacity <= 0:
            raise ValueError("capacity must be positive")
        self._tokens = self.capacity
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
        self._last_refill = now

    def acquire(self, tokens: float = 1.0) -> bool:
        """Try to acquire *tokens* from the bucket. Returns True if successful."""
        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    @property
    def available(self) -> float:
        """Current number of available tokens (approximate)."""
        with self._lock:
            self._refill()
            return self._tokens


def make_rate_limited_hook(
    limiter: RateLimiter,
    on_throttled: Optional[callable] = None,
):
    """Return a retry hook that blocks if the rate limiter cannot be acquired."""

    def hook(attempt: int, exception=None, result=None) -> None:
        while not limiter.acquire():
            if on_throttled is not None:
                on_throttled(attempt)
            time.sleep(1.0 / limiter.rate)

    return hook

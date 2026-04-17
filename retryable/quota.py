"""Retry quota: limit total retry attempts across a time window per key."""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import defaultdict, deque
import time


class QuotaExceeded(Exception):
    def __init__(self, key: str, limit: int, window: float) -> None:
        self.key = key
        self.limit = limit
        self.window = window
        super().__init__(
            f"Retry quota exceeded for key={key!r}: "
            f"limit={limit} per {window}s window"
        )


@dataclass
class RetryQuota:
    limit: int
    window: float
    _timestamps: dict[str, deque] = field(default_factory=lambda: defaultdict(deque), init=False, repr=False)

    def __post_init__(self) -> None:
        if self.limit <= 0:
            raise ValueError("limit must be positive")
        if self.window <= 0:
            raise ValueError("window must be positive")

    def _evict(self, key: str, now: float) -> None:
        dq = self._timestamps[key]
        cutoff = now - self.window
        while dq and dq[0] <= cutoff:
            dq.popleft()

    def acquire(self, key: str = "default", *, now: float | None = None) -> None:
        t = now if now is not None else time.monotonic()
        self._evict(key, t)
        dq = self._timestamps[key]
        if len(dq) >= self.limit:
            raise QuotaExceeded(key, self.limit, self.window)
        dq.append(t)

    def remaining(self, key: str = "default", *, now: float | None = None) -> int:
        t = now if now is not None else time.monotonic()
        self._evict(key, t)
        return max(0, self.limit - len(self._timestamps[key]))

    def reset(self, key: str = "default") -> None:
        self._timestamps[key].clear()

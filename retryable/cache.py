"""Retry result caching — skip retries when a cached success exists."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Hashable, Optional


@dataclass
class CachedEntry:
    value: Any
    expires_at: float  # monotonic timestamp

    def is_expired(self, now: Optional[float] = None) -> bool:
        if now is None:
            now = time.monotonic()
        return now >= self.expires_at


@dataclass
class RetryCache:
    """A simple TTL cache used to short-circuit retry logic on repeated calls."""

    ttl: float  # seconds
    max_size: int = 256
    _store: dict[Hashable, CachedEntry] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.ttl <= 0:
            raise ValueError(f"ttl must be positive, got {self.ttl}")
        if self.max_size < 1:
            raise ValueError(f"max_size must be at least 1, got {self.max_size}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, key: Hashable) -> Optional[Any]:
        """Return cached value or *None* if absent / expired."""
        entry = self._store.get(key)
        if entry is None:
            return None
        if entry.is_expired():
            del self._store[key]
            return None
        return entry.value

    def set(self, key: Hashable, value: Any) -> None:
        """Store *value* under *key* with the configured TTL."""
        self._evict_if_full()
        self._store[key] = CachedEntry(
            value=value,
            expires_at=time.monotonic() + self.ttl,
        )

    def invalidate(self, key: Hashable) -> None:
        """Remove a specific key from the cache."""
        self._store.pop(key, None)

    def clear(self) -> None:
        """Remove all entries."""
        self._store.clear()

    @property
    def size(self) -> int:
        """Number of entries currently held (including potentially expired ones)."""
        return len(self._store)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _evict_if_full(self) -> None:
        if len(self._store) < self.max_size:
            return
        now = time.monotonic()
        expired = [k for k, v in self._store.items() if v.is_expired(now)]
        for k in expired:
            del self._store[k]
        # If still full after evicting expired entries, drop oldest insertion.
        if len(self._store) >= self.max_size:
            oldest = next(iter(self._store))
            del self._store[oldest]


def make_cache_key(fn: Callable, args: tuple, kwargs: dict) -> Hashable:
    """Build a hashable cache key from a callable and its arguments."""
    try:
        return (fn.__qualname__, args, tuple(sorted(kwargs.items())))
    except TypeError:
        # Fallback for unhashable args — use string representation.
        return (fn.__qualname__, str(args), str(sorted(kwargs.items())))

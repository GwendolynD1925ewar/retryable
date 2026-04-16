"""Combine RetryProbe with RetryCache so probe results are cached briefly."""
from __future__ import annotations

import time
from typing import Callable, Optional

from retryable.probe import RetryProbe


class CachedProbe:
    """Wraps a RetryProbe and caches the last result for *ttl* seconds.

    This avoids hammering a health-check endpoint on every retry attempt.

    Args:
        probe: Underlying RetryProbe to delegate to.
        ttl: Seconds to cache a healthy result.
    """

    def __init__(self, probe: RetryProbe, ttl: float = 1.0) -> None:
        if ttl <= 0:
            raise ValueError("ttl must be positive")
        self._probe = probe
        self._ttl = ttl
        self._cached_at: Optional[float] = None
        self._cached_value: Optional[bool] = None

    def available(self) -> bool:
        now = time.monotonic()
        if (
            self._cached_at is not None
            and self._cached_value is True
            and (now - self._cached_at) < self._ttl
        ):
            return True
        result = self._probe.available()
        if result:
            self._cached_at = now
            self._cached_value = True
        else:
            self._cached_at = None
            self._cached_value = False
        return result

    def invalidate(self) -> None:
        """Force the next call to available() to re-probe."""
        self._cached_at = None
        self._cached_value = None


def build_cached_probe_on_retry(probe: RetryProbe, ttl: float = 1.0) -> dict:
    """Return @retry kwargs using a TTL-cached probe."""
    cached = CachedProbe(probe, ttl=ttl)

    from retryable.probe import ProbeUnavailable

    def hook(attempt: int, exception=None, result=None) -> None:
        if not cached.available():
            raise ProbeUnavailable("cached probe reported unavailable")

    return {"on_retry": hook}

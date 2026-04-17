"""Integration helpers for RetryQuota with the retry decorator."""
from __future__ import annotations
from typing import Any
from retryable.quota import RetryQuota, QuotaExceeded


def build_quota_on_retry(
    limit: int,
    window: float,
    key: str = "default",
) -> dict[str, Any]:
    """Return kwargs for retry() that enforce a per-key quota."""
    quota = RetryQuota(limit=limit, window=window)

    def hook(exc: BaseException | None = None, result: Any = None) -> None:
        quota.acquire(key)

    return {"on_retry": hook, "quota": quota}


def quota_predicate(quota: RetryQuota, key: str = "default"):
    """Return a predicate that stops retrying when quota is exhausted."""
    def predicate(exc: BaseException | None = None, result: Any = None) -> bool:
        return quota.remaining(key) > 0
    return predicate

"""Integration helpers for using LeakyBucket with the retry decorator."""
from __future__ import annotations
from typing import Any
from retryable.leaky_bucket import LeakyBucket, BucketOverflow


def build_leaky_bucket_on_retry(
    rate: float,
    capacity: int,
    tokens_per_attempt: int = 1,
) -> dict[str, Any]:
    """Return kwargs suitable for passing to @retry.

    Example::

        @retry(**build_leaky_bucket_on_retry(rate=2.0, capacity=5))
        def fetch(): ...
    """
    bucket = LeakyBucket(rate=rate, capacity=capacity)

    def hook(exc: BaseException | None = None, result: Any = None, **_: Any) -> None:
        try:
            bucket.acquire(tokens_per_attempt)
        except BucketOverflow as e:
            raise e

    return {"on_retry": hook, "bucket": bucket}


def leaky_bucket_predicate(bucket: LeakyBucket, tokens: int = 1):
    """Return a predicate that stops retrying when the bucket would overflow."""

    def predicate(exc: BaseException | None = None, result: Any = None, **_: Any) -> bool:
        return bucket.available >= tokens

    return predicate

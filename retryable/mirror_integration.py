"""Integration helpers for RetryMirror with the retry decorator."""
from __future__ import annotations

from typing import Any, Optional

from retryable.mirror import RetryMirror


def build_mirror_on_retry(
    key: str,
    threshold: float = 0.5,
    min_samples: int = 5,
    mirror: Optional[RetryMirror] = None,
) -> dict:
    """Return kwargs suitable for passing to the ``retry`` decorator.

    Example::

        mirror_kwargs = build_mirror_on_retry("payment-service", threshold=0.6)

        @retry(max_attempts=4, **mirror_kwargs)
        def charge_card(amount: float) -> dict:
            ...
    """
    if mirror is None:
        mirror = RetryMirror(threshold=threshold, min_samples=min_samples)

    def hook(exc: Optional[BaseException], result: Any, attempt: int) -> None:
        if exc is None:
            mirror.record_success(key)
        else:
            mirror.record_failure(key)
        mirror.check(key)

    return {"on_retry": hook, "mirror": mirror}


def mirror_predicate(mirror: RetryMirror, key: str):  # noqa: ANN201
    """Return a predicate that blocks retries once the mirror is imbalanced."""
    from retryable.mirror import MirrorImbalanced

    def predicate(exc: Optional[BaseException], result: Any) -> bool:
        try:
            mirror.check(key)
            return True
        except MirrorImbalanced:
            return False

    return predicate


def format_mirror_stats(mirror: RetryMirror, key: str) -> str:
    """Return a human-readable summary of mirror stats for *key*."""
    stats = mirror.stats(key)
    if stats is None:
        return f"[mirror:{key}] no data"
    return (
        f"[mirror:{key}] successes={stats.successes} failures={stats.failures} "
        f"ratio={stats.imbalance_ratio:.2f}"
    )

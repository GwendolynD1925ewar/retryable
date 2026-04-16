"""Integration helpers for RetrySentinel with the retry decorator."""
from __future__ import annotations
from typing import Any, Callable, Optional

from retryable.sentinel import RetrySentinel, SentinelHistory, is_sentinel, unwrap


def build_sentinel_on_retry(
    history: Optional[SentinelHistory] = None,
) -> dict:
    """Return kwargs for retry() that handle RetrySentinel results.

    Usage::

        from retryable import retry
        from retryable.sentinel_integration import build_sentinel_on_retry

        kwargs = build_sentinel_on_retry()

        @retry(max_attempts=5, **kwargs)
        def fetch() -> str:
            result = call_service()
            if result is None:
                return RetrySentinel(value=None, reason="empty response")
            return result
    """
    _history = history if history is not None else SentinelHistory()

    def on_retry(result: Any, exc: Optional[BaseException], attempt: int) -> None:
        if result is not None and is_sentinel(result):
            _history.record(result)

    def should_retry(result: Any, exc: Optional[BaseException]) -> bool:
        if exc is not None:
            return False
        return is_sentinel(result)

    return {
        "on_retry": on_retry,
        "retry_on": should_retry,
        "sentinel_history": _history,
    }


def make_sentinel_result_hook(
    history: SentinelHistory,
) -> Callable[[Any, Optional[BaseException], int], None]:
    """Return a hook that records sentinel results into the given history."""
    def hook(result: Any, exc: Optional[BaseException], attempt: int) -> None:
        if result is not None and is_sentinel(result):
            history.record(result)
    return hook

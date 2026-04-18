"""Integration helpers for attaching RetryTrace to the retry decorator."""
from __future__ import annotations

from typing import Any, Optional
import time

from retryable.trace import RetryTrace


def build_trace_on_retry(trace: Optional[RetryTrace] = None) -> dict:
    """Return kwargs suitable for passing to @retry that populate a RetryTrace.

    Example::

        trace = RetryTrace()
        @retry(max_attempts=3, **build_trace_on_retry(trace))
        def fetch(): ...
    """
    if trace is None:
        trace = RetryTrace()

    _started: dict = {}

    def on_retry(attempt: int, exception: Optional[BaseException] = None, result: Any = None, **_: Any) -> None:
        started_at = _started.pop(attempt, time.monotonic())
        trace.record(attempt=attempt, started_at=started_at, exception=exception, result=result)

    def before_attempt(attempt: int, **_: Any) -> None:
        _started[attempt] = time.monotonic()

    return {"on_retry": on_retry, "trace": trace}


def trace_predicate(trace: RetryTrace, max_failures: int = 5):
    """Return a predicate that stops retrying once the trace records too many failures."""
    def predicate(attempt: int, exception: Optional[BaseException] = None, result: Any = None) -> bool:
        return len(trace.failures) < max_failures
    return predicate

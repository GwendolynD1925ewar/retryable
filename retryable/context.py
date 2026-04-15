"""Retry context passed to hooks and predicates, capturing per-attempt metadata."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class RetryContext:
    """Immutable snapshot of the current retry state passed to hooks and predicates."""

    attempt: int
    """1-based attempt number (1 = first call, 2 = first retry, …)."""

    elapsed: float
    """Seconds elapsed since the first attempt was made."""

    delay: float
    """Seconds the caller will sleep before the next attempt (0 on final attempt)."""

    exception: Optional[BaseException] = field(default=None)
    """Exception raised by the most recent attempt, or *None* if it returned a value."""

    result: Any = field(default=None)
    """Value returned by the most recent attempt, or *None* if it raised."""

    max_attempts: Optional[int] = field(default=None)
    """Maximum number of attempts configured, or *None* if unlimited."""

    @property
    def is_first_attempt(self) -> bool:
        """Return *True* when this is the very first call (no retries yet)."""
        return self.attempt == 1

    @property
    def is_last_attempt(self) -> bool:
        """Return *True* when no further attempts will be made after this one."""
        if self.max_attempts is None:
            return False
        return self.attempt >= self.max_attempts

    @property
    def retry_number(self) -> int:
        """0-based retry count (0 on first attempt, 1 on first retry, …)."""
        return self.attempt - 1


def build_context(
    *,
    attempt: int,
    start_time: float,
    delay: float = 0.0,
    exception: Optional[BaseException] = None,
    result: Any = None,
    max_attempts: Optional[int] = None,
) -> RetryContext:
    """Construct a :class:`RetryContext` using *start_time* to compute elapsed seconds."""
    return RetryContext(
        attempt=attempt,
        elapsed=time.monotonic() - start_time,
        delay=delay,
        exception=exception,
        result=result,
        max_attempts=max_attempts,
    )

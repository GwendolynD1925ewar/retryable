"""retryable — configurable retry logic with exponential backoff and jitter support."""

from retryable.backoff import (
    equal_jitter,
    exponential_backoff,
    full_jitter,
    no_jitter,
)
from retryable.core import retry
from retryable.predicates import (
    always_retry,
    never_retry,
    on_exception,
    on_result,
)

__all__ = [
    # Core decorator
    "retry",
    # Backoff strategies
    "exponential_backoff",
    "full_jitter",
    "equal_jitter",
    "no_jitter",
    # Retry predicates
    "on_exception",
    "on_result",
    "never_retry",
    "always_retry",
]

__version__ = "0.2.0"

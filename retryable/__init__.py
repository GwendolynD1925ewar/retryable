"""retryable — configurable retry logic with exponential backoff and jitter."""

from retryable.core import retry
from retryable.backoff import (
    exponential_backoff,
    full_jitter,
    equal_jitter,
    no_jitter,
)
from retryable.predicates import (
    on_exception,
    on_result,
    never_retry,
)
from retryable.budget import RetryBudget
from retryable.hooks import (
    on_retry,
    log_retry,
    composite_hook,
)

__all__ = [
    # Core
    "retry",
    # Backoff strategies
    "exponential_backoff",
    "full_jitter",
    "equal_jitter",
    "no_jitter",
    # Predicates
    "on_exception",
    "on_result",
    "never_retry",
    # Budget
    "RetryBudget",
    # Hooks
    "on_retry",
    "log_retry",
    "composite_hook",
]

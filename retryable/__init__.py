"""retryable — A Python decorator library for configurable retry logic
with exponential backoff and jitter support.
"""

from retryable.core import retry
from retryable.backoff import (
    exponential_backoff,
    full_jitter,
    equal_jitter,
    no_jitter,
    JITTER_STRATEGIES,
)

__all__ = [
    "retry",
    "exponential_backoff",
    "full_jitter",
    "equal_jitter",
    "no_jitter",
    "JITTER_STRATEGIES",
]

__version__ = "0.1.0"

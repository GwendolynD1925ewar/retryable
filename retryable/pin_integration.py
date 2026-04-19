"""Integration helpers that wire RetryPin into the retry decorator."""
from __future__ import annotations

from typing import Any, Optional

from retryable.pin import RetryPin


def build_pin_on_retry(pin: RetryPin, record_attempts: bool = True):
    """Return kwargs suitable for passing to @retry that attach *pin* tracking.

    Usage::

        pin = make_pin(service="payments", region="us-east-1")
        @retry(**build_pin_on_retry(pin), max_attempts=4)
        def call_service(): ...
    """

    def hook(exc: Optional[BaseException], result: Any, attempt: int) -> None:
        if record_attempts:
            pin.set("last_attempt", attempt)
        if exc is not None:
            pin.set("last_exception", type(exc).__name__)
        else:
            pin.remove("last_exception")

    return {"on_retry": hook, "pin": pin}


def pin_predicate(pin: RetryPin, block_key: str):
    """Return a predicate that stops retrying when *block_key* is pinned truthy.

    This lets external code signal "stop retrying" by pinning a key.
    """

    def predicate(exc: Optional[BaseException], result: Any) -> bool:
        if pin.has(block_key) and pin.get(block_key):
            return False  # blocked — do not retry
        return exc is not None

    return predicate

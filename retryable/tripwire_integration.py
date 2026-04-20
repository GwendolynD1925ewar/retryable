"""Integration helpers for RetryTripwire with the retry decorator."""
from __future__ import annotations

from typing import Any

from retryable.tripwire import RetryTripwire, TripwireTripped


def build_tripwire_on_retry(
    threshold: int,
    label: str = "default",
) -> dict[str, Any]:
    """Return kwargs suitable for passing to ``retry()``.

    Example::

        @retry(**build_tripwire_on_retry(threshold=3, label="my-service"))
        def call_service():
            ...
    """
    tripwire = RetryTripwire(threshold=threshold, label=label)

    def hook(exc: BaseException | None = None, result: Any = None, **kwargs: Any) -> None:
        if exc is not None:
            try:
                tripwire.record_failure()
            except TripwireTripped:
                raise
        else:
            tripwire.record_success()

    return {"on_retry": hook, "tripwire": tripwire}


def tripwire_predicate(tripwire: RetryTripwire):
    """Return a predicate that stops retrying once the tripwire has tripped."""

    def predicate(exc: BaseException | None = None, result: Any = None, **kwargs: Any) -> bool:
        if tripwire.tripped:
            return False
        return exc is not None

    return predicate

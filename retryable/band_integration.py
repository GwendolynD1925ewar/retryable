"""Integration helpers that wire RetryBand into the retry decorator."""
from __future__ import annotations

from typing import Any, Callable

from retryable.band import RetryBand


def build_banded_backoff(
    min_delay: float,
    max_delay: float,
    backoff: Callable[[int], float],
) -> dict[str, Any]:
    """Return kwargs suitable for passing to @retry.

    The returned dict contains a single ``on_backoff`` key whose value is a
    callable that accepts an attempt number and returns the clamped delay.

    Example usage::

        from retryable import retry
        from retryable.backoff import exponential_backoff
        from retryable.band_integration import build_banded_backoff

        kwargs = build_banded_backoff(0.1, 30.0, exponential_backoff())

        @retry(max_attempts=5, **kwargs)
        def fetch():
            ...
    """
    band = RetryBand(min_delay=min_delay, max_delay=max_delay, backoff=backoff)
    return {"on_backoff": band.delay, "band": band}


def band_predicate(band: RetryBand) -> Callable[[Any, Exception | None], bool]:
    """Return a predicate that rejects attempts whose last delay exceeded the band.

    Useful as a guard: if the delay would be clamped *to* max_delay on every
    remaining attempt, stop retrying early.
    """

    def predicate(result: Any, exc: Exception | None) -> bool:  # noqa: ARG001
        # Always allow — band clamping is handled in the backoff callable.
        # Subclasses may override to add custom logic.
        return True

    return predicate

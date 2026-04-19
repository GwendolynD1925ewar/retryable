"""Convenience factory that combines a backoff strategy with a RetryBand."""
from __future__ import annotations

from typing import Callable

from retryable.band import RetryBand
from retryable.backoff import exponential_backoff, no_jitter


def make_banded_exponential(
    min_delay: float = 0.5,
    max_delay: float = 60.0,
    base_delay: float = 1.0,
    multiplier: float = 2.0,
    jitter: Callable[[float], float] | None = None,
) -> RetryBand:
    """Return a RetryBand backed by exponential backoff.

    Parameters
    ----------
    min_delay:
        Floor for any computed delay (seconds).
    max_delay:
        Ceiling for any computed delay (seconds).
    base_delay:
        Starting delay passed to :func:`exponential_backoff`.
    multiplier:
        Growth factor passed to :func:`exponential_backoff`.
    jitter:
        Optional jitter callable; defaults to :func:`no_jitter`.
    """
    if jitter is None:
        jitter = no_jitter

    raw_backoff = exponential_backoff(
        base_delay=base_delay,
        multiplier=multiplier,
        jitter=jitter,
    )
    return RetryBand(min_delay=min_delay, max_delay=max_delay, backoff=raw_backoff)


def make_banded_linear(
    min_delay: float = 0.5,
    max_delay: float = 30.0,
    step: float = 2.0,
) -> RetryBand:
    """Return a RetryBand backed by a simple linear backoff.

    Delay for attempt *n* (0-indexed) is ``step * (n + 1)``.
    """
    if step <= 0:
        raise ValueError("step must be > 0")

    def linear_backoff(attempt: int) -> float:
        return step * (attempt + 1)

    return RetryBand(min_delay=min_delay, max_delay=max_delay, backoff=linear_backoff)

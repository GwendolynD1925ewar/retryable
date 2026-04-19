"""Integration helpers for RetrySieve with the retry decorator."""
from __future__ import annotations

from typing import Optional

from retryable.sieve import RetrySieve


def build_sieve_on_retry(
    threshold: float,
    scorer,
) -> dict:
    """Return kwargs suitable for passing to @retry that wire up a RetrySieve.

    Example
    -------
    >>> sieve = RetrySieve(threshold=0.5, scorer=lambda attempt, exc: 1.0 if exc is None else 0.0)
    >>> kwargs = build_sieve_on_retry(threshold=0.5, scorer=lambda a, e: 1.0)
    >>> 'on_retry' in kwargs and 'sieve' in kwargs
    True
    """
    sieve = RetrySieve(threshold=threshold, scorer=scorer)

    def hook(attempt: int, exc: Optional[Exception] = None, result=None, **_) -> None:
        sieve.evaluate(attempt, exc)

    return {"on_retry": hook, "sieve": sieve}


def sieve_predicate(sieve: RetrySieve):
    """Return a predicate that blocks retry when the sieve rejects the attempt."""

    def predicate(attempt: int, exc: Optional[Exception] = None, result=None, **_) -> bool:
        return sieve.allowed(attempt, exc)

    return predicate

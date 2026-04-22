"""Integration helpers that wire RetryRunway into the retry decorator.

Typical usage::

    from retryable import retry
    from retryable.runway_integration import build_runway_on_retry, runway_predicate

    runway = RetryRunway(max_attempts=5)
    kwargs = build_runway_on_retry(runway)

    @retry(max_attempts=5, **kwargs)
    def call_service():
        ...
"""

from __future__ import annotations

from typing import Any

from retryable.runway import RetryRunway, RunwayExhausted


def build_runway_on_retry(
    runway: RetryRunway,
) -> dict[str, Any]:
    """Return keyword arguments suitable for ``retry(...)``.

    The returned dict contains:

    * ``on_retry`` — a hook that calls :py:meth:`RetryRunway.consume` on
      every retry attempt.
    * ``runway`` — the :class:`RetryRunway` instance for external
      inspection.

    Parameters
    ----------
    runway:
        A pre-configured :class:`RetryRunway` instance.
    """

    def hook(
        attempt: int,
        exception: BaseException | None = None,
        result: object = None,
    ) -> None:
        runway.consume()

    return {"on_retry": hook, "runway": runway}


def runway_predicate(runway: RetryRunway):  # type: ignore[return]
    """Return a predicate that stops retrying once the runway is exhausted.

    The predicate returns ``True`` (keep retrying) only while
    :py:attr:`RetryRunway.remaining` is greater than zero.

    Parameters
    ----------
    runway:
        A :class:`RetryRunway` instance shared with the retry loop.
    """

    def predicate(
        attempt: int,
        exception: BaseException | None = None,
        result: object = None,
    ) -> bool:
        return not runway.exhausted

    return predicate

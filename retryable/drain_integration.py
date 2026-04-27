"""Integration helpers that wire :class:`RetryDrain` into the retry decorator."""
from __future__ import annotations

from typing import Any, Callable

from retryable.drain import DrainExhausted, RetryDrain


def build_drain_on_retry(
    capacity: float,
    refill_rate: float,
    *,
    cost: float = 1.0,
) -> dict[str, Any]:
    """Return keyword arguments suitable for passing to :func:`retry`.

    Example::

        @retry(**build_drain_on_retry(capacity=5, refill_rate=1.0))
        def call_service():
            ...

    Args:
        capacity:    Maximum reservoir size.
        refill_rate: Tokens restored per second.
        cost:        Token cost consumed on each retry attempt.

    Returns:
        A dict with ``on_retry`` and ``drain`` keys.
    """
    drain = RetryDrain(capacity=capacity, refill_rate=refill_rate)

    def hook(
        attempt: int,
        exception: BaseException | None = None,
        result: object = None,
    ) -> None:
        drain.acquire(cost)

    return {"on_retry": hook, "drain": drain}


def drain_predicate(drain: RetryDrain, *, cost: float = 1.0) -> Callable[..., bool]:
    """Return a predicate that blocks retries when the drain is exhausted.

    The predicate returns ``True`` (allow retry) only when there are enough
    tokens available.  It does *not* consume tokens — consumption happens in
    the ``on_retry`` hook produced by :func:`build_drain_on_retry`.

    Args:
        drain: The :class:`RetryDrain` instance to inspect.
        cost:  Token cost to check against available capacity.
    """

    def predicate(
        attempt: int,
        exception: BaseException | None = None,
        result: object = None,
    ) -> bool:
        return drain.available >= cost

    return predicate

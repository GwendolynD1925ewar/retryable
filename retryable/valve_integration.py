"""Integration helpers that wire :class:`RetryValve` into the retry decorator."""
from __future__ import annotations

from typing import Any

from retryable.valve import RetryValve, ValveThrottled


def build_valve_on_retry(
    max_throughput: int,
    window_seconds: float,
) -> dict[str, Any]:
    """Return ``on_retry`` and ``valve`` kwargs ready for :func:`retryable.retry`.

    Example usage::

        from retryable import retry
        from retryable.valve_integration import build_valve_on_retry

        kwargs = build_valve_on_retry(max_throughput=5, window_seconds=10.0)

        @retry(max_attempts=10, **kwargs)
        def call_service():
            ...
    """
    valve = RetryValve(max_throughput=max_throughput, window_seconds=window_seconds)

    def hook(attempt: int, exception: BaseException | None, result: Any) -> None:  # noqa: ANN401
        valve.acquire()

    return {"on_retry": hook, "valve": valve}


def valve_predicate(valve: RetryValve):
    """Return a *should_retry* predicate that stops retrying when the valve is closed.

    The predicate returns ``False`` (stop retrying) once the valve's
    throughput ceiling has been reached for the current window.
    """

    def predicate(attempt: int, exception: BaseException | None, result: Any) -> bool:  # noqa: ANN401
        return valve.open

    return predicate

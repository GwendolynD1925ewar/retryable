"""Integration helpers that connect RetryThrottle with the retry decorator."""

from __future__ import annotations

from typing import Any, Callable, Optional

from retryable.throttle import RetryThrottle, ThrottleExceeded


def build_throttled_on_retry(
    min_interval: float,
    max_wait: Optional[float] = None,
    *,
    throttle: Optional[RetryThrottle] = None,
) -> dict[str, Any]:
    """Build ``on_retry`` kwargs that enforce a minimum interval between retries.

    Args:
        min_interval: Minimum seconds between successive retries.
        max_wait: If set, block up to this many seconds; otherwise raise.
        throttle: Reuse an existing RetryThrottle instance (optional).

    Returns:
        A dict with an ``on_retry`` key ready to be unpacked into ``retry()``.
    """
    _throttle = throttle or RetryThrottle(min_interval=min_interval, max_wait=max_wait)

    def hook(
        attempt: int,
        exception: Optional[BaseException],
        result: Any,
    ) -> None:
        _throttle.acquire()

    return {"on_retry": hook, "throttle": _throttle}


def throttle_predicate(
    throttle: RetryThrottle,
) -> Callable[[int, Optional[BaseException], Any], bool]:
    """Return a predicate that stops retrying when the throttle would be exceeded.

    Useful when you want to abort retries rather than block.
    """

    def predicate(
        attempt: int,
        exception: Optional[BaseException],
        result: Any,
    ) -> bool:
        if throttle.seconds_until_ready > (throttle.max_wait or float("inf")):
            return False
        return True

    return predicate

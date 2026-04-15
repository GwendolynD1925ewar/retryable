"""Integration helpers connecting RetryCooldown with the retry decorator."""

from __future__ import annotations

from typing import Any, Callable, Optional

from retryable.cooldown import RetryCooldown
from retryable.hooks import on_retry


def build_cooldown_on_retry(
    min_wait: float,
    max_wait: Optional[float] = None,
) -> dict[str, Any]:
    """Return kwargs suitable for ``retry(on_retry=...)`` that enforce a cooldown.

    The cooldown records each attempt and raises :class:`CooldownActive` if the
    next attempt arrives before the minimum wait has elapsed.

    Example::

        from retryable import retry
        from retryable.cooldown_integration import build_cooldown_on_retry

        @retry(attempts=5, **build_cooldown_on_retry(min_wait=2.0))
        def fetch():
            ...
    """
    cooldown = RetryCooldown(min_wait=min_wait, max_wait=max_wait)

    @on_retry
    def hook(
        *,
        attempt: int,
        exception: Optional[BaseException] = None,
        result: Any = None,
    ) -> None:
        cooldown.record()

    return {"on_retry": hook, "_cooldown": cooldown}


def cooldown_predicate(
    cooldown: RetryCooldown,
) -> Callable[..., bool]:
    """Return a predicate that blocks retries while the cooldown is active.

    Intended for use with ``retry(should_retry=...)``.  Returns ``False``
    (do not retry) when the cooldown has not yet elapsed.

    Args:
        cooldown: A :class:`RetryCooldown` instance shared with
            :func:`build_cooldown_on_retry`.
    """

    def predicate(
        *,
        attempt: int,
        exception: Optional[BaseException] = None,
        result: Any = None,
    ) -> bool:
        return cooldown.is_clear()

    return predicate

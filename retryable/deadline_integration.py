"""Integration helpers that wire AttemptDeadline into the retry decorator."""

from __future__ import annotations

from typing import Any, Callable, Optional

from retryable.deadline import AttemptDeadline, AttemptDeadlineExceeded, make_attempt_deadline


def build_deadline_on_retry(
    per_attempt_seconds: float,
) -> Callable[..., None]:
    """Return an ``on_retry`` hook that creates a fresh AttemptDeadline each attempt.

    The deadline object is stored on the hook closure so downstream code can
    call ``check()`` inside the wrapped function if desired.  More commonly,
    pair this with :func:`deadline_predicate` to abort retries when an attempt
    exceeded its budget.

    Args:
        per_attempt_seconds: Maximum seconds allowed per individual attempt.

    Returns:
        A hook compatible with the ``on_retry`` keyword argument of ``retry``.
    """
    state: dict[str, Optional[AttemptDeadline]] = {"current": None}

    def hook(
        attempt: int,
        exception: Optional[BaseException] = None,
        result: Any = None,
    ) -> None:
        state["current"] = make_attempt_deadline(per_attempt_seconds)

    hook.__name__ = "deadline_on_retry_hook"  # type: ignore[attr-defined]
    hook._state = state  # type: ignore[attr-defined]
    return hook


def deadline_predicate(
    per_attempt_seconds: float,
) -> Callable[[Optional[BaseException], Any], bool]:
    """Return a retry predicate that prevents retrying after a deadline breach.

    If the exception is an :class:`~retryable.deadline.AttemptDeadlineExceeded`
    whose recorded deadline matches *per_attempt_seconds*, the predicate returns
    ``False`` (do not retry) so the exception propagates to the caller.

    Args:
        per_attempt_seconds: The deadline value to match against.

    Returns:
        A predicate compatible with the ``should_retry`` keyword of ``retry``.
    """

    def predicate(
        exception: Optional[BaseException] = None,
        result: Any = None,
    ) -> bool:
        if isinstance(exception, AttemptDeadlineExceeded):
            if exception.deadline_seconds == per_attempt_seconds:
                return False
        return exception is not None

    predicate.__name__ = "deadline_predicate"  # type: ignore[attr-defined]
    return predicate

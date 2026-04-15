"""Integration helpers that wire fallback support into the retry decorator."""

from __future__ import annotations

from typing import Any, Callable, Optional

from retryable.fallback import (
    FallbackResult,
    apply_fallback,
    build_fallback_hook,
    callable_fallback,
    static_fallback,
)


def with_static_fallback(
    value: Any,
    **retry_kwargs: Any,
) -> dict:
    """
    Return a dict of keyword arguments suitable for passing to ``retry()``
    that adds a static fallback value when all retries are exhausted.

    Example::

        @retry(**with_static_fallback(default_user, max_attempts=3))
        def fetch_user(user_id): ...
    """
    hook = build_fallback_hook(static_fallback(value))
    return _merge_on_retry(hook, retry_kwargs)


def with_callable_fallback(
    fn: Callable[..., Any],
    *,
    pass_exception: bool = False,
    **retry_kwargs: Any,
) -> dict:
    """
    Return retry kwargs that invoke *fn* as a fallback after all attempts fail.

    If *pass_exception* is True, the last raised exception is forwarded to
    *fn* as the ``exception`` keyword argument.
    """
    hook = build_fallback_hook(callable_fallback(fn, pass_exception=pass_exception))
    return _merge_on_retry(hook, retry_kwargs)


def guarded_call(
    fn: Callable[..., Any],
    args: tuple,
    kwargs: dict,
    *,
    fallback_hook: Callable[..., Any],
    last_exception: Optional[BaseException] = None,
) -> Any:
    """
    Attempt to call *fn*; if it raises, invoke the fallback attached to
    *fallback_hook* and return that value instead.

    This is a low-level helper for use inside custom retry wrappers.

    Raises
    ------
    TypeError
        If *fallback_hook* does not have the expected ``__retryable_fallback__``
        attribute, indicating it was not created via :func:`build_fallback_hook`.
    """
    if not hasattr(fallback_hook, "__retryable_fallback__"):
        raise TypeError(
            "fallback_hook must be created via build_fallback_hook(); "
            f"got {fallback_hook!r} which lacks '__retryable_fallback__'."
        )
    try:
        return fn(*args, **kwargs)
    except Exception as exc:
        return apply_fallback(fallback_hook, args, kwargs, last_exception=exc)


def _merge_on_retry(
    new_hook: Callable[..., Any],
    retry_kwargs: dict,
) -> dict:
    """Merge *new_hook* with any existing ``on_retry`` in *retry_kwargs*."""
    existing = retry_kwargs.pop("on_retry", None)

    if existing is None:
        merged = new_hook
    else:
        def merged(attempt: int, exception: Any = None, result: Any = None) -> None:
            existing(attempt, exception=exception, result=result)
            new_hook(attempt, exception=exception, result=result)

        # Propagate fallback metadata so apply_fallback still works.
        merged.__retryable_fallback__ = new_hook.__retryable_fallback__  # type: ignore[attr-defined]
        merged.__retryable_fallback_on_exception__ = new_hook.__retryable_fallback_on_exception__  # type: ignore[attr-defined]
        merged.__retryable_fallback_on_result__ = new_hook.__retryable_fallback_on_result__  # type: ignore[attr-defined]

    return {"on_retry": merged, **retry_kwargs}

"""Fallback support for retry decorator — execute a fallback callable when all retries are exhausted."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class FallbackResult:
    """Wraps the outcome of a fallback invocation."""

    value: Any
    triggered: bool = True


def static_fallback(value: Any) -> Callable[..., FallbackResult]:
    """Return a fallback that always yields *value* regardless of context."""

    def _fallback(*args: Any, **kwargs: Any) -> FallbackResult:
        return FallbackResult(value=value)

    return _fallback


def raise_fallback(exc: BaseException) -> Callable[..., Any]:
    """Return a fallback that re-raises *exc* when invoked."""

    def _fallback(*args: Any, **kwargs: Any) -> Any:
        raise exc

    return _fallback


def callable_fallback(
    fn: Callable[..., Any],
    *,
    pass_exception: bool = False,
) -> Callable[..., FallbackResult]:
    """
    Wrap *fn* as a fallback.

    If *pass_exception* is True the last exception is forwarded to *fn* as
    the keyword argument ``exception``.
    """

    def _fallback(
        *args: Any,
        _last_exception: Optional[BaseException] = None,
        **kwargs: Any,
    ) -> FallbackResult:
        if pass_exception and _last_exception is not None:
            result = fn(*args, exception=_last_exception, **kwargs)
        else:
            result = fn(*args, **kwargs)
        return FallbackResult(value=result)

    return _fallback


def build_fallback_hook(
    fallback: Callable[..., Any],
    *,
    on_exception: bool = True,
    on_result: bool = False,
) -> Callable[..., None]:
    """
    Return an ``on_retry`` compatible hook that stores the fallback callable
    and the conditions under which it should fire.

    The hook itself is a no-op; the fallback is invoked by
    ``apply_fallback`` after retries are exhausted.
    """

    def hook(
        attempt: int,
        exception: Optional[BaseException] = None,
        result: Any = None,
    ) -> None:  # pragma: no cover
        pass

    hook.__retryable_fallback__ = fallback  # type: ignore[attr-defined]
    hook.__retryable_fallback_on_exception__ = on_exception  # type: ignore[attr-defined]
    hook.__retryable_fallback_on_result__ = on_result  # type: ignore[attr-defined]
    return hook


def apply_fallback(
    hook: Callable[..., Any],
    args: tuple,
    kwargs: dict,
    *,
    last_exception: Optional[BaseException] = None,
) -> Any:
    """Invoke the fallback attached to *hook* and return its raw value."""
    fallback = getattr(hook, "__retryable_fallback__", None)
    if fallback is None:
        raise AttributeError("Hook does not carry a fallback callable.")
    result = fallback(*args, _last_exception=last_exception, **kwargs)
    if isinstance(result, FallbackResult):
        return result.value
    return result

"""Retry predicates for determining whether an exception or result should trigger a retry."""

from typing import Any, Callable, Iterable, Optional, Type, Union


ExceptionTypes = Union[Type[Exception], Iterable[Type[Exception]]]


def on_exception(
    *exception_types: Type[Exception],
) -> Callable[[Exception], bool]:
    """Return a predicate that retries on any of the given exception types.

    Args:
        *exception_types: One or more exception classes to retry on.

    Returns:
        A callable that returns True if the exception matches any of the given types.

    Example:
        >>> predicate = on_exception(ValueError, TypeError)
        >>> predicate(ValueError("bad"))
        True
        >>> predicate(RuntimeError("oops"))
        False
    """
    if not exception_types:
        raise ValueError("At least one exception type must be provided.")

    def predicate(exc: Exception) -> bool:
        return isinstance(exc, tuple(exception_types))

    predicate.__name__ = f"on_exception({', '.join(t.__name__ for t in exception_types)})"
    return predicate


def on_result(
    check: Callable[[Any], bool],
) -> Callable[[Any], bool]:
    """Return a predicate that retries when the result satisfies a condition.

    Args:
        check: A callable that takes the return value and returns True if a retry
               should be attempted.

    Returns:
        A callable wrapping the check.

    Example:
        >>> predicate = on_result(lambda r: r is None)
        >>> predicate(None)
        True
        >>> predicate(42)
        False
    """
    def predicate(result: Any) -> bool:
        return bool(check(result))

    predicate.__name__ = f"on_result({getattr(check, '__name__', repr(check))})"
    return predicate


def never_retry(_: Any) -> bool:
    """Predicate that never triggers a retry."""
    return False


def always_retry(_: Any) -> bool:
    """Predicate that always triggers a retry (useful for testing)."""
    return True

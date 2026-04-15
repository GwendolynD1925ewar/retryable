"""Core retry decorator with backoff, jitter, predicates, budget, hooks,
and optional overall timeout support."""

import time
import functools
from typing import Callable, Optional, Type, Tuple

from retryable.backoff import exponential_backoff, no_jitter
from retryable.predicates import on_exception
from retryable.hooks import on_retry
from retryable.timeout import RetryTimeout


def retry(
    max_attempts: int = 3,
    backoff=None,
    jitter=None,
    predicate=None,
    budget=None,
    hook=None,
    timeout: Optional[float] = None,
    exceptions: Tuple[Type[BaseException], ...] = (Exception,),
):
    """Decorator factory that wraps a callable with configurable retry logic.

    Args:
        max_attempts: Maximum number of total attempts (including the first).
        backoff: Callable ``(attempt) -> float`` returning base delay in
            seconds.  Defaults to :func:`~retryable.backoff.exponential_backoff`.
        jitter: Callable ``(delay) -> float`` that adds randomness to the
            delay.  Defaults to :func:`~retryable.backoff.no_jitter`.
        predicate: Callable ``(exc_or_result) -> bool`` that decides whether
            to retry.  Defaults to :func:`~retryable.predicates.on_exception`.
        budget: Optional :class:`~retryable.budget.RetryBudget` instance.
        hook: Callable invoked before each retry sleep.  Defaults to
            :func:`~retryable.hooks.on_retry`.
        timeout: Optional overall wall-clock deadline in seconds.  When set,
            delays are clamped so the total time never exceeds the budget, and
            a :class:`TimeoutError` is raised if the deadline expires before
            the function succeeds.
        exceptions: Tuple of exception types that trigger a retry when the
            default predicate is used.

    Returns:
        A decorator that applies the retry logic to the wrapped function.
    """
    if backoff is None:
        backoff = exponential_backoff()
    if jitter is None:
        jitter = no_jitter
    if predicate is None:
        predicate = on_exception(*exceptions)
    if hook is None:
        hook = on_retry()

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            timer: Optional[RetryTimeout] = (
                RetryTimeout(timeout) if timeout is not None else None
            )
            last_exc: Optional[BaseException] = None

            for attempt in range(1, max_attempts + 1):
                if timer is not None and timer.expired:
                    raise TimeoutError(
                        f"Retry timeout of {timeout}s exceeded after "
                        f"{attempt - 1} attempt(s)."
                    )

                try:
                    result = func(*args, **kwargs)
                    if not predicate(result):
                        return result
                    last_exc = None
                except Exception as exc:
                    if not predicate(exc):
                        raise
                    last_exc = exc
                    result = exc

                if attempt == max_attempts:
                    break

                if budget is not None and not budget.acquire():
                    break

                delay = jitter(backoff(attempt))
                if timer is not None:
                    delay = timer.clamp_delay(delay)

                hook(attempt, result if last_exc is None else last_exc)
                if delay > 0:
                    time.sleep(delay)

            if last_exc is not None:
                raise last_exc
            raise RuntimeError("Retry predicate never satisfied.")

        return wrapper

    return decorator

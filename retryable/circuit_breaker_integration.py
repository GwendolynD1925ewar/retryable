"""Integration helpers for using CircuitBreaker with the retry decorator."""

from typing import Callable, Optional, Type

from retryable.circuit_breaker import CircuitBreaker, CircuitBreakerError
from retryable.hooks import on_retry


def circuit_breaker_hook(
    breaker: CircuitBreaker,
    record_on: Optional[tuple] = None,
) -> Callable:
    """Return an on_retry hook that records outcomes on the circuit breaker.

    Args:
        breaker: The CircuitBreaker instance to update.
        record_on: Exception types that count as failures. Defaults to
                   (Exception,) — any exception is a failure.

    Returns:
        An on_retry-compatible hook function.
    """
    failure_types = record_on if record_on is not None else (Exception,)

    def hook(attempt: int, delay: float, exc=None, result=None) -> None:
        if exc is not None and isinstance(exc, failure_types):
            breaker.record_failure()
        else:
            breaker.record_success()

    return on_retry(hook)


def guard_with_circuit_breaker(
    breaker: CircuitBreaker,
    func: Callable,
    *args,
    **kwargs,
):
    """Call *func* only if the circuit breaker allows it.

    Raises:
        CircuitBreakerError: If the circuit is open.
    """
    if not breaker.allow_request():
        raise CircuitBreakerError(breaker.name, breaker.reset_in())
    try:
        result = func(*args, **kwargs)
        breaker.record_success()
        return result
    except Exception as exc:
        breaker.record_failure()
        raise


def make_circuit_breaker_predicate(
    breaker: CircuitBreaker,
    exception_types: tuple = (Exception,),
) -> Callable:
    """Return a retry predicate that also updates the circuit breaker.

    The predicate always returns True for matching exceptions (letting
    the main retry logic decide whether to continue), but side-effects
    the circuit breaker on every evaluation.
    """

    def predicate(exc=None, result=None) -> bool:
        if exc is not None and isinstance(exc, exception_types):
            breaker.record_failure()
            return True
        if exc is None:
            breaker.record_success()
        return False

    return predicate

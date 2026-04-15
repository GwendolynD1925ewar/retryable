"""Tests for retryable.circuit_breaker_integration."""

import pytest
from unittest.mock import MagicMock, call

from retryable.circuit_breaker import CircuitBreaker, CircuitBreakerError, CircuitState
from retryable.circuit_breaker_integration import (
    circuit_breaker_hook,
    guard_with_circuit_breaker,
    make_circuit_breaker_predicate,
)


class TestCircuitBreakerHook:
    def test_records_failure_on_exception(self):
        breaker = MagicMock(spec=CircuitBreaker)
        hook = circuit_breaker_hook(breaker)
        hook(attempt=1, delay=0.5, exc=ValueError("oops"))
        breaker.record_failure.assert_called_once()
        breaker.record_success.assert_not_called()

    def test_records_success_on_no_exception(self):
        breaker = MagicMock(spec=CircuitBreaker)
        hook = circuit_breaker_hook(breaker)
        hook(attempt=1, delay=0.0, exc=None, result="ok")
        breaker.record_success.assert_called_once()
        breaker.record_failure.assert_not_called()

    def test_ignores_exception_not_in_record_on(self):
        breaker = MagicMock(spec=CircuitBreaker)
        hook = circuit_breaker_hook(breaker, record_on=(TimeoutError,))
        hook(attempt=1, delay=0.0, exc=ValueError("not timeout"))
        breaker.record_failure.assert_not_called()

    def test_records_failure_for_matching_record_on_type(self):
        breaker = MagicMock(spec=CircuitBreaker)
        hook = circuit_breaker_hook(breaker, record_on=(TimeoutError,))
        hook(attempt=1, delay=0.0, exc=TimeoutError("timed out"))
        breaker.record_failure.assert_called_once()


class TestGuardWithCircuitBreaker:
    def test_calls_function_when_circuit_closed(self):
        breaker = CircuitBreaker()
        fn = MagicMock(return_value=42)
        result = guard_with_circuit_breaker(breaker, fn, "arg", kw="val")
        assert result == 42
        fn.assert_called_once_with("arg", kw="val")

    def test_raises_circuit_breaker_error_when_open(self):
        breaker = CircuitBreaker(failure_threshold=1)
        breaker.record_failure()
        fn = MagicMock()
        with pytest.raises(CircuitBreakerError) as exc_info:
            guard_with_circuit_breaker(breaker, fn)
        fn.assert_not_called()
        assert exc_info.value.name == breaker.name

    def test_records_success_after_successful_call(self):
        breaker = MagicMock(spec=CircuitBreaker)
        breaker.allow_request.return_value = True
        fn = MagicMock(return_value="done")
        guard_with_circuit_breaker(breaker, fn)
        breaker.record_success.assert_called_once()

    def test_records_failure_and_reraises_on_exception(self):
        breaker = MagicMock(spec=CircuitBreaker)
        breaker.allow_request.return_value = True
        fn = MagicMock(side_effect=RuntimeError("boom"))
        with pytest.raises(RuntimeError, match="boom"):
            guard_with_circuit_breaker(breaker, fn)
        breaker.record_failure.assert_called_once()
        breaker.record_success.assert_not_called()


class TestMakeCircuitBreakerPredicate:
    def test_returns_true_and_records_failure_on_matching_exc(self):
        breaker = MagicMock(spec=CircuitBreaker)
        pred = make_circuit_breaker_predicate(breaker, exception_types=(ValueError,))
        assert pred(exc=ValueError("bad")) is True
        breaker.record_failure.assert_called_once()

    def test_returns_false_for_non_matching_exception(self):
        breaker = MagicMock(spec=CircuitBreaker)
        pred = make_circuit_breaker_predicate(breaker, exception_types=(TimeoutError,))
        assert pred(exc=ValueError("bad")) is False
        breaker.record_failure.assert_not_called()

    def test_returns_false_and_records_success_on_no_exception(self):
        breaker = MagicMock(spec=CircuitBreaker)
        pred = make_circuit_breaker_predicate(breaker)
        assert pred(exc=None, result="ok") is False
        breaker.record_success.assert_called_once()

    def test_default_exception_types_matches_any_exception(self):
        breaker = MagicMock(spec=CircuitBreaker)
        pred = make_circuit_breaker_predicate(breaker)
        assert pred(exc=KeyError("k")) is True
        breaker.record_failure.assert_called_once()

"""Tests for retryable.circuit_breaker."""

import time
import pytest
from unittest.mock import patch

from retryable.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerError,
    CircuitState,
)


class TestCircuitBreakerInit:
    def test_valid_construction(self):
        cb = CircuitBreaker(name="svc", failure_threshold=3, recovery_timeout=10.0)
        assert cb.name == "svc"
        assert cb.failure_threshold == 3
        assert cb.recovery_timeout == 10.0
        assert cb.state == CircuitState.CLOSED

    def test_negative_failure_threshold_raises(self):
        with pytest.raises(ValueError, match="failure_threshold"):
            CircuitBreaker(failure_threshold=0)

    def test_zero_recovery_timeout_raises(self):
        with pytest.raises(ValueError, match="recovery_timeout"):
            CircuitBreaker(recovery_timeout=0)

    def test_negative_recovery_timeout_raises(self):
        with pytest.raises(ValueError, match="recovery_timeout"):
            CircuitBreaker(recovery_timeout=-5.0)

    def test_zero_half_open_max_calls_raises(self):
        with pytest.raises(ValueError, match="half_open_max_calls"):
            CircuitBreaker(half_open_max_calls=0)


class TestCircuitBreakerClosed:
    def test_allows_requests_when_closed(self):
        cb = CircuitBreaker(failure_threshold=3)
        assert cb.allow_request() is True

    def test_stays_closed_below_threshold(self):
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        assert cb.allow_request() is True

    def test_opens_at_threshold(self):
        cb = CircuitBreaker(failure_threshold=3)
        for _ in range(3):
            cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_success_resets_failure_count(self):
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED


class TestCircuitBreakerOpen:
    def test_blocks_requests_when_open(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=60.0)
        cb.record_failure()
        assert cb.allow_request() is False

    def test_transitions_to_half_open_after_timeout(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=1.0)
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        time.sleep(1.05)
        assert cb.state == CircuitState.HALF_OPEN

    def test_reset_in_returns_positive_when_open(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=30.0)
        cb.record_failure()
        remaining = cb.reset_in()
        assert 0 < remaining <= 30.0

    def test_reset_in_returns_zero_when_closed(self):
        cb = CircuitBreaker()
        assert cb.reset_in() == 0.0


class TestCircuitBreakerHalfOpen:
    def test_allows_limited_calls_in_half_open(self):
        cb = CircuitBreaker(
            failure_threshold=1, recovery_timeout=0.01, half_open_max_calls=1
        )
        cb.record_failure()
        time.sleep(0.02)
        assert cb.allow_request() is True
        assert cb.allow_request() is False

    def test_success_in_half_open_closes_circuit(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.01)
        cb.record_failure()
        time.sleep(0.02)
        cb.allow_request()
        cb.record_success()
        assert cb.state == CircuitState.CLOSED

    def test_failure_in_half_open_reopens_circuit(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.01)
        cb.record_failure()
        time.sleep(0.02)
        cb.allow_request()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN


class TestCircuitBreakerReset:
    def test_manual_reset_closes_circuit(self):
        cb = CircuitBreaker(failure_threshold=1)
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb.allow_request() is True


class TestCircuitBreakerError:
    def test_error_message_contains_name(self):
        err = CircuitBreakerError("my-service", 15.3)
        assert "my-service" in str(err)
        assert err.name == "my-service"
        assert err.reset_in == 15.3

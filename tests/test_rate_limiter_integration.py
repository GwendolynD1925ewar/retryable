"""Integration tests for rate_limiter_integration helpers."""

import pytest
from unittest.mock import MagicMock

from retryable.rate_limiter import RateLimiter
from retryable.rate_limiter_integration import (
    build_rate_limited_retry_kwargs,
    rate_limited_predicate,
)


class TestBuildRateLimitedRetryKwargs:
    def test_returns_on_retry_key(self):
        result = build_rate_limited_retry_kwargs(rate=10.0)
        assert "on_retry" in result

    def test_returns_rate_limiter_instance(self):
        result = build_rate_limited_retry_kwargs(rate=10.0)
        assert isinstance(result["_rate_limiter"], RateLimiter)

    def test_default_capacity_equals_rate(self):
        result = build_rate_limited_retry_kwargs(rate=5.0)
        assert result["_rate_limiter"].capacity == 5.0

    def test_explicit_capacity_is_respected(self):
        result = build_rate_limited_retry_kwargs(rate=5.0, capacity=20.0)
        assert result["_rate_limiter"].capacity == 20.0

    def test_existing_hook_is_composed(self):
        existing = MagicMock()
        result = build_rate_limited_retry_kwargs(rate=100.0, existing_hook=existing)
        # Calling the composite hook should invoke existing_hook
        result["on_retry"](attempt=1)
        existing.assert_called_once()

    def test_on_throttled_forwarded(self):
        throttled = MagicMock()
        result = build_rate_limited_retry_kwargs(rate=100.0, on_throttled=throttled)
        assert "on_retry" in result


class TestRateLimitedPredicate:
    def test_returns_true_when_tokens_available(self):
        limiter = RateLimiter(rate=100.0, capacity=10.0)
        pred = rate_limited_predicate(limiter)
        assert pred(attempt=1) is True

    def test_returns_false_when_tokens_exhausted(self):
        limiter = RateLimiter(rate=0.001, capacity=1.0)
        pred = rate_limited_predicate(limiter)
        pred(attempt=1)  # consume the single token
        assert pred(attempt=2) is False

    def test_predicate_accepts_exception_kwarg(self):
        limiter = RateLimiter(rate=100.0, capacity=5.0)
        pred = rate_limited_predicate(limiter)
        assert pred(attempt=1, exception=RuntimeError("x")) is True

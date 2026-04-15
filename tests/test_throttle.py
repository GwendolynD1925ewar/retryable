"""Tests for retryable.throttle and retryable.throttle_integration."""

from __future__ import annotations

import pytest

from retryable.throttle import RetryThrottle, ThrottleExceeded
from retryable.throttle_integration import build_throttled_on_retry, throttle_predicate


class TestRetryThrottleInit:
    def test_valid_construction(self):
        t = RetryThrottle(min_interval=0.5)
        assert t.min_interval == 0.5
        assert t.max_wait is None

    def test_zero_min_interval_raises(self):
        with pytest.raises(ValueError, match="min_interval must be positive"):
            RetryThrottle(min_interval=0)

    def test_negative_min_interval_raises(self):
        with pytest.raises(ValueError, match="min_interval must be positive"):
            RetryThrottle(min_interval=-1.0)

    def test_negative_max_wait_raises(self):
        with pytest.raises(ValueError, match="max_wait must be non-negative"):
            RetryThrottle(min_interval=1.0, max_wait=-0.1)

    def test_zero_max_wait_is_allowed(self):
        t = RetryThrottle(min_interval=1.0, max_wait=0.0)
        assert t.max_wait == 0.0


class TestRetryThrottleAcquire:
    def test_first_acquire_always_succeeds(self):
        t = RetryThrottle(min_interval=5.0)
        # _last_retry_at starts at 0, so elapsed is large — no wait needed
        waited = t.acquire(_now=1_000_000.0)
        assert waited == 0.0

    def test_acquire_raises_when_wait_exceeds_max_wait(self):
        t = RetryThrottle(min_interval=10.0, max_wait=1.0)
        # Simulate a very recent last retry
        t._last_retry_at = 1_000_000.0
        with pytest.raises(ThrottleExceeded) as exc_info:
            t.acquire(_now=1_000_000.5)  # only 0.5s elapsed, need 10s
        assert exc_info.value.retry_after > 0

    def test_throttle_exceeded_message(self):
        err = ThrottleExceeded(retry_after=3.5)
        assert "3.500" in str(err)

    def test_seconds_until_ready_is_zero_after_enough_time(self):
        t = RetryThrottle(min_interval=0.001)
        t.acquire()  # mark last retry
        import time
        time.sleep(0.005)
        assert t.seconds_until_ready == 0.0


class TestBuildThrottledOnRetry:
    def test_returns_on_retry_key(self):
        result = build_throttled_on_retry(min_interval=0.001)
        assert "on_retry" in result

    def test_returns_throttle_instance(self):
        result = build_throttled_on_retry(min_interval=0.001)
        assert isinstance(result["throttle"], RetryThrottle)

    def test_reuses_provided_throttle(self):
        existing = RetryThrottle(min_interval=0.5)
        result = build_throttled_on_retry(min_interval=0.5, throttle=existing)
        assert result["throttle"] is existing

    def test_hook_is_callable(self):
        result = build_throttled_on_retry(min_interval=0.001)
        hook = result["on_retry"]
        assert callable(hook)
        hook(1, None, None)  # should not raise


class TestThrottlePredicate:
    def test_returns_true_when_ready(self):
        t = RetryThrottle(min_interval=0.001, max_wait=5.0)
        pred = throttle_predicate(t)
        assert pred(1, None, None) is True

    def test_returns_false_when_wait_exceeds_max_wait(self):
        t = RetryThrottle(min_interval=100.0, max_wait=0.0)
        t._last_retry_at = 1e9  # very recent
        pred = throttle_predicate(t)
        # seconds_until_ready ≈ 100s > max_wait=0 → should return False
        # We patch monotonic indirectly via the property
        import time
        t._last_retry_at = time.monotonic()  # just now
        assert pred(1, None, None) is False

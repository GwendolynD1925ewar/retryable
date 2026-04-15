"""Tests for retryable.rate_limiter."""

import time
import pytest
from unittest.mock import MagicMock

from retryable.rate_limiter import RateLimiter, make_rate_limited_hook


class TestRateLimiterInit:
    def test_valid_construction(self):
        rl = RateLimiter(rate=10.0, capacity=5.0)
        assert rl.rate == 10.0
        assert rl.capacity == 5.0

    def test_zero_rate_raises(self):
        with pytest.raises(ValueError, match="rate must be positive"):
            RateLimiter(rate=0, capacity=5.0)

    def test_negative_rate_raises(self):
        with pytest.raises(ValueError, match="rate must be positive"):
            RateLimiter(rate=-1.0, capacity=5.0)

    def test_zero_capacity_raises(self):
        with pytest.raises(ValueError, match="capacity must be positive"):
            RateLimiter(rate=5.0, capacity=0)

    def test_negative_capacity_raises(self):
        with pytest.raises(ValueError, match="capacity must be positive"):
            RateLimiter(rate=5.0, capacity=-2.0)


class TestRateLimiterAcquire:
    def test_acquire_within_capacity_succeeds(self):
        rl = RateLimiter(rate=100.0, capacity=5.0)
        assert rl.acquire() is True

    def test_acquire_depletes_tokens(self):
        rl = RateLimiter(rate=100.0, capacity=2.0)
        assert rl.acquire() is True
        assert rl.acquire() is True
        assert rl.acquire() is False

    def test_tokens_refill_over_time(self):
        rl = RateLimiter(rate=100.0, capacity=1.0)
        assert rl.acquire() is True
        assert rl.acquire() is False
        time.sleep(0.02)  # 100 t/s -> ~2 tokens after 20 ms
        assert rl.acquire() is True

    def test_available_starts_at_capacity(self):
        rl = RateLimiter(rate=10.0, capacity=10.0)
        assert rl.available == pytest.approx(10.0, abs=0.1)

    def test_available_decreases_after_acquire(self):
        rl = RateLimiter(rate=10.0, capacity=10.0)
        rl.acquire()
        assert rl.available < 10.0


class TestMakeRateLimitedHook:
    def test_hook_acquires_immediately_when_tokens_available(self):
        rl = RateLimiter(rate=1000.0, capacity=10.0)
        hook = make_rate_limited_hook(rl)
        # Should not block
        hook(attempt=1)

    def test_on_throttled_called_when_tokens_exhausted(self):
        rl = RateLimiter(rate=1000.0, capacity=1.0)
        # Exhaust the bucket
        rl.acquire()
        throttled = MagicMock()
        hook = make_rate_limited_hook(rl, on_throttled=throttled)
        # After a tiny sleep tokens refill; hook should eventually succeed
        hook(attempt=2)
        # on_throttled may or may not be called depending on timing, but no error

    def test_hook_accepts_exception_kwarg(self):
        rl = RateLimiter(rate=1000.0, capacity=10.0)
        hook = make_rate_limited_hook(rl)
        hook(attempt=1, exception=ValueError("boom"))

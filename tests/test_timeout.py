"""Tests for retryable.timeout."""

import time

import pytest

from retryable.timeout import RetryTimeout, no_timeout


class TestRetryTimeoutInit:
    def test_valid_construction(self):
        t = RetryTimeout(5.0)
        assert t.total_seconds == 5.0

    def test_zero_raises(self):
        with pytest.raises(ValueError, match="positive"):
            RetryTimeout(0)

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="positive"):
            RetryTimeout(-1)


class TestRetryTimeoutRemaining:
    def test_remaining_is_positive_immediately(self):
        t = RetryTimeout(10.0)
        assert t.remaining > 0

    def test_remaining_does_not_exceed_total(self):
        t = RetryTimeout(10.0)
        assert t.remaining <= 10.0

    def test_remaining_decreases_over_time(self):
        t = RetryTimeout(5.0)
        r1 = t.remaining
        time.sleep(0.05)
        r2 = t.remaining
        assert r2 < r1

    def test_remaining_never_negative(self):
        t = RetryTimeout(0.01)
        time.sleep(0.05)
        assert t.remaining == 0.0


class TestRetryTimeoutExpired:
    def test_not_expired_immediately(self):
        t = RetryTimeout(10.0)
        assert not t.expired

    def test_expired_after_deadline(self):
        t = RetryTimeout(0.01)
        time.sleep(0.05)
        assert t.expired


class TestClampDelay:
    def test_clamp_returns_delay_when_plenty_of_time(self):
        t = RetryTimeout(100.0)
        assert t.clamp_delay(1.0) == pytest.approx(1.0)

    def test_clamp_returns_remaining_when_delay_too_large(self):
        t = RetryTimeout(0.5)
        clamped = t.clamp_delay(10.0)
        assert clamped <= 0.5

    def test_clamp_returns_zero_when_expired(self):
        t = RetryTimeout(0.01)
        time.sleep(0.05)
        assert t.clamp_delay(5.0) == 0.0


class TestNoTimeout:
    def test_returns_none(self):
        assert no_timeout() is None

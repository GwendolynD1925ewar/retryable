"""Tests for retryable.window.RetryWindow."""
import pytest
from retryable.window import RetryWindow


class TestRetryWindowInit:
    def test_valid_construction(self):
        w = RetryWindow(window_seconds=10.0, max_attempts=5)
        assert w.window_seconds == 10.0
        assert w.max_attempts == 5

    def test_zero_window_raises(self):
        with pytest.raises(ValueError, match="window_seconds"):
            RetryWindow(window_seconds=0, max_attempts=3)

    def test_negative_window_raises(self):
        with pytest.raises(ValueError, match="window_seconds"):
            RetryWindow(window_seconds=-1.0, max_attempts=3)

    def test_zero_max_attempts_raises(self):
        with pytest.raises(ValueError, match="max_attempts"):
            RetryWindow(window_seconds=5.0, max_attempts=0)

    def test_negative_max_attempts_raises(self):
        with pytest.raises(ValueError, match="max_attempts"):
            RetryWindow(window_seconds=5.0, max_attempts=-1)


class TestRetryWindowAllowed:
    def test_allowed_when_empty(self):
        w = RetryWindow(window_seconds=10.0, max_attempts=3)
        assert w.allowed(now=100.0) is True

    def test_not_allowed_when_full(self):
        w = RetryWindow(window_seconds=10.0, max_attempts=2)
        w.record(now=100.0)
        w.record(now=101.0)
        assert w.allowed(now=102.0) is False

    def test_allowed_after_window_expires(self):
        w = RetryWindow(window_seconds=5.0, max_attempts=2)
        w.record(now=100.0)
        w.record(now=101.0)
        # advance past window
        assert w.allowed(now=106.1) is True

    def test_partial_expiry_opens_slot(self):
        w = RetryWindow(window_seconds=5.0, max_attempts=2)
        w.record(now=100.0)
        w.record(now=103.0)
        # first record expires, one slot free
        assert w.allowed(now=105.1) is True


class TestRetryWindowAttemptCount:
    def test_count_zero_initially(self):
        w = RetryWindow(window_seconds=10.0, max_attempts=5)
        assert w.attempt_count(now=0.0) == 0

    def test_count_increases_with_records(self):
        w = RetryWindow(window_seconds=10.0, max_attempts=5)
        w.record(now=1.0)
        w.record(now=2.0)
        assert w.attempt_count(now=3.0) == 2

    def test_count_decreases_after_expiry(self):
        w = RetryWindow(window_seconds=5.0, max_attempts=5)
        w.record(now=1.0)
        w.record(now=7.0)
        assert w.attempt_count(now=7.0) == 1


class TestRetryWindowReset:
    def test_reset_clears_all(self):
        w = RetryWindow(window_seconds=10.0, max_attempts=3)
        w.record(now=1.0)
        w.record(now=2.0)
        w.reset()
        assert w.attempt_count(now=3.0) == 0

    def test_allowed_after_reset(self):
        w = RetryWindow(window_seconds=10.0, max_attempts=2)
        w.record(now=1.0)
        w.record(now=2.0)
        w.reset()
        assert w.allowed(now=3.0) is True

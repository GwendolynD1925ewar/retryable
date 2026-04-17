"""Tests for retryable.quota."""
import pytest
import time
from retryable.quota import RetryQuota, QuotaExceeded


class TestRetryQuotaInit:
    def test_valid_construction(self):
        q = RetryQuota(limit=5, window=10.0)
        assert q.limit == 5
        assert q.window == 10.0

    def test_zero_limit_raises(self):
        with pytest.raises(ValueError, match="limit"):
            RetryQuota(limit=0, window=1.0)

    def test_negative_limit_raises(self):
        with pytest.raises(ValueError, match="limit"):
            RetryQuota(limit=-1, window=1.0)

    def test_zero_window_raises(self):
        with pytest.raises(ValueError, match="window"):
            RetryQuota(limit=5, window=0.0)

    def test_negative_window_raises(self):
        with pytest.raises(ValueError, match="window"):
            RetryQuota(limit=5, window=-1.0)


class TestRetryQuotaAcquire:
    def test_acquire_within_limit(self):
        q = RetryQuota(limit=3, window=60.0)
        now = 100.0
        q.acquire("k", now=now)
        q.acquire("k", now=now)
        q.acquire("k", now=now)

    def test_acquire_exceeds_limit_raises(self):
        q = RetryQuota(limit=2, window=60.0)
        now = 100.0
        q.acquire("k", now=now)
        q.acquire("k", now=now)
        with pytest.raises(QuotaExceeded) as exc_info:
            q.acquire("k", now=now)
        assert exc_info.value.key == "k"
        assert exc_info.value.limit == 2

    def test_old_entries_evicted_after_window(self):
        q = RetryQuota(limit=2, window=10.0)
        q.acquire("k", now=0.0)
        q.acquire("k", now=1.0)
        # After window passes, old entries gone
        q.acquire("k", now=11.0)
        q.acquire("k", now=12.0)

    def test_default_key(self):
        q = RetryQuota(limit=1, window=60.0)
        q.acquire(now=0.0)
        with pytest.raises(QuotaExceeded):
            q.acquire(now=1.0)

    def test_separate_keys_are_independent(self):
        q = RetryQuota(limit=1, window=60.0)
        q.acquire("a", now=0.0)
        q.acquire("b", now=0.0)  # should not raise


class TestRetryQuotaRemaining:
    def test_full_remaining_initially(self):
        q = RetryQuota(limit=5, window=60.0)
        assert q.remaining("k", now=0.0) == 5

    def test_remaining_decrements(self):
        q = RetryQuota(limit=3, window=60.0)
        q.acquire("k", now=0.0)
        assert q.remaining("k", now=1.0) == 2

    def test_remaining_recovers_after_window(self):
        q = RetryQuota(limit=2, window=10.0)
        q.acquire("k", now=0.0)
        q.acquire("k", now=1.0)
        assert q.remaining("k", now=0.0) == 0
        assert q.remaining("k", now=11.0) == 2

    def test_reset_clears_key(self):
        q = RetryQuota(limit=2, window=60.0)
        q.acquire("k", now=0.0)
        q.reset("k")
        assert q.remaining("k", now=1.0) == 2

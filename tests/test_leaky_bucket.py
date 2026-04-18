"""Tests for retryable.leaky_bucket and leaky_bucket_integration."""
from __future__ import annotations
import pytest
from unittest.mock import patch
from retryable.leaky_bucket import LeakyBucket, BucketOverflow
from retryable.leaky_bucket_integration import build_leaky_bucket_on_retry, leaky_bucket_predicate


class TestLeakyBucketInit:
    def test_valid_construction(self):
        b = LeakyBucket(rate=1.0, capacity=5)
        assert b.rate == 1.0
        assert b.capacity == 5

    def test_zero_rate_raises(self):
        with pytest.raises(ValueError, match="rate"):
            LeakyBucket(rate=0, capacity=5)

    def test_negative_rate_raises(self):
        with pytest.raises(ValueError, match="rate"):
            LeakyBucket(rate=-1.0, capacity=5)

    def test_zero_capacity_raises(self):
        with pytest.raises(ValueError, match="capacity"):
            LeakyBucket(rate=1.0, capacity=0)


class TestLeakyBucketAcquire:
    def test_acquire_within_capacity(self):
        b = LeakyBucket(rate=1.0, capacity=5)
        b.acquire(3)
        assert b.level == pytest.approx(3.0, abs=0.1)

    def test_overflow_raises(self):
        b = LeakyBucket(rate=1.0, capacity=3)
        with pytest.raises(BucketOverflow) as exc_info:
            b.acquire(5)
        assert exc_info.value.capacity == 3

    def test_zero_tokens_raises(self):
        b = LeakyBucket(rate=1.0, capacity=5)
        with pytest.raises(ValueError):
            b.acquire(0)

    def test_drains_over_time(self):
        b = LeakyBucket(rate=2.0, capacity=10)
        b.acquire(4)
        with patch("retryable.leaky_bucket.monotonic", return_value=b._last_check + 2.0):
            assert b.level == pytest.approx(0.0, abs=0.1)

    def test_available_decreases_after_acquire(self):
        b = LeakyBucket(rate=1.0, capacity=10)
        b.acquire(3)
        assert b.available == pytest.approx(7.0, abs=0.1)


class TestBuildLeakyBucketOnRetry:
    def test_returns_on_retry_key(self):
        result = build_leaky_bucket_on_retry(rate=1.0, capacity=5)
        assert "on_retry" in result

    def test_returns_bucket_instance(self):
        result = build_leaky_bucket_on_retry(rate=1.0, capacity=5)
        assert isinstance(result["bucket"], LeakyBucket)

    def test_hook_is_callable(self):
        result = build_leaky_bucket_on_retry(rate=1.0, capacity=5)
        assert callable(result["on_retry"])

    def test_hook_raises_on_overflow(self):
        result = build_leaky_bucket_on_retry(rate=1.0, capacity=1, tokens_per_attempt=1)
        hook = result["on_retry"]
        hook()  # first succeeds
        with pytest.raises(BucketOverflow):
            hook()  # bucket now full


class TestLeakyBucketPredicate:
    def test_returns_true_when_space_available(self):
        b = LeakyBucket(rate=1.0, capacity=10)
        pred = leaky_bucket_predicate(b, tokens=1)
        assert pred() is True

    def test_returns_false_when_full(self):
        b = LeakyBucket(rate=0.001, capacity=5)
        b.acquire(5)
        pred = leaky_bucket_predicate(b, tokens=1)
        assert pred() is False

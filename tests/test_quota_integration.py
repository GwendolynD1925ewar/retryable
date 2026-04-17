"""Tests for retryable.quota_integration."""
import pytest
from retryable.quota import RetryQuota, QuotaExceeded
from retryable.quota_integration import build_quota_on_retry, quota_predicate


class TestBuildQuotaOnRetry:
    def test_returns_on_retry_key(self):
        result = build_quota_on_retry(limit=5, window=60.0)
        assert "on_retry" in result

    def test_returns_quota_instance(self):
        result = build_quota_on_retry(limit=5, window=60.0)
        assert isinstance(result["quota"], RetryQuota)

    def test_quota_limit_and_window_set(self):
        result = build_quota_on_retry(limit=3, window=30.0)
        q = result["quota"]
        assert q.limit == 3
        assert q.window == 30.0

    def test_on_retry_is_callable(self):
        result = build_quota_on_retry(limit=5, window=60.0)
        assert callable(result["on_retry"])

    def test_on_retry_acquires_quota(self):
        result = build_quota_on_retry(limit=2, window=60.0, key="x")
        hook = result["on_retry"]
        quota = result["quota"]
        hook()
        assert quota.remaining("x") == 1

    def test_on_retry_raises_when_quota_exhausted(self):
        result = build_quota_on_retry(limit=1, window=60.0, key="y")
        hook = result["on_retry"]
        hook()  # consumes the 1 allowed
        with pytest.raises(QuotaExceeded):
            hook()


class TestQuotaPredicate:
    def test_returns_true_when_quota_available(self):
        q = RetryQuota(limit=3, window=60.0)
        pred = quota_predicate(q, "k")
        assert pred() is True

    def test_returns_false_when_quota_exhausted(self):
        q = RetryQuota(limit=1, window=60.0)
        q.acquire("k")
        pred = quota_predicate(q, "k")
        assert pred() is False

    def test_accepts_exc_and_result_kwargs(self):
        q = RetryQuota(limit=5, window=60.0)
        pred = quota_predicate(q)
        assert pred(exc=None, result="ok") is True

"""Tests for retryable.mirror_integration."""
import pytest

from retryable.mirror import MirrorImbalanced, RetryMirror
from retryable.mirror_integration import (
    build_mirror_on_retry,
    format_mirror_stats,
    mirror_predicate,
)


class TestBuildMirrorOnRetry:
    def test_returns_on_retry_key(self):
        result = build_mirror_on_retry("svc")
        assert "on_retry" in result

    def test_returns_mirror_instance(self):
        result = build_mirror_on_retry("svc")
        assert "mirror" in result
        assert isinstance(result["mirror"], RetryMirror)

    def test_threshold_is_respected(self):
        result = build_mirror_on_retry("svc", threshold=0.7)
        assert result["mirror"].threshold == 0.7

    def test_min_samples_is_respected(self):
        result = build_mirror_on_retry("svc", min_samples=10)
        assert result["mirror"].min_samples == 10

    def test_existing_mirror_is_reused(self):
        existing = RetryMirror(threshold=0.4, min_samples=2)
        result = build_mirror_on_retry("svc", mirror=existing)
        assert result["mirror"] is existing

    def test_on_retry_is_callable(self):
        result = build_mirror_on_retry("svc")
        assert callable(result["on_retry"])

    def test_on_retry_records_success_on_no_exception(self):
        result = build_mirror_on_retry("svc", min_samples=100)
        hook = result["on_retry"]
        mirror = result["mirror"]
        hook(None, "ok", 1)
        assert mirror.stats("svc").successes == 1

    def test_on_retry_records_failure_on_exception(self):
        result = build_mirror_on_retry("svc", min_samples=100)
        hook = result["on_retry"]
        mirror = result["mirror"]
        hook(ValueError("boom"), None, 1)
        assert mirror.stats("svc").failures == 1

    def test_on_retry_raises_when_imbalanced(self):
        result = build_mirror_on_retry("svc", threshold=0.5, min_samples=2)
        hook = result["on_retry"]
        hook(ValueError(), None, 1)
        with pytest.raises(MirrorImbalanced):
            hook(ValueError(), None, 2)


class TestMirrorPredicate:
    def test_returns_true_when_balanced(self):
        mirror = RetryMirror(threshold=0.5, min_samples=10)
        pred = mirror_predicate(mirror, "svc")
        assert pred(None, "ok") is True

    def test_returns_false_when_imbalanced(self):
        mirror = RetryMirror(threshold=0.5, min_samples=2)
        mirror.record_failure("svc")
        mirror.record_failure("svc")
        pred = mirror_predicate(mirror, "svc")
        assert pred(ValueError(), None) is False


class TestFormatMirrorStats:
    def test_no_data_message(self):
        mirror = RetryMirror(threshold=0.5)
        msg = format_mirror_stats(mirror, "svc")
        assert "no data" in msg
        assert "svc" in msg

    def test_includes_counts(self):
        mirror = RetryMirror(threshold=0.5, min_samples=100)
        mirror.record_success("svc")
        mirror.record_failure("svc")
        msg = format_mirror_stats(mirror, "svc")
        assert "successes=1" in msg
        assert "failures=1" in msg
        assert "ratio=" in msg

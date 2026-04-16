"""Tests for retryable.sentinel and retryable.sentinel_integration."""
import pytest
from retryable.sentinel import (
    RetrySentinel,
    SentinelHistory,
    is_sentinel,
    sentinel_predicate,
    unwrap,
)
from retryable.sentinel_integration import (
    build_sentinel_on_retry,
    make_sentinel_result_hook,
)


class TestRetrySentinel:
    def test_default_value_is_none(self):
        s = RetrySentinel()
        assert s.value is None

    def test_custom_value(self):
        s = RetrySentinel(value=42)
        assert s.value == 42

    def test_reason_stored(self):
        s = RetrySentinel(reason="timeout")
        assert s.reason == "timeout"

    def test_repr_contains_value(self):
        s = RetrySentinel(value="x", reason="r")
        assert "'x'" in repr(s)
        assert "'r'" in repr(s)


class TestIsSentinel:
    def test_returns_true_for_sentinel(self):
        assert is_sentinel(RetrySentinel()) is True

    def test_returns_false_for_none(self):
        assert is_sentinel(None) is False

    def test_returns_false_for_string(self):
        assert is_sentinel("ok") is False


class TestSentinelPredicate:
    def test_returns_true_for_sentinel_result(self):
        assert sentinel_predicate(RetrySentinel(), None) is True

    def test_returns_false_when_exception_present(self):
        assert sentinel_predicate(RetrySentinel(), ValueError()) is False

    def test_returns_false_for_plain_result(self):
        assert sentinel_predicate("done", None) is False


class TestUnwrap:
    def test_unwraps_sentinel(self):
        assert unwrap(RetrySentinel(value=99)) == 99

    def test_passthrough_for_plain_value(self):
        assert unwrap("hello") == "hello"


class TestSentinelHistory:
    def setup_method(self):
        self.history = SentinelHistory()

    def test_initial_count_is_zero(self):
        assert self.history.count == 0

    def test_record_increments_count(self):
        self.history.record(RetrySentinel())
        assert self.history.count == 1

    def test_reasons_collected(self):
        self.history.record(RetrySentinel(reason="a"))
        self.history.record(RetrySentinel(reason="b"))
        assert self.history.reasons == ["a", "b"]

    def test_empty_reason_not_added(self):
        self.history.record(RetrySentinel())
        assert self.history.reasons == []

    def test_reset_clears_state(self):
        self.history.record(RetrySentinel(reason="x"))
        self.history.reset()
        assert self.history.count == 0
        assert self.history.reasons == []


class TestBuildSentinelOnRetry:
    def test_returns_on_retry_key(self):
        result = build_sentinel_on_retry()
        assert "on_retry" in result

    def test_returns_retry_on_key(self):
        result = build_sentinel_on_retry()
        assert "retry_on" in result

    def test_on_retry_records_sentinel(self):
        history = SentinelHistory()
        result = build_sentinel_on_retry(history=history)
        result["on_retry"](RetrySentinel(reason="z"), None, 1)
        assert history.count == 1

    def test_retry_on_true_for_sentinel(self):
        result = build_sentinel_on_retry()
        assert result["retry_on"](RetrySentinel(), None) is True

    def test_retry_on_false_for_exception(self):
        result = build_sentinel_on_retry()
        assert result["retry_on"](None, RuntimeError()) is False


class TestMakeSentinelResultHook:
    def test_records_sentinel_into_history(self):
        history = SentinelHistory()
        hook = make_sentinel_result_hook(history)
        hook(RetrySentinel(reason="slow"), None, 2)
        assert history.count == 1
        assert history.reasons == ["slow"]

    def test_ignores_non_sentinel(self):
        history = SentinelHistory()
        hook = make_sentinel_result_hook(history)
        hook("ok", None, 1)
        assert history.count == 0

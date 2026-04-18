"""Tests for retryable.signal."""
import pytest
from retryable.signal import RetrySignal, RetrySignalEvent, build_signal_on_retry


class TestRetrySignalEvent:
    def test_succeeded_true_when_no_exception(self):
        e = RetrySignalEvent(attempt=1)
        assert e.succeeded is True

    def test_succeeded_false_when_exception(self):
        e = RetrySignalEvent(attempt=1, exception=ValueError("boom"))
        assert e.succeeded is False

    def test_succeeded_false_when_cancelled(self):
        e = RetrySignalEvent(attempt=1, cancelled=True)
        assert e.succeeded is False

    def test_repr_contains_attempt(self):
        e = RetrySignalEvent(attempt=3)
        assert "attempt=3" in repr(e)


class TestRetrySignal:
    def setup_method(self):
        self.signal = RetrySignal()

    def test_initial_subscriber_count_is_zero(self):
        assert self.signal.subscriber_count == 0

    def test_subscribe_increments_count(self):
        self.signal.subscribe(lambda e: None)
        assert self.signal.subscriber_count == 1

    def test_non_callable_raises(self):
        with pytest.raises(TypeError):
            self.signal.subscribe("not_callable")

    def test_emit_calls_handler(self):
        received = []
        self.signal.subscribe(received.append)
        event = RetrySignalEvent(attempt=1)
        self.signal.emit(event)
        assert received == [event]

    def test_emit_calls_multiple_handlers(self):
        calls = []
        self.signal.subscribe(lambda e: calls.append("a"))
        self.signal.subscribe(lambda e: calls.append("b"))
        self.signal.emit(RetrySignalEvent(attempt=1))
        assert calls == ["a", "b"]

    def test_unsubscribe_removes_handler(self):
        calls = []
        handler = lambda e: calls.append(e)
        self.signal.subscribe(handler)
        self.signal.unsubscribe(handler)
        self.signal.emit(RetrySignalEvent(attempt=1))
        assert calls == []

    def test_unsubscribe_unknown_raises(self):
        with pytest.raises(ValueError):
            self.signal.unsubscribe(lambda e: None)

    def test_clear_removes_all_handlers(self):
        self.signal.subscribe(lambda e: None)
        self.signal.subscribe(lambda e: None)
        self.signal.clear()
        assert self.signal.subscriber_count == 0


class TestBuildSignalOnRetry:
    def test_returns_on_retry_key(self):
        sig = RetrySignal()
        result = build_signal_on_retry(sig)
        assert "on_retry" in result

    def test_returns_signal_key(self):
        sig = RetrySignal()
        result = build_signal_on_retry(sig)
        assert result["signal"] is sig

    def test_on_retry_emits_event(self):
        sig = RetrySignal()
        received = []
        sig.subscribe(received.append)
        hook = build_signal_on_retry(sig)["on_retry"]
        hook(attempt=2, exception=RuntimeError("x"))
        assert len(received) == 1
        assert received[0].attempt == 2
        assert isinstance(received[0].exception, RuntimeError)

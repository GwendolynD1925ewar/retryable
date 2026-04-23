"""Tests for retryable.valve and retryable.valve_integration."""
from __future__ import annotations

import pytest

from retryable.valve import RetryValve, ValveThrottled
from retryable.valve_integration import build_valve_on_retry, valve_predicate


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

class TestRetryValveInit:
    def test_valid_construction(self):
        v = RetryValve(max_throughput=3, window_seconds=5.0)
        assert v.max_throughput == 3
        assert v.window_seconds == 5.0

    def test_zero_max_throughput_raises(self):
        with pytest.raises(ValueError, match="max_throughput"):
            RetryValve(max_throughput=0, window_seconds=1.0)

    def test_negative_max_throughput_raises(self):
        with pytest.raises(ValueError, match="max_throughput"):
            RetryValve(max_throughput=-1, window_seconds=1.0)

    def test_zero_window_raises(self):
        with pytest.raises(ValueError, match="window_seconds"):
            RetryValve(max_throughput=1, window_seconds=0.0)

    def test_negative_window_raises(self):
        with pytest.raises(ValueError, match="window_seconds"):
            RetryValve(max_throughput=1, window_seconds=-1.0)


# ---------------------------------------------------------------------------
# open / acquire / remaining
# ---------------------------------------------------------------------------

class TestRetryValveAcquire:
    def _make(self, max_throughput: int = 3, window: float = 10.0) -> RetryValve:
        clock = iter(range(1000))
        return RetryValve(
            max_throughput=max_throughput,
            window_seconds=window,
            _clock=lambda: float(next(clock)),
        )

    def test_initially_open(self):
        v = self._make()
        assert v.open is True

    def test_acquire_increments_count(self):
        v = self._make(max_throughput=3)
        v.acquire()
        assert v.current_count == 1

    def test_remaining_decreases_after_acquire(self):
        v = self._make(max_throughput=3)
        v.acquire()
        assert v.remaining == 2

    def test_valve_closes_at_limit(self):
        v = self._make(max_throughput=2)
        v.acquire()
        v.acquire()
        assert v.open is False

    def test_acquire_raises_when_closed(self):
        v = self._make(max_throughput=1)
        v.acquire()
        with pytest.raises(ValveThrottled):
            v.acquire()

    def test_remaining_is_zero_when_closed(self):
        v = self._make(max_throughput=2)
        v.acquire()
        v.acquire()
        assert v.remaining == 0

    def test_old_entries_evicted_after_window(self):
        tick = [0.0]

        def clock():
            return tick[0]

        v = RetryValve(max_throughput=2, window_seconds=5.0, _clock=clock)
        v.acquire()  # recorded at t=0
        v.acquire()  # recorded at t=0 — valve now closed
        assert v.open is False

        tick[0] = 6.0  # advance past window
        assert v.open is True  # old entries evicted


# ---------------------------------------------------------------------------
# ValveThrottled
# ---------------------------------------------------------------------------

class TestValveThrottled:
    def test_default_message(self):
        exc = ValveThrottled()
        assert "closed" in str(exc).lower()

    def test_custom_message(self):
        exc = ValveThrottled("custom")
        assert str(exc) == "custom"

    def test_is_exception(self):
        assert isinstance(ValveThrottled(), Exception)


# ---------------------------------------------------------------------------
# Integration helpers
# ---------------------------------------------------------------------------

class TestBuildValveOnRetry:
    def test_returns_on_retry_key(self):
        result = build_valve_on_retry(max_throughput=5, window_seconds=10.0)
        assert "on_retry" in result

    def test_returns_valve_instance(self):
        result = build_valve_on_retry(max_throughput=5, window_seconds=10.0)
        assert isinstance(result["valve"], RetryValve)

    def test_on_retry_is_callable(self):
        result = build_valve_on_retry(max_throughput=5, window_seconds=10.0)
        assert callable(result["on_retry"])

    def test_on_retry_acquires_slot(self):
        result = build_valve_on_retry(max_throughput=2, window_seconds=60.0)
        hook = result["on_retry"]
        valve: RetryValve = result["valve"]
        hook(1, None, None)
        assert valve.current_count == 1

    def test_on_retry_raises_when_exhausted(self):
        result = build_valve_on_retry(max_throughput=1, window_seconds=60.0)
        hook = result["on_retry"]
        hook(1, None, None)
        with pytest.raises(ValveThrottled):
            hook(2, None, None)


class TestValvePredicate:
    def test_returns_true_when_open(self):
        valve = RetryValve(max_throughput=5, window_seconds=60.0)
        pred = valve_predicate(valve)
        assert pred(1, None, None) is True

    def test_returns_false_when_closed(self):
        tick = [0.0]
        valve = RetryValve(max_throughput=1, window_seconds=60.0, _clock=lambda: tick[0])
        valve.acquire()
        pred = valve_predicate(valve)
        assert pred(2, None, None) is False

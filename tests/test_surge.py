"""Tests for retryable.surge."""

from __future__ import annotations

import pytest

from retryable.surge import RetrySurge, SurgeLimitExceeded


class TestRetrySurgeInit:
    def test_valid_construction(self):
        surge = RetrySurge(limit=5, window=10.0)
        assert surge.limit == 5
        assert surge.window == 10.0

    def test_zero_limit_raises(self):
        with pytest.raises(ValueError, match="limit"):
            RetrySurge(limit=0, window=1.0)

    def test_negative_limit_raises(self):
        with pytest.raises(ValueError, match="limit"):
            RetrySurge(limit=-1, window=1.0)

    def test_zero_window_raises(self):
        with pytest.raises(ValueError, match="window"):
            RetrySurge(limit=3, window=0.0)

    def test_negative_window_raises(self):
        with pytest.raises(ValueError, match="window"):
            RetrySurge(limit=3, window=-5.0)

    def test_custom_clock_is_used(self):
        clock = lambda: 42.0
        surge = RetrySurge(limit=2, window=1.0, clock=clock)
        assert surge.clock is clock


class TestRetrySurgeAcquire:
    def _make(self, limit: int = 3, window: float = 60.0):
        ticks = [0.0]

        def clock():
            return ticks[0]

        surge = RetrySurge(limit=limit, window=window, clock=clock)
        return surge, ticks

    def test_first_acquire_succeeds(self):
        surge, _ = self._make()
        surge.acquire()  # should not raise

    def test_acquire_up_to_limit_succeeds(self):
        surge, _ = self._make(limit=3)
        for _ in range(3):
            surge.acquire()

    def test_acquire_beyond_limit_raises(self):
        surge, _ = self._make(limit=2)
        surge.acquire()
        surge.acquire()
        with pytest.raises(SurgeLimitExceeded):
            surge.acquire()

    def test_expired_attempts_are_evicted(self):
        surge, ticks = self._make(limit=2, window=10.0)
        surge.acquire()  # t=0
        surge.acquire()  # t=0 — now at limit
        ticks[0] = 11.0  # advance past window
        # old entries evicted; should succeed again
        surge.acquire()

    def test_surge_limit_exceeded_carries_metadata(self):
        surge, _ = self._make(limit=1)
        surge.acquire()
        with pytest.raises(SurgeLimitExceeded) as exc_info:
            surge.acquire()
        err = exc_info.value
        assert err.limit == 1
        assert err.window == 60.0


class TestRetrySurgeProperties:
    def _make(self, limit: int = 3, window: float = 60.0):
        ticks = [0.0]
        surge = RetrySurge(limit=limit, window=window, clock=lambda: ticks[0])
        return surge, ticks

    def test_initial_current_count_is_zero(self):
        surge, _ = self._make()
        assert surge.current_count == 0

    def test_current_count_increments_on_acquire(self):
        surge, _ = self._make()
        surge.acquire()
        surge.acquire()
        assert surge.current_count == 2

    def test_remaining_equals_limit_initially(self):
        surge, _ = self._make(limit=4)
        assert surge.remaining == 4

    def test_remaining_decrements_on_acquire(self):
        surge, _ = self._make(limit=3)
        surge.acquire()
        assert surge.remaining == 2

    def test_remaining_resets_after_window_expires(self):
        surge, ticks = self._make(limit=2, window=5.0)
        surge.acquire()
        surge.acquire()
        assert surge.remaining == 0
        ticks[0] = 6.0
        assert surge.remaining == 2

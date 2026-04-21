"""Tests for retryable.tide."""
from __future__ import annotations

import pytest

from retryable.tide import RetryTide, TideSurge


class TestRetryTideInit:
    def test_valid_construction(self):
        tide = RetryTide(window=10.0, surge_threshold=5)
        assert tide.window == 10.0
        assert tide.surge_threshold == 5

    def test_zero_window_raises(self):
        with pytest.raises(ValueError, match="window must be positive"):
            RetryTide(window=0.0, surge_threshold=5)

    def test_negative_window_raises(self):
        with pytest.raises(ValueError, match="window must be positive"):
            RetryTide(window=-1.0, surge_threshold=5)

    def test_zero_surge_threshold_raises(self):
        with pytest.raises(ValueError, match="surge_threshold must be >= 1"):
            RetryTide(window=10.0, surge_threshold=0)

    def test_negative_surge_threshold_raises(self):
        with pytest.raises(ValueError, match="surge_threshold must be >= 1"):
            RetryTide(window=10.0, surge_threshold=-3)

    def test_threshold_of_one_is_valid(self):
        tide = RetryTide(window=5.0, surge_threshold=1)
        assert tide.surge_threshold == 1


class TestRetryTideCount:
    def _make(self, window: float = 10.0, threshold: int = 5) -> RetryTide:
        now = 1000.0
        clock_state = [now]

        def clock() -> float:
            return clock_state[0]

        tide = RetryTide(window=window, surge_threshold=threshold, _clock=clock)
        tide._advance = lambda delta: clock_state.__setitem__(0, clock_state[0] + delta)
        return tide

    def test_initial_count_is_zero(self):
        tide = RetryTide(window=10.0, surge_threshold=5)
        assert tide.count() == 0

    def test_record_increments_count(self):
        tide = self._make()
        tide.record()
        tide.record()
        assert tide.count() == 2

    def test_old_timestamps_are_evicted(self):
        tide = self._make(window=5.0)
        tide.record()
        tide.record()
        tide._advance(6.0)  # advance past window
        assert tide.count() == 0

    def test_only_recent_timestamps_counted(self):
        tide = self._make(window=5.0)
        tide.record()  # at t=1000
        tide._advance(6.0)  # now t=1006, first record is outside window
        tide.record()  # at t=1006
        assert tide.count() == 1

    def test_reset_clears_all(self):
        tide = self._make()
        tide.record()
        tide.record()
        tide.reset()
        assert tide.count() == 0


class TestRetryTideSurge:
    def _make_at_surge(self, threshold: int = 3) -> RetryTide:
        tide = RetryTide(window=60.0, surge_threshold=threshold)
        for _ in range(threshold):
            tide.record()
        return tide

    def test_surging_false_below_threshold(self):
        tide = RetryTide(window=60.0, surge_threshold=3)
        tide.record()
        tide.record()
        assert not tide.surging()

    def test_surging_true_at_threshold(self):
        tide = self._make_at_surge(threshold=3)
        assert tide.surging()

    def test_check_raises_tide_surge_at_threshold(self):
        tide = self._make_at_surge(threshold=2)
        with pytest.raises(TideSurge) as exc_info:
            tide.check()
        err = exc_info.value
        assert err.count == 2
        assert err.threshold == 2

    def test_check_passes_below_threshold(self):
        tide = RetryTide(window=60.0, surge_threshold=5)
        tide.record()
        tide.check()  # should not raise

    def test_tide_surge_message(self):
        err = TideSurge(count=4, window=10.0, threshold=3)
        assert "4" in str(err)
        assert "10.0" in str(err)
        assert "3" in str(err)

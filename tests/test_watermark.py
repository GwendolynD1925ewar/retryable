"""Tests for retryable.watermark."""
from __future__ import annotations

import pytest

from retryable.watermark import RetryWatermark, watermark_hook


class TestRetryWatermarkInit:
    def test_valid_construction(self):
        wm = RetryWatermark(_threshold=3)
        assert wm.peak == 0
        assert wm.total_calls == 0

    def test_default_threshold_is_one(self):
        wm = RetryWatermark()
        assert wm._threshold == 1

    def test_zero_threshold_raises(self):
        with pytest.raises(ValueError, match="threshold"):
            RetryWatermark(_threshold=0)

    def test_negative_threshold_raises(self):
        with pytest.raises(ValueError, match="threshold"):
            RetryWatermark(_threshold=-1)


class TestRetryWatermarkRecord:
    def test_first_record_sets_peak(self):
        wm = RetryWatermark()
        wm.record(3)
        assert wm.peak == 3

    def test_higher_value_updates_peak(self):
        wm = RetryWatermark()
        wm.record(2)
        wm.record(5)
        assert wm.peak == 5

    def test_lower_value_does_not_update_peak(self):
        wm = RetryWatermark()
        wm.record(5)
        wm.record(2)
        assert wm.peak == 5

    def test_total_calls_increments(self):
        wm = RetryWatermark()
        wm.record(1)
        wm.record(1)
        wm.record(1)
        assert wm.total_calls == 3

    def test_zero_attempts_raises(self):
        wm = RetryWatermark()
        with pytest.raises(ValueError, match="attempts"):
            wm.record(0)

    def test_negative_attempts_raises(self):
        wm = RetryWatermark()
        with pytest.raises(ValueError, match="attempts"):
            wm.record(-1)


class TestRetryWatermarkThresholdBreached:
    def test_not_breached_when_peak_equals_threshold(self):
        wm = RetryWatermark(_threshold=3)
        wm.record(3)
        assert wm.threshold_breached is False

    def test_breached_when_peak_exceeds_threshold(self):
        wm = RetryWatermark(_threshold=3)
        wm.record(4)
        assert wm.threshold_breached is True

    def test_not_breached_initially(self):
        wm = RetryWatermark(_threshold=1)
        assert wm.threshold_breached is False


class TestRetryWatermarkReset:
    def test_reset_clears_peak_and_calls(self):
        wm = RetryWatermark()
        wm.record(5)
        wm.reset()
        assert wm.peak == 0
        assert wm.total_calls == 0


class TestWatermarkHook:
    def test_hook_records_attempt(self):
        wm = RetryWatermark()
        hook = watermark_hook(wm)
        hook(attempt=2)
        assert wm.peak == 2

    def test_hook_accepts_exception_kwarg(self):
        wm = RetryWatermark()
        hook = watermark_hook(wm)
        hook(attempt=1, exception=ValueError("boom"))
        assert wm.total_calls == 1

    def test_hook_accepts_result_kwarg(self):
        wm = RetryWatermark()
        hook = watermark_hook(wm)
        hook(attempt=1, result="ok")
        assert wm.peak == 1

    def test_hook_updates_peak_across_multiple_calls(self):
        wm = RetryWatermark()
        hook = watermark_hook(wm)
        for attempts in [1, 3, 2, 5, 4]:
            hook(attempt=attempts)
        assert wm.peak == 5
        assert wm.total_calls == 5

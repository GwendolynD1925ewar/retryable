"""Tests for retryable.band."""
import pytest

from retryable.band import RetryBand


def _linear(attempt: int) -> float:
    """Simple linear backoff: attempt * 5.0."""
    return attempt * 5.0


class TestRetryBandInit:
    def test_valid_construction(self):
        band = RetryBand(min_delay=1.0, max_delay=30.0, backoff=_linear)
        assert band.min_delay == 1.0
        assert band.max_delay == 30.0

    def test_zero_min_delay_is_valid(self):
        band = RetryBand(min_delay=0.0, max_delay=10.0, backoff=_linear)
        assert band.min_delay == 0.0

    def test_negative_min_delay_raises(self):
        with pytest.raises(ValueError, match="min_delay"):
            RetryBand(min_delay=-1.0, max_delay=10.0, backoff=_linear)

    def test_zero_max_delay_raises(self):
        with pytest.raises(ValueError, match="max_delay"):
            RetryBand(min_delay=0.0, max_delay=0.0, backoff=_linear)

    def test_negative_max_delay_raises(self):
        with pytest.raises(ValueError, match="max_delay"):
            RetryBand(min_delay=0.0, max_delay=-5.0, backoff=_linear)

    def test_min_greater_than_max_raises(self):
        with pytest.raises(ValueError, match="min_delay must be <= max_delay"):
            RetryBand(min_delay=20.0, max_delay=10.0, backoff=_linear)


class TestRetryBandDelay:
    def setup_method(self):
        self.band = RetryBand(min_delay=2.0, max_delay=20.0, backoff=_linear)

    def test_clamps_below_min(self):
        # attempt=0 -> raw=0.0, clamped to min_delay=2.0
        assert self.band.delay(0) == 2.0

    def test_passes_through_within_band(self):
        # attempt=2 -> raw=10.0, within [2, 20]
        assert self.band.delay(2) == 10.0

    def test_clamps_above_max(self):
        # attempt=10 -> raw=50.0, clamped to max_delay=20.0
        assert self.band.delay(10) == 20.0

    def test_exact_min_boundary(self):
        # attempt that produces exactly min_delay
        band = RetryBand(min_delay=5.0, max_delay=50.0, backoff=_linear)
        assert band.delay(1) == 5.0

    def test_exact_max_boundary(self):
        band = RetryBand(min_delay=1.0, max_delay=20.0, backoff=_linear)
        assert band.delay(4) == 20.0


class TestRetryBandWithinBand:
    def setup_method(self):
        self.band = RetryBand(min_delay=1.0, max_delay=10.0, backoff=_linear)

    def test_value_within_band(self):
        assert self.band.within_band(5.0) is True

    def test_value_at_min(self):
        assert self.band.within_band(1.0) is True

    def test_value_at_max(self):
        assert self.band.within_band(10.0) is True

    def test_value_below_min(self):
        assert self.band.within_band(0.5) is False

    def test_value_above_max(self):
        assert self.band.within_band(10.1) is False

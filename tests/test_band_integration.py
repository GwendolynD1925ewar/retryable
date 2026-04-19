"""Tests for retryable.band_integration."""
import pytest

from retryable.band import RetryBand
from retryable.band_integration import build_banded_backoff, band_predicate


def _constant(attempt: int) -> float:  # noqa: ARG001
    return 5.0


class TestBuildBandedBackoff:
    def test_returns_on_backoff_key(self):
        result = build_banded_backoff(1.0, 10.0, _constant)
        assert "on_backoff" in result

    def test_returns_band_key(self):
        result = build_banded_backoff(1.0, 10.0, _constant)
        assert "band" in result

    def test_band_instance_is_retry_band(self):
        result = build_banded_backoff(1.0, 10.0, _constant)
        assert isinstance(result["band"], RetryBand)

    def test_on_backoff_is_callable(self):
        result = build_banded_backoff(1.0, 10.0, _constant)
        assert callable(result["on_backoff"])

    def test_on_backoff_clamps_to_max(self):
        def big(_attempt: int) -> float:
            return 999.0

        result = build_banded_backoff(1.0, 10.0, big)
        assert result["on_backoff"](1) == 10.0

    def test_on_backoff_clamps_to_min(self):
        def tiny(_attempt: int) -> float:
            return 0.0

        result = build_banded_backoff(2.0, 10.0, tiny)
        assert result["on_backoff"](1) == 2.0

    def test_band_min_max_set_correctly(self):
        result = build_banded_backoff(3.0, 15.0, _constant)
        band = result["band"]
        assert band.min_delay == 3.0
        assert band.max_delay == 15.0


class TestBandPredicate:
    def test_returns_callable(self):
        band = RetryBand(min_delay=1.0, max_delay=10.0, backoff=_constant)
        pred = band_predicate(band)
        assert callable(pred)

    def test_predicate_returns_true_no_exception(self):
        band = RetryBand(min_delay=1.0, max_delay=10.0, backoff=_constant)
        pred = band_predicate(band)
        assert pred("some_result", None) is True

    def test_predicate_returns_true_with_exception(self):
        band = RetryBand(min_delay=1.0, max_delay=10.0, backoff=_constant)
        pred = band_predicate(band)
        assert pred(None, ValueError("boom")) is True

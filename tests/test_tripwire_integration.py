"""Tests for tripwire integration helpers."""
import pytest

from retryable.tripwire import RetryTripwire, TripwireTripped
from retryable.tripwire_integration import build_tripwire_on_retry, tripwire_predicate


class TestBuildTripwireOnRetry:
    def test_returns_on_retry_key(self):
        result = build_tripwire_on_retry(threshold=3)
        assert "on_retry" in result

    def test_returns_tripwire_instance(self):
        result = build_tripwire_on_retry(threshold=3)
        assert isinstance(result["tripwire"], RetryTripwire)

    def test_threshold_is_set(self):
        result = build_tripwire_on_retry(threshold=5)
        assert result["tripwire"].threshold == 5

    def test_label_is_set(self):
        result = build_tripwire_on_retry(threshold=2, label="svc")
        assert result["tripwire"].label == "svc"

    def test_on_retry_is_callable(self):
        result = build_tripwire_on_retry(threshold=3)
        assert callable(result["on_retry"])

    def test_hook_records_failure_on_exception(self):
        result = build_tripwire_on_retry(threshold=5)
        hook = result["on_retry"]
        tw = result["tripwire"]
        hook(exc=ValueError("boom"))
        assert tw.consecutive == 1

    def test_hook_records_success_on_no_exception(self):
        result = build_tripwire_on_retry(threshold=5)
        hook = result["on_retry"]
        tw = result["tripwire"]
        hook(exc=ValueError("boom"))
        hook(exc=None, result="ok")
        assert tw.consecutive == 0

    def test_hook_raises_when_tripwire_trips(self):
        result = build_tripwire_on_retry(threshold=2)
        hook = result["on_retry"]
        hook(exc=ValueError("e1"))
        with pytest.raises(TripwireTripped):
            hook(exc=ValueError("e2"))


class TestTripwirePredicate:
    def test_allows_retry_when_not_tripped(self):
        tw = RetryTripwire(threshold=5)
        pred = tripwire_predicate(tw)
        assert pred(exc=ValueError("x")) is True

    def test_blocks_retry_when_tripped(self):
        tw = RetryTripwire(threshold=1)
        pred = tripwire_predicate(tw)
        with pytest.raises(TripwireTripped):
            tw.record_failure()
        assert pred(exc=ValueError("x")) is False

    def test_blocks_retry_when_no_exception(self):
        tw = RetryTripwire(threshold=5)
        pred = tripwire_predicate(tw)
        assert pred(exc=None, result="ok") is False

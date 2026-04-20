"""Tests for RetryTripwire."""
import pytest

from retryable.tripwire import RetryTripwire, TripwireTripped


class TestRetryTripwireInit:
    def test_valid_construction(self):
        tw = RetryTripwire(threshold=3)
        assert tw.threshold == 3
        assert tw.label == "default"

    def test_valid_with_label(self):
        tw = RetryTripwire(threshold=2, label="svc")
        assert tw.label == "svc"

    def test_zero_threshold_raises(self):
        with pytest.raises(ValueError, match="threshold"):
            RetryTripwire(threshold=0)

    def test_negative_threshold_raises(self):
        with pytest.raises(ValueError, match="threshold"):
            RetryTripwire(threshold=-1)

    def test_empty_label_raises(self):
        with pytest.raises(ValueError, match="label"):
            RetryTripwire(threshold=1, label="")

    def test_blank_label_raises(self):
        with pytest.raises(ValueError, match="label"):
            RetryTripwire(threshold=1, label="   ")


class TestRetryTripwireRecordFailure:
    def test_single_failure_does_not_trip(self):
        tw = RetryTripwire(threshold=3)
        tw.record_failure()
        assert not tw.tripped
        assert tw.consecutive == 1

    def test_trips_at_threshold(self):
        tw = RetryTripwire(threshold=2)
        tw.record_failure()
        with pytest.raises(TripwireTripped) as exc_info:
            tw.record_failure()
        assert tw.tripped
        assert exc_info.value.consecutive == 2
        assert exc_info.value.label == "default"

    def test_raises_immediately_when_already_tripped(self):
        tw = RetryTripwire(threshold=1)
        with pytest.raises(TripwireTripped):
            tw.record_failure()
        with pytest.raises(TripwireTripped):
            tw.record_failure()

    def test_consecutive_count_increments(self):
        tw = RetryTripwire(threshold=5)
        for i in range(1, 4):
            tw.record_failure()
            assert tw.consecutive == i


class TestRetryTripwireRecordSuccess:
    def test_success_resets_consecutive(self):
        tw = RetryTripwire(threshold=5)
        tw.record_failure()
        tw.record_failure()
        tw.record_success()
        assert tw.consecutive == 0
        assert not tw.tripped

    def test_success_clears_tripped_state(self):
        tw = RetryTripwire(threshold=1)
        with pytest.raises(TripwireTripped):
            tw.record_failure()
        tw.record_success()
        assert not tw.tripped

    def test_can_record_failures_after_reset_via_success(self):
        tw = RetryTripwire(threshold=2)
        tw.record_failure()
        tw.record_success()
        tw.record_failure()
        assert tw.consecutive == 1


class TestRetryTripwireReset:
    def test_reset_clears_all_state(self):
        tw = RetryTripwire(threshold=2)
        tw.record_failure()
        tw.reset()
        assert tw.consecutive == 0
        assert not tw.tripped

    def test_repr_contains_fields(self):
        tw = RetryTripwire(threshold=3, label="x")
        r = repr(tw)
        assert "threshold=3" in r
        assert "label='x'" in r
        assert "tripped=False" in r

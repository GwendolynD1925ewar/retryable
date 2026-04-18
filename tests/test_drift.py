"""Tests for retryable.drift — RetryDriftTracker and DriftEntry."""
import time
import pytest
from retryable.drift import DriftEntry, RetryDriftTracker


class TestDriftEntry:
    def test_drift_positive_when_actual_longer(self):
        e = DriftEntry(attempt=1, scheduled_delay=0.5, actual_delay=0.7)
        assert pytest.approx(e.drift, abs=1e-9) == 0.2

    def test_drift_negative_when_actual_shorter(self):
        e = DriftEntry(attempt=1, scheduled_delay=0.5, actual_delay=0.3)
        assert pytest.approx(e.drift, abs=1e-9) == -0.2

    def test_drift_zero_when_equal(self):
        e = DriftEntry(attempt=2, scheduled_delay=1.0, actual_delay=1.0)
        assert e.drift == 0.0

    def test_repr_contains_fields(self):
        e = DriftEntry(attempt=3, scheduled_delay=0.1, actual_delay=0.15)
        r = repr(e)
        assert "attempt=3" in r
        assert "drift=" in r


class TestRetryDriftTrackerInit:
    def test_starts_empty(self):
        t = RetryDriftTracker()
        assert t.entries == []

    def test_total_drift_zero_when_empty(self):
        assert RetryDriftTracker().total_drift == 0.0

    def test_average_drift_zero_when_empty(self):
        assert RetryDriftTracker().average_drift == 0.0

    def test_max_drift_none_when_empty(self):
        assert RetryDriftTracker().max_drift is None


class TestRetryDriftTrackerSchedule:
    def test_negative_delay_raises(self):
        t = RetryDriftTracker()
        with pytest.raises(ValueError, match="non-negative"):
            t.schedule(-0.1)

    def test_zero_delay_is_valid(self):
        t = RetryDriftTracker()
        t.schedule(0.0)  # should not raise


class TestRetryDriftTrackerRecord:
    def test_record_without_schedule_returns_none(self):
        t = RetryDriftTracker()
        assert t.record(attempt=1) is None

    def test_record_after_schedule_returns_entry(self):
        t = RetryDriftTracker()
        t.schedule(0.01)
        time.sleep(0.01)
        entry = t.record(attempt=1)
        assert entry is not None
        assert entry.attempt == 1
        assert entry.scheduled_delay == 0.01
        assert entry.actual_delay >= 0.0

    def test_record_appends_to_entries(self):
        t = RetryDriftTracker()
        t.schedule(0.01)
        time.sleep(0.01)
        t.record(attempt=1)
        assert len(t.entries) == 1

    def test_second_record_without_reschedule_returns_none(self):
        t = RetryDriftTracker()
        t.schedule(0.01)
        time.sleep(0.01)
        t.record(attempt=1)
        assert t.record(attempt=2) is None

    def test_total_and_average_drift_computed(self):
        t = RetryDriftTracker()
        for i in range(3):
            t.schedule(0.01)
            time.sleep(0.01)
            t.record(attempt=i + 1)
        assert len(t.entries) == 3
        assert isinstance(t.total_drift, float)
        assert isinstance(t.average_drift, float)

    def test_max_drift_returns_largest(self):
        t = RetryDriftTracker()
        for i in range(2):
            t.schedule(0.01)
            time.sleep(0.01)
            t.record(attempt=i + 1)
        assert t.max_drift is not None

    def test_reset_clears_state(self):
        t = RetryDriftTracker()
        t.schedule(0.01)
        time.sleep(0.01)
        t.record(attempt=1)
        t.reset()
        assert t.entries == []
        assert t.record(attempt=2) is None

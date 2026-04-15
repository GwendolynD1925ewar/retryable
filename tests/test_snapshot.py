"""Tests for retryable.snapshot."""
from __future__ import annotations

import time

import pytest

from retryable.snapshot import RetrySnapshot, SnapshotHistory


# ---------------------------------------------------------------------------
# RetrySnapshot
# ---------------------------------------------------------------------------

class TestRetrySnapshot:
    def _make(self, *, attempt=1, exception=None, result=None, delay=0.0, elapsed=0.0):
        return RetrySnapshot(
            attempt=attempt,
            timestamp=time.time(),
            elapsed=elapsed,
            exception=exception,
            result=result,
            delay=delay,
        )

    def test_succeeded_true_when_no_exception(self):
        s = self._make(result="ok")
        assert s.succeeded is True

    def test_succeeded_false_when_exception_present(self):
        s = self._make(exception=ValueError("boom"))
        assert s.succeeded is False

    def test_failed_true_when_exception_present(self):
        s = self._make(exception=RuntimeError("oops"))
        assert s.failed is True

    def test_failed_false_when_no_exception(self):
        s = self._make(result=42)
        assert s.failed is False

    def test_attempt_number_stored(self):
        s = self._make(attempt=3)
        assert s.attempt == 3

    def test_delay_stored(self):
        s = self._make(delay=1.5)
        assert s.delay == pytest.approx(1.5)

    def test_result_stored(self):
        s = self._make(result={"key": "value"})
        assert s.result == {"key": "value"}

    def test_snapshot_is_immutable(self):
        s = self._make()
        with pytest.raises((AttributeError, TypeError)):
            s.attempt = 99  # type: ignore[misc]


# ---------------------------------------------------------------------------
# SnapshotHistory
# ---------------------------------------------------------------------------

class TestSnapshotHistory:
    def test_initial_state_is_empty(self):
        h = SnapshotHistory()
        assert h.total_attempts == 0
        assert h.snapshots == []
        assert h.last is None

    def test_record_increments_total_attempts(self):
        h = SnapshotHistory()
        h.record(attempt=1)
        h.record(attempt=2)
        assert h.total_attempts == 2

    def test_last_returns_most_recent_snapshot(self):
        h = SnapshotHistory()
        h.record(attempt=1, result="first")
        h.record(attempt=2, result="second")
        assert h.last is not None
        assert h.last.result == "second"

    def test_record_returns_snapshot(self):
        h = SnapshotHistory()
        s = h.record(attempt=1, exception=ValueError("x"), delay=0.5)
        assert isinstance(s, RetrySnapshot)
        assert s.attempt == 1
        assert s.delay == pytest.approx(0.5)

    def test_failures_filters_correctly(self):
        h = SnapshotHistory()
        h.record(attempt=1, exception=ValueError("bad"))
        h.record(attempt=2, result="ok")
        h.record(attempt=3, exception=RuntimeError("also bad"))
        failures = h.failures()
        assert len(failures) == 2
        assert all(f.failed for f in failures)

    def test_snapshots_returns_copy(self):
        h = SnapshotHistory()
        h.record(attempt=1)
        copy = h.snapshots
        copy.clear()
        assert h.total_attempts == 1

    def test_elapsed_increases_over_time(self):
        h = SnapshotHistory()
        s1 = h.record(attempt=1)
        time.sleep(0.05)
        s2 = h.record(attempt=2)
        assert s2.elapsed > s1.elapsed

    def test_reset_clears_history(self):
        h = SnapshotHistory()
        h.record(attempt=1, exception=ValueError())
        h.reset()
        assert h.total_attempts == 0
        assert h.last is None

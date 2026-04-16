"""Tests for retryable.replay."""

import pytest
from retryable.replay import ReplayEntry, RetryReplayLog


class TestReplayEntry:
    def test_succeeded_true_when_no_exception(self):
        e = ReplayEntry(attempt=1, timestamp=0.0)
        assert e.succeeded is True

    def test_succeeded_false_when_exception_present(self):
        e = ReplayEntry(attempt=1, timestamp=0.0, exception=ValueError("boom"))
        assert e.succeeded is False

    def test_repr_ok(self):
        e = ReplayEntry(attempt=1, timestamp=0.0)
        assert "ok" in repr(e)

    def test_repr_err(self):
        e = ReplayEntry(attempt=2, timestamp=0.0, exception=RuntimeError("x"))
        assert "RuntimeError" in repr(e)


class TestRetryReplayLogInit:
    def test_valid_construction(self):
        log = RetryReplayLog(max_entries=10)
        assert len(log) == 0

    def test_zero_max_entries_raises(self):
        with pytest.raises(ValueError):
            RetryReplayLog(max_entries=0)

    def test_negative_max_entries_raises(self):
        with pytest.raises(ValueError):
            RetryReplayLog(max_entries=-1)


class TestRetryReplayLogRecord:
    def setup_method(self):
        self.log = RetryReplayLog()

    def test_record_adds_entry(self):
        self.log.record(1)
        assert len(self.log) == 1

    def test_record_exception(self):
        exc = ValueError("fail")
        self.log.record(1, exception=exc)
        assert self.log.last().exception is exc

    def test_record_result(self):
        self.log.record(1, result=42)
        assert self.log.last().result == 42

    def test_entries_returns_copy(self):
        self.log.record(1)
        entries = self.log.entries()
        entries.clear()
        assert len(self.log) == 1

    def test_last_returns_none_when_empty(self):
        assert self.log.last() is None

    def test_failures_filters_correctly(self):
        self.log.record(1)
        self.log.record(2, exception=RuntimeError())
        assert len(self.log.failures()) == 1

    def test_successes_filters_correctly(self):
        self.log.record(1)
        self.log.record(2, exception=RuntimeError())
        assert len(self.log.successes()) == 1

    def test_max_entries_evicts_oldest(self):
        log = RetryReplayLog(max_entries=3)
        for i in range(5):
            log.record(i)
        assert len(log) == 3
        assert log.entries()[0].attempt == 2

    def test_clear_empties_log(self):
        self.log.record(1)
        self.log.clear()
        assert len(self.log) == 0

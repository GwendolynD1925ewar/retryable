"""Tests for retryable.trace and retryable.trace_integration."""
from __future__ import annotations

import time
import pytest

from retryable.trace import TraceEntry, RetryTrace
from retryable.trace_integration import build_trace_on_retry, trace_predicate


class TestTraceEntry:
    def _make(self, attempt=1, elapsed=0.1, exception=None, result=None):
        return TraceEntry(attempt=attempt, started_at=time.monotonic() - elapsed, elapsed=elapsed, exception=exception, result=result)

    def test_succeeded_true_when_no_exception(self):
        assert self._make().succeeded is True

    def test_succeeded_false_when_exception(self):
        assert self._make(exception=ValueError("x")).succeeded is False

    def test_repr_ok(self):
        r = repr(self._make())
        assert "TraceEntry" in r
        assert "ok" in r

    def test_repr_err(self):
        r = repr(self._make(exception=RuntimeError("boom")))
        assert "err=" in r


class TestRetryTrace:
    def test_initial_state(self):
        t = RetryTrace()
        assert t.total_attempts == 0
        assert t.succeeded is False
        assert t.total_elapsed == 0.0
        assert t.failures == []

    def test_record_success(self):
        t = RetryTrace()
        t.record(attempt=1, started_at=time.monotonic() - 0.05)
        assert t.total_attempts == 1
        assert t.succeeded is True

    def test_record_failure(self):
        t = RetryTrace()
        t.record(attempt=1, started_at=time.monotonic() - 0.01, exception=ValueError("x"))
        assert t.succeeded is False
        assert len(t.failures) == 1

    def test_total_elapsed_sums_entries(self):
        t = RetryTrace()
        t.record(attempt=1, started_at=time.monotonic() - 0.1, exception=IOError())
        t.record(attempt=2, started_at=time.monotonic() - 0.2)
        assert t.total_elapsed >= 0.3

    def test_repr(self):
        t = RetryTrace()
        t.record(attempt=1, started_at=time.monotonic())
        assert "RetryTrace" in repr(t)


class TestBuildTraceOnRetry:
    def test_returns_on_retry_key(self):
        result = build_trace_on_retry()
        assert "on_retry" in result

    def test_returns_trace_instance(self):
        result = build_trace_on_retry()
        assert "trace" in result
        assert isinstance(result["trace"], RetryTrace)

    def test_uses_provided_trace(self):
        trace = RetryTrace()
        result = build_trace_on_retry(trace)
        assert result["trace"] is trace

    def test_on_retry_records_entry(self):
        trace = RetryTrace()
        result = build_trace_on_retry(trace)
        result["on_retry"](attempt=1, exception=ValueError("x"), result=None)
        assert trace.total_attempts == 1


class TestTracePredicate:
    def test_allows_when_under_limit(self):
        trace = RetryTrace()
        pred = trace_predicate(trace, max_failures=3)
        assert pred(attempt=1, exception=ValueError()) is True

    def test_blocks_when_limit_reached(self):
        trace = RetryTrace()
        for i in range(3):
            trace.record(attempt=i + 1, started_at=time.monotonic(), exception=IOError())
        pred = trace_predicate(trace, max_failures=3)
        assert pred(attempt=4, exception=IOError()) is False

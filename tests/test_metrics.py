"""Tests for retryable.metrics and retryable.metrics_hook."""
from __future__ import annotations

import pytest

from retryable.metrics import RetryMetrics, get_metrics, reset_all
from retryable.metrics_hook import make_tracked_hook, metrics_hook


class TestRetryMetrics:
    def setup_method(self):
        self.m = RetryMetrics()

    def test_initial_state(self):
        assert self.m.total_calls == 0
        assert self.m.total_attempts == 0
        assert self.m.total_successes == 0
        assert self.m.total_failures == 0
        assert self.m.total_retries == 0
        assert self.m.average_attempts is None

    def test_record_attempt_increments_counter(self):
        self.m.record_attempt()
        self.m.record_attempt()
        assert self.m.total_attempts == 2

    def test_record_call_success(self):
        self.m.record_call_result(attempts=1, succeeded=True)
        assert self.m.total_calls == 1
        assert self.m.total_successes == 1
        assert self.m.total_failures == 0
        assert self.m.total_retries == 0

    def test_record_call_failure(self):
        self.m.record_call_result(attempts=3, succeeded=False)
        assert self.m.total_calls == 1
        assert self.m.total_failures == 1
        assert self.m.total_retries == 2

    def test_average_attempts_single(self):
        self.m.record_call_result(attempts=2, succeeded=True)
        assert self.m.average_attempts == 2.0

    def test_average_attempts_multiple(self):
        self.m.record_call_result(attempts=1, succeeded=True)
        self.m.record_call_result(attempts=3, succeeded=True)
        assert self.m.average_attempts == 2.0

    def test_reset_clears_all(self):
        self.m.record_attempt()
        self.m.record_call_result(attempts=2, succeeded=True)
        self.m.reset()
        assert self.m.total_calls == 0
        assert self.m.total_attempts == 0
        assert self.m.average_attempts is None


class TestRegistry:
    def setup_method(self):
        reset_all()

    def test_get_metrics_returns_same_instance(self):
        a = get_metrics("svc")
        b = get_metrics("svc")
        assert a is b

    def test_different_names_return_different_instances(self):
        a = get_metrics("alpha")
        b = get_metrics("beta")
        assert a is not b

    def test_reset_all_clears_counts(self):
        m = get_metrics("x")
        m.record_attempt()
        reset_all()
        assert m.total_attempts == 0


class TestMetricsHook:
    def test_hook_records_attempt(self):
        m = RetryMetrics()
        hook = metrics_hook(metrics=m)
        hook(attempt=1, exception=ValueError("boom"))
        hook(attempt=2, exception=ValueError("boom"))
        assert m.total_attempts == 2

    def test_make_tracked_hook_calls_inner(self):
        m = RetryMetrics()
        calls = []
        inner = lambda attempt, exception=None, result=None: calls.append(attempt)
        hook = make_tracked_hook(metrics=m, inner_hook=inner)
        hook(attempt=1, exception=RuntimeError())
        assert m.total_attempts == 1
        assert calls == [1]

    def test_make_tracked_hook_without_inner(self):
        m = RetryMetrics()
        hook = make_tracked_hook(metrics=m)
        hook(attempt=1)
        assert m.total_attempts == 1

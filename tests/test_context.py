"""Tests for retryable.context."""
from __future__ import annotations

import time

import pytest

from retryable.context import RetryContext, build_context


class TestRetryContextProperties:
    def _make(self, attempt: int, max_attempts=None, **kwargs) -> RetryContext:
        return RetryContext(
            attempt=attempt,
            elapsed=0.0,
            delay=0.0,
            max_attempts=max_attempts,
            **kwargs,
        )

    def test_is_first_attempt_true_on_attempt_one(self):
        ctx = self._make(attempt=1)
        assert ctx.is_first_attempt is True

    def test_is_first_attempt_false_on_later_attempts(self):
        ctx = self._make(attempt=2)
        assert ctx.is_first_attempt is False

    def test_retry_number_is_zero_on_first_attempt(self):
        ctx = self._make(attempt=1)
        assert ctx.retry_number == 0

    def test_retry_number_increments_with_attempt(self):
        ctx = self._make(attempt=4)
        assert ctx.retry_number == 3

    def test_is_last_attempt_false_when_max_attempts_none(self):
        ctx = self._make(attempt=99, max_attempts=None)
        assert ctx.is_last_attempt is False

    def test_is_last_attempt_true_at_max(self):
        ctx = self._make(attempt=3, max_attempts=3)
        assert ctx.is_last_attempt is True

    def test_is_last_attempt_false_below_max(self):
        ctx = self._make(attempt=2, max_attempts=3)
        assert ctx.is_last_attempt is False

    def test_exception_defaults_to_none(self):
        ctx = self._make(attempt=1)
        assert ctx.exception is None

    def test_result_defaults_to_none(self):
        ctx = self._make(attempt=1)
        assert ctx.result is None

    def test_stores_exception(self):
        exc = ValueError("boom")
        ctx = self._make(attempt=2, exception=exc)
        assert ctx.exception is exc

    def test_stores_result(self):
        ctx = self._make(attempt=1, result=42)
        assert ctx.result == 42


class TestBuildContext:
    def test_elapsed_is_non_negative(self):
        start = time.monotonic()
        ctx = build_context(attempt=1, start_time=start)
        assert ctx.elapsed >= 0.0

    def test_elapsed_grows_over_time(self):
        start = time.monotonic() - 0.05  # simulate 50 ms already elapsed
        ctx = build_context(attempt=1, start_time=start)
        assert ctx.elapsed >= 0.05

    def test_attempt_is_set_correctly(self):
        ctx = build_context(attempt=3, start_time=time.monotonic())
        assert ctx.attempt == 3

    def test_delay_defaults_to_zero(self):
        ctx = build_context(attempt=1, start_time=time.monotonic())
        assert ctx.delay == 0.0

    def test_delay_is_forwarded(self):
        ctx = build_context(attempt=1, start_time=time.monotonic(), delay=1.5)
        assert ctx.delay == 1.5

    def test_max_attempts_forwarded(self):
        ctx = build_context(attempt=1, start_time=time.monotonic(), max_attempts=5)
        assert ctx.max_attempts == 5

    def test_exception_forwarded(self):
        exc = RuntimeError("oops")
        ctx = build_context(attempt=2, start_time=time.monotonic(), exception=exc)
        assert ctx.exception is exc

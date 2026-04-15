"""Tests for retryable.deadline and retryable.deadline_integration."""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from retryable.deadline import (
    AttemptDeadline,
    AttemptDeadlineExceeded,
    make_attempt_deadline,
)
from retryable.deadline_integration import (
    build_deadline_on_retry,
    deadline_predicate,
)


# ---------------------------------------------------------------------------
# AttemptDeadline
# ---------------------------------------------------------------------------

class TestAttemptDeadlineInit:
    def test_valid_construction(self):
        d = AttemptDeadline(seconds=1.0)
        assert d.seconds == 1.0

    def test_zero_raises(self):
        with pytest.raises(ValueError):
            AttemptDeadline(seconds=0)

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            AttemptDeadline(seconds=-5)


class TestAttemptDeadlineExpiry:
    def test_not_expired_immediately(self):
        d = AttemptDeadline(seconds=10.0)
        assert not d.expired

    def test_expired_after_deadline(self):
        with patch("retryable.deadline.time.monotonic", side_effect=[0.0, 5.0]):
            d = AttemptDeadline(seconds=2.0)
            assert d.expired

    def test_remaining_decreases(self):
        with patch("retryable.deadline.time.monotonic", side_effect=[0.0, 1.0]):
            d = AttemptDeadline(seconds=3.0)
            assert d.remaining == pytest.approx(2.0)

    def test_remaining_never_negative(self):
        with patch("retryable.deadline.time.monotonic", side_effect=[0.0, 99.0]):
            d = AttemptDeadline(seconds=1.0)
            assert d.remaining == 0.0

    def test_check_raises_when_expired(self):
        with patch("retryable.deadline.time.monotonic", side_effect=[0.0, 10.0]):
            d = AttemptDeadline(seconds=1.0)
            with pytest.raises(AttemptDeadlineExceeded) as exc_info:
                d.check()
        assert exc_info.value.deadline_seconds == 1.0

    def test_check_passes_when_within_deadline(self):
        with patch("retryable.deadline.time.monotonic", side_effect=[0.0, 0.1]):
            d = AttemptDeadline(seconds=5.0)
            d.check()  # should not raise


class TestMakeAttemptDeadline:
    def test_returns_none_for_none(self):
        assert make_attempt_deadline(None) is None

    def test_returns_deadline_for_positive_float(self):
        d = make_attempt_deadline(2.5)
        assert isinstance(d, AttemptDeadline)
        assert d.seconds == 2.5


# ---------------------------------------------------------------------------
# deadline_integration
# ---------------------------------------------------------------------------

class TestBuildDeadlineOnRetry:
    def test_hook_is_callable(self):
        hook = build_deadline_on_retry(1.0)
        assert callable(hook)

    def test_hook_creates_deadline_in_state(self):
        hook = build_deadline_on_retry(2.0)
        hook(attempt=1, exception=ValueError("boom"))
        assert hook._state["current"] is not None
        assert hook._state["current"].seconds == 2.0

    def test_hook_resets_deadline_each_call(self):
        hook = build_deadline_on_retry(1.0)
        hook(attempt=1)
        first = hook._state["current"]
        time.sleep(0.01)
        hook(attempt=2)
        second = hook._state["current"]
        assert second is not first


class TestDeadlinePredicate:
    def test_returns_false_for_matching_deadline_exceeded(self):
        pred = deadline_predicate(1.0)
        exc = AttemptDeadlineExceeded(deadline_seconds=1.0, elapsed=1.5)
        assert pred(exception=exc) is False

    def test_returns_true_for_non_deadline_exception(self):
        pred = deadline_predicate(1.0)
        assert pred(exception=ValueError("x")) is True

    def test_returns_false_for_no_exception(self):
        pred = deadline_predicate(1.0)
        assert pred(exception=None, result="ok") is False

    def test_ignores_deadline_with_different_seconds(self):
        pred = deadline_predicate(1.0)
        exc = AttemptDeadlineExceeded(deadline_seconds=5.0, elapsed=6.0)
        # different deadline — treated as a regular exception, so retry
        assert pred(exception=exc) is True

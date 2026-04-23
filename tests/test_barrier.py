"""Tests for retryable.barrier and retryable.barrier_integration."""
from __future__ import annotations

import time

import pytest

from retryable.barrier import BarrierBlocked, RetryBarrier
from retryable.barrier_integration import barrier_predicate, build_barrier_on_retry


# ---------------------------------------------------------------------------
# RetryBarrier — init validation
# ---------------------------------------------------------------------------

class TestRetryBarrierInit:
    def test_valid_construction(self):
        b = RetryBarrier(label="test")
        assert b.label == "test"
        assert b.auto_lower_after is None

    def test_valid_with_auto_lower(self):
        b = RetryBarrier(label="test", auto_lower_after=5.0)
        assert b.auto_lower_after == 5.0

    def test_empty_label_raises(self):
        with pytest.raises(ValueError, match="label"):
            RetryBarrier(label="")

    def test_blank_label_raises(self):
        with pytest.raises(ValueError, match="label"):
            RetryBarrier(label="   ")

    def test_zero_auto_lower_raises(self):
        with pytest.raises(ValueError, match="auto_lower_after"):
            RetryBarrier(label="x", auto_lower_after=0)

    def test_negative_auto_lower_raises(self):
        with pytest.raises(ValueError, match="auto_lower_after"):
            RetryBarrier(label="x", auto_lower_after=-1.0)


# ---------------------------------------------------------------------------
# RetryBarrier — raise / lower / check
# ---------------------------------------------------------------------------

class TestRetryBarrierBehaviour:
    def test_not_raised_by_default(self):
        b = RetryBarrier(label="x")
        assert not b.is_raised

    def test_raised_after_raise_barrier(self):
        b = RetryBarrier(label="x")
        b.raise_barrier()
        assert b.is_raised

    def test_lowered_after_lower(self):
        b = RetryBarrier(label="x")
        b.raise_barrier()
        b.lower()
        assert not b.is_raised

    def test_check_passes_when_lowered(self):
        b = RetryBarrier(label="x")
        b.check()  # should not raise

    def test_check_raises_when_raised(self):
        b = RetryBarrier(label="gate")
        b.raise_barrier()
        with pytest.raises(BarrierBlocked) as exc_info:
            b.check()
        assert "gate" in str(exc_info.value)

    def test_auto_lower_expires(self):
        b = RetryBarrier(label="x", auto_lower_after=0.05)
        b.raise_barrier()
        assert b.is_raised
        time.sleep(0.1)
        assert not b.is_raised


# ---------------------------------------------------------------------------
# barrier_integration
# ---------------------------------------------------------------------------

class TestBuildBarrierOnRetry:
    def test_returns_on_retry_key(self):
        result = build_barrier_on_retry("svc")
        assert "on_retry" in result

    def test_returns_barrier_instance(self):
        result = build_barrier_on_retry("svc")
        assert isinstance(result["barrier"], RetryBarrier)

    def test_hook_passes_when_barrier_lowered(self):
        result = build_barrier_on_retry("svc")
        hook = result["on_retry"]
        hook(None, None, 1)  # should not raise

    def test_hook_raises_when_barrier_raised(self):
        result = build_barrier_on_retry("svc")
        hook = result["on_retry"]
        barrier: RetryBarrier = result["barrier"]
        barrier.raise_barrier()
        with pytest.raises(BarrierBlocked):
            hook(None, None, 2)


class TestBarrierPredicate:
    def test_returns_true_when_lowered(self):
        b = RetryBarrier(label="x")
        pred = barrier_predicate(b)
        assert pred(None, None) is True

    def test_returns_false_when_raised(self):
        b = RetryBarrier(label="x")
        b.raise_barrier()
        pred = barrier_predicate(b)
        assert pred(None, None) is False

    def test_returns_true_after_lower(self):
        b = RetryBarrier(label="x")
        b.raise_barrier()
        b.lower()
        pred = barrier_predicate(b)
        assert pred(None, None) is True

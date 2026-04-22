"""Tests for retryable.runway and retryable.runway_integration."""

from __future__ import annotations

import pytest

from retryable.runway import RetryRunway, RunwayExhausted
from retryable.runway_integration import build_runway_on_retry, runway_predicate


# ---------------------------------------------------------------------------
# RetryRunway — initialisation
# ---------------------------------------------------------------------------

class TestRetryRunwayInit:
    def test_valid_construction(self):
        rw = RetryRunway(max_attempts=3)
        assert rw.max_attempts == 3

    def test_zero_max_attempts_raises(self):
        with pytest.raises(ValueError, match="max_attempts must be >= 1"):
            RetryRunway(max_attempts=0)

    def test_negative_max_attempts_raises(self):
        with pytest.raises(ValueError, match="max_attempts must be >= 1"):
            RetryRunway(max_attempts=-1)

    def test_initial_used_is_zero(self):
        assert RetryRunway(max_attempts=4).used == 0

    def test_initial_remaining_equals_max(self):
        rw = RetryRunway(max_attempts=4)
        assert rw.remaining == 4

    def test_not_exhausted_initially(self):
        assert not RetryRunway(max_attempts=2).exhausted


# ---------------------------------------------------------------------------
# RetryRunway — consume
# ---------------------------------------------------------------------------

class TestRetryRunwayConsume:
    def test_consume_decrements_remaining(self):
        rw = RetryRunway(max_attempts=3)
        rw.consume()
        assert rw.remaining == 2

    def test_consume_increments_used(self):
        rw = RetryRunway(max_attempts=3)
        rw.consume()
        assert rw.used == 1

    def test_exhausted_after_all_consumed(self):
        rw = RetryRunway(max_attempts=2)
        rw.consume()
        rw.consume()
        assert rw.exhausted

    def test_remaining_never_negative(self):
        rw = RetryRunway(max_attempts=1)
        rw.consume()
        # exhausted; remaining should be 0, not negative
        assert rw.remaining == 0

    def test_consume_when_exhausted_raises(self):
        rw = RetryRunway(max_attempts=1)
        rw.consume()
        with pytest.raises(RunwayExhausted):
            rw.consume()

    def test_runway_exhausted_message(self):
        rw = RetryRunway(max_attempts=2)
        rw.consume()
        rw.consume()
        with pytest.raises(RunwayExhausted, match="2 attempt"):
            rw.consume()


# ---------------------------------------------------------------------------
# RetryRunway — fraction_used and reset
# ---------------------------------------------------------------------------

class TestRetryRunwayFraction:
    def test_fraction_zero_initially(self):
        assert RetryRunway(max_attempts=4).fraction_used == 0.0

    def test_fraction_half_after_half_consumed(self):
        rw = RetryRunway(max_attempts=4)
        rw.consume()
        rw.consume()
        assert rw.fraction_used == 0.5

    def test_fraction_one_when_exhausted(self):
        rw = RetryRunway(max_attempts=2)
        rw.consume()
        rw.consume()
        assert rw.fraction_used == 1.0

    def test_reset_restores_state(self):
        rw = RetryRunway(max_attempts=3)
        rw.consume()
        rw.consume()
        rw.reset()
        assert rw.used == 0
        assert rw.remaining == 3
        assert not rw.exhausted


# ---------------------------------------------------------------------------
# Integration helpers
# ---------------------------------------------------------------------------

class TestBuildRunwayOnRetry:
    def test_returns_on_retry_key(self):
        rw = RetryRunway(max_attempts=3)
        result = build_runway_on_retry(rw)
        assert "on_retry" in result

    def test_returns_runway_instance(self):
        rw = RetryRunway(max_attempts=3)
        result = build_runway_on_retry(rw)
        assert result["runway"] is rw

    def test_on_retry_is_callable(self):
        rw = RetryRunway(max_attempts=3)
        result = build_runway_on_retry(rw)
        assert callable(result["on_retry"])

    def test_hook_consumes_runway(self):
        rw = RetryRunway(max_attempts=3)
        hook = build_runway_on_retry(rw)["on_retry"]
        hook(attempt=1)
        assert rw.used == 1

    def test_runway_predicate_true_when_not_exhausted(self):
        rw = RetryRunway(max_attempts=3)
        pred = runway_predicate(rw)
        assert pred(attempt=1) is True

    def test_runway_predicate_false_when_exhausted(self):
        rw = RetryRunway(max_attempts=1)
        rw.consume()
        pred = runway_predicate(rw)
        assert pred(attempt=1) is False

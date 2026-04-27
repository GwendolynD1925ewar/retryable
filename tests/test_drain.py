"""Tests for retryable.drain and retryable.drain_integration."""
from __future__ import annotations

import pytest

from retryable.drain import DrainExhausted, RetryDrain
from retryable.drain_integration import build_drain_on_retry, drain_predicate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _ManualClock:
    def __init__(self, t: float = 0.0) -> None:
        self._t = t

    def __call__(self) -> float:
        return self._t

    def advance(self, seconds: float) -> None:
        self._t += seconds


# ---------------------------------------------------------------------------
# RetryDrain — init validation
# ---------------------------------------------------------------------------

class TestRetryDrainInit:
    def test_valid_construction(self):
        d = RetryDrain(capacity=10.0, refill_rate=1.0)
        assert d.capacity == 10.0
        assert d.refill_rate == 1.0

    def test_zero_capacity_raises(self):
        with pytest.raises(ValueError, match="capacity"):
            RetryDrain(capacity=0, refill_rate=1.0)

    def test_negative_capacity_raises(self):
        with pytest.raises(ValueError, match="capacity"):
            RetryDrain(capacity=-1, refill_rate=1.0)

    def test_zero_refill_rate_raises(self):
        with pytest.raises(ValueError, match="refill_rate"):
            RetryDrain(capacity=5, refill_rate=0)

    def test_negative_refill_rate_raises(self):
        with pytest.raises(ValueError, match="refill_rate"):
            RetryDrain(capacity=5, refill_rate=-0.5)


# ---------------------------------------------------------------------------
# RetryDrain — acquire / available
# ---------------------------------------------------------------------------

class TestRetryDrainAcquire:
    def _make(self, capacity: float = 5.0, refill_rate: float = 1.0) -> tuple[RetryDrain, _ManualClock]:
        clock = _ManualClock()
        drain = RetryDrain(capacity=capacity, refill_rate=refill_rate, clock=clock)
        return drain, clock

    def test_initial_available_equals_capacity(self):
        drain, _ = self._make(capacity=5.0)
        assert drain.available == pytest.approx(5.0)

    def test_acquire_reduces_available(self):
        drain, _ = self._make(capacity=5.0)
        drain.acquire(2.0)
        assert drain.available == pytest.approx(3.0)

    def test_acquire_exhausted_raises(self):
        drain, _ = self._make(capacity=2.0)
        drain.acquire(2.0)
        with pytest.raises(DrainExhausted):
            drain.acquire(1.0)

    def test_drain_exhausted_stores_available(self):
        drain, _ = self._make(capacity=1.0)
        drain.acquire(1.0)
        with pytest.raises(DrainExhausted) as exc_info:
            drain.acquire(1.0)
        assert exc_info.value.available == pytest.approx(0.0)
        assert exc_info.value.required == pytest.approx(1.0)

    def test_zero_token_acquire_raises(self):
        drain, _ = self._make()
        with pytest.raises(ValueError, match="tokens"):
            drain.acquire(0)

    def test_refill_over_time(self):
        drain, clock = self._make(capacity=5.0, refill_rate=2.0)
        drain.acquire(4.0)  # 1 token left
        clock.advance(1.5)  # +3 tokens → capped at 5
        assert drain.available == pytest.approx(4.0)  # 1 + 3

    def test_refill_capped_at_capacity(self):
        drain, clock = self._make(capacity=3.0, refill_rate=10.0)
        drain.acquire(1.0)
        clock.advance(5.0)  # would add 50 tokens, capped at 3
        assert drain.available == pytest.approx(3.0)

    def test_reset_restores_full_capacity(self):
        drain, _ = self._make(capacity=4.0)
        drain.acquire(4.0)
        drain.reset()
        assert drain.available == pytest.approx(4.0)


# ---------------------------------------------------------------------------
# Integration helpers
# ---------------------------------------------------------------------------

class TestBuildDrainOnRetry:
    def test_returns_on_retry_key(self):
        result = build_drain_on_retry(capacity=5, refill_rate=1.0)
        assert "on_retry" in result

    def test_returns_drain_instance(self):
        result = build_drain_on_retry(capacity=5, refill_rate=1.0)
        assert isinstance(result["drain"], RetryDrain)

    def test_on_retry_is_callable(self):
        result = build_drain_on_retry(capacity=5, refill_rate=1.0)
        assert callable(result["on_retry"])

    def test_hook_consumes_token(self):
        result = build_drain_on_retry(capacity=3, refill_rate=1.0)
        drain: RetryDrain = result["drain"]
        hook = result["on_retry"]
        hook(attempt=1)
        assert drain.available == pytest.approx(2.0)

    def test_hook_raises_when_exhausted(self):
        result = build_drain_on_retry(capacity=1, refill_rate=1.0)
        hook = result["on_retry"]
        hook(attempt=1)  # consumes the only token
        with pytest.raises(DrainExhausted):
            hook(attempt=2)


class TestDrainPredicate:
    def _make_drain(self, capacity: float = 5.0) -> RetryDrain:
        clock = _ManualClock()
        return RetryDrain(capacity=capacity, refill_rate=1.0, clock=clock)

    def test_allows_when_tokens_available(self):
        drain = self._make_drain(5.0)
        pred = drain_predicate(drain)
        assert pred(attempt=1) is True

    def test_blocks_when_exhausted(self):
        drain = self._make_drain(1.0)
        drain.acquire(1.0)
        pred = drain_predicate(drain)
        assert pred(attempt=2) is False

    def test_respects_custom_cost(self):
        drain = self._make_drain(1.5)
        pred = drain_predicate(drain, cost=2.0)
        assert pred(attempt=1) is False  # 1.5 < 2.0

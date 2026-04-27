"""Tests for retryable.slot_integration."""
import pytest
from retryable.slot import RetrySlot, SlotUnavailable
from retryable.slot_integration import build_slot_on_retry, slot_predicate


class TestBuildSlotOnRetry:
    def test_returns_on_retry_key(self):
        result = build_slot_on_retry(capacity=2)
        assert "on_retry" in result

    def test_returns_slot_instance(self):
        result = build_slot_on_retry(capacity=2)
        assert "slot" in result
        assert isinstance(result["slot"], RetrySlot)

    def test_slot_capacity_is_set(self):
        result = build_slot_on_retry(capacity=5)
        assert result["slot"].capacity == 5

    def test_on_retry_is_callable(self):
        result = build_slot_on_retry(capacity=2)
        assert callable(result["on_retry"])

    def test_on_retry_acquires_slot(self):
        result = build_slot_on_retry(capacity=2)
        hook = result["on_retry"]
        slot: RetrySlot = result["slot"]
        # First call: releases 0 (noop) then acquires 1
        hook(attempt=1)
        assert slot.occupied == 1

    def test_on_retry_releases_before_reacquire(self):
        result = build_slot_on_retry(capacity=1)
        hook = result["on_retry"]
        slot: RetrySlot = result["slot"]
        hook(attempt=1)  # occupied → 1
        hook(attempt=2)  # releases 1 → 0, then acquires → 1 again
        assert slot.occupied == 1

    def test_on_retry_raises_when_pool_full(self):
        result = build_slot_on_retry(capacity=1)
        hook = result["on_retry"]
        slot: RetrySlot = result["slot"]
        # Manually fill the pool from outside
        slot.acquire()
        with pytest.raises(SlotUnavailable):
            hook(attempt=2)  # release frees nothing (occupied by external); re-acquire fails


class TestSlotPredicate:
    def test_returns_true_when_slots_available(self):
        slot = RetrySlot(capacity=3)
        pred = slot_predicate(slot)
        assert pred(attempt=1) is True

    def test_returns_false_when_pool_full(self):
        slot = RetrySlot(capacity=1)
        slot.acquire()
        pred = slot_predicate(slot)
        assert pred(attempt=2) is False

    def test_returns_true_after_slot_released(self):
        slot = RetrySlot(capacity=1)
        slot.acquire()
        pred = slot_predicate(slot)
        slot.release()
        assert pred(attempt=2) is True

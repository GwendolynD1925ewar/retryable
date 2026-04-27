"""Tests for retryable.slot."""
import pytest
from retryable.slot import RetrySlot, SlotUnavailable


class TestRetrySlotInit:
    def test_valid_construction(self):
        s = RetrySlot(capacity=3)
        assert s.capacity == 3

    def test_zero_capacity_raises(self):
        with pytest.raises(ValueError, match="capacity must be >= 1"):
            RetrySlot(capacity=0)

    def test_negative_capacity_raises(self):
        with pytest.raises(ValueError, match="capacity must be >= 1"):
            RetrySlot(capacity=-1)

    def test_initial_occupied_is_zero(self):
        s = RetrySlot(capacity=2)
        assert s.occupied == 0

    def test_initial_available_equals_capacity(self):
        s = RetrySlot(capacity=4)
        assert s.available == 4


class TestRetrySlotAcquire:
    def test_acquire_decrements_available(self):
        s = RetrySlot(capacity=2)
        s.acquire()
        assert s.available == 1
        assert s.occupied == 1

    def test_acquire_fills_pool(self):
        s = RetrySlot(capacity=2)
        s.acquire()
        s.acquire()
        assert s.available == 0
        assert s.occupied == 2

    def test_acquire_beyond_capacity_raises(self):
        s = RetrySlot(capacity=1)
        s.acquire()
        with pytest.raises(SlotUnavailable) as exc_info:
            s.acquire()
        assert exc_info.value.capacity == 1

    def test_slot_unavailable_message(self):
        s = RetrySlot(capacity=2)
        s.acquire()
        s.acquire()
        with pytest.raises(SlotUnavailable, match="All 2 retry slot"):
            s.acquire()


class TestRetrySlotRelease:
    def test_release_increments_available(self):
        s = RetrySlot(capacity=2)
        s.acquire()
        s.release()
        assert s.available == 2

    def test_release_when_empty_is_noop(self):
        s = RetrySlot(capacity=2)
        s.release()  # should not raise
        assert s.available == 2

    def test_acquire_after_release_succeeds(self):
        s = RetrySlot(capacity=1)
        s.acquire()
        s.release()
        s.acquire()  # must not raise
        assert s.occupied == 1


class TestRetrySlotReset:
    def test_reset_clears_all_slots(self):
        s = RetrySlot(capacity=3)
        s.acquire()
        s.acquire()
        s.reset()
        assert s.occupied == 0
        assert s.available == 3

    def test_acquire_after_reset_succeeds(self):
        s = RetrySlot(capacity=1)
        s.acquire()
        s.reset()
        s.acquire()  # must not raise
        assert s.occupied == 1

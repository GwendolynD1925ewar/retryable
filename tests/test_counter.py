"""Tests for retryable.counter."""
import pytest
from retryable.counter import RetryCounter, CounterCapExceeded


class TestRetryCounterInit:
    def test_valid_construction(self):
        c = RetryCounter()
        assert c.cap is None

    def test_valid_construction_with_cap(self):
        c = RetryCounter(cap=5)
        assert c.cap == 5

    def test_zero_cap_raises(self):
        with pytest.raises(ValueError):
            RetryCounter(cap=0)

    def test_negative_cap_raises(self):
        with pytest.raises(ValueError):
            RetryCounter(cap=-1)


class TestRetryCounterIncrement:
    def test_first_increment_returns_one(self):
        c = RetryCounter()
        assert c.increment("svc") == 1

    def test_subsequent_increments_accumulate(self):
        c = RetryCounter()
        c.increment("svc")
        c.increment("svc")
        assert c.increment("svc") == 3

    def test_different_keys_tracked_independently(self):
        c = RetryCounter()
        c.increment("a")
        c.increment("a")
        c.increment("b")
        assert c.get("a") == 2
        assert c.get("b") == 1

    def test_cap_not_exceeded_at_limit(self):
        c = RetryCounter(cap=3)
        for _ in range(3):
            c.increment("x")
        assert c.get("x") == 3

    def test_cap_exceeded_raises(self):
        c = RetryCounter(cap=2)
        c.increment("x")
        c.increment("x")
        with pytest.raises(CounterCapExceeded) as exc_info:
            c.increment("x")
        assert exc_info.value.key == "x"
        assert exc_info.value.cap == 2


class TestRetryCounterReset:
    def test_reset_clears_single_key(self):
        c = RetryCounter()
        c.increment("a")
        c.reset("a")
        assert c.get("a") == 0

    def test_reset_nonexistent_key_is_safe(self):
        c = RetryCounter()
        c.reset("missing")  # should not raise

    def test_reset_all_clears_everything(self):
        c = RetryCounter()
        c.increment("a")
        c.increment("b")
        c.reset_all()
        assert c.get("a") == 0
        assert c.get("b") == 0
        assert c.keys() == []


class TestRetryCounterRepr:
    def test_repr_contains_cap(self):
        c = RetryCounter(cap=10)
        assert "cap=10" in repr(c)

    def test_repr_contains_tracked_keys_count(self):
        c = RetryCounter()
        c.increment("a")
        c.increment("b")
        assert "tracked_keys=2" in repr(c)

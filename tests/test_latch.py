"""Tests for retryable.latch."""
import pytest

from retryable.latch import LatchTripped, RetryLatch


class TestRetryLatchInit:
    def test_valid_construction(self):
        latch = RetryLatch(label="my-latch")
        assert latch.label == "my-latch"

    def test_default_label(self):
        latch = RetryLatch()
        assert latch.label == "default"

    def test_empty_label_raises(self):
        with pytest.raises(ValueError):
            RetryLatch(label="")

    def test_blank_label_raises(self):
        with pytest.raises(ValueError):
            RetryLatch(label="   ")

    def test_initially_not_tripped(self):
        latch = RetryLatch()
        assert latch.tripped is False

    def test_initial_reason_is_empty(self):
        latch = RetryLatch()
        assert latch.reason == ""


class TestRetryLatchTrip:
    def test_trip_sets_tripped(self):
        latch = RetryLatch()
        latch.trip()
        assert latch.tripped is True

    def test_trip_stores_reason(self):
        latch = RetryLatch()
        latch.trip(reason="too many errors")
        assert latch.reason == "too many errors"

    def test_trip_without_reason(self):
        latch = RetryLatch()
        latch.trip()
        assert latch.reason == ""

    def test_trip_is_idempotent(self):
        latch = RetryLatch()
        latch.trip(reason="first")
        latch.trip(reason="second")
        assert latch.tripped is True
        assert latch.reason == "second"


class TestRetryLatchCheck:
    def test_check_does_not_raise_when_not_tripped(self):
        latch = RetryLatch()
        latch.check()  # should not raise

    def test_check_raises_when_tripped(self):
        latch = RetryLatch()
        latch.trip(reason="overloaded")
        with pytest.raises(LatchTripped) as exc_info:
            latch.check()
        assert "overloaded" in str(exc_info.value)

    def test_check_raises_latch_tripped_type(self):
        latch = RetryLatch()
        latch.trip()
        with pytest.raises(LatchTripped):
            latch.check()

    def test_latch_tripped_reason_attribute(self):
        err = LatchTripped(reason="timeout")
        assert err.reason == "timeout"

    def test_latch_tripped_empty_reason(self):
        err = LatchTripped()
        assert err.reason == ""
        assert "Latch tripped" in str(err)


class TestRetryLatchReset:
    def test_reset_clears_tripped(self):
        latch = RetryLatch()
        latch.trip(reason="x")
        latch.reset()
        assert latch.tripped is False

    def test_reset_clears_reason(self):
        latch = RetryLatch()
        latch.trip(reason="x")
        latch.reset()
        assert latch.reason == ""

    def test_check_passes_after_reset(self):
        latch = RetryLatch()
        latch.trip()
        latch.reset()
        latch.check()  # should not raise


class TestRetryLatchRepr:
    def test_repr_not_tripped(self):
        latch = RetryLatch(label="gate")
        r = repr(latch)
        assert "gate" in r
        assert "False" in r

    def test_repr_tripped_with_reason(self):
        latch = RetryLatch(label="gate")
        latch.trip(reason="overload")
        r = repr(latch)
        assert "overload" in r
        assert "True" in r

"""Tests for RetryFence."""
import threading
import pytest
from retryable.fence import RetryFence, FenceExhausted


class TestRetryFenceInit:
    def test_valid_construction(self):
        f = RetryFence(max_concurrent=3)
        assert f.max_concurrent == 3

    def test_zero_max_concurrent_raises(self):
        with pytest.raises(ValueError, match="positive integer"):
            RetryFence(max_concurrent=0)

    def test_negative_max_concurrent_raises(self):
        with pytest.raises(ValueError, match="positive integer"):
            RetryFence(max_concurrent=-1)


class TestRetryFenceAcquire:
    def test_acquire_increments_active(self):
        f = RetryFence(max_concurrent=2)
        f.acquire()
        assert f.active == 1

    def test_acquire_up_to_limit(self):
        f = RetryFence(max_concurrent=2)
        f.acquire()
        f.acquire()
        assert f.active == 2

    def test_acquire_beyond_limit_raises(self):
        f = RetryFence(max_concurrent=1)
        f.acquire()
        with pytest.raises(FenceExhausted) as exc_info:
            f.acquire()
        assert exc_info.value.limit == 1

    def test_fence_exhausted_message(self):
        f = RetryFence(max_concurrent=2)
        f.acquire()
        f.acquire()
        with pytest.raises(FenceExhausted, match="max 2 concurrent"):
            f.acquire()


class TestRetryFenceRelease:
    def test_release_decrements_active(self):
        f = RetryFence(max_concurrent=2)
        f.acquire()
        f.release()
        assert f.active == 0

    def test_release_below_zero_is_safe(self):
        f = RetryFence(max_concurrent=2)
        f.release()  # no error
        assert f.active == 0

    def test_acquire_after_release_succeeds(self):
        f = RetryFence(max_concurrent=1)
        f.acquire()
        f.release()
        f.acquire()  # should not raise
        assert f.active == 1


class TestRetryFenceAvailable:
    def test_available_starts_at_max(self):
        f = RetryFence(max_concurrent=3)
        assert f.available == 3

    def test_available_decreases_on_acquire(self):
        f = RetryFence(max_concurrent=3)
        f.acquire()
        assert f.available == 2

    def test_available_increases_on_release(self):
        f = RetryFence(max_concurrent=3)
        f.acquire()
        f.acquire()
        f.release()
        assert f.available == 2


class TestRetryFenceThreadSafety:
    def test_concurrent_acquires_respect_limit(self):
        f = RetryFence(max_concurrent=5)
        errors = []

        def task():
            try:
                f.acquire()
            except FenceExhausted as e:
                errors.append(e)

        threads = [threading.Thread(target=task) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert f.active <= 5
        assert len(errors) == 5

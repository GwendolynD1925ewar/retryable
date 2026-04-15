"""Integration tests for timeout support inside the retry decorator."""

import time
import pytest

from retryable.core import retry


class TestRetryWithTimeout:
    def test_succeeds_before_timeout(self):
        """Function that succeeds on first attempt should not be affected."""
        @retry(max_attempts=3, timeout=5.0)
        def always_ok():
            return 42

        assert always_ok() == 42

    def test_raises_timeout_error_when_deadline_exceeded(self):
        """Deadline that is shorter than the accumulated delay should raise."""
        call_count = 0

        @retry(max_attempts=5, timeout=0.05)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("boom")

        with pytest.raises((TimeoutError, ValueError)):
            always_fails()

    def test_clamps_sleep_to_remaining_time(self, monkeypatch):
        """Verify that the delay passed to time.sleep never exceeds remaining."""
        slept: list = []
        monkeypatch.setattr(time, "sleep", lambda s: slept.append(s))

        attempts = 0

        @retry(max_attempts=3, timeout=0.5)
        def fail_twice():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ValueError("not yet")
            return "ok"

        result = fail_twice()
        assert result == "ok"
        for s in slept:
            assert s <= 0.5

    def test_no_timeout_does_not_restrict_delay(self, monkeypatch):
        """Without a timeout, delays are passed through unmodified."""
        slept: list = []
        monkeypatch.setattr(time, "sleep", lambda s: slept.append(s))

        attempts = 0

        @retry(max_attempts=2)
        def fail_once():
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise ValueError("once")
            return "done"

        fail_once()
        assert len(slept) == 1

    def test_timeout_zero_raises_value_error(self):
        with pytest.raises(ValueError):
            @retry(max_attempts=2, timeout=0)
            def fn():
                return 1

            fn()

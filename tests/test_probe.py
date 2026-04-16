"""Tests for retryable.probe."""
import pytest
from unittest.mock import MagicMock, patch

from retryable.probe import ProbeUnavailable, RetryProbe


class TestRetryProbeInit:
    def test_valid_construction(self):
        p = RetryProbe(check=lambda: True, timeout=2.0, interval=0.1)
        assert p.timeout == 2.0
        assert p.interval == 0.1

    def test_zero_timeout_raises(self):
        with pytest.raises(ValueError, match="timeout"):
            RetryProbe(check=lambda: True, timeout=0)

    def test_negative_timeout_raises(self):
        with pytest.raises(ValueError, match="timeout"):
            RetryProbe(check=lambda: True, timeout=-1)

    def test_zero_interval_raises(self):
        with pytest.raises(ValueError, match="interval"):
            RetryProbe(check=lambda: True, interval=0)

    def test_interval_exceeds_timeout_raises(self):
        with pytest.raises(ValueError, match="interval"):
            RetryProbe(check=lambda: True, timeout=1.0, interval=2.0)


class TestRetryProbeAvailable:
    def test_returns_true_when_check_succeeds_immediately(self):
        p = RetryProbe(check=lambda: True, timeout=1.0, interval=0.1)
        assert p.available() is True

    def test_returns_false_when_check_always_fails(self):
        p = RetryProbe(check=lambda: False, timeout=0.2, interval=0.05)
        assert p.available() is False

    def test_last_result_updated_on_success(self):
        p = RetryProbe(check=lambda: True, timeout=1.0, interval=0.1)
        p.available()
        assert p.last_result is True

    def test_last_result_updated_on_failure(self):
        p = RetryProbe(check=lambda: False, timeout=0.2, interval=0.05)
        p.available()
        assert p.last_result is False

    def test_check_exception_treated_as_unavailable(self):
        def bad_check():
            raise RuntimeError("network down")

        p = RetryProbe(check=bad_check, timeout=0.2, interval=0.05)
        assert p.available() is False

    def test_succeeds_on_second_poll(self):
        calls = iter([False, True])
        p = RetryProbe(check=lambda: next(calls), timeout=1.0, interval=0.01)
        assert p.available() is True


class TestProbeUnavailable:
    def test_default_message(self):
        err = ProbeUnavailable()
        assert "unavailable" in str(err)

    def test_custom_message(self):
        err = ProbeUnavailable("custom")
        assert str(err) == "custom"

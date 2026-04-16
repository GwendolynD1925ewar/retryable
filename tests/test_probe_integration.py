"""Tests for retryable.probe_integration."""
import pytest
from unittest.mock import MagicMock

from retryable.probe import ProbeUnavailable, RetryProbe
from retryable.probe_integration import (
    build_probe_on_retry,
    probe_predicate,
    _make_probe_hook,
)


class TestBuildProbeOnRetry:
    def test_returns_on_retry_key(self):
        probe = RetryProbe(check=lambda: True)
        result = build_probe_on_retry(probe)
        assert "on_retry" in result

    def test_on_retry_is_callable(self):
        probe = RetryProbe(check=lambda: True)
        result = build_probe_on_retry(probe)
        assert callable(result["on_retry"])


class TestMakeProbeHook:
    def test_does_not_raise_when_probe_available(self):
        probe = RetryProbe(check=lambda: True)
        hook = _make_probe_hook(probe)
        hook(attempt=1, exception=RuntimeError("x"))

    def test_raises_probe_unavailable_when_probe_fails(self):
        probe = RetryProbe(check=lambda: False, timeout=0.1, interval=0.02)
        hook = _make_probe_hook(probe)
        with pytest.raises(ProbeUnavailable):
            hook(attempt=1, exception=RuntimeError("x"))


class TestProbePredicate:
    def test_returns_true_when_probe_available_and_exception_present(self):
        probe = RetryProbe(check=lambda: True)
        pred = probe_predicate(probe)
        assert pred(attempt=1, exception=RuntimeError()) is True

    def test_returns_false_when_no_exception(self):
        probe = RetryProbe(check=lambda: True)
        pred = probe_predicate(probe)
        assert pred(attempt=1, exception=None, result="ok") is False

    def test_returns_false_when_probe_unavailable(self):
        probe = RetryProbe(check=lambda: False, timeout=0.1, interval=0.02)
        pred = probe_predicate(probe)
        assert pred(attempt=1, exception=RuntimeError()) is False

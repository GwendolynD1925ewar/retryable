"""Tests for retryable.hooks."""
import logging
import pytest
from unittest.mock import MagicMock, call, patch

from retryable.hooks import on_retry, log_retry, composite_hook


class TestOnRetry:
    def test_default_hook_returns_none(self):
        assert on_retry(attempt=1, delay=0.5) is None

    def test_default_hook_accepts_exception(self):
        assert on_retry(attempt=2, delay=1.0, exception=ValueError("boom")) is None

    def test_default_hook_accepts_result(self):
        assert on_retry(attempt=1, delay=0.0, result=42) is None


class TestLogRetry:
    def _make_logger(self):
        logger = MagicMock(spec=logging.Logger)
        logger.warning = MagicMock()
        logger.error = MagicMock()
        return logger

    def test_logs_exception_at_warning_by_default(self):
        logger = self._make_logger()
        hook = log_retry(logger)
        exc = RuntimeError("fail")
        hook(attempt=1, delay=0.25, exception=exc)
        logger.warning.assert_called_once()
        args = logger.warning.call_args[0]
        assert 1 in args
        assert exc in args
        assert 0.25 in args

    def test_logs_result_when_no_exception(self):
        logger = self._make_logger()
        hook = log_retry(logger)
        hook(attempt=2, delay=0.5, result="bad_value")
        logger.warning.assert_called_once()
        args = logger.warning.call_args[0]
        assert "bad_value" in args

    def test_custom_log_level(self):
        logger = self._make_logger()
        hook = log_retry(logger, level="error")
        hook(attempt=3, delay=1.0, exception=ValueError("x"))
        logger.error.assert_called_once()
        logger.warning.assert_not_called()

    def test_multiple_calls_log_each_attempt(self):
        logger = self._make_logger()
        hook = log_retry(logger)
        hook(attempt=1, delay=0.1, exception=IOError())
        hook(attempt=2, delay=0.2, exception=IOError())
        assert logger.warning.call_count == 2


class TestCompositeHook:
    def test_calls_all_hooks(self):
        h1 = MagicMock()
        h2 = MagicMock()
        hook = composite_hook(h1, h2)
        hook(attempt=1, delay=0.1, exception=ValueError())
        h1.assert_called_once()
        h2.assert_called_once()

    def test_calls_hooks_in_order(self):
        order = []
        hook = composite_hook(
            lambda **kw: order.append("first"),
            lambda **kw: order.append("second"),
        )
        hook(attempt=1, delay=0.0)
        assert order == ["first", "second"]

    def test_suppresses_exception_in_hook(self):
        bad_hook = MagicMock(side_effect=RuntimeError("hook exploded"))
        good_hook = MagicMock()
        hook = composite_hook(bad_hook, good_hook)
        # Should not raise
        hook(attempt=1, delay=0.0)
        good_hook.assert_called_once()

    def test_empty_composite_is_noop(self):
        hook = composite_hook()
        assert hook(attempt=1, delay=0.0) is None

"""Tests for retryable.fallback."""

from __future__ import annotations

import pytest

from retryable.fallback import (
    FallbackResult,
    apply_fallback,
    build_fallback_hook,
    callable_fallback,
    raise_fallback,
    static_fallback,
)


class TestStaticFallback:
    def test_returns_fallback_result(self):
        fb = static_fallback(42)
        result = fb()
        assert isinstance(result, FallbackResult)

    def test_value_is_preserved(self):
        fb = static_fallback("hello")
        assert fb().value == "hello"

    def test_ignores_positional_args(self):
        fb = static_fallback(99)
        assert fb(1, 2, 3).value == 99

    def test_ignores_keyword_args(self):
        fb = static_fallback(None)
        assert fb(x=1).value is None


class TestRaiseFallback:
    def test_raises_given_exception(self):
        exc = ValueError("boom")
        fb = raise_fallback(exc)
        with pytest.raises(ValueError, match="boom"):
            fb()

    def test_raises_on_any_call(self):
        fb = raise_fallback(RuntimeError("err"))
        with pytest.raises(RuntimeError):
            fb(a=1)


class TestCallableFallback:
    def test_calls_wrapped_function(self):
        called_with = {}

        def inner(x, y):
            called_with["x"] = x
            called_with["y"] = y
            return x + y

        fb = callable_fallback(inner)
        result = fb(3, 4)
        assert result.value == 7
        assert called_with == {"x": 3, "y": 4}

    def test_pass_exception_true_forwards_exception(self):
        received = {}

        def inner(exception=None):
            received["exc"] = exception
            return "ok"

        exc = TypeError("oops")
        fb = callable_fallback(inner, pass_exception=True)
        fb(_last_exception=exc)
        assert received["exc"] is exc

    def test_pass_exception_false_does_not_forward(self):
        def inner():
            return "safe"

        fb = callable_fallback(inner, pass_exception=False)
        result = fb(_last_exception=RuntimeError("ignored"))
        assert result.value == "safe"


class TestBuildFallbackHook:
    def test_hook_is_callable(self):
        fb = static_fallback(0)
        hook = build_fallback_hook(fb)
        assert callable(hook)

    def test_hook_carries_fallback_attribute(self):
        fb = static_fallback(1)
        hook = build_fallback_hook(fb)
        assert hook.__retryable_fallback__ is fb  # type: ignore[attr-defined]

    def test_default_flags(self):
        hook = build_fallback_hook(static_fallback(None))
        assert hook.__retryable_fallback_on_exception__ is True  # type: ignore[attr-defined]
        assert hook.__retryable_fallback_on_result__ is False  # type: ignore[attr-defined]

    def test_custom_flags(self):
        hook = build_fallback_hook(static_fallback(None), on_exception=False, on_result=True)
        assert hook.__retryable_fallback_on_exception__ is False  # type: ignore[attr-defined]
        assert hook.__retryable_fallback_on_result__ is True  # type: ignore[attr-defined]


class TestApplyFallback:
    def test_returns_static_value(self):
        hook = build_fallback_hook(static_fallback("default"))
        value = apply_fallback(hook, (), {})
        assert value == "default"

    def test_raises_when_no_fallback_attached(self):
        def plain_hook(attempt, exception=None, result=None):
            pass

        with pytest.raises(AttributeError):
            apply_fallback(plain_hook, (), {})

    def test_last_exception_forwarded_to_callable_fallback(self):
        received = {}

        def inner(exception=None):
            received["exc"] = exception
            return "recovered"

        hook = build_fallback_hook(callable_fallback(inner, pass_exception=True))
        exc = ValueError("original")
        value = apply_fallback(hook, (), {}, last_exception=exc)
        assert value == "recovered"
        assert received["exc"] is exc

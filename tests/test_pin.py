"""Tests for retryable.pin and retryable.pin_integration."""
import pytest

from retryable.pin import RetryPin, make_pin
from retryable.pin_integration import build_pin_on_retry, pin_predicate


class TestRetryPinInit:
    def test_starts_empty(self):
        pin = RetryPin()
        assert pin.as_dict() == {}

    def test_empty_key_raises(self):
        pin = RetryPin()
        with pytest.raises(ValueError):
            pin.set("", "value")

    def test_blank_key_raises(self):
        pin = RetryPin()
        with pytest.raises(ValueError):
            pin.set("   ", "value")


class TestRetryPinOperations:
    def test_set_and_get(self):
        pin = RetryPin()
        pin.set("env", "prod")
        assert pin.get("env") == "prod"

    def test_get_missing_returns_default(self):
        pin = RetryPin()
        assert pin.get("missing") is None
        assert pin.get("missing", 42) == 42

    def test_has_true_after_set(self):
        pin = RetryPin()
        pin.set("x", 1)
        assert pin.has("x") is True

    def test_has_false_before_set(self):
        pin = RetryPin()
        assert pin.has("x") is False

    def test_remove_existing_key(self):
        pin = RetryPin()
        pin.set("x", 1)
        pin.remove("x")
        assert pin.has("x") is False

    def test_remove_missing_key_is_noop(self):
        pin = RetryPin()
        pin.remove("nonexistent")  # should not raise

    def test_keys_returns_list(self):
        pin = RetryPin()
        pin.set("a", 1)
        pin.set("b", 2)
        assert sorted(pin.keys()) == ["a", "b"]

    def test_as_dict_is_copy(self):
        pin = RetryPin()
        pin.set("k", "v")
        d = pin.as_dict()
        d["k"] = "mutated"
        assert pin.get("k") == "v"

    def test_clear_removes_all(self):
        pin = RetryPin()
        pin.set("a", 1)
        pin.set("b", 2)
        pin.clear()
        assert pin.as_dict() == {}


class TestMakePin:
    def test_prepopulated(self):
        pin = make_pin(service="auth", region="eu")
        assert pin.get("service") == "auth"
        assert pin.get("region") == "eu"

    def test_empty_make_pin(self):
        pin = make_pin()
        assert pin.as_dict() == {}


class TestBuildPinOnRetry:
    def test_returns_on_retry_key(self):
        pin = RetryPin()
        result = build_pin_on_retry(pin)
        assert "on_retry" in result

    def test_returns_pin_key(self):
        pin = RetryPin()
        result = build_pin_on_retry(pin)
        assert result["pin"] is pin

    def test_hook_records_last_attempt(self):
        pin = RetryPin()
        hook = build_pin_on_retry(pin)["on_retry"]
        hook(None, "ok", 3)
        assert pin.get("last_attempt") == 3

    def test_hook_records_exception_name(self):
        pin = RetryPin()
        hook = build_pin_on_retry(pin)["on_retry"]
        hook(ValueError("boom"), None, 1)
        assert pin.get("last_exception") == "ValueError"

    def test_hook_clears_exception_on_success(self):
        pin = RetryPin()
        hook = build_pin_on_retry(pin)["on_retry"]
        hook(ValueError("boom"), None, 1)
        hook(None, "ok", 2)
        assert not pin.has("last_exception")


class TestPinPredicate:
    def test_retries_on_exception_when_not_blocked(self):
        pin = RetryPin()
        pred = pin_predicate(pin, "stop")
        assert pred(ValueError(), None) is True

    def test_does_not_retry_when_blocked(self):
        pin = RetryPin()
        pin.set("stop", True)
        pred = pin_predicate(pin, "stop")
        assert pred(ValueError(), None) is False

    def test_does_not_retry_without_exception(self):
        pin = RetryPin()
        pred = pin_predicate(pin, "stop")
        assert pred(None, "result") is False

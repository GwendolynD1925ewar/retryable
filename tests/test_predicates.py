"""Tests for retryable.predicates."""

import pytest

from retryable.predicates import (
    always_retry,
    never_retry,
    on_exception,
    on_result,
)


class TestOnException:
    def test_matches_single_exception_type(self):
        predicate = on_exception(ValueError)
        assert predicate(ValueError("bad value")) is True

    def test_does_not_match_unrelated_exception(self):
        predicate = on_exception(ValueError)
        assert predicate(TypeError("bad type")) is False

    def test_matches_any_of_multiple_exception_types(self):
        predicate = on_exception(ValueError, TypeError)
        assert predicate(ValueError("v")) is True
        assert predicate(TypeError("t")) is True

    def test_matches_subclass_of_exception(self):
        predicate = on_exception(OSError)
        assert predicate(FileNotFoundError("missing")) is True

    def test_does_not_match_parent_when_child_specified(self):
        predicate = on_exception(FileNotFoundError)
        assert predicate(OSError("generic")) is False

    def test_raises_when_no_exception_types_given(self):
        with pytest.raises(ValueError):
            on_exception()

    def test_predicate_has_descriptive_name(self):
        predicate = on_exception(ValueError, RuntimeError)
        assert "ValueError" in predicate.__name__
        assert "RuntimeError" in predicate.__name__


class TestOnResult:
    def test_retries_when_result_is_none(self):
        predicate = on_result(lambda r: r is None)
        assert predicate(None) is True

    def test_does_not_retry_when_result_is_valid(self):
        predicate = on_result(lambda r: r is None)
        assert predicate(42) is False

    def test_retries_on_falsy_result(self):
        predicate = on_result(lambda r: not r)
        assert predicate("") is True
        assert predicate(0) is True
        assert predicate([]) is True

    def test_does_not_retry_on_truthy_result(self):
        predicate = on_result(lambda r: not r)
        assert predicate("ok") is False
        assert predicate(1) is False

    def test_retries_on_specific_value(self):
        predicate = on_result(lambda r: r == -1)
        assert predicate(-1) is True
        assert predicate(0) is False

    def test_predicate_has_descriptive_name(self):
        def my_check(r):
            return r is None

        predicate = on_result(my_check)
        assert "my_check" in predicate.__name__


class TestBuiltinPredicates:
    def test_never_retry_returns_false_for_any_value(self):
        assert never_retry(None) is False
        assert never_retry(Exception()) is False
        assert never_retry(True) is False

    def test_always_retry_returns_true_for_any_value(self):
        assert always_retry(None) is True
        assert always_retry(Exception()) is True
        assert always_retry(False) is True

"""Tests for retryable.label and retryable.label_integration."""
import pytest
from retryable.label import RetryLabel
from retryable.label_integration import (
    build_labeled_on_retry,
    label_predicate,
    format_label_attempt,
)


class TestRetryLabelInit:
    def test_valid_construction(self):
        label = RetryLabel(name="fetch")
        assert label.name == "fetch"
        assert label.group is None

    def test_valid_with_group(self):
        label = RetryLabel(name="fetch", group="network")
        assert label.group == "network"

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            RetryLabel(name="")

    def test_blank_name_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            RetryLabel(name="   ")

    def test_blank_group_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            RetryLabel(name="ok", group="  ")

    def test_strips_whitespace(self):
        label = RetryLabel(name="  fetch  ", group=" net ")
        assert label.name == "fetch"
        assert label.group == "net"


class TestRetryLabelMethods:
    def test_qualified_with_group(self):
        label = RetryLabel(name="fetch", group="network")
        assert label.qualified() == "network.fetch"

    def test_qualified_without_group(self):
        label = RetryLabel(name="fetch")
        assert label.qualified() == "fetch"

    def test_matches_true(self):
        label = RetryLabel(name="fetch")
        assert label.matches("fetch") is True

    def test_matches_false(self):
        label = RetryLabel(name="fetch")
        assert label.matches("other") is False

    def test_in_group_true(self):
        label = RetryLabel(name="fetch", group="network")
        assert label.in_group("network") is True

    def test_in_group_false(self):
        label = RetryLabel(name="fetch", group="network")
        assert label.in_group("db") is False

    def test_repr(self):
        label = RetryLabel(name="fetch", group="net")
        assert "fetch" in repr(label)
        assert "net" in repr(label)


class TestLabelIntegration:
    def test_build_labeled_on_retry_returns_keys(self):
        result = build_labeled_on_retry("fetch")
        assert "on_retry" in result
        assert "label" in result

    def test_build_labeled_on_retry_label_type(self):
        result = build_labeled_on_retry("fetch", group="net")
        assert isinstance(result["label"], RetryLabel)
        assert result["label"].qualified() == "net.fetch"

    def test_on_retry_is_callable(self):
        result = build_labeled_on_retry("fetch")
        assert callable(result["on_retry"])

    def test_label_predicate_no_groups_allows(self):
        label = RetryLabel(name="fetch")
        pred = label_predicate(label)
        assert pred() is True

    def test_label_predicate_matching_group_allows(self):
        label = RetryLabel(name="fetch", group="net")
        pred = label_predicate(label, allowed_groups=["net", "db"])
        assert pred() is True

    def test_label_predicate_non_matching_group_denies(self):
        label = RetryLabel(name="fetch", group="cache")
        pred = label_predicate(label, allowed_groups=["net"])
        assert pred() is False

    def test_format_label_attempt(self):
        label = RetryLabel(name="fetch", group="net")
        result = format_label_attempt(label, 3)
        assert result == "[net.fetch] attempt 3"

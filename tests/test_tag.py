"""Tests for retryable.tag."""
import pytest
from retryable.tag import RetryTag, make_tag


class TestRetryTagInit:
    def test_valid_single_tag(self):
        t = make_tag("db")
        assert t.has("db")

    def test_valid_multiple_tags(self):
        t = make_tag("db", "network")
        assert t.has("db") and t.has("network")

    def test_empty_tags_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            RetryTag(frozenset())

    def test_blank_string_tag_raises(self):
        with pytest.raises(ValueError):
            make_tag("  ")

    def test_non_string_tag_raises(self):
        with pytest.raises((ValueError, TypeError)):
            RetryTag(frozenset([123]))  # type: ignore


class TestRetryTagMatching:
    def test_has_returns_false_for_missing(self):
        t = make_tag("db")
        assert not t.has("network")

    def test_matches_any_true(self):
        t = make_tag("db", "cache")
        assert t.matches_any(["cache", "other"])

    def test_matches_any_false(self):
        t = make_tag("db")
        assert not t.matches_any(["network", "cache"])

    def test_matches_all_true(self):
        t = make_tag("db", "network")
        assert t.matches_all(["db", "network"])

    def test_matches_all_false_partial(self):
        t = make_tag("db")
        assert not t.matches_all(["db", "network"])


class TestRetryTagMerge:
    def test_merge_combines_tags(self):
        a = make_tag("db")
        b = make_tag("network")
        merged = a.merge(b)
        assert merged.has("db") and merged.has("network")

    def test_merge_deduplicates(self):
        a = make_tag("db")
        b = make_tag("db", "cache")
        merged = a.merge(b)
        assert sorted(merged.tags) == ["cache", "db"]

    def test_repr_contains_tags(self):
        t = make_tag("db")
        assert "db" in repr(t)

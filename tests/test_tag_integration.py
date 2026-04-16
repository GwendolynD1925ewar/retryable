"""Tests for retryable.tag_integration."""
import pytest
from retryable.tag import make_tag
from retryable.tag_integration import build_tagged_on_retry, tag_predicate


class TestBuildTaggedOnRetry:
    def test_returns_on_retry_key(self):
        result = build_tagged_on_retry("db")
        assert "on_retry" in result

    def test_returns_tag_key(self):
        result = build_tagged_on_retry("db")
        assert "tag" in result

    def test_tag_value_is_retry_tag(self):
        from retryable.tag import RetryTag
        result = build_tagged_on_retry("db", "cache")
        assert isinstance(result["tag"], RetryTag)

    def test_on_retry_is_callable(self):
        result = build_tagged_on_retry("db")
        assert callable(result["on_retry"])

    def test_on_retry_sets_last_tag(self):
        result = build_tagged_on_retry("db")
        hook = result["on_retry"]
        hook(exception=None, result=42)
        assert hook.last_tag is not None
        assert hook.last_tag.has("db")

    def test_upstream_hook_is_called(self):
        calls = []
        def upstream(**kwargs):
            calls.append(kwargs)

        result = build_tagged_on_retry("db", on_retry=upstream)
        result["on_retry"](exception=RuntimeError("x"), result=None)
        assert len(calls) == 1

    def test_upstream_not_called_when_none(self):
        result = build_tagged_on_retry("db")
        # Should not raise
        result["on_retry"](exception=None, result=None)


class TestTagPredicate:
    def _always_retry(self, **kwargs):
        return True

    def _never_retry(self, **kwargs):
        return False

    def test_passes_through_when_no_tag(self):
        pred = tag_predicate(["db"], self._always_retry)
        assert pred(exception=None, result=None, tag=None) is True

    def test_allows_when_tags_match(self):
        t = make_tag("db", "network")
        pred = tag_predicate(["db"], self._always_retry)
        assert pred(exception=None, result=None, tag=t) is True

    def test_blocks_when_tags_do_not_match(self):
        t = make_tag("cache")
        pred = tag_predicate(["db"], self._always_retry)
        assert pred(exception=None, result=None, tag=t) is False

    def test_inner_false_still_false(self):
        t = make_tag("db")
        pred = tag_predicate(["db"], self._never_retry)
        assert pred(exception=None, result=None, tag=t) is False

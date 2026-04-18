"""Tests for retryable.stamp."""

from __future__ import annotations

import time
from datetime import datetime, timezone

import pytest

from retryable.stamp import RetryStamp, build_stamp_on_retry, make_stamp


class TestRetryStampInit:
    def test_valid_construction(self):
        s = RetryStamp()
        assert s.call_id
        assert s.created_at is not None
        assert s.label is None

    def test_custom_call_id(self):
        s = RetryStamp(call_id="abc-123")
        assert s.call_id == "abc-123"

    def test_custom_label(self):
        s = RetryStamp(label="fetch-user")
        assert s.label == "fetch-user"

    def test_empty_call_id_raises(self):
        with pytest.raises(ValueError, match="call_id"):
            RetryStamp(call_id="")

    def test_blank_call_id_raises(self):
        with pytest.raises(ValueError, match="call_id"):
            RetryStamp(call_id="   ")

    def test_unique_ids(self):
        a = RetryStamp()
        b = RetryStamp()
        assert a.call_id != b.call_id


class TestRetryStampAge:
    def test_age_is_non_negative(self):
        s = RetryStamp()
        assert s.age_seconds() >= 0.0

    def test_age_increases_over_time(self):
        s = RetryStamp()
        time.sleep(0.05)
        assert s.age_seconds() >= 0.04

    def test_age_with_explicit_now(self):
        created = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        s = RetryStamp(call_id="x", created_at=created)
        now = datetime(2024, 1, 1, 0, 0, 5, tzinfo=timezone.utc)
        assert s.age_seconds(now=now) == pytest.approx(5.0)


class TestRetryStampRepr:
    def test_repr_contains_call_id(self):
        s = RetryStamp(call_id="my-id")
        assert "my-id" in repr(s)

    def test_repr_contains_label_when_set(self):
        s = RetryStamp(call_id="my-id", label="svc")
        assert "svc" in repr(s)

    def test_repr_omits_label_when_none(self):
        s = RetryStamp(call_id="my-id")
        assert "label" not in repr(s)


class TestMakeStamp:
    def test_returns_retry_stamp(self):
        s = make_stamp()
        assert isinstance(s, RetryStamp)

    def test_label_forwarded(self):
        s = make_stamp(label="test")
        assert s.label == "test"


class TestBuildStampOnRetry:
    def test_returns_on_retry_key(self):
        result = build_stamp_on_retry()
        assert "on_retry" in result

    def test_returns_stamp_key(self):
        result = build_stamp_on_retry()
        assert "stamp" in result

    def test_stamp_is_retry_stamp(self):
        result = build_stamp_on_retry()
        assert isinstance(result["stamp"], RetryStamp)

    def test_on_retry_is_callable(self):
        result = build_stamp_on_retry()
        assert callable(result["on_retry"])

    def test_on_retry_does_not_raise(self):
        result = build_stamp_on_retry(label="svc")
        result["on_retry"](exc=None, result=42, attempt=1)

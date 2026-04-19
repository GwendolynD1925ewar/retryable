"""Tests for retryable.sieve_integration."""
from __future__ import annotations

import pytest

from retryable.sieve import RetrySieve
from retryable.sieve_integration import build_sieve_on_retry, sieve_predicate


class TestBuildSieveOnRetry:
    def test_returns_on_retry_key(self):
        result = build_sieve_on_retry(threshold=0.5, scorer=lambda a, e: 1.0)
        assert "on_retry" in result

    def test_returns_sieve_instance(self):
        result = build_sieve_on_retry(threshold=0.5, scorer=lambda a, e: 1.0)
        assert isinstance(result["sieve"], RetrySieve)

    def test_sieve_threshold_is_set(self):
        result = build_sieve_on_retry(threshold=0.7, scorer=lambda a, e: 1.0)
        assert result["sieve"].threshold == pytest.approx(0.7)

    def test_on_retry_is_callable(self):
        result = build_sieve_on_retry(threshold=0.5, scorer=lambda a, e: 1.0)
        assert callable(result["on_retry"])

    def test_on_retry_records_score(self):
        result = build_sieve_on_retry(threshold=0.5, scorer=lambda a, e: 0.9)
        hook = result["on_retry"]
        sieve = result["sieve"]
        hook(attempt=1, exc=None, result=None)
        assert sieve.scores == [0.9]

    def test_on_retry_accepts_exception(self):
        seen = []
        def scorer(attempt, exc):
            seen.append(exc)
            return 1.0
        result = build_sieve_on_retry(threshold=0.0, scorer=scorer)
        exc = RuntimeError("fail")
        result["on_retry"](attempt=1, exc=exc, result=None)
        assert seen[0] is exc


class TestSievePredicate:
    def test_returns_true_when_allowed(self):
        sieve = RetrySieve(threshold=0.5, scorer=lambda a, e: 0.9)
        pred = sieve_predicate(sieve)
        assert pred(attempt=1) is True

    def test_returns_false_when_rejected(self):
        sieve = RetrySieve(threshold=0.5, scorer=lambda a, e: 0.1)
        pred = sieve_predicate(sieve)
        assert pred(attempt=1) is False

    def test_predicate_records_score(self):
        sieve = RetrySieve(threshold=0.0, scorer=lambda a, e: 0.6)
        pred = sieve_predicate(sieve)
        pred(attempt=2)
        assert sieve.scores == [0.6]

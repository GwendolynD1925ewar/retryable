"""Tests for retryable.sieve."""
from __future__ import annotations

import pytest

from retryable.sieve import RetrySieve, SieveRejected


class TestRetrySieveInit:
    def test_valid_construction(self):
        s = RetrySieve(threshold=0.5, scorer=lambda a, e: 1.0)
        assert s.threshold == 0.5

    def test_zero_threshold_is_valid(self):
        s = RetrySieve(threshold=0.0, scorer=lambda a, e: 0.0)
        assert s.threshold == 0.0

    def test_one_threshold_is_valid(self):
        s = RetrySieve(threshold=1.0, scorer=lambda a, e: 1.0)
        assert s.threshold == 1.0

    def test_below_zero_raises(self):
        with pytest.raises(ValueError):
            RetrySieve(threshold=-0.1, scorer=lambda a, e: 0.0)

    def test_above_one_raises(self):
        with pytest.raises(ValueError):
            RetrySieve(threshold=1.1, scorer=lambda a, e: 1.0)


class TestRetrySieveEvaluate:
    def test_evaluate_records_score(self):
        s = RetrySieve(threshold=0.5, scorer=lambda a, e: 0.8)
        s.evaluate(1)
        assert s.scores == [0.8]

    def test_evaluate_multiple_scores(self):
        s = RetrySieve(threshold=0.5, scorer=lambda a, e: float(a) / 10)
        s.evaluate(1)
        s.evaluate(2)
        assert s.scores == [0.1, 0.2]

    def test_average_score_none_when_empty(self):
        s = RetrySieve(threshold=0.5, scorer=lambda a, e: 1.0)
        assert s.average_score is None

    def test_average_score_computed(self):
        s = RetrySieve(threshold=0.5, scorer=lambda a, e: float(a))
        s.evaluate(1)
        s.evaluate(3)
        assert s.average_score == 2.0


class TestRetrySieveAllowed:
    def test_allowed_when_score_meets_threshold(self):
        s = RetrySieve(threshold=0.5, scorer=lambda a, e: 0.5)
        assert s.allowed(1) is True

    def test_rejected_when_score_below_threshold(self):
        s = RetrySieve(threshold=0.5, scorer=lambda a, e: 0.4)
        assert s.allowed(1) is False

    def test_allowed_passes_exception_to_scorer(self):
        received = []
        def scorer(attempt, exc):
            received.append(exc)
            return 1.0
        s = RetrySieve(threshold=0.0, scorer=scorer)
        exc = ValueError("boom")
        s.allowed(1, exc)
        assert received[0] is exc


class TestRetrySieveRequire:
    def test_require_passes_when_allowed(self):
        s = RetrySieve(threshold=0.5, scorer=lambda a, e: 1.0)
        s.require(1)  # should not raise

    def test_require_raises_when_rejected(self):
        s = RetrySieve(threshold=0.5, scorer=lambda a, e: 0.2)
        with pytest.raises(SieveRejected) as exc_info:
            s.require(2)
        err = exc_info.value
        assert err.attempt == 2
        assert err.score == pytest.approx(0.2)
        assert err.threshold == pytest.approx(0.5)


class TestRetrySieveReset:
    def test_reset_clears_scores(self):
        s = RetrySieve(threshold=0.5, scorer=lambda a, e: 0.9)
        s.evaluate(1)
        s.evaluate(2)
        s.reset()
        assert s.scores == []
        assert s.average_score is None

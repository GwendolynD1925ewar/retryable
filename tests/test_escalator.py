"""Tests for RetryEscalator and escalator_integration."""
import pytest
from retryable.escalator import RetryEscalator, EscalationLimitReached
from retryable.escalator_integration import build_escalating_on_retry, escalator_predicate


class TestRetryEscalatorInit:
    def test_valid_construction(self):
        e = RetryEscalator(step=2.0, max_level=3)
        assert e.step == 2.0
        assert e.max_level == 3

    def test_step_must_be_greater_than_one(self):
        with pytest.raises(ValueError):
            RetryEscalator(step=1.0)

    def test_step_below_one_raises(self):
        with pytest.raises(ValueError):
            RetryEscalator(step=0.5)

    def test_max_level_zero_raises(self):
        with pytest.raises(ValueError):
            RetryEscalator(step=2.0, max_level=0)

    def test_max_level_negative_raises(self):
        with pytest.raises(ValueError):
            RetryEscalator(step=2.0, max_level=-1)


class TestRetryEscalatorBehaviour:
    def test_initial_level_is_zero(self):
        e = RetryEscalator()
        assert e.level == 0

    def test_initial_multiplier_is_one(self):
        e = RetryEscalator(step=2.0)
        assert e.multiplier == 1.0

    def test_escalate_increments_level(self):
        e = RetryEscalator(step=2.0)
        e.escalate()
        assert e.level == 1

    def test_escalate_returns_multiplier(self):
        e = RetryEscalator(step=3.0)
        m = e.escalate()
        assert m == 3.0

    def test_second_escalation_squares_step(self):
        e = RetryEscalator(step=2.0)
        e.escalate()
        m = e.escalate()
        assert m == 4.0

    def test_escalation_beyond_max_raises(self):
        e = RetryEscalator(step=2.0, max_level=2)
        e.escalate()
        e.escalate()
        with pytest.raises(EscalationLimitReached):
            e.escalate()

    def test_reset_returns_level_to_zero(self):
        e = RetryEscalator(step=2.0)
        e.escalate()
        e.reset()
        assert e.level == 0

    def test_history_length_matches_level_plus_one(self):
        e = RetryEscalator(step=2.0)
        e.escalate()
        e.escalate()
        assert len(e.history()) == 3

    def test_repr_contains_level(self):
        e = RetryEscalator(step=2.0)
        assert "level=0" in repr(e)


class TestBuildEscalatingOnRetry:
    def test_returns_on_retry_key(self):
        result = build_escalating_on_retry()
        assert "on_retry" in result

    def test_returns_escalator_instance(self):
        result = build_escalating_on_retry()
        assert isinstance(result["escalator"], RetryEscalator)

    def test_hook_escalates_on_exception(self):
        result = build_escalating_on_retry(step=2.0)
        hook = result["on_retry"]
        escalator = result["escalator"]
        hook(attempt=1, exception=ValueError("boom"))
        assert escalator.level == 1

    def test_hook_resets_on_success(self):
        result = build_escalating_on_retry(reset_on_success=True)
        hook = result["on_retry"]
        escalator = result["escalator"]
        hook(attempt=1, exception=ValueError())
        hook(attempt=2, result="ok")
        assert escalator.level == 0

    def test_hook_no_reset_when_disabled(self):
        result = build_escalating_on_retry(reset_on_success=False)
        hook = result["on_retry"]
        escalator = result["escalator"]
        hook(attempt=1, exception=ValueError())
        hook(attempt=2, result="ok")
        assert escalator.level == 1


class TestEscalatorPredicate:
    def test_allows_retry_while_below_max(self):
        e = RetryEscalator(step=2.0, max_level=3)
        pred = escalator_predicate(e)
        assert pred(attempt=1, exception=ValueError()) is True

    def test_stops_retry_at_max_level(self):
        e = RetryEscalator(step=2.0, max_level=1)
        e.escalate()
        pred = escalator_predicate(e, hard_stop=True)
        assert pred(attempt=2, exception=ValueError()) is False

    def test_no_exception_returns_false(self):
        e = RetryEscalator()
        pred = escalator_predicate(e)
        assert pred(attempt=1, exception=None, result="ok") is False

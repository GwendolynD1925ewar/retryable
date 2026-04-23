"""Tests for retryable.lever and retryable.lever_integration."""
from __future__ import annotations

import pytest

from retryable.lever import LeverOutOfRange, RetryLever
from retryable.lever_integration import build_lever_on_backoff, lever_predicate


# ---------------------------------------------------------------------------
# RetryLever — init
# ---------------------------------------------------------------------------

class TestRetryLeverInit:
    def test_valid_construction(self) -> None:
        lv = RetryLever(max_position=8.0)
        assert lv.max_position == 8.0

    def test_default_max_position(self) -> None:
        lv = RetryLever()
        assert lv.max_position == 4.0

    def test_zero_max_position_raises(self) -> None:
        with pytest.raises(ValueError):
            RetryLever(max_position=0.0)

    def test_negative_max_position_raises(self) -> None:
        with pytest.raises(ValueError):
            RetryLever(max_position=-1.0)

    def test_default_position_is_one(self) -> None:
        lv = RetryLever()
        assert lv.position == 1.0


# ---------------------------------------------------------------------------
# RetryLever — set / reset
# ---------------------------------------------------------------------------

class TestRetryLeverSet:
    def test_set_valid_position(self) -> None:
        lv = RetryLever()
        lv.set(2.5)
        assert lv.position == 2.5

    def test_set_zero_is_valid(self) -> None:
        lv = RetryLever()
        lv.set(0.0)
        assert lv.position == 0.0

    def test_set_max_is_valid(self) -> None:
        lv = RetryLever(max_position=4.0)
        lv.set(4.0)
        assert lv.position == 4.0

    def test_set_above_max_raises(self) -> None:
        lv = RetryLever(max_position=4.0)
        with pytest.raises(LeverOutOfRange) as exc_info:
            lv.set(5.0)
        assert exc_info.value.position == 5.0

    def test_set_negative_raises(self) -> None:
        lv = RetryLever()
        with pytest.raises(LeverOutOfRange):
            lv.set(-0.1)

    def test_reset_returns_to_one(self) -> None:
        lv = RetryLever()
        lv.set(3.0)
        lv.reset()
        assert lv.position == 1.0


# ---------------------------------------------------------------------------
# RetryLever — scale
# ---------------------------------------------------------------------------

class TestRetryLeverScale:
    def test_neutral_position_unchanged(self) -> None:
        lv = RetryLever()
        assert lv.scale(2.0) == pytest.approx(2.0)

    def test_double_position_doubles_delay(self) -> None:
        lv = RetryLever()
        lv.set(2.0)
        assert lv.scale(3.0) == pytest.approx(6.0)

    def test_zero_position_collapses_delay(self) -> None:
        lv = RetryLever()
        lv.set(0.0)
        assert lv.scale(10.0) == pytest.approx(0.0)

    def test_fractional_position_compresses_delay(self) -> None:
        lv = RetryLever()
        lv.set(0.5)
        assert lv.scale(4.0) == pytest.approx(2.0)


# ---------------------------------------------------------------------------
# Integration — build_lever_on_backoff
# ---------------------------------------------------------------------------

class TestBuildLeverOnBackoff:
    def test_returns_on_backoff_key(self) -> None:
        config = build_lever_on_backoff()
        assert "on_backoff" in config

    def test_returns_lever_key(self) -> None:
        config = build_lever_on_backoff()
        assert "lever" in config

    def test_lever_is_retry_lever_instance(self) -> None:
        config = build_lever_on_backoff()
        assert isinstance(config["lever"], RetryLever)

    def test_on_backoff_scales_delay(self) -> None:
        config = build_lever_on_backoff(initial_position=2.0)
        scaled = config["on_backoff"](delay=5.0)
        assert scaled == pytest.approx(10.0)

    def test_initial_position_respected(self) -> None:
        config = build_lever_on_backoff(initial_position=3.0)
        assert config["lever"].position == pytest.approx(3.0)

    def test_lever_adjustment_affects_hook(self) -> None:
        config = build_lever_on_backoff()
        lever: RetryLever = config["lever"]
        lever.set(0.5)
        assert config["on_backoff"](delay=8.0) == pytest.approx(4.0)


# ---------------------------------------------------------------------------
# Integration — lever_predicate
# ---------------------------------------------------------------------------

class TestLeverPredicate:
    def test_allows_retry_when_position_positive(self) -> None:
        lv = RetryLever()
        pred = lever_predicate(lv)
        assert pred(exception=None) is True

    def test_blocks_retry_when_position_zero(self) -> None:
        lv = RetryLever()
        lv.set(0.0)
        pred = lever_predicate(lv)
        assert pred(exception=RuntimeError()) is False

    def test_allows_retry_after_reset(self) -> None:
        lv = RetryLever()
        lv.set(0.0)
        lv.reset()
        pred = lever_predicate(lv)
        assert pred() is True

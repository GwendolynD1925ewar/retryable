"""Tests for backoff strategy implementations."""

import pytest
from retryable.backoff import (
    exponential_backoff,
    full_jitter,
    equal_jitter,
    no_jitter,
    JITTER_STRATEGIES,
)


class TestExponentialBackoff:
    def test_first_attempt_returns_base_delay(self):
        assert exponential_backoff(0, base_delay=1.0, multiplier=2.0) == 1.0

    def test_second_attempt_doubles_delay(self):
        assert exponential_backoff(1, base_delay=1.0, multiplier=2.0) == 2.0

    def test_third_attempt_quadruples_delay(self):
        assert exponential_backoff(2, base_delay=1.0, multiplier=2.0) == 4.0

    def test_custom_base_delay(self):
        assert exponential_backoff(0, base_delay=0.5, multiplier=2.0) == 0.5

    def test_custom_multiplier(self):
        assert exponential_backoff(1, base_delay=1.0, multiplier=3.0) == 3.0

    def test_max_delay_caps_result(self):
        result = exponential_backoff(10, base_delay=1.0, multiplier=2.0, max_delay=30.0)
        assert result == 30.0

    def test_max_delay_not_applied_when_below_cap(self):
        result = exponential_backoff(1, base_delay=1.0, multiplier=2.0, max_delay=100.0)
        assert result == 2.0


class TestFullJitter:
    def test_returns_value_within_range(self):
        for _ in range(50):
            result = full_jitter(10.0)
            assert 0 <= result <= 10.0

    def test_zero_delay_returns_zero(self):
        assert full_jitter(0.0) == 0.0


class TestEqualJitter:
    def test_returns_value_within_range(self):
        for _ in range(50):
            result = equal_jitter(10.0)
            assert 5.0 <= result <= 10.0

    def test_zero_delay_returns_zero(self):
        assert equal_jitter(0.0) == 0.0


class TestNoJitter:
    def test_returns_same_value(self):
        assert no_jitter(5.0) == 5.0

    def test_returns_zero_for_zero(self):
        assert no_jitter(0.0) == 0.0


class TestJitterStrategies:
    def test_all_strategies_present(self):
        assert "full" in JITTER_STRATEGIES
        assert "equal" in JITTER_STRATEGIES
        assert "none" in JITTER_STRATEGIES

    def test_strategies_are_callable(self):
        for name, fn in JITTER_STRATEGIES.items():
            assert callable(fn), f"Strategy '{name}' is not callable"

    def test_none_strategy_returns_exact_delay(self):
        assert JITTER_STRATEGIES["none"](7.5) == 7.5

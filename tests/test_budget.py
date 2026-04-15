"""Tests for retryable.budget.RetryBudget."""

import time
import pytest
from unittest.mock import patch
from retryable.budget import RetryBudget


class TestRetryBudgetInit:
    def test_valid_construction(self):
        budget = RetryBudget(max_retries=5, window_seconds=30.0)
        assert budget.max_retries == 5
        assert budget.window_seconds == 30.0

    def test_negative_max_retries_raises(self):
        with pytest.raises(ValueError, match="max_retries must be non-negative"):
            RetryBudget(max_retries=-1)

    def test_zero_window_raises(self):
        with pytest.raises(ValueError, match="window_seconds must be positive"):
            RetryBudget(max_retries=5, window_seconds=0)

    def test_negative_window_raises(self):
        with pytest.raises(ValueError, match="window_seconds must be positive"):
            RetryBudget(max_retries=5, window_seconds=-10.0)

    def test_repr(self):
        budget = RetryBudget(max_retries=3, window_seconds=60.0)
        assert repr(budget) == "RetryBudget(max_retries=3, window_seconds=60.0)"


class TestRetryBudgetAcquire:
    def test_acquire_within_budget(self):
        budget = RetryBudget(max_retries=3)
        assert budget.acquire() is True
        assert budget.acquire() is True
        assert budget.acquire() is True

    def test_acquire_exceeds_budget(self):
        budget = RetryBudget(max_retries=2)
        budget.acquire()
        budget.acquire()
        assert budget.acquire() is False

    def test_zero_budget_always_denies(self):
        budget = RetryBudget(max_retries=0)
        assert budget.acquire() is False

    def test_acquire_replenishes_after_window(self):
        budget = RetryBudget(max_retries=2, window_seconds=1.0)
        budget.acquire()
        budget.acquire()
        assert budget.acquire() is False

        # Simulate time passing beyond the window
        with patch("time.monotonic", return_value=time.monotonic() + 2.0):
            assert budget.acquire() is True


class TestRetryBudgetRemaining:
    def test_full_budget_remaining(self):
        budget = RetryBudget(max_retries=5)
        assert budget.remaining() == 5

    def test_remaining_decreases_on_acquire(self):
        budget = RetryBudget(max_retries=5)
        budget.acquire()
        budget.acquire()
        assert budget.remaining() == 3

    def test_remaining_zero_when_exhausted(self):
        budget = RetryBudget(max_retries=2)
        budget.acquire()
        budget.acquire()
        assert budget.remaining() == 0

    def test_remaining_replenishes_after_window(self):
        budget = RetryBudget(max_retries=3, window_seconds=1.0)
        budget.acquire()
        budget.acquire()
        assert budget.remaining() == 1

        with patch("time.monotonic", return_value=time.monotonic() + 2.0):
            assert budget.remaining() == 3


class TestRetryBudgetReset:
    def test_reset_restores_full_budget(self):
        budget = RetryBudget(max_retries=3)
        budget.acquire()
        budget.reset()
        assert budget.remaining() == 3

    def test_reset_allows_acquire_after_exhaustion(self):
        budget = RetryBudget(max_retries=2)
        budget.acquire()
        budget.acquire()
        assert budget.acquire() is False
        budget.reset()
        assert budget.acquire() is True

    def test_reset_idempotent_on_full_budget(self):
        budget = RetryBudget(max_retries=4)
        budget.reset()
        assert budget.remaining() == 4

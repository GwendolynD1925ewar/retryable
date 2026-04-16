"""Tests for retryable.hedge_integration."""
from __future__ import annotations

import pytest

from retryable.hedge import HedgePolicy
from retryable.hedge_integration import build_hedged_on_retry, hedged


class TestBuildHedgedOnRetry:
    def test_returns_on_retry_key(self):
        kwargs = build_hedged_on_retry(HedgePolicy(delay=0.1))
        assert "on_retry" in kwargs

    def test_returns_hedge_policy_key(self):
        policy = HedgePolicy(delay=0.1)
        kwargs = build_hedged_on_retry(policy)
        assert kwargs["_hedge_policy"] is policy

    def test_on_retry_is_callable(self):
        kwargs = build_hedged_on_retry(HedgePolicy(delay=0.1))
        assert callable(kwargs["on_retry"])

    def test_on_retry_accepts_args(self):
        kwargs = build_hedged_on_retry(HedgePolicy(delay=0.1))
        # should not raise
        kwargs["on_retry"](None, None, 1)


class TestHedgedDecorator:
    def test_wraps_function(self):
        policy = HedgePolicy(delay=0.5)

        @hedged(policy)
        def fn():
            return 99

        assert fn() == 99

    def test_preserves_wrapped_attribute(self):
        policy = HedgePolicy(delay=0.5)

        def original():
            return 0

        wrapped = hedged(policy)(original)
        assert wrapped.__wrapped__ is original

    def test_raises_on_failure(self):
        policy = HedgePolicy(delay=0.01, max_hedges=1)

        @hedged(policy)
        def boom():
            raise ValueError("nope")

        with pytest.raises(ValueError, match="nope"):
            boom()

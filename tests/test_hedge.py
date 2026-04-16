"""Tests for retryable.hedge."""
from __future__ import annotations

import threading
import time

import pytest

from retryable.hedge import HedgePolicy, hedge


class TestHedgePolicyInit:
    def test_valid_construction(self):
        p = HedgePolicy(delay=0.1)
        assert p.delay == 0.1
        assert p.max_hedges == 1

    def test_custom_max_hedges(self):
        p = HedgePolicy(delay=0.2, max_hedges=3)
        assert p.max_hedges == 3

    def test_zero_delay_raises(self):
        with pytest.raises(ValueError, match="delay"):
            HedgePolicy(delay=0)

    def test_negative_delay_raises(self):
        with pytest.raises(ValueError, match="delay"):
            HedgePolicy(delay=-1)

    def test_zero_max_hedges_raises(self):
        with pytest.raises(ValueError, match="max_hedges"):
            HedgePolicy(delay=0.1, max_hedges=0)


class TestHedge:
    def test_returns_result_on_first_success(self):
        policy = HedgePolicy(delay=0.5)
        result = hedge(policy, lambda: 42)
        assert result == 42

    def test_raises_if_all_attempts_fail(self):
        policy = HedgePolicy(delay=0.01, max_hedges=1)
        with pytest.raises(RuntimeError, match="boom"):
            hedge(policy, lambda: (_ for _ in ()).throw(RuntimeError("boom")))

    def test_hedge_issued_after_delay(self):
        call_times: list[float] = []
        lock = threading.Lock()

        def slow_fn():
            with lock:
                call_times.append(time.monotonic())
            time.sleep(0.05)
            return "ok"

        policy = HedgePolicy(delay=0.02, max_hedges=1)
        hedge(policy, slow_fn)
        assert len(call_times) == 2
        assert call_times[1] - call_times[0] >= 0.01

    def test_first_result_wins(self):
        results: list[int] = []

        def fast():
            return 1

        policy = HedgePolicy(delay=0.001, max_hedges=1)
        r = hedge(policy, fast)
        assert r == 1

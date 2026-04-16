"""Tests for retryable.scoreboard."""
import pytest
from retryable.scoreboard import KeyStats, RetryScoreboard


class TestKeyStats:
    def test_initial_state(self):
        ks = KeyStats()
        assert ks.successes == 0
        assert ks.failures == 0
        assert ks.total == 0
        assert ks.failure_rate == 0.0

    def test_failure_rate_all_failures(self):
        ks = KeyStats(successes=0, failures=4)
        assert ks.failure_rate == 1.0

    def test_failure_rate_mixed(self):
        ks = KeyStats(successes=3, failures=1)
        assert ks.failure_rate == pytest.approx(0.25)

    def test_repr(self):
        ks = KeyStats(successes=2, failures=2)
        assert "failure_rate=0.50" in repr(ks)


class TestRetryScoreboard:
    def setup_method(self):
        self.sb = RetryScoreboard()

    def test_initial_stats_empty(self):
        s = self.sb.stats("x")
        assert s.total == 0

    def test_record_success(self):
        self.sb.record_success("a")
        assert self.sb.stats("a").successes == 1

    def test_record_failure(self):
        self.sb.record_failure("a")
        assert self.sb.stats("a").failures == 1

    def test_multiple_keys_independent(self):
        self.sb.record_success("a")
        self.sb.record_failure("b")
        assert self.sb.stats("a").successes == 1
        assert self.sb.stats("b").failures == 1

    def test_keys_returns_all(self):
        self.sb.record_success("x")
        self.sb.record_success("y")
        assert set(self.sb.keys()) == {"x", "y"}

    def test_reset_single_key(self):
        self.sb.record_failure("a")
        self.sb.reset("a")
        assert self.sb.stats("a").total == 0

    def test_reset_all(self):
        self.sb.record_failure("a")
        self.sb.record_success("b")
        self.sb.reset()
        assert self.sb.keys() == []

    def test_top_failing_order(self):
        for _ in range(3):
            self.sb.record_failure("high")
        self.sb.record_failure("low")
        top = self.sb.top_failing(2)
        assert top[0][0] == "high"
        assert top[1][0] == "low"

    def test_top_failing_respects_n(self):
        for k in ["a", "b", "c"]:
            self.sb.record_failure(k)
        assert len(self.sb.top_failing(2)) == 2

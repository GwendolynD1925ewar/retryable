"""Tests for retryable.scoreboard_integration."""
from retryable.scoreboard import RetryScoreboard
from retryable.scoreboard_integration import build_scoreboard_on_retry, scoreboard_predicate


class TestBuildScoreboardOnRetry:
    def setup_method(self):
        self.sb = RetryScoreboard()

    def test_returns_on_retry_key(self):
        result = build_scoreboard_on_retry(self.sb, "k")
        assert "on_retry" in result

    def test_returns_scoreboard_instance(self):
        result = build_scoreboard_on_retry(self.sb, "k")
        assert result["scoreboard"] is self.sb

    def test_hook_records_failure_on_exception(self):
        result = build_scoreboard_on_retry(self.sb, "svc")
        result["on_retry"](exc=ValueError("boom"))
        assert self.sb.stats("svc").failures == 1

    def test_hook_records_success_on_no_exception(self):
        result = build_scoreboard_on_retry(self.sb, "svc")
        result["on_retry"](exc=None, result=42)
        assert self.sb.stats("svc").successes == 1

    def test_hook_ignores_non_matching_exception_type(self):
        result = build_scoreboard_on_retry(self.sb, "svc", record_on=TypeError)
        result["on_retry"](exc=ValueError("x"))
        assert self.sb.stats("svc").failures == 0

    def test_hook_records_matching_exception_type(self):
        result = build_scoreboard_on_retry(self.sb, "svc", record_on=ValueError)
        result["on_retry"](exc=ValueError("x"))
        assert self.sb.stats("svc").failures == 1


class TestScoreboardPredicate:
    def setup_method(self):
        self.sb = RetryScoreboard()

    def test_allows_retry_when_no_data(self):
        pred = scoreboard_predicate(self.sb, "k")
        assert pred() is True

    def test_allows_retry_below_threshold(self):
        self.sb.record_failure("k")
        self.sb.record_success("k")
        pred = scoreboard_predicate(self.sb, "k", max_failure_rate=0.6)
        assert pred() is True

    def test_blocks_retry_above_threshold(self):
        self.sb.record_failure("k")
        self.sb.record_failure("k")
        pred = scoreboard_predicate(self.sb, "k", max_failure_rate=0.4)
        assert pred() is False

    def test_allows_at_exact_threshold(self):
        self.sb.record_failure("k")
        self.sb.record_success("k")
        pred = scoreboard_predicate(self.sb, "k", max_failure_rate=0.5)
        assert pred() is True

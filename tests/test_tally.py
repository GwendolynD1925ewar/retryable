import pytest
from retryable.tally import RetryTally, TallyLimitExceeded
from retryable.tally_integration import build_tally_on_retry, tally_predicate


class TestRetryTallyInit:
    def test_valid_construction(self):
        t = RetryTally(default_limit=3)
        assert t.default_limit == 3

    def test_zero_default_limit_raises(self):
        with pytest.raises(ValueError):
            RetryTally(default_limit=0)

    def test_negative_default_limit_raises(self):
        with pytest.raises(ValueError):
            RetryTally(default_limit=-1)

    def test_invalid_key_limit_raises(self):
        with pytest.raises(ValueError):
            RetryTally(default_limit=3, key_limits={"svc": 0})


class TestRetryTallyIncrement:
    def test_increment_returns_new_count(self):
        t = RetryTally(default_limit=3)
        assert t.increment("a") == 1
        assert t.increment("a") == 2

    def test_exceeds_limit_raises(self):
        t = RetryTally(default_limit=2)
        t.increment("x")
        t.increment("x")
        with pytest.raises(TallyLimitExceeded) as exc_info:
            t.increment("x")
        assert exc_info.value.key == "x"
        assert exc_info.value.limit == 2

    def test_per_key_limit_overrides_default(self):
        t = RetryTally(default_limit=10, key_limits={"svc": 1})
        t.increment("svc")
        with pytest.raises(TallyLimitExceeded):
            t.increment("svc")

    def test_independent_keys(self):
        t = RetryTally(default_limit=2)
        t.increment("a")
        t.increment("a")
        assert t.increment("b") == 1


class TestRetryTallyHelpers:
    def test_count_starts_at_zero(self):
        t = RetryTally(default_limit=5)
        assert t.count("k") == 0

    def test_remaining_decrements(self):
        t = RetryTally(default_limit=3)
        t.increment("k")
        assert t.remaining("k") == 2

    def test_reset_single_key(self):
        t = RetryTally(default_limit=3)
        t.increment("k")
        t.reset("k")
        assert t.count("k") == 0

    def test_reset_all_keys(self):
        t = RetryTally(default_limit=3)
        t.increment("a")
        t.increment("b")
        t.reset()
        assert t.count("a") == 0
        assert t.count("b") == 0


class TestTallyIntegration:
    def test_build_returns_on_retry_key(self):
        result = build_tally_on_retry()
        assert "on_retry" in result

    def test_build_returns_tally_instance(self):
        result = build_tally_on_retry()
        assert isinstance(result["tally"], RetryTally)

    def test_hook_increments_tally(self):
        result = build_tally_on_retry(default_limit=5, key="svc")
        result["on_retry"]()
        assert result["tally"].count("svc") == 1

    def test_predicate_allows_while_remaining(self):
        t = RetryTally(default_limit=3)
        pred = tally_predicate(t, key="k")
        assert pred() is True

    def test_predicate_blocks_when_exhausted(self):
        t = RetryTally(default_limit=1)
        t.increment("k")
        pred = tally_predicate(t, key="k")
        assert pred() is False

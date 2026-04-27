"""Tests for retryable.mirror."""
import pytest

from retryable.mirror import MirrorImbalanced, MirrorStats, RetryMirror


class TestMirrorStatsProperties:
    def test_total_is_sum(self):
        s = MirrorStats(successes=3, failures=2)
        assert s.total == 5

    def test_imbalance_ratio_all_failures(self):
        s = MirrorStats(successes=0, failures=4)
        assert s.imbalance_ratio == 1.0

    def test_imbalance_ratio_no_data(self):
        s = MirrorStats()
        assert s.imbalance_ratio == 0.0

    def test_imbalance_ratio_mixed(self):
        s = MirrorStats(successes=3, failures=1)
        assert s.imbalance_ratio == pytest.approx(0.25)

    def test_repr_contains_fields(self):
        s = MirrorStats(successes=2, failures=2)
        r = repr(s)
        assert "successes=2" in r
        assert "failures=2" in r
        assert "ratio=" in r


class TestRetryMirrorInit:
    def test_valid_construction(self):
        m = RetryMirror(threshold=0.5)
        assert m.threshold == 0.5

    def test_threshold_zero_raises(self):
        with pytest.raises(ValueError, match="threshold"):
            RetryMirror(threshold=0.0)

    def test_threshold_above_one_raises(self):
        with pytest.raises(ValueError, match="threshold"):
            RetryMirror(threshold=1.1)

    def test_threshold_one_is_valid(self):
        m = RetryMirror(threshold=1.0)
        assert m.threshold == 1.0

    def test_min_samples_zero_raises(self):
        with pytest.raises(ValueError, match="min_samples"):
            RetryMirror(threshold=0.5, min_samples=0)

    def test_min_samples_negative_raises(self):
        with pytest.raises(ValueError, match="min_samples"):
            RetryMirror(threshold=0.5, min_samples=-1)


class TestRetryMirrorRecording:
    def setup_method(self):
        self.mirror = RetryMirror(threshold=0.5, min_samples=3)

    def test_record_success_increments(self):
        self.mirror.record_success("svc")
        assert self.mirror.stats("svc").successes == 1

    def test_record_failure_increments(self):
        self.mirror.record_failure("svc")
        assert self.mirror.stats("svc").failures == 1

    def test_stats_returns_none_for_unknown_key(self):
        assert self.mirror.stats("unknown") is None

    def test_check_does_not_raise_below_min_samples(self):
        self.mirror.record_failure("svc")
        self.mirror.record_failure("svc")
        self.mirror.check("svc")  # only 2 samples — should not raise

    def test_check_raises_when_imbalanced(self):
        for _ in range(3):
            self.mirror.record_failure("svc")
        with pytest.raises(MirrorImbalanced) as exc_info:
            self.mirror.check("svc")
        assert exc_info.value.key == "svc"
        assert exc_info.value.failures == 3

    def test_check_does_not_raise_when_balanced(self):
        self.mirror.record_success("svc")
        self.mirror.record_success("svc")
        self.mirror.record_failure("svc")
        self.mirror.check("svc")  # ratio = 0.33 < 0.5

    def test_reset_clears_key(self):
        self.mirror.record_failure("svc")
        self.mirror.reset("svc")
        assert self.mirror.stats("svc") is None

    def test_reset_all_clears_everything(self):
        self.mirror.record_failure("a")
        self.mirror.record_success("b")
        self.mirror.reset_all()
        assert self.mirror.stats("a") is None
        assert self.mirror.stats("b") is None

    def test_independent_keys(self):
        self.mirror.record_failure("x")
        self.mirror.record_success("y")
        assert self.mirror.stats("x").failures == 1
        assert self.mirror.stats("y").successes == 1

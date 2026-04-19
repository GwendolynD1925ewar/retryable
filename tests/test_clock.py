"""Tests for retryable.clock."""
from __future__ import annotations

import pytest

from retryable.clock import ManualClock, OffsetClock, make_clock, system_clock


class TestSystemClock:
    def test_returns_float(self):
        assert isinstance(system_clock(), float)

    def test_non_decreasing(self):
        a = system_clock()
        b = system_clock()
        assert b >= a


class TestManualClock:
    def test_initial_value_is_zero(self):
        c = ManualClock()
        assert c() == 0.0

    def test_custom_initial_value(self):
        c = ManualClock(_now=100.0)
        assert c() == 100.0

    def test_advance_increases_time(self):
        c = ManualClock()
        c.advance(5.0)
        assert c() == 5.0

    def test_multiple_advances_accumulate(self):
        c = ManualClock()
        c.advance(3.0)
        c.advance(2.0)
        assert c() == 5.0

    def test_advance_negative_raises(self):
        c = ManualClock()
        with pytest.raises(ValueError, match="negative"):
            c.advance(-1.0)

    def test_set_changes_time(self):
        c = ManualClock()
        c.set(42.0)
        assert c() == 42.0

    def test_total_advances_counts_calls(self):
        c = ManualClock()
        c.advance(1.0)
        c.advance(2.0)
        assert c.total_advances == 2

    def test_advance_zero_is_allowed(self):
        c = ManualClock()
        c.advance(0.0)
        assert c() == 0.0


class TestOffsetClock:
    def test_applies_positive_offset(self):
        base = ManualClock(_now=10.0)
        oc = OffsetClock(base=base, offset=5.0)
        assert oc() == 15.0

    def test_applies_negative_offset(self):
        base = ManualClock(_now=10.0)
        oc = OffsetClock(base=base, offset=-3.0)
        assert oc() == 7.0

    def test_tracks_base_advances(self):
        base = ManualClock(_now=0.0)
        oc = OffsetClock(base=base, offset=1.0)
        base.advance(4.0)
        assert oc() == 5.0

    def test_non_callable_base_raises(self):
        with pytest.raises(TypeError, match="callable"):
            OffsetClock(base="not_a_clock", offset=0.0)  # type: ignore[arg-type]


class TestMakeClock:
    def test_returns_system_clock_when_none(self):
        c = make_clock(None)
        assert c is system_clock

    def test_returns_provided_clock(self):
        manual = ManualClock()
        assert make_clock(manual) is manual

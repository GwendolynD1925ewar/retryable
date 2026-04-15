"""Tests for retryable.cache."""
from __future__ import annotations

import time

import pytest

from retryable.cache import CachedEntry, RetryCache, make_cache_key


# ---------------------------------------------------------------------------
# CachedEntry
# ---------------------------------------------------------------------------

class TestCachedEntry:
    def test_not_expired_before_ttl(self):
        entry = CachedEntry(value=42, expires_at=time.monotonic() + 10)
        assert not entry.is_expired()

    def test_expired_after_ttl(self):
        entry = CachedEntry(value=42, expires_at=time.monotonic() - 1)
        assert entry.is_expired()

    def test_expired_uses_provided_now(self):
        entry = CachedEntry(value=1, expires_at=100.0)
        assert entry.is_expired(now=200.0)
        assert not entry.is_expired(now=50.0)


# ---------------------------------------------------------------------------
# RetryCache — construction
# ---------------------------------------------------------------------------

class TestRetryCacheInit:
    def test_valid_construction(self):
        cache = RetryCache(ttl=5.0)
        assert cache.ttl == 5.0
        assert cache.max_size == 256

    def test_zero_ttl_raises(self):
        with pytest.raises(ValueError, match="ttl must be positive"):
            RetryCache(ttl=0)

    def test_negative_ttl_raises(self):
        with pytest.raises(ValueError, match="ttl must be positive"):
            RetryCache(ttl=-1)

    def test_zero_max_size_raises(self):
        with pytest.raises(ValueError, match="max_size must be at least 1"):
            RetryCache(ttl=1.0, max_size=0)


# ---------------------------------------------------------------------------
# RetryCache — get / set
# ---------------------------------------------------------------------------

class TestRetryCacheGetSet:
    def test_returns_none_for_missing_key(self):
        cache = RetryCache(ttl=5.0)
        assert cache.get("missing") is None

    def test_returns_stored_value(self):
        cache = RetryCache(ttl=5.0)
        cache.set("k", "hello")
        assert cache.get("k") == "hello"

    def test_returns_none_after_expiry(self):
        cache = RetryCache(ttl=0.05)
        cache.set("k", "value")
        time.sleep(0.1)
        assert cache.get("k") is None

    def test_invalidate_removes_key(self):
        cache = RetryCache(ttl=5.0)
        cache.set("k", 99)
        cache.invalidate("k")
        assert cache.get("k") is None

    def test_clear_removes_all_entries(self):
        cache = RetryCache(ttl=5.0)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.size == 0

    def test_evicts_when_full(self):
        cache = RetryCache(ttl=5.0, max_size=2)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)  # should evict one entry
        assert cache.size <= 2


# ---------------------------------------------------------------------------
# make_cache_key
# ---------------------------------------------------------------------------

class TestMakeCacheKey:
    def test_same_args_produce_same_key(self):
        def fn(): ...
        k1 = make_cache_key(fn, (1, 2), {"x": 3})
        k2 = make_cache_key(fn, (1, 2), {"x": 3})
        assert k1 == k2

    def test_different_args_produce_different_keys(self):
        def fn(): ...
        k1 = make_cache_key(fn, (1,), {})
        k2 = make_cache_key(fn, (2,), {})
        assert k1 != k2

    def test_unhashable_args_do_not_raise(self):
        def fn(): ...
        key = make_cache_key(fn, ([1, 2],), {})
        assert key is not None

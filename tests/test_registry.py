"""Tests for retryable.registry and retryable.registry_integration."""
import pytest
from retryable.registry import (
    RetryRegistry,
    RegistryKeyError,
    get_default_registry,
    reset_default_registry,
)
from retryable.registry_integration import build_from_profile, register_profile


class TestRetryRegistryInit:
    def test_starts_empty(self):
        r = RetryRegistry()
        assert len(r) == 0

    def test_empty_name_raises(self):
        r = RetryRegistry()
        with pytest.raises(ValueError):
            r.register("", max_attempts=3)

    def test_blank_name_raises(self):
        r = RetryRegistry()
        with pytest.raises(ValueError):
            r.register("   ", max_attempts=3)


class TestRetryRegistryOperations:
    def setup_method(self):
        self.r = RetryRegistry()
        self.r.register("default", max_attempts=3, delay=1.0)

    def test_register_and_get(self):
        profile = self.r.get("default")
        assert profile["max_attempts"] == 3
        assert profile["delay"] == 1.0

    def test_get_returns_copy(self):
        p1 = self.r.get("default")
        p1["max_attempts"] = 99
        assert self.r.get("default")["max_attempts"] == 3

    def test_contains_true(self):
        assert "default" in self.r

    def test_contains_false(self):
        assert "missing" not in self.r

    def test_names_returns_list(self):
        self.r.register("fast", max_attempts=1)
        assert set(self.r.names()) == {"default", "fast"}

    def test_remove_existing(self):
        self.r.remove("default")
        assert "default" not in self.r

    def test_remove_missing_raises(self):
        with pytest.raises(RegistryKeyError):
            self.r.remove("nope")

    def test_update_merges(self):
        self.r.update("default", delay=5.0)
        assert self.r.get("default")["delay"] == 5.0
        assert self.r.get("default")["max_attempts"] == 3

    def test_update_missing_raises(self):
        with pytest.raises(RegistryKeyError):
            self.r.update("ghost", delay=1)

    def test_get_missing_raises(self):
        with pytest.raises(RegistryKeyError):
            self.r.get("ghost")


class TestDefaultRegistry:
    def setup_method(self):
        reset_default_registry()

    def test_get_default_registry_singleton(self):
        r1 = get_default_registry()
        r2 = get_default_registry()
        assert r1 is r2

    def test_reset_creates_fresh(self):
        r1 = get_default_registry()
        r1.register("x", max_attempts=1)
        reset_default_registry()
        r2 = get_default_registry()
        assert "x" not in r2


class TestBuildFromProfile:
    def setup_method(self):
        reset_default_registry()
        register_profile("standard", max_attempts=5, delay=2.0)

    def test_returns_profile_kwargs(self):
        kwargs = build_from_profile("standard")
        assert kwargs["max_attempts"] == 5

    def test_overrides_applied(self):
        kwargs = build_from_profile("standard", max_attempts=1)
        assert kwargs["max_attempts"] == 1
        assert kwargs["delay"] == 2.0

    def test_original_profile_unchanged_after_override(self):
        build_from_profile("standard", max_attempts=1)
        assert get_default_registry().get("standard")["max_attempts"] == 5

    def test_missing_profile_raises(self):
        with pytest.raises(RegistryKeyError):
            build_from_profile("nonexistent")

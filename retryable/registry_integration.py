"""Integration helpers: build retry kwargs from a named registry profile."""
from __future__ import annotations
from typing import Any, Dict

from retryable.registry import RetryRegistry, get_default_registry


def build_from_profile(
    name: str,
    registry: RetryRegistry | None = None,
    **overrides: Any,
) -> Dict[str, Any]:
    """Return retry kwargs from a named profile, with optional overrides.

    Args:
        name: Profile name to look up.
        registry: Registry to use; defaults to the module-level default.
        **overrides: Keys that override the stored profile values.

    Returns:
        A dict suitable for unpacking into ``retry(...)``.
    """
    reg = registry if registry is not None else get_default_registry()
    kwargs = reg.get(name)
    kwargs.update(overrides)
    return kwargs


def register_profile(
    name: str,
    registry: RetryRegistry | None = None,
    **kwargs: Any,
) -> None:
    """Convenience wrapper to register a profile on the default registry."""
    reg = registry if registry is not None else get_default_registry()
    reg.register(name, **kwargs)

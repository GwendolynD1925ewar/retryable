"""Named retry configuration registry for reusable retry profiles."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


class RegistryKeyError(KeyError):
    def __init__(self, name: str) -> None:
        super().__init__(f"No retry profile registered under '{name}'")
        self.name = name


@dataclass
class RetryRegistry:
    """A named registry of retry keyword-argument profiles."""
    _profiles: Dict[str, Dict[str, Any]] = field(default_factory=dict, init=False)

    def register(self, name: str, **kwargs: Any) -> None:
        """Register a retry profile by name."""
        if not name or not name.strip():
            raise ValueError("Profile name must be a non-empty string")
        self._profiles[name] = dict(kwargs)

    def get(self, name: str) -> Dict[str, Any]:
        """Retrieve a profile by name, raising RegistryKeyError if missing."""
        if name not in self._profiles:
            raise RegistryKeyError(name)
        return dict(self._profiles[name])

    def remove(self, name: str) -> None:
        """Remove a registered profile."""
        if name not in self._profiles:
            raise RegistryKeyError(name)
        del self._profiles[name]

    def update(self, name: str, **kwargs: Any) -> None:
        """Merge kwargs into an existing profile."""
        if name not in self._profiles:
            raise RegistryKeyError(name)
        self._profiles[name].update(kwargs)

    def names(self) -> list:
        return list(self._profiles.keys())

    def __contains__(self, name: str) -> bool:
        return name in self._profiles

    def __len__(self) -> int:
        return len(self._profiles)


_default_registry: Optional[RetryRegistry] = None


def get_default_registry() -> RetryRegistry:
    global _default_registry
    if _default_registry is None:
        _default_registry = RetryRegistry()
    return _default_registry


def reset_default_registry() -> None:
    global _default_registry
    _default_registry = None

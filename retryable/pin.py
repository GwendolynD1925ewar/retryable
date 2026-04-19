"""RetryPin — attach a sticky key/value annotation to a retry call session."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class RetryPin:
    """Holds arbitrary key/value annotations pinned to a retry session."""

    _data: Dict[str, Any] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        pass  # reserved for future validation

    def set(self, key: str, value: Any) -> None:
        """Pin a value under *key*."""
        if not key or not key.strip():
            raise ValueError("key must be a non-empty string")
        self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Return the pinned value for *key*, or *default* if absent."""
        return self._data.get(key, default)

    def remove(self, key: str) -> None:
        """Remove a pinned key (no-op if absent)."""
        self._data.pop(key, None)

    def has(self, key: str) -> bool:
        """Return True if *key* is currently pinned."""
        return key in self._data

    def keys(self):
        return list(self._data.keys())

    def as_dict(self) -> Dict[str, Any]:
        """Return a shallow copy of all pinned data."""
        return dict(self._data)

    def clear(self) -> None:
        """Remove all pinned entries."""
        self._data.clear()

    def __repr__(self) -> str:  # pragma: no cover
        return f"RetryPin(data={self._data!r})"


def make_pin(**initial: Any) -> RetryPin:
    """Create a RetryPin pre-populated with *initial* key/value pairs."""
    pin = RetryPin()
    for k, v in initial.items():
        pin.set(k, v)
    return pin

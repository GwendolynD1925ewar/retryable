"""Retry attempt counter with per-key tracking and optional cap enforcement."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional


class CounterCapExceeded(Exception):
    def __init__(self, key: str, cap: int) -> None:
        super().__init__(f"Retry counter cap of {cap} exceeded for key '{key}'")
        self.key = key
        self.cap = cap


@dataclass
class RetryCounter:
    cap: Optional[int] = None
    _counts: Dict[str, int] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.cap is not None and self.cap <= 0:
            raise ValueError("cap must be a positive integer or None")

    def increment(self, key: str) -> int:
        """Increment count for key. Raises CounterCapExceeded if cap is hit."""
        current = self._counts.get(key, 0) + 1
        if self.cap is not None and current > self.cap:
            raise CounterCapExceeded(key, self.cap)
        self._counts[key] = current
        return current

    def get(self, key: str) -> int:
        """Return current count for key (0 if never incremented)."""
        return self._counts.get(key, 0)

    def reset(self, key: str) -> None:
        """Reset count for a specific key."""
        self._counts.pop(key, None)

    def reset_all(self) -> None:
        """Reset all tracked counts."""
        self._counts.clear()

    def keys(self):
        return list(self._counts.keys())

    def __repr__(self) -> str:
        return f"RetryCounter(cap={self.cap}, tracked_keys={len(self._counts)})"

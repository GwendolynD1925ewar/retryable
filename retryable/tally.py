from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional


class TallyLimitExceeded(Exception):
    def __init__(self, key: str, limit: int) -> None:
        super().__init__(f"Retry tally limit {limit} exceeded for key '{key}'")
        self.key = key
        self.limit = limit


@dataclass
class RetryTally:
    """Tracks per-key retry counts with optional per-key limits."""

    default_limit: int
    key_limits: Dict[str, int] = field(default_factory=dict)
    _counts: Dict[str, int] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.default_limit < 1:
            raise ValueError("default_limit must be >= 1")
        for k, v in self.key_limits.items():
            if v < 1:
                raise ValueError(f"limit for key '{k}' must be >= 1")

    def increment(self, key: str) -> int:
        """Increment count for key. Raises TallyLimitExceeded if limit hit."""
        limit = self.key_limits.get(key, self.default_limit)
        current = self._counts.get(key, 0)
        if current >= limit:
            raise TallyLimitExceeded(key, limit)
        self._counts[key] = current + 1
        return self._counts[key]

    def count(self, key: str) -> int:
        return self._counts.get(key, 0)

    def reset(self, key: Optional[str] = None) -> None:
        if key is None:
            self._counts.clear()
        else:
            self._counts.pop(key, None)

    def remaining(self, key: str) -> int:
        limit = self.key_limits.get(key, self.default_limit)
        return max(0, limit - self._counts.get(key, 0))

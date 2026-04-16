"""Sentinel values for retry logic — track and detect special retry outcomes."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional


_MISSING = object()


@dataclass
class RetrySentinel:
    """Wraps a result value to signal a forced retry regardless of success."""
    value: Any = None
    reason: str = ""

    def __repr__(self) -> str:
        return f"RetrySentinel(value={self.value!r}, reason={self.reason!r})"


def is_sentinel(value: Any) -> bool:
    """Return True if value is a RetrySentinel instance."""
    return isinstance(value, RetrySentinel)


def sentinel_predicate(result: Any, exc: Optional[BaseException]) -> bool:
    """Predicate that triggers a retry when the result is a RetrySentinel."""
    if exc is not None:
        return False
    return is_sentinel(result)


def unwrap(value: Any) -> Any:
    """Unwrap a RetrySentinel to its inner value, or return value as-is."""
    if is_sentinel(value):
        return value.value
    return value


@dataclass
class SentinelHistory:
    """Tracks how many times a sentinel result was observed across retry calls."""
    _count: int = field(default=0, init=False)
    _reasons: list[str] = field(default_factory=list, init=False)

    def record(self, sentinel: RetrySentinel) -> None:
        self._count += 1
        if sentinel.reason:
            self._reasons.append(sentinel.reason)

    @property
    def count(self) -> int:
        return self._count

    @property
    def reasons(self) -> list[str]:
        return list(self._reasons)

    def reset(self) -> None:
        self._count = 0
        self._reasons.clear()

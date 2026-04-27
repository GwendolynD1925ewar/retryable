"""RetryMirror — tracks per-key success/failure symmetry across retry attempts."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


class MirrorImbalanced(Exception):
    """Raised when a mirror key exceeds its allowed failure-to-success ratio."""

    def __init__(self, key: str, failures: int, successes: int) -> None:
        self.key = key
        self.failures = failures
        self.successes = successes
        super().__init__(
            f"Mirror imbalance for '{key}': {failures} failures vs {successes} successes"
        )


@dataclass
class MirrorStats:
    successes: int = 0
    failures: int = 0

    @property
    def total(self) -> int:
        return self.successes + self.failures

    @property
    def imbalance_ratio(self) -> float:
        """Return failures / total, or 0.0 when no data."""
        if self.total == 0:
            return 0.0
        return self.failures / self.total

    def __repr__(self) -> str:
        return (
            f"MirrorStats(successes={self.successes}, failures={self.failures}, "
            f"ratio={self.imbalance_ratio:.2f})"
        )


@dataclass
class RetryMirror:
    """Tracks success/failure symmetry per key and raises when imbalance exceeds threshold."""

    threshold: float
    min_samples: int = 5
    _stats: Dict[str, MirrorStats] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        if not (0.0 < self.threshold <= 1.0):
            raise ValueError("threshold must be in (0.0, 1.0]")
        if self.min_samples < 1:
            raise ValueError("min_samples must be >= 1")

    def _get(self, key: str) -> MirrorStats:
        if key not in self._stats:
            self._stats[key] = MirrorStats()
        return self._stats[key]

    def record_success(self, key: str) -> None:
        self._get(key).successes += 1

    def record_failure(self, key: str) -> None:
        self._get(key).failures += 1

    def check(self, key: str) -> None:
        """Raise MirrorImbalanced if the key's ratio exceeds threshold after min_samples."""
        stats = self._get(key)
        if stats.total >= self.min_samples and stats.imbalance_ratio > self.threshold:
            raise MirrorImbalanced(key, stats.failures, stats.successes)

    def stats(self, key: str) -> Optional[MirrorStats]:
        return self._stats.get(key)

    def reset(self, key: str) -> None:
        if key in self._stats:
            del self._stats[key]

    def reset_all(self) -> None:
        self._stats.clear()

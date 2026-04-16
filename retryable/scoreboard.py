"""RetryScoreboard — tracks per-key retry success/failure tallies."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Hashable


@dataclass
class KeyStats:
    successes: int = 0
    failures: int = 0

    @property
    def total(self) -> int:
        return self.successes + self.failures

    @property
    def failure_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return self.failures / self.total

    def __repr__(self) -> str:
        return (
            f"KeyStats(successes={self.successes}, failures={self.failures}, "
            f"failure_rate={self.failure_rate:.2f})"
        )


@dataclass
class RetryScoreboard:
    """Accumulates retry outcome tallies indexed by an arbitrary hashable key."""

    _board: Dict[Hashable, KeyStats] = field(default_factory=dict, init=False)

    def record_success(self, key: Hashable) -> None:
        self._board.setdefault(key, KeyStats()).successes += 1

    def record_failure(self, key: Hashable) -> None:
        self._board.setdefault(key, KeyStats()).failures += 1

    def stats(self, key: Hashable) -> KeyStats:
        return self._board.get(key, KeyStats())

    def keys(self):
        return list(self._board.keys())

    def reset(self, key: Hashable | None = None) -> None:
        if key is None:
            self._board.clear()
        else:
            self._board.pop(key, None)

    def top_failing(self, n: int = 5):
        """Return up to *n* keys sorted by failure count descending."""
        ranked = sorted(self._board.items(), key=lambda kv: kv[1].failures, reverse=True)
        return [(k, v) for k, v in ranked[:n]]

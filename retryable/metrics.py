"""Metrics collection for retry attempts."""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class RetryMetrics:
    """Tracks statistics for a retried callable."""

    total_calls: int = 0
    total_attempts: int = 0
    total_successes: int = 0
    total_failures: int = 0
    total_retries: int = 0
    attempt_counts: List[int] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)

    def record_attempt(self) -> None:
        with self._lock:
            self.total_attempts += 1

    def record_call_result(self, attempts: int, succeeded: bool) -> None:
        """Record the outcome of a single decorated call."""
        with self._lock:
            self.total_calls += 1
            self.total_retries += max(0, attempts - 1)
            self.attempt_counts.append(attempts)
            if succeeded:
                self.total_successes += 1
            else:
                self.total_failures += 1

    @property
    def average_attempts(self) -> Optional[float]:
        with self._lock:
            if not self.attempt_counts:
                return None
            return sum(self.attempt_counts) / len(self.attempt_counts)

    def reset(self) -> None:
        with self._lock:
            self.total_calls = 0
            self.total_attempts = 0
            self.total_successes = 0
            self.total_failures = 0
            self.total_retries = 0
            self.attempt_counts.clear()


_registry: Dict[str, RetryMetrics] = {}
_registry_lock = threading.Lock()


def get_metrics(name: str) -> RetryMetrics:
    """Return (or create) the RetryMetrics instance for *name*."""
    with _registry_lock:
        if name not in _registry:
            _registry[name] = RetryMetrics()
        return _registry[name]


def reset_all() -> None:
    """Reset every registered metrics instance."""
    with _registry_lock:
        for m in _registry.values():
            m.reset()

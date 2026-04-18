"""Retry trace: captures a structured record of every attempt in a call."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional
import time


@dataclass
class TraceEntry:
    attempt: int
    started_at: float
    elapsed: float
    exception: Optional[BaseException] = None
    result: Any = None

    @property
    def succeeded(self) -> bool:
        return self.exception is None

    def __repr__(self) -> str:
        status = "ok" if self.succeeded else f"err={self.exception!r}"
        return f"TraceEntry(attempt={self.attempt}, elapsed={self.elapsed:.4f}s, {status})"


@dataclass
class RetryTrace:
    entries: List[TraceEntry] = field(default_factory=list)

    def record(self, attempt: int, started_at: float, exception: Optional[BaseException] = None, result: Any = None) -> None:
        elapsed = time.monotonic() - started_at
        self.entries.append(TraceEntry(attempt=attempt, started_at=started_at, elapsed=elapsed, exception=exception, result=result))

    @property
    def total_attempts(self) -> int:
        return len(self.entries)

    @property
    def succeeded(self) -> bool:
        return bool(self.entries) and self.entries[-1].succeeded

    @property
    def total_elapsed(self) -> float:
        if not self.entries:
            return 0.0
        return sum(e.elapsed for e in self.entries)

    @property
    def failures(self) -> List[TraceEntry]:
        return [e for e in self.entries if not e.succeeded]

    def __repr__(self) -> str:
        return f"RetryTrace(attempts={self.total_attempts}, succeeded={self.succeeded}, total_elapsed={self.total_elapsed:.4f}s)"

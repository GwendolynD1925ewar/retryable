"""Replay log for recording and inspecting retry attempt history."""

from dataclasses import dataclass, field
from typing import Any, List, Optional
import time


@dataclass
class ReplayEntry:
    attempt: int
    timestamp: float
    exception: Optional[BaseException] = None
    result: Any = None

    @property
    def succeeded(self) -> bool:
        return self.exception is None

    def __repr__(self) -> str:
        status = "ok" if self.succeeded else f"err={type(self.exception).__name__}"
        return f"ReplayEntry(attempt={self.attempt}, {status})"


@dataclass
class RetryReplayLog:
    max_entries: int = 100
    _entries: List[ReplayEntry] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.max_entries < 1:
            raise ValueError("max_entries must be at least 1")

    def record(self, attempt: int, *, exception: Optional[BaseException] = None, result: Any = None) -> None:
        entry = ReplayEntry(
            attempt=attempt,
            timestamp=time.monotonic(),
            exception=exception,
            result=result,
        )
        self._entries.append(entry)
        if len(self._entries) > self.max_entries:
            self._entries.pop(0)

    def entries(self) -> List[ReplayEntry]:
        return list(self._entries)

    def last(self) -> Optional[ReplayEntry]:
        return self._entries[-1] if self._entries else None

    def failures(self) -> List[ReplayEntry]:
        return [e for e in self._entries if not e.succeeded]

    def successes(self) -> List[ReplayEntry]:
        return [e for e in self._entries if e.succeeded]

    def clear(self) -> None:
        self._entries.clear()

    def __len__(self) -> int:
        return len(self._entries)

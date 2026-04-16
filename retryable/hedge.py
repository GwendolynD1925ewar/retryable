"""Hedged retry support: issue a speculative second attempt after a delay."""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


class HedgeCancelled(Exception:
    """Raised internally to signal a hedge attempt was cancelled."""


@dataclass
class HedgePolicy:
    """Configuration for hedged requests."""

    delay: float  # seconds before issuing the hedge
    max_hedges: int = 1

    def __post_init__(self) -> None:
        if self.delay <= 0:
            raise ValueError("delay must be positive")
        if self.max_hedges < 1:
            raise ValueError("max_hedges must be at least 1")


def hedge(policy: HedgePolicy, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Run *fn* and, after *policy.delay* seconds, issue up to *policy.max_hedges*
    speculative duplicate calls.  Return the first result that arrives.
    """
    result_holder: list[Any] = []
    exc_holder: list[BaseException] = []
    winner = threading.Event()
    lock = threading.Lock()

    def attempt() -> None:
        try:
            value = fn(*args, **kwargs)
            with lock:
                if not winner.is_set():
                    result_holder.append(value)
                    winner.set()
        except Exception as exc:  # noqa: BLE001
            with lock:
                exc_holder.append(exc)
                if len(exc_holder) == 1 + policy.max_hedges:
                    winner.set()

    threads = [threading.Thread(target=attempt, daemon=True)]
    threads[0].start()

    for _ in range(policy.max_hedges):
        winner.wait(timeout=policy.delay)
        if winner.is_set():
            break
        t = threading.Thread(target=attempt, daemon=True)
        t.start()
        threads.append(t)

    winner.wait()

    if result_holder:
        return result_holder[0]
    raise exc_holder[0]

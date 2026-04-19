"""Integration helpers for RetryEscalator with the retry decorator."""
from __future__ import annotations
from typing import Any, Optional
from retryable.escalator import RetryEscalator


def build_escalating_on_retry(
    step: float = 2.0,
    max_level: int = 5,
    reset_on_success: bool = True,
) -> dict:
    """Return kwargs suitable for passing to @retry.

    The returned dict contains:
      - 'on_retry': a hook that escalates on each failure
      - 'escalator': the shared RetryEscalator instance
    """
    escalator = RetryEscalator(step=step, max_level=max_level)

    def hook(
        attempt: int,
        exception: Optional[BaseException] = None,
        result: Any = None,
    ) -> None:
        if exception is not None:
            try:
                escalator.escalate()
            except Exception:
                pass
        elif reset_on_success:
            escalator.reset()

    return {"on_retry": hook, "escalator": escalator}


def escalator_predicate(escalator: RetryEscalator, hard_stop: bool = True):
    """Return a predicate that stops retrying once escalator hits max_level."""
    def predicate(
        attempt: int,
        exception: Optional[BaseException] = None,
        result: Any = None,
    ) -> bool:
        if hard_stop and escalator.level >= escalator.max_level:
            return False
        return exception is not None

    return predicate

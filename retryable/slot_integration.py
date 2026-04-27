"""Integration helpers that wire a RetrySlot into the retry decorator."""
from __future__ import annotations

from typing import Any, Optional

from retryable.slot import RetrySlot, SlotUnavailable


def build_slot_on_retry(
    capacity: int,
) -> dict[str, Any]:
    """Return keyword-arguments suitable for passing to ``retry()``.

    The returned dict contains:
    - ``"on_retry"`` – a hook that acquires a slot before each retry and
      releases it when the hook exits (best-effort).
    - ``"slot"`` – the underlying :class:`RetrySlot` instance so callers
      can inspect or reset it.

    Example::

        from retryable import retry
        from retryable.slot_integration import build_slot_on_retry

        kwargs = build_slot_on_retry(capacity=3)
        slot   = kwargs["slot"]

        @retry(max_attempts=5, **{k: v for k, v in kwargs.items() if k != "slot"})
        def call_service():
            ...
    """
    slot = RetrySlot(capacity=capacity)

    def hook(
        attempt: int,
        exception: Optional[BaseException] = None,
        result: Any = None,
    ) -> None:
        # Release the slot from the *previous* attempt before acquiring a new one
        # so that a single logical caller never holds more than one slot.
        slot.release()
        slot.acquire()  # raises SlotUnavailable if pool is full

    return {"on_retry": hook, "slot": slot}


def slot_predicate(slot: RetrySlot):
    """Return a predicate that blocks retries when the slot pool is exhausted."""

    def predicate(
        attempt: int,
        exception: Optional[BaseException] = None,
        result: Any = None,
    ) -> bool:
        return slot.available > 0

    return predicate

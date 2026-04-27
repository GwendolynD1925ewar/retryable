"""Combine RetrySlot with RetryContext for richer per-attempt slot management."""
from __future__ import annotations

from typing import Any, Optional

from retryable.slot import RetrySlot, SlotUnavailable
from retryable.context import RetryContext


def build_context_aware_slot_on_retry(
    capacity: int,
) -> dict[str, Any]:
    """Return retry kwargs that gate retries via a slot pool, logging context.

    Unlike :func:`~retryable.slot_integration.build_slot_on_retry`, this
    variant is intended for use alongside ``RetryContext`` and skips slot
    acquisition on the *first* attempt (attempt == 1) because the first call
    is not a retry.

    Returns a dict with:
    - ``"on_retry"`` – context-aware hook
    - ``"slot"``     – the shared :class:`RetrySlot` instance
    """
    slot = RetrySlot(capacity=capacity)

    def hook(
        attempt: int,
        exception: Optional[BaseException] = None,
        result: Any = None,
    ) -> None:
        """Acquire a slot for each genuine retry (attempt > 1)."""
        if attempt <= 1:
            return
        # Release the slot held by the previous retry before taking a new one.
        slot.release()
        slot.acquire()

    return {"on_retry": hook, "slot": slot}


def release_all(slot: RetrySlot) -> None:
    """Convenience helper — drain the slot pool entirely (e.g. in a finally block)."""
    slot.reset()


def make_slot_summary(slot: RetrySlot) -> str:
    """Return a human-readable summary of the current slot state."""
    return (
        f"RetrySlot capacity={slot.capacity} "
        f"occupied={slot.occupied} available={slot.available}"
    )

"""Integration helpers that connect RetryBarrier with the retry decorator."""
from __future__ import annotations

from typing import Any, Optional

from retryable.barrier import BarrierBlocked, RetryBarrier


def build_barrier_on_retry(
    label: str,
    *,
    auto_lower_after: Optional[float] = None,
) -> dict[str, Any]:
    """Return keyword arguments suitable for passing to ``@retry``.

    The returned dict contains:
    - ``"on_retry"`` — a hook that calls :meth:`RetryBarrier.check` before
      each retry attempt, aborting if the barrier is raised.
    - ``"barrier"`` — the :class:`RetryBarrier` instance so callers can
      raise or lower it externally.

    Example::

        kwargs = build_barrier_on_retry("db-maintenance", auto_lower_after=30.0)
        barrier = kwargs["barrier"]

        @retry(max_attempts=5, on_retry=kwargs["on_retry"])
        def fetch():
            ...

        # Somewhere else:
        barrier.raise_barrier()   # pause retries
        barrier.lower()           # resume retries
    """
    barrier = RetryBarrier(label=label, auto_lower_after=auto_lower_after)

    def hook(exc: Optional[Exception], result: Any, attempt: int) -> None:  # noqa: ANN001
        barrier.check()

    return {"on_retry": hook, "barrier": barrier}


def barrier_predicate(barrier: RetryBarrier):
    """Return a *should-retry* predicate that blocks when the barrier is raised.

    When the barrier is raised the predicate returns ``False``, stopping
    the retry loop immediately (without raising ``BarrierBlocked``).
    """

    def predicate(exc: Optional[Exception], result: Any) -> bool:
        return not barrier.is_raised

    return predicate

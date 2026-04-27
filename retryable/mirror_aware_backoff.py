"""Backoff strategies that incorporate RetryMirror imbalance data."""
from __future__ import annotations

from typing import Callable, Optional

from retryable.mirror import RetryMirror


def make_mirror_scaled_backoff(
    mirror: RetryMirror,
    key: str,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    scale_factor: float = 2.0,
) -> Callable[[int], float]:
    """Return a backoff callable that scales delay by the mirror's imbalance ratio.

    When the mirror shows a high failure ratio for *key*, delays grow faster,
    giving the downstream service more time to recover.

    Args:
        mirror: A :class:`RetryMirror` instance tracking the key.
        key: The mirror key to read the imbalance ratio from.
        base_delay: Minimum delay in seconds (before scaling).
        max_delay: Upper bound on the computed delay.
        scale_factor: Multiplier applied to the base exponential delay.

    Returns:
        A callable ``(attempt: int) -> float`` suitable for use as
        ``on_backoff`` in the ``retry`` decorator.
    """
    if base_delay <= 0:
        raise ValueError("base_delay must be > 0")
    if max_delay <= 0:
        raise ValueError("max_delay must be > 0")
    if scale_factor <= 1.0:
        raise ValueError("scale_factor must be > 1.0")

    def backoff(attempt: int) -> float:
        stats = mirror.stats(key)
        ratio = stats.imbalance_ratio if stats is not None else 0.0
        # Exponential base scaled by imbalance ratio in [1.0, scale_factor]
        dynamic_scale = 1.0 + ratio * (scale_factor - 1.0)
        delay = base_delay * (2 ** (attempt - 1)) * dynamic_scale
        return min(delay, max_delay)

    return backoff


def make_mirror_adaptive_delay(
    mirror: RetryMirror,
    key: str,
    min_delay: float = 0.5,
    max_delay: float = 30.0,
) -> Callable[[int], float]:
    """Return a simpler adaptive delay based purely on the imbalance ratio.

    Interpolates linearly between *min_delay* and *max_delay* using the
    current failure ratio for *key*.
    """
    if min_delay < 0:
        raise ValueError("min_delay must be >= 0")
    if max_delay <= min_delay:
        raise ValueError("max_delay must be > min_delay")

    def backoff(attempt: int) -> float:  # noqa: ARG001
        stats = mirror.stats(key)
        ratio = stats.imbalance_ratio if stats is not None else 0.0
        return min_delay + ratio * (max_delay - min_delay)

    return backoff

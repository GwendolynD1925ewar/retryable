"""Jitter strategies for retry delay randomisation.

Provides standalone jitter callables that can be composed with any
backoff function.  Each strategy accepts a computed ``delay`` (in
seconds, a non-negative float) and returns a new delay value with
randomness applied.

Strategies
----------
- ``no_jitter``      – returns the delay unchanged.
- ``full_jitter``    – uniform random in ``[0, delay]``.
- ``equal_jitter``   – ``delay / 2 + uniform(0, delay / 2)``.
- ``decorrelated``   – decorrelated jitter that drifts away from the
  base delay over successive retries (requires tracking previous delay).
- ``capped_jitter``  – full jitter capped at an absolute maximum.

All callables satisfy the signature::

    (delay: float) -> float

except ``decorrelated``, which requires an additional ``previous``
keyword argument.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable

__all__ = [
    "no_jitter",
    "full_jitter",
    "equal_jitter",
    "capped_jitter",
    "DecorrelatedJitter",
    "make_capped_jitter",
    "JitterFn",
]

# Type alias for a jitter callable.
JitterFn = Callable[[float], float]


def no_jitter(delay: float) -> float:
    """Return *delay* unchanged — effectively disables jitter."""
    return delay


def full_jitter(delay: float) -> float:
    """Return a uniform random value in ``[0, delay]``.

    This is the strategy recommended by AWS for most use-cases because
    it spreads retrying clients evenly across the retry window.
    """
    if delay <= 0:
        return 0.0
    return random.uniform(0.0, delay)


def equal_jitter(delay: float) -> float:
    """Return ``delay / 2`` plus a random value in ``[0, delay / 2]``.

    Guarantees at least half the computed delay is preserved, while
    still introducing meaningful randomness.
    """
    if delay <= 0:
        return 0.0
    half = delay / 2.0
    return half + random.uniform(0.0, half)


def make_capped_jitter(cap: float) -> JitterFn:
    """Return a full-jitter function whose output is capped at *cap* seconds.

    Parameters
    ----------
    cap:
        Maximum delay in seconds.  Must be positive.

    Raises
    ------
    ValueError
        If *cap* is not positive.
    """
    if cap <= 0:
        raise ValueError(f"cap must be positive, got {cap!r}")

    def capped_jitter(delay: float) -> float:  # noqa: WPS430
        effective = min(delay, cap)
        return full_jitter(effective)

    capped_jitter.__doc__ = (
        f"Full jitter capped at {cap} seconds."
    )
    return capped_jitter


# Convenience instance with no cap configuration required.
capped_jitter = make_capped_jitter.__doc__ and None  # placeholder removed below


@dataclass
class DecorrelatedJitter:
    """Stateful decorrelated jitter as described by Marc Brooker.

    Each call returns ``uniform(base, previous * multiplier)``, where
    *previous* is the delay returned by the last call.  This causes
    delays to drift upward over successive retries while remaining
    bounded by *cap*.

    Parameters
    ----------
    base:
        Minimum delay in seconds (also the starting *previous* value).
    cap:
        Maximum delay in seconds.
    multiplier:
        Scaling factor applied to the previous delay.  Defaults to 3.

    Raises
    ------
    ValueError
        If *base* or *cap* are non-positive, or *multiplier* <= 1.
    """

    base: float
    cap: float
    multiplier: float = 3.0
    _previous: float = field(init=False)

    def __post_init__(self) -> None:
        if self.base <= 0:
            raise ValueError(f"base must be positive, got {self.base!r}")
        if self.cap <= 0:
            raise ValueError(f"cap must be positive, got {self.cap!r}")
        if self.multiplier <= 1:
            raise ValueError(
                f"multiplier must be greater than 1, got {self.multiplier!r}"
            )
        self._previous = self.base

    def __call__(self, delay: float) -> float:  # noqa: ARG002
        """Return the next decorrelated jitter value.

        The *delay* argument is accepted for API compatibility with
        other jitter callables but is not used — the internal state
        tracks the previous value instead.
        """
        value = random.uniform(self.base, self._previous * self.multiplier)
        value = min(value, self.cap)
        self._previous = value
        return value

    def reset(self) -> None:
        """Reset internal state so the next call starts from *base*."""
        self._previous = self.base

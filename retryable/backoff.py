"""Backoff strategy implementations for retry logic."""

import random
from typing import Optional


def exponential_backoff(
    attempt: int,
    base_delay: float = 1.0,
    multiplier: float = 2.0,
    max_delay: Optional[float] = None,
) -> float:
    """Calculate exponential backoff delay.

    Args:
        attempt: The current attempt number (0-indexed).
        base_delay: Initial delay in seconds.
        multiplier: Factor by which delay increases each attempt.
        max_delay: Optional cap on the maximum delay.

    Returns:
        Computed delay in seconds.
    """
    delay = base_delay * (multiplier ** attempt)
    if max_delay is not None:
        delay = min(delay, max_delay)
    return delay


def full_jitter(
    delay: float,
) -> float:
    """Apply full jitter to a delay value.

    Randomizes the delay uniformly between 0 and the given delay.

    Args:
        delay: The base delay to jitter.

    Returns:
        A randomized delay between 0 and delay.
    """
    return random.uniform(0, delay)


def equal_jitter(
    delay: float,
) -> float:
    """Apply equal jitter to a delay value.

    Keeps half the delay and randomizes the other half.

    Args:
        delay: The base delay to jitter.

    Returns:
        A jittered delay between delay/2 and delay.
    """
    half = delay / 2.0
    return half + random.uniform(0, half)


def no_jitter(
    delay: float,
) -> float:
    """Return the delay unchanged (no jitter).

    Args:
        delay: The base delay.

    Returns:
        The same delay value.
    """
    return delay


JITTER_STRATEGIES = {
    "full": full_jitter,
    "equal": equal_jitter,
    "none": no_jitter,
}

"""Integration helpers that wire a RateLimiter into the retry decorator."""

from typing import Optional

from retryable.rate_limiter import RateLimiter, make_rate_limited_hook
from retryable.hooks import composite_hook


def build_rate_limited_retry_kwargs(
    rate: float,
    capacity: Optional[float] = None,
    existing_hook=None,
    on_throttled=None,
) -> dict:
    """Build kwargs suitable for passing to @retry that include rate-limiting.

    Args:
        rate: Maximum retry attempts per second.
        capacity: Maximum burst size (defaults to *rate*).
        existing_hook: An existing on_retry hook to compose with.
        on_throttled: Optional callback invoked each time a throttle spin occurs.

    Returns:
        A dict with an ``on_retry`` key ready to unpack into @retry.
    """
    limiter = RateLimiter(rate=rate, capacity=capacity if capacity is not None else rate)
    rl_hook = make_rate_limited_hook(limiter, on_throttled=on_throttled)

    if existing_hook is not None:
        combined = composite_hook(existing_hook, rl_hook)
    else:
        combined = rl_hook

    return {"on_retry": combined, "_rate_limiter": limiter}


def rate_limited_predicate(limiter: RateLimiter):
    """Return a retry predicate that denies retries when no tokens are available.

    Useful when you want hard rejection rather than blocking.
    """

    def predicate(attempt: int, exception=None, result=None) -> bool:
        return limiter.acquire()

    return predicate

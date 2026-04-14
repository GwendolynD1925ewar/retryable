import time
import random
import functools
import logging
from typing import Callable, Optional, Tuple, Type, Union

logger = logging.getLogger(__name__)


def retry(
    max_attempts: int = 3,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    on_retry: Optional[Callable] = None,
):
    """
    A decorator for retrying a function with exponential backoff and optional jitter.

    Args:
        max_attempts: Maximum number of attempts before giving up.
        exceptions: Exception type(s) that trigger a retry.
        base_delay: Initial delay in seconds between retries.
        max_delay: Maximum delay in seconds between retries.
        exponential_base: Base for exponential backoff calculation.
        jitter: Whether to add random jitter to the delay.
        on_retry: Optional callback invoked on each retry with (attempt, exception, delay).
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    if base_delay < 0:
        raise ValueError("base_delay must be non-negative")
    if max_delay < base_delay:
        raise ValueError("max_delay must be >= base_delay")

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exception = exc

                    if attempt == max_attempts:
                        logger.warning(
                            "Function '%s' failed after %d attempts. Giving up.",
                            func.__name__,
                            max_attempts,
                        )
                        raise

                    delay = min(base_delay * (exponential_base ** (attempt - 1)), max_delay)
                    if jitter:
                        delay = random.uniform(0, delay)

                    logger.debug(
                        "Attempt %d/%d for '%s' failed: %s. Retrying in %.2fs.",
                        attempt,
                        max_attempts,
                        func.__name__,
                        exc,
                        delay,
                    )

                    if on_retry is not None:
                        on_retry(attempt, exc, delay)

                    time.sleep(delay)

            raise last_exception  # pragma: no cover

        return wrapper

    return decorator

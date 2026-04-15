"""Lifecycle hooks for retry events."""
from typing import Callable, Optional, Any


def on_retry(
    attempt: int,
    delay: float,
    exception: Optional[BaseException] = None,
    result: Any = None,
) -> None:
    """Default no-op retry hook."""
    pass


def log_retry(
    logger,
    level: str = "warning",
) -> Callable:
    """Return a hook that logs retry attempts using the given logger.

    Args:
        logger: A logger instance (e.g. ``logging.getLogger(__name__)``).
        level:  Log level name to use (default ``"warning"``).

    Returns:
        A hook callable compatible with the ``on_retry`` signature.
    """
    log_fn = getattr(logger, level)

    def hook(
        attempt: int,
        delay: float,
        exception: Optional[BaseException] = None,
        result: Any = None,
    ) -> None:
        if exception is not None:
            log_fn(
                "Retry attempt %d after exception %r; sleeping %.3fs",
                attempt,
                exception,
                delay,
            )
        else:
            log_fn(
                "Retry attempt %d after unsatisfactory result %r; sleeping %.3fs",
                attempt,
                result,
                delay,
            )

    return hook


def composite_hook(*hooks: Callable) -> Callable:
    """Combine multiple hooks into a single callable.

    Each hook is called in order with the same arguments.  Exceptions raised
    by individual hooks are silently suppressed so that one misbehaving hook
    cannot prevent subsequent hooks from running.

    Args:
        *hooks: Hook callables to combine.

    Returns:
        A single hook callable that invokes all provided hooks.
    """
    def hook(
        attempt: int,
        delay: float,
        exception: Optional[BaseException] = None,
        result: Any = None,
    ) -> None:
        for h in hooks:
            try:
                h(attempt=attempt, delay=delay, exception=exception, result=result)
            except Exception:  # noqa: BLE001
                pass

    return hook

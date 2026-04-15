"""Helpers that wire :class:`RetryContext` into the standard retry hook/predicate APIs."""
from __future__ import annotations

from typing import Any, Callable, Optional

from retryable.context import RetryContext

# Type aliases
ContextHook = Callable[[RetryContext], None]
ContextPredicate = Callable[[RetryContext], bool]


def context_hook(fn: ContextHook) -> Callable[..., None]:
    """Adapt a *context-aware* hook ``fn(ctx)`` to the standard ``hook(attempt, exc, result)``
    signature expected by :func:`retryable.core.retry`.

    The returned hook rebuilds a minimal :class:`RetryContext` from the positional
    arguments supplied by the retry engine.  *elapsed* is set to ``0.0`` because the
    engine does not currently expose timing information via the hook signature; use
    :func:`retryable.context.build_context` directly when full timing is required.
    """

    def hook(
        attempt: int,
        exception: Optional[BaseException] = None,
        result: Any = None,
        delay: float = 0.0,
        max_attempts: Optional[int] = None,
    ) -> None:
        ctx = RetryContext(
            attempt=attempt,
            elapsed=0.0,
            delay=delay,
            exception=exception,
            result=result,
            max_attempts=max_attempts,
        )
        fn(ctx)

    return hook


def context_predicate(fn: ContextPredicate) -> Callable[..., bool]:
    """Adapt a *context-aware* predicate ``fn(ctx) -> bool`` to the standard
    ``predicate(attempt, exc, result)`` signature.

    Returns *True* when the retry engine should perform another attempt.
    """

    def predicate(
        attempt: int,
        exception: Optional[BaseException] = None,
        result: Any = None,
        delay: float = 0.0,
        max_attempts: Optional[int] = None,
    ) -> bool:
        ctx = RetryContext(
            attempt=attempt,
            elapsed=0.0,
            delay=delay,
            exception=exception,
            result=result,
            max_attempts=max_attempts,
        )
        return fn(ctx)

    return predicate


def log_context_hook(logger: Any, level: str = "warning") -> ContextHook:
    """Return a :class:`RetryContext`-aware hook that logs retry attempts.

    *logger* should be a standard :class:`logging.Logger` instance.
    *level* must be a valid logger method name (e.g. ``"warning"``, ``"info"``).
    """
    log_fn = getattr(logger, level)

    def hook(ctx: RetryContext) -> None:
        if ctx.exception is not None:
            log_fn(
                "Retry attempt %d after exception: %s (delay=%.3fs)",
                ctx.attempt,
                ctx.exception,
                ctx.delay,
            )
        else:
            log_fn(
                "Retry attempt %d due to unwanted result: %r (delay=%.3fs)",
                ctx.attempt,
                ctx.result,
                ctx.delay,
            )

    return hook

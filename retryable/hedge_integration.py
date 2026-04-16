"""Integration helpers that connect HedgePolicy with the retry decorator."""
from __future__ import annotations

from typing import Any, Callable

from retryable.hedge import HedgePolicy, hedge


def build_hedged_on_retry(policy: HedgePolicy) -> dict[str, Any]:
    """Return kwargs suitable for passing to ``retry()`` that wrap each attempt
    with hedging via *policy*.

    Usage::

        @retry(**build_hedged_on_retry(HedgePolicy(delay=0.05)))
        def fetch(url: str) -> str:
            ...
    """

    def on_retry(exc: BaseException | None, result: Any, attempt: int) -> None:  # noqa: ARG001
        # hook is a no-op; hedging happens inside the wrapped call
        pass

    return {"on_retry": on_retry, "_hedge_policy": policy}


def hedged(policy: HedgePolicy) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator that wraps a callable so every invocation is hedged."""

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return hedge(policy, fn, *args, **kwargs)

        wrapper.__wrapped__ = fn  # type: ignore[attr-defined]
        return wrapper

    return decorator

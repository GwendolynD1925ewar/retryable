"""Integration helpers that wire a RetryLever into the retry decorator."""
from __future__ import annotations

from typing import Any

from retryable.lever import RetryLever


def build_lever_on_backoff(
    *,
    max_position: float = 4.0,
    initial_position: float = 1.0,
) -> dict[str, Any]:
    """Return kwargs suitable for passing to ``@retry`` that apply a lever.

    The returned dict contains:
    - ``"on_backoff"`` — a hook that scales the computed delay via the lever.
    - ``"lever"`` — the :class:`RetryLever` instance so callers can adjust it
      at runtime.

    Example::

        config = build_lever_on_backoff(max_position=8.0)
        lever: RetryLever = config["lever"]

        @retry(max_attempts=5, on_backoff=config["on_backoff"])
        def call_service():
            ...

        # Later, under load, stretch all delays by 3×:
        lever.set(3.0)
    """
    lever = RetryLever(max_position=max_position)
    lever.set(initial_position)

    def on_backoff(delay: float, **_kwargs: Any) -> float:  # type: ignore[return]
        return lever.scale(delay)

    return {"on_backoff": on_backoff, "lever": lever}


def lever_predicate(lever: RetryLever) -> Any:
    """Return a predicate that blocks retries when the lever is at 0.

    A lever position of ``0.0`` signals "stop retrying" — all delays would
    collapse to zero and the caller has explicitly disabled retries.
    """

    def predicate(*, exception: BaseException | None = None, **_: Any) -> bool:
        return lever.position > 0.0

    return predicate

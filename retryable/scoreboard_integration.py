"""Integration helpers that wire RetryScoreboard into retry decorator kwargs."""
from __future__ import annotations
from typing import Any, Hashable
from retryable.scoreboard import RetryScoreboard


def build_scoreboard_on_retry(
    scoreboard: RetryScoreboard,
    key: Hashable,
    *,
    record_on: type[Exception] | tuple[type[Exception], ...] = Exception,
) -> dict:
    """Return ``on_retry`` kwargs that post outcomes to *scoreboard* under *key*.

    Usage::

        sb = RetryScoreboard()
        @retry(**build_scoreboard_on_retry(sb, "fetch_user"), max_attempts=3)
        def fetch_user(uid): ...
    """

    def hook(exc: BaseException | None = None, result: Any = None, **_: Any) -> None:
        if exc is not None and isinstance(exc, record_on):
            scoreboard.record_failure(key)
        else:
            scoreboard.record_success(key)

    return {"on_retry": hook, "scoreboard": scoreboard}


def scoreboard_predicate(scoreboard: RetryScoreboard, key: Hashable, max_failure_rate: float = 1.0):
    """Return a predicate that blocks retries once *key*'s failure rate exceeds threshold."""

    def predicate(exc: BaseException | None = None, result: Any = None, **_: Any) -> bool:
        stats = scoreboard.stats(key)
        if stats.total == 0:
            return True
        return stats.failure_rate <= max_failure_rate

    return predicate

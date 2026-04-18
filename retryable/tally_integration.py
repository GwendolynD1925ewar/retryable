from __future__ import annotations
from typing import Any, Callable, Optional
from retryable.tally import RetryTally, TallyLimitExceeded


def build_tally_on_retry(
    default_limit: int = 5,
    key: str = "default",
    key_limits: Optional[dict] = None,
) -> dict:
    """Build on_retry kwargs dict integrating RetryTally into retry decorator."""
    tally = RetryTally(
        default_limit=default_limit,
        key_limits=key_limits or {},
    )

    def hook(exc: Optional[BaseException] = None, result: Any = None) -> None:
        tally.increment(key)

    return {"on_retry": hook, "tally": tally}


def tally_predicate(tally: RetryTally, key: str = "default") -> Callable[..., bool]:
    """Return a predicate that blocks retries once tally limit is reached."""

    def predicate(exc: Optional[BaseException] = None, result: Any = None) -> bool:
        return tally.remaining(key) > 0

    return predicate

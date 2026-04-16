"""Integration helpers that connect RetryProbe to the retry decorator."""
from __future__ import annotations

from typing import Any, Optional

from retryable.probe import ProbeUnavailable, RetryProbe


def build_probe_on_retry(
    probe: RetryProbe,
) -> dict:
    """Return kwargs suitable for passing to @retry that gate retries via probe.

    Usage::

        probe = RetryProbe(check=lambda: requests.get(url).ok)
        @retry(**build_probe_on_retry(probe), max_attempts=5)
        def fetch(): ...
    """
    return {"on_retry": _make_probe_hook(probe)}


def _make_probe_hook(probe: RetryProbe):
    def hook(
        attempt: int,
        exception: Optional[BaseException] = None,
        result: Any = None,
    ) -> None:
        if not probe.available():
            raise ProbeUnavailable(
                f"probe unavailable after {probe.timeout}s; aborting retry"
            )

    return hook


def probe_predicate(probe: RetryProbe):
    """Return a retry predicate that blocks retries when probe is unavailable."""

    def predicate(
        attempt: int,
        exception: Optional[BaseException] = None,
        result: Any = None,
    ) -> bool:
        if exception is None:
            return False
        return probe.available()

    return predicate

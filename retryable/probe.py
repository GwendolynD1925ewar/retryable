"""Retry probe: health-check predicate that gates retry attempts."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Optional


class ProbeUnavailable(Exception):
    """Raised when a probe reports the target is unavailable."""

    def __init__(self, message: str = "probe reported unavailable") -> None:
        super().__init__(message)


@dataclass
class RetryProbe:
    """Calls a health-check function before allowing a retry.

    Args:
        check: Callable that returns True when the target is healthy.
        timeout: Seconds to wait for the probe to succeed.
        interval: Seconds between probe polls.
    """

    check: Callable[[], bool]
    timeout: float = 5.0
    interval: float = 0.5
    _last_result: Optional[bool] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")
        if self.interval <= 0:
            raise ValueError("interval must be positive")
        if self.interval > self.timeout:
            raise ValueError("interval must not exceed timeout")

    def available(self) -> bool:
        """Poll the probe until healthy or timeout expires."""
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            try:
                result = self.check()
            except Exception:
                result = False
            self._last_result = result
            if result:
                return True
            time.sleep(self.interval)
        return False

    @property
    def last_result(self) -> Optional[bool]:
        return self._last_result

"""RetrySignal — a lightweight pub/sub mechanism for retry lifecycle events."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional


@dataclass
class RetrySignalEvent:
    attempt: int
    exception: Optional[BaseException] = None
    result: object = None
    cancelled: bool = False

    @property
    def succeeded(self) -> bool:
        return self.exception is None and not self.cancelled

    def __repr__(self) -> str:
        return (
            f"RetrySignalEvent(attempt={self.attempt}, "
            f"succeeded={self.succeeded}, cancelled={self.cancelled})"
        )


Handler = Callable[[RetrySignalEvent], None]


@dataclass
class RetrySignal:
    """Broadcast retry lifecycle events to registered handlers."""

    _handlers: List[Handler] = field(default_factory=list, init=False, repr=False)

    def subscribe(self, handler: Handler) -> None:
        """Register a handler to receive events."""
        if not callable(handler):
            raise TypeError("handler must be callable")
        self._handlers.append(handler)

    def unsubscribe(self, handler: Handler) -> None:
        """Remove a previously registered handler."""
        self._handlers.remove(handler)

    def emit(self, event: RetrySignalEvent) -> None:
        """Broadcast event to all registered handlers."""
        for handler in list(self._handlers):
            handler(event)

    @property
    def subscriber_count(self) -> int:
        return len(self._handlers)

    def clear(self) -> None:
        """Remove all registered handlers."""
        self._handlers.clear()


def build_signal_on_retry(signal: RetrySignal) -> dict:
    """Return retry kwargs that emit a signal on each retry hook call."""

    def hook(attempt: int, exception: Optional[BaseException] = None, result: object = None, **_) -> None:
        event = RetrySignalEvent(attempt=attempt, exception=exception, result=result)
        signal.emit(event)

    return {"on_retry": hook, "signal": signal}

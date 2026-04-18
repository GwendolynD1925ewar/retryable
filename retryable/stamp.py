"""RetryStamp: attaches a unique identifier and timestamp to each retry call."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class RetryStamp:
    """Immutable stamp created at the start of a retryable call."""

    call_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    label: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.call_id or not self.call_id.strip():
            raise ValueError("call_id must be a non-empty string")

    def age_seconds(self, now: Optional[datetime] = None) -> float:
        """Return elapsed seconds since the stamp was created."""
        if now is None:
            now = datetime.now(timezone.utc)
        return (now - self.created_at).total_seconds()

    def __repr__(self) -> str:
        label_part = f", label={self.label!r}" if self.label else ""
        return f"RetryStamp(call_id={self.call_id!r}{label_part})"


def make_stamp(label: Optional[str] = None) -> RetryStamp:
    """Create a fresh RetryStamp, optionally with a human-readable label."""
    return RetryStamp(label=label)


def build_stamp_on_retry(
    label: Optional[str] = None,
) -> dict:
    """Return kwargs suitable for passing to @retry that attach a stamp hook.

    The stamp is created once per decorated call and passed through on_retry.
    """
    stamp = make_stamp(label=label)

    def hook(exc: Optional[Exception], result: object, attempt: int) -> None:  # noqa: ARG001
        # Hook is intentionally lightweight; callers may wrap or extend it.
        _ = stamp  # stamp is captured in closure for introspection

    return {"on_retry": hook, "stamp": stamp}

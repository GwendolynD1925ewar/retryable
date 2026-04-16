"""Retry tagging — attach arbitrary string tags to retry attempts for filtering and observability."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import FrozenSet, Iterable


@dataclass(frozen=True)
class RetryTag:
    """An immutable set of string tags associated with a retry call."""
    tags: FrozenSet[str]

    def __post_init__(self) -> None:
        if not self.tags:
            raise ValueError("tags must not be empty")
        for t in self.tags:
            if not isinstance(t, str) or not t.strip():
                raise ValueError(f"each tag must be a non-empty string, got {t!r}")

    def has(self, tag: str) -> bool:
        """Return True if the given tag is present."""
        return tag in self.tags

    def matches_any(self, tags: Iterable[str]) -> bool:
        """Return True if any of the given tags are present."""
        return bool(self.tags & frozenset(tags))

    def matches_all(self, tags: Iterable[str]) -> bool:
        """Return True if all of the given tags are present."""
        return frozenset(tags) <= self.tags

    def merge(self, other: "RetryTag") -> "RetryTag":
        """Return a new RetryTag combining both sets."""
        return RetryTag(self.tags | other.tags)

    def __repr__(self) -> str:
        return f"RetryTag(tags={sorted(self.tags)!r})"


def make_tag(*tags: str) -> RetryTag:
    """Convenience constructor for RetryTag."""
    return RetryTag(frozenset(tags))

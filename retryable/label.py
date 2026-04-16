"""Retry label support for tagging attempts with named identifiers."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RetryLabel:
    """Associates a string label with a retry operation for logging/tracking."""
    name: str
    group: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("label name must be a non-empty string")
        if self.group is not None and not self.group.strip():
            raise ValueError("label group must be a non-empty string if provided")
        self.name = self.name.strip()
        if self.group:
            self.group = self.group.strip()

    def qualified(self) -> str:
        """Return group.name if group is set, else just name."""
        if self.group:
            return f"{self.group}.{self.name}"
        return self.name

    def matches(self, name: str) -> bool:
        return self.name == name

    def in_group(self, group: str) -> bool:
        return self.group == group

    def __repr__(self) -> str:
        return f"RetryLabel(name={self.name!r}, group={self.group!r})"

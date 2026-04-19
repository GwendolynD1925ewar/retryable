"""RetryEscalator: escalate delay multiplier after repeated failures."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


class EscalationLimitReached(Exception):
    def __init__(self, level: int) -> None:
        super().__init__(f"Escalation limit reached at level {level}")
        self.level = level


@dataclass
class RetryEscalator:
    """Tracks escalation levels and returns an increasing multiplier."""
    step: float = 2.0
    max_level: int = 5
    _level: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.step <= 1.0:
            raise ValueError("step must be greater than 1.0")
        if self.max_level < 1:
            raise ValueError("max_level must be at least 1")

    def escalate(self) -> float:
        """Increment level and return current multiplier."""
        if self._level >= self.max_level:
            raise EscalationLimitReached(self._level)
        self._level += 1
        return self.multiplier

    def reset(self) -> None:
        self._level = 0

    @property
    def level(self) -> int:
        return self._level

    @property
    def multiplier(self) -> float:
        return self.step ** self._level

    def history(self) -> List[float]:
        return [self.step ** i for i in range(self._level + 1)]

    def __repr__(self) -> str:
        return (
            f"RetryEscalator(step={self.step}, max_level={self.max_level}, "
            f"level={self._level}, multiplier={self.multiplier})"
        )

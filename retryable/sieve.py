"""RetryS ieve — filter which attempts are eligible for retry based on a scoring function."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional


class SieveRejected(Exception):
    """Raised when the sieve rejects an attempt."""

    def __init__(self, attempt: int, score: float, threshold: float) -> None:
        self.attempt = attempt
        self.score = score
        self.threshold = threshold
        super().__init__(
            f"Attempt {attempt} rejected by sieve (score={score:.3f} < threshold={threshold:.3f})"
        )


@dataclass
class RetrySieve:
    """Allows retry only when a scorer returns a value >= threshold."""

    threshold: float
    scorer: Callable[[int, Optional[Exception]], float]
    _scores: list[float] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        if not 0.0 <= self.threshold <= 1.0:
            raise ValueError("threshold must be between 0.0 and 1.0")

    def evaluate(self, attempt: int, exc: Optional[Exception] = None) -> float:
        """Compute and record the score for this attempt."""
        score = self.scorer(attempt, exc)
        self._scores.append(score)
        return score

    def allowed(self, attempt: int, exc: Optional[Exception] = None) -> bool:
        """Return True if the attempt passes the sieve."""
        return self.evaluate(attempt, exc) >= self.threshold

    def require(self, attempt: int, exc: Optional[Exception] = None) -> None:
        """Raise SieveRejected if the attempt does not pass."""
        score = self.evaluate(attempt, exc)
        if score < self.threshold:
            raise SieveRejected(attempt, score, self.threshold)

    @property
    def scores(self) -> list[float]:
        return list(self._scores)

    @property
    def average_score(self) -> Optional[float]:
        if not self._scores:
            return None
        return sum(self._scores) / len(self._scores)

    def reset(self) -> None:
        self._scores.clear()

"""RetryLever — a manually adjustable multiplier that scales retry delays at runtime."""
from __future__ import annotations

from dataclasses import dataclass, field


class LeverOutOfRange(Exception):
    """Raised when the lever position is set outside its allowed bounds."""

    def __init__(self, position: float, lo: float, hi: float) -> None:
        super().__init__(
            f"Lever position {position!r} is outside allowed range [{lo}, {hi}]."
        )
        self.position = position
        self.lo = lo
        self.hi = hi


@dataclass
class RetryLever:
    """A runtime-adjustable multiplier applied to computed backoff delays.

    The lever sits between 0.0 and *max_position* (inclusive).  A position of
    ``1.0`` is neutral (no scaling).  Values above 1.0 stretch delays; values
    below 1.0 compress them.
    """

    max_position: float = 4.0
    _position: float = field(default=1.0, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.max_position <= 0.0:
            raise ValueError("max_position must be greater than 0.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def position(self) -> float:
        """Current lever position."""
        return self._position

    def set(self, position: float) -> None:
        """Move the lever to *position*.

        Raises:
            LeverOutOfRange: if *position* is outside ``[0.0, max_position]``.
        """
        if not (0.0 <= position <= self.max_position):
            raise LeverOutOfRange(position, 0.0, self.max_position)
        self._position = position

    def reset(self) -> None:
        """Return the lever to the neutral position (1.0)."""
        self._position = 1.0

    def scale(self, delay: float) -> float:
        """Return *delay* multiplied by the current lever position."""
        return delay * self._position

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"RetryLever(position={self._position!r}, "
            f"max_position={self.max_position!r})"
        )

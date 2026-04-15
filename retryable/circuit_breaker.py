"""Circuit breaker support for retryable."""

import threading
import time
from enum import Enum
from typing import Optional


class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation, requests allowed
    OPEN = "open"          # Failing, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerError(Exception):
    """Raised when the circuit breaker is open and rejects a call."""

    def __init__(self, name: str, reset_in: float):
        self.name = name
        self.reset_in = reset_in
        super().__init__(
            f"Circuit breaker '{name}' is OPEN. "
            f"Resets in {reset_in:.2f}s."
        )


class CircuitBreaker:
    """Thread-safe circuit breaker that integrates with the retry decorator."""

    def __init__(
        self,
        name: str = "default",
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 1,
    ):
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        if recovery_timeout <= 0:
            raise ValueError("recovery_timeout must be > 0")
        if half_open_max_calls < 1:
            raise ValueError("half_open_max_calls must be >= 1")

        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._opened_at: Optional[float] = None
        self._half_open_calls = 0
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            return self._get_state()

    def _get_state(self) -> CircuitState:
        """Internal state check; must be called with lock held."""
        if self._state == CircuitState.OPEN:
            elapsed = time.monotonic() - (self._opened_at or 0)
            if elapsed >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0
        return self._state

    def allow_request(self) -> bool:
        """Return True if a request should be allowed through."""
        with self._lock:
            state = self._get_state()
            if state == CircuitState.CLOSED:
                return True
            if state == CircuitState.OPEN:
                return False
            # HALF_OPEN
            if self._half_open_calls < self.half_open_max_calls:
                self._half_open_calls += 1
                return True
            return False

    def record_success(self) -> None:
        """Record a successful call; closes the circuit if half-open."""
        with self._lock:
            self._failure_count = 0
            self._state = CircuitState.CLOSED
            self._opened_at = None

    def record_failure(self) -> None:
        """Record a failed call; may open the circuit."""
        with self._lock:
            self._failure_count += 1
            if (
                self._state == CircuitState.HALF_OPEN
                or self._failure_count >= self.failure_threshold
            ):
                self._state = CircuitState.OPEN
                self._opened_at = time.monotonic()

    def reset(self) -> None:
        """Manually reset the circuit breaker to closed state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._opened_at = None
            self._half_open_calls = 0

    def reset_in(self) -> float:
        """Seconds until the circuit transitions from OPEN to HALF_OPEN."""
        with self._lock:
            if self._state != CircuitState.OPEN or self._opened_at is None:
                return 0.0
            elapsed = time.monotonic() - self._opened_at
            return max(0.0, self.recovery_timeout - elapsed)

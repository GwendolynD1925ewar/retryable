"""retryable — configurable retry logic with exponential backoff and jitter support."""
from retryable.core import retry
from retryable.backoff import exponential_backoff, full_jitter, equal_jitter, no_jitter
from retryable.predicates import on_exception, on_result, never_retry
from retryable.budget import RetryBudget
from retryable.hooks import on_retry, log_retry, composite_hook
from retryable.timeout import RetryTimeout
from retryable.circuit_breaker import CircuitBreaker, CircuitBreakerError, CircuitState
from retryable.circuit_breaker_integration import (
    circuit_breaker_hook,
    guard_with_circuit_breaker,
    make_circuit_breaker_predicate,
)
from retryable.metrics import RetryMetrics
from retryable.metrics_hook import metrics_hook, make_tracked_hook
from retryable.rate_limiter import RateLimiter
from retryable.rate_limiter_integration import build_rate_limited_retry_kwargs
from retryable.context import RetryContext, build_context
from retryable.context_integration import context_hook, context_predicate, log_context_hook
from retryable.fallback import FallbackResult, static_fallback, raise_fallback
from retryable.fallback_integration import with_static_fallback, with_callable_fallback
from retryable.deadline import AttemptDeadline, AttemptDeadlineExceeded
from retryable.deadline_integration import build_deadline_on_retry, deadline_predicate
from retryable.throttle import RetryThrottle, ThrottleExceeded
from retryable.throttle_integration import build_throttled_on_retry, throttle_predicate
from retryable.cache import RetryCache
from retryable.snapshot import RetrySnapshot, SnapshotHistory
from retryable.cooldown import RetryCooldown, CooldownActive
from retryable.cooldown_integration import build_cooldown_on_retry, cooldown_predicate
from retryable.watermark import RetryWatermark
from retryable.replay import RetryReplayLog, ReplayEntry
from retryable.window import RetryWindow
from retryable.hedge import HedgePolicy, HedgeCancelled
from retryable.hedge_integration import build_hedged_on_retry
from retryable.probe import RetryProbe, ProbeUnavailable
from retryable.probe_integration import build_probe_on_retry
from retryable.probe_cache_integration import CachedProbe, build_cached_probe_on_retry
from retryable.tag import RetryTag, make_tag
from retryable.tag_integration import build_tagged_on_retry, tag_predicate

__all__ = [
    "retry",
    "exponential_backoff", "full_jitter", "equal_jitter", "no_jitter",
    "on_exception", "on_result", "never_retry",
    "RetryBudget",
    "on_retry", "log_retry", "composite_hook",
    "RetryTimeout",
    "CircuitBreaker", "CircuitBreakerError", "CircuitState",
    "circuit_breaker_hook", "guard_with_circuit_breaker", "make_circuit_breaker_predicate",
    "RetryMetrics", "metrics_hook", "make_tracked_hook",
    "RateLimiter", "build_rate_limited_retry_kwargs",
    "RetryContext", "build_context",
    "context_hook", "context_predicate", "log_context_hook",
    "FallbackResult", "static_fallback", "raise_fallback",
    "with_static_fallback", "with_callable_fallback",
    "AttemptDeadline", "AttemptDeadlineExceeded",
    "build_deadline_on_retry", "deadline_predicate",
    "RetryThrottle", "ThrottleExceeded",
    "build_throttled_on_retry", "throttle_predicate",
    "RetryCache",
    "RetrySnapshot", "SnapshotHistory",
    "RetryCooldown", "CooldownActive",
    "build_cooldown_on_retry", "cooldown_predicate",
    "RetryWatermark",
    "RetryReplayLog", "ReplayEntry",
    "RetryWindow",
    "HedgePolicy", "HedgeCancelled", "build_hedged_on_retry",
    "RetryProbe", "ProbeUnavailable", "build_probe_on_retry",
    "CachedProbe", "build_cached_probe_on_retry",
    "RetryTag", "make_tag",
    "build_tagged_on_retry", "tag_predicate",
]

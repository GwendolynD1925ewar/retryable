"""Hook integration that feeds retry events into RetryMetrics."""
from __future__ import annotations

from typing import Any, Callable, Optional

from retryable.metrics import RetryMetrics, get_metrics


def metrics_hook(
    metrics: Optional[RetryMetrics] = None,
    name: str = "default",
) -> Callable[..., None]:
    """Return a retry hook that records each retry attempt.

    Parameters
    ----------
    metrics:
        An explicit :class:`RetryMetrics` instance to use.  When *None* the
        global registry is consulted via *name*.
    name:
        Registry key used when *metrics* is not provided.
    """
    _metrics = metrics if metrics is not None else get_metrics(name)

    def hook(
        attempt: int,
        exception: Optional[BaseException] = None,
        result: Any = None,
    ) -> None:
        _metrics.record_attempt()

    return hook


def make_tracked_hook(
    metrics: Optional[RetryMetrics] = None,
    name: str = "default",
    inner_hook: Optional[Callable[..., None]] = None,
) -> Callable[..., None]:
    """Combine metrics recording with an optional user-supplied hook.

    The *inner_hook* is called **after** metrics are recorded so that
    metrics are always updated even if *inner_hook* raises.
    """
    _m_hook = metrics_hook(metrics=metrics, name=name)

    def hook(
        attempt: int,
        exception: Optional[BaseException] = None,
        result: Any = None,
    ) -> None:
        _m_hook(attempt, exception=exception, result=result)
        if inner_hook is not None:
            inner_hook(attempt, exception=exception, result=result)

    return hook

"""Integration helpers for using RetryLabel with the retry decorator."""
from typing import Any, Optional
from retryable.label import RetryLabel


def build_labeled_on_retry(name: str, group: Optional[str] = None):
    """Return kwargs for retry() that attach a RetryLabel via on_retry hook."""
    label = RetryLabel(name=name, group=group)

    def hook(exception: Optional[Exception] = None, result: Any = None) -> None:
        # Hook is a no-op by default; label is accessible via closure.
        pass

    return {"on_retry": hook, "label": label}


def label_predicate(label: RetryLabel, allowed_groups: Optional[list] = None):
    """Return a predicate that allows retries only for matching label groups."""
    def predicate(exception: Optional[Exception] = None, result: Any = None) -> bool:
        if allowed_groups is None:
            return True
        return label.group in allowed_groups
    return predicate


def format_label_attempt(label: RetryLabel, attempt: int) -> str:
    """Format a human-readable string for a labeled retry attempt."""
    return f"[{label.qualified()}] attempt {attempt}"

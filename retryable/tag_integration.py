"""Integration helpers for attaching RetryTag to retry decorator kwargs."""
from __future__ import annotations
from typing import Any, Callable, Dict
from retryable.tag import RetryTag, make_tag


def build_tagged_on_retry(
    *tags: str,
    on_retry: Callable[..., None] | None = None,
) -> Dict[str, Any]:
    """Return kwargs dict with an on_retry hook that stamps each attempt with tags.

    The hook records which tags are active; an optional upstream hook is also called.
    """
    tag = make_tag(*tags)

    def hook(exception: BaseException | None = None, result: Any = None, **kwargs: Any) -> None:
        # Expose tag on the hook closure for introspection in tests / observability.
        hook.last_tag = tag  # type: ignore[attr-defined]
        if on_retry is not None:
            on_retry(exception=exception, result=result, **kwargs)

    hook.last_tag = None  # type: ignore[attr-defined]
    hook.tag = tag  # type: ignore[attr-defined]

    return {"on_retry": hook, "tag": tag}


def tag_predicate(required_tags: list[str], inner_predicate: Callable[..., bool]) -> Callable[..., bool]:
    """Wrap a predicate so it only retries when the RetryTag matches required tags.

    If no tag is available the inner predicate result is returned unchanged.
    """
    required = frozenset(required_tags)

    def predicate(exception: BaseException | None = None, result: Any = None, tag: RetryTag | None = None, **kwargs: Any) -> bool:
        if tag is not None and not tag.matches_all(required):
            return False
        return inner_predicate(exception=exception, result=result, **kwargs)

    return predicate

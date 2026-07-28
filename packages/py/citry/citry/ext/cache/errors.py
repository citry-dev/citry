"""Public errors raised by render-cache key construction."""

from __future__ import annotations


class CacheArtifactError(ValueError):
    """A stored render artifact is malformed, unsupported, or unsafe to replay."""


class _CacheArtifactCompatibilityError(CacheArtifactError):
    """A well-formed artifact targets another render-cache format generation."""


class _CacheUncacheableError(CacheArtifactError):
    """A settled subtree contains output that an extension cannot replay."""

    def __init__(self, extension_name: str) -> None:
        self.extension_name = extension_name
        super().__init__(f"Extension {extension_name!r} participated in this render and denies render caching.")


class _CacheArtifactOversizedError(CacheArtifactError):
    """A rendered artifact exceeds a configured or absolute storage limit."""

    def __init__(self, *, size: int | None, limit: int) -> None:
        self.size = size
        self.limit = limit
        size_text = "unknown" if size is None else f"{size:,}"
        super().__init__(f"Cached render artifact is {size_text} bytes, exceeding max_entry_bytes={limit:,}.")


class _CacheRevisionChanged(CacheArtifactError):
    """Internal retry signal when invalidation crosses a cache lookup."""

    def __init__(self) -> None:
        super().__init__("The render-cache revision changed during the cache operation.")


class CacheKeyError(ValueError):
    """
    A value cannot be represented safely in a render-cache key.

    Attributes:
        path: Location of the rejected value within the semantic variation.
        reason: Human-readable reason the value was rejected.

    """

    def __init__(self, path: str, reason: str) -> None:
        self.path = path
        self.reason = reason
        super().__init__(
            f"Invalid render-cache key value at {path}: {reason}. Convert it to supported built-in values in "
            'Cache.vary() or <c-cache c-vary="...">.'
        )

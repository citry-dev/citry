"""
The pluggable cache backend.

Citry stores some derived content in a cache: today the dependencies
extension's processed JS/CSS scripts (so they can be served over HTTP, see
docs/design/dependencies.md section 10), later also cached component renders.
The backend is pluggable so that deployments with multiple processes can point
all of them at one shared store::

    app = Citry(cache=MyRedisCache())          # any object with the 4 methods
    app = Citry(cache="myproj.caches.Cache")   # or an import string

When no cache is given, each ``Citry`` instance gets its own
:class:`InMemoryCache`. That is right for a single process; with multiple
workers, content written by one process (for example the JS-variables scripts
behind fragment requests) is not visible to the others, so production setups
that use fragments should configure a shared backend.

Values are strings on purpose (citry stores JSON), so any string store can be
adapted in a few lines.
"""

from __future__ import annotations

import time
from collections import OrderedDict
from typing import Protocol, runtime_checkable


@runtime_checkable
class CitryCache(Protocol):
    """
    The cache backend interface.

    Implement these four methods to plug in any store (Redis, diskcache,
    Django's cache framework, ...). Keys and values are strings.
    """

    def get(self, key: str) -> str | None:
        """Return the value for ``key``, or ``None`` when absent or expired."""
        ...  # pragma: no cover - protocol

    def set(self, key: str, value: str, ttl: float | None = None) -> None:
        """Store ``value`` under ``key``. ``ttl`` is seconds until expiry; ``None`` means keep forever."""
        ...  # pragma: no cover - protocol

    def delete(self, key: str) -> None:
        """Remove ``key`` if present (no error when absent)."""
        ...  # pragma: no cover - protocol

    def has(self, key: str) -> bool:
        """Whether ``key`` is present (and not expired)."""
        ...  # pragma: no cover - protocol


class InMemoryCache:
    """
    The default cache backend: a plain in-process dict.

    Unbounded by default. Pass ``max_entries`` to cap the size; when full,
    the entry that was read or written longest ago is dropped to make room.

    Single-process only: each instance is its own store. For multi-worker
    deployments use a shared backend instead (see the module docstring).
    """

    def __init__(self, max_entries: int | None = None) -> None:
        if max_entries is not None and max_entries <= 0:
            msg = f"max_entries must be a positive number or None, got {max_entries!r}"
            raise ValueError(msg)
        self._max_entries = max_entries
        # key -> (value, expiry deadline in time.monotonic() terms, or None).
        # Insertion order doubles as recency order: reads and writes move the
        # entry to the end, so the front is always the stalest entry.
        self._data: OrderedDict[str, tuple[str, float | None]] = OrderedDict()

    def get(self, key: str) -> str | None:
        entry = self._data.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if expires_at is not None and time.monotonic() >= expires_at:
            del self._data[key]
            return None
        self._data.move_to_end(key)
        return value

    def set(self, key: str, value: str, ttl: float | None = None) -> None:
        expires_at = time.monotonic() + ttl if ttl is not None else None
        self._data[key] = (value, expires_at)
        self._data.move_to_end(key)
        if self._max_entries is not None:
            while len(self._data) > self._max_entries:
                self._data.popitem(last=False)

    def delete(self, key: str) -> None:
        self._data.pop(key, None)

    def has(self, key: str) -> bool:
        return self.get(key) is not None

    def clear(self) -> None:
        """Drop all entries. Called by ``Citry.clear()``."""
        self._data.clear()

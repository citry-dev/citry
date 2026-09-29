"""
The pluggable cache backend.

Citry stores derived content in a cache: replayable component and named-fragment
render artifacts, the dependencies extension's processed JS/CSS scripts and
served ``Dependencies`` files, optional server-held Events State, and, when
a backend is configured, the compiled Vue definition bundles and stylesheets
that interactive pages load. (Without one, each engine keeps those in its
process, up to ``CitrySettings.vue_asset_max_bytes``.)
The backend is pluggable so deployments with multiple processes can point all
of them at one shared store::

    app = Citry(cache=MyRedisCache())          # any object with the 4 methods
    app = Citry(cache="myproj.caches.Cache")   # or an import string

When no cache is given, each ``Citry`` instance gets its own
:class:`InMemoryCache`. That is right for a single process. With multiple
workers, content written by one process is not visible to the others: a page
rendered by one worker links a Vue definition bundle or a ``css_data()``
stylesheet by URL, and the browser may fetch that URL from another worker,
which answers 404. Production setups with more than one worker should
configure a shared backend.

Values are strings on purpose (citry stores JSON), so any string store can be
adapted in a few lines.
"""

from __future__ import annotations

import math
import time
from collections import OrderedDict
from threading import Lock
from typing import TYPE_CHECKING, Protocol, cast, runtime_checkable
from weakref import WeakKeyDictionary

if TYPE_CHECKING:
    from collections.abc import Callable


def _normalize_ttl(value: object, *, source: str = "ttl") -> float | None:
    """Validate and normalize one first-party cache TTL in seconds."""
    if value is None:
        return None
    if type(value) not in (int, float):
        msg = f"{source} must be None or a non-negative finite int or float; got {value!r}"
        raise ValueError(msg)
    try:
        normalized = float(cast("int | float", value))
    except OverflowError as err:
        msg = f"{source} must be representable as finite seconds; got an integer that is too large"
        raise ValueError(msg) from err
    if not math.isfinite(normalized) or normalized < 0:
        msg = f"{source} must be None or a non-negative finite int or float; got {value!r}"
        raise ValueError(msg)
    # All first-party stores treat either signed zero as immediate expiry.
    return 0.0 if normalized == 0 else normalized


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
    The default cache backend: a thread-safe in-process LRU store.

    Unbounded by default. Pass ``max_entries`` to cap the size; when full,
    the entry that was read or written longest ago is dropped to make room.

    Single-process only: each instance is its own store. For multi-worker
    deployments use a shared backend instead (see the module docstring).
    """

    def __init__(self, max_entries: int | None = None) -> None:
        if max_entries is not None and (type(max_entries) is not int or max_entries <= 0):
            msg = f"max_entries must be a positive int or None, got {max_entries!r}"
            raise ValueError(msg)
        self._max_entries = max_entries
        self._lock = Lock()
        # key -> (value, expiry deadline in time.monotonic() terms, or None).
        # Insertion order doubles as recency order: reads and writes move the
        # entry to the end, so the front is always the stalest entry.
        self._data: OrderedDict[str, tuple[str, float | None]] = OrderedDict()

    def get(self, key: str) -> str | None:
        with self._lock:
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
        normalized_ttl = _normalize_ttl(ttl)
        with self._lock:
            if normalized_ttl == 0:
                self._data.pop(key, None)
                return
            now = time.monotonic()
            expires_at = now + normalized_ttl if normalized_ttl is not None else None
            self._data[key] = (value, expires_at)
            self._data.move_to_end(key)
            if self._max_entries is not None:
                self._purge_expired(now)
                while len(self._data) > self._max_entries:
                    self._data.popitem(last=False)

    def _purge_expired(self, now: float) -> None:
        """Remove expired entries while the caller holds ``_lock``."""
        expired = [key for key, (_, deadline) in self._data.items() if deadline is not None and now >= deadline]
        for key in expired:
            del self._data[key]

    def delete(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)

    def has(self, key: str) -> bool:
        return self.get(key) is not None

    def clear(self) -> None:
        """Drop all entries. Called by ``Citry.clear()``."""
        with self._lock:
            self._data.clear()


# Content-addressed entries (compiled Vue code, stylesheets, served
# ``Dependencies`` files) are written once and read many times, but the page
# that links one is rendered again and again. Asking a shared backend "do you
# still have it?" on every render costs one network round trip per asset per
# render, so each process remembers which keys it has already seen stored.
# The memory is per ``Citry`` instance (the owner below), because two engines
# may point at different backends.
#
# How long a remembered key is trusted before the backend is asked again. A
# shared backend can drop an entry (memory pressure, a manual flush), and
# only a process that renders a page linking it can write it back. Re-asking
# after this interval bounds how long other workers may answer 404 for it,
# while keeping the check to one per key per interval instead of per render.
_STORED_KEY_RECHECK_SECONDS = 60.0
# How many keys each engine remembers. A forgotten key is only re-checked on
# its next write, so this bounds memory without affecting correctness.
_STORED_KEY_LIMIT = 4096
_STORED_KEYS: WeakKeyDictionary[object, OrderedDict[str, float]] = WeakKeyDictionary()
# Renders on several threads write through the same engine's record.
_STORED_KEYS_LOCK = Lock()


def _store_if_missing(owner: object, cache: CitryCache, key: str, value: Callable[[], str]) -> None:
    """
    Make sure ``cache`` holds ``key``, asking the backend at most once per recheck interval.

    ``value`` is called only when the entry must be written, so a large body
    is encoded and sent only then. The entry is written without a TTL: an
    open page can ask for it at any later time. Backend errors propagate, so
    a render never links an entry that failed to store.
    """
    now = time.monotonic()
    with _STORED_KEYS_LOCK:
        remembered = _STORED_KEYS.get(owner)
        confirmed_at = None if remembered is None else remembered.get(key)
    # Seen stored recently: trust it and skip the round trip.
    if confirmed_at is not None and now - confirmed_at < _STORED_KEY_RECHECK_SECONDS:
        return
    # ``has`` before ``set`` sends the body only when the backend lacks it,
    # including after the backend dropped it.
    if not cache.has(key):
        cache.set(key, value())
    with _STORED_KEYS_LOCK:
        remembered = _STORED_KEYS.setdefault(owner, OrderedDict())
        remembered[key] = now
        remembered.move_to_end(key)
        while len(remembered) > _STORED_KEY_LIMIT:
            remembered.popitem(last=False)


def _forget_stored_key(owner: object, key: str) -> None:
    """Make the next ``_store_if_missing`` for ``key`` ask the backend again (the entry was removed)."""
    with _STORED_KEYS_LOCK:
        remembered = _STORED_KEYS.get(owner)
        if remembered is not None:
            remembered.pop(key, None)


def _forget_stored_keys(owner: object) -> None:
    """Forget every key remembered for ``owner``, e.g. after ``Citry.clear()`` emptied its cache."""
    with _STORED_KEYS_LOCK:
        _STORED_KEYS.pop(owner, None)

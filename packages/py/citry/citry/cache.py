"""
The pluggable cache backend.

Citry stores derived content in a cache: replayable component and named-fragment
render artifacts, the dependencies extension's processed JS/CSS scripts and
served ``Dependencies`` files, and optional server-held Events State. When a
backend is configured, it also holds the compiled Vue definition bundles and
stylesheets that interactive pages load, and the stylesheets that
``css_data()`` produces; without one, each ``Citry`` instance keeps those in
its process, up to ``CitrySettings.vue_asset_max_bytes``.
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

import heapq
import math
import sys
import time
from collections import OrderedDict
from threading import Lock
from typing import TYPE_CHECKING, Protocol, cast, runtime_checkable
from weakref import WeakKeyDictionary

from citry.util.logger import logger

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


# Keys that hold server-stored Events State (``State._storage = "server"``).
# The Events extension writes them; ``InMemoryCache`` keeps them in a store of
# their own with its own byte budget.
STATE_KEY_PREFIX = "citry:state:"
# The default byte budget for those entries in one ``InMemoryCache``. One
# entry from a browser write is at most 64 KiB of ASCII text (the default
# server ``State._max_bytes``), so 64 MiB keeps hundreds of the largest
# entries, and about 100,000 of the few-hundred-byte entries a page view
# usually writes. That is small next to a typical worker's memory, yet
# enough that ordinary traffic rarely drops a visitor's State before it
# expires.
DEFAULT_STATE_MAX_BYTES = 64 * 1024 * 1024
# What one stored entry costs beyond its two strings, whose own size
# `sys.getsizeof` gives: the stored tuple and expiry, the dictionary slot,
# and its pair in the deadline list. Counting it makes many tiny entries
# count toward the budget too.
_STATE_ENTRY_OVERHEAD_BYTES = 256


class InMemoryCache:
    """
    The default cache backend: a thread-safe store inside the current process.

    Unbounded by default for ordinary entries. Pass ``max_entries`` to cap
    them; when full, the entry that was read or written longest ago is
    dropped to make room. An entry written with a ``ttl`` is removed once it
    expires, at the next write, even when nothing reads its key again.

    Server-stored Events State (keys that start with ``citry:state:``) is
    kept apart, under its own budget of ``state_max_bytes`` (64 MiB by
    default), and does not count toward ``max_entries``. When the budget is
    full, the State entry read or written longest ago is dropped, so many
    State writes cannot push out page assets. A dropped entry makes that
    visitor's next call answer ``stale_state``, and the page offers a
    reload. An entry larger than the whole budget is not stored, and Citry
    logs a warning. ``state_max_bytes=None`` removes the budget.

    Single-process only: each instance is its own store. With several worker
    processes, a page rendered by one worker can link a generated Vue bundle
    or ``css_data()`` stylesheet that another worker then answers with a
    404, so use a shared backend such as
    [`RedisCache`][citry.contrib.caches.RedisCache] or
    [`DjangoCache`][citry.contrib.django.DjangoCache] instead.

    Raises:
        ValueError: When ``max_entries`` or ``state_max_bytes`` is not a
            positive ``int`` or ``None``.

    """

    def __init__(
        self,
        max_entries: int | None = None,
        *,
        state_max_bytes: int | None = DEFAULT_STATE_MAX_BYTES,
    ) -> None:
        if max_entries is not None and (type(max_entries) is not int or max_entries <= 0):
            msg = f"max_entries must be a positive int or None, got {max_entries!r}"
            raise ValueError(msg)
        if state_max_bytes is not None and (type(state_max_bytes) is not int or state_max_bytes <= 0):
            msg = f"state_max_bytes must be a positive int or None, got {state_max_bytes!r}"
            raise ValueError(msg)
        self._max_entries = max_entries
        self._state_max_bytes = state_max_bytes
        self._lock = Lock()
        # key -> (value, expiry deadline in time.monotonic() terms, or None).
        # Insertion order doubles as recency order: reads and writes move the
        # entry to the end, so the front is always the stalest entry.
        self._data: OrderedDict[str, tuple[str, float | None]] = OrderedDict()
        # The same shape for State keys. A separate store means dropping
        # State to fit its budget never touches the entries in `_data`.
        self._state: OrderedDict[str, tuple[str, float | None]] = OrderedDict()
        self._state_bytes = 0
        # (deadline, key) for every entry written with a TTL, soonest first.
        # Many keys (server-held State among them) are written once and never
        # read again, so expiry cannot wait for a read; each write removes the
        # entries whose deadline has passed. A rewritten key leaves its old
        # pair behind, which the purge skips because the deadline differs.
        self._deadlines: list[tuple[float, str]] = []

    @staticmethod
    def _entry_bytes(key: str, value: str) -> int:
        """Estimate what one State entry holds in memory, for its budget."""
        # `getsizeof` counts the bytes CPython really uses for each string:
        # one character above U+00FF makes the whole string take two or four
        # bytes per character, which `len` would not show.
        return sys.getsizeof(key) + sys.getsizeof(value) + _STATE_ENTRY_OVERHEAD_BYTES

    def _store(self, key: str) -> OrderedDict[str, tuple[str, float | None]]:
        """Return the store that holds ``key``: the State store or the ordinary one."""
        return self._state if key.startswith(STATE_KEY_PREFIX) else self._data

    def _remove(self, key: str) -> None:
        """Remove ``key`` from its store, keeping the State byte count right; caller holds ``_lock``."""
        store = self._store(key)
        entry = store.pop(key, None)
        if entry is not None and store is self._state:
            self._state_bytes -= self._entry_bytes(key, entry[0])

    def get(self, key: str) -> str | None:
        with self._lock:
            store = self._store(key)
            entry = store.get(key)
            if entry is None:
                return None
            value, expires_at = entry
            if expires_at is not None and time.monotonic() >= expires_at:
                self._remove(key)
                return None
            store.move_to_end(key)
            return value

    def set(self, key: str, value: str, ttl: float | None = None) -> None:
        normalized_ttl = _normalize_ttl(ttl)
        with self._lock:
            # A rewrite replaces the old value, so its bytes leave the count first.
            self._remove(key)
            if normalized_ttl == 0:
                return
            now = time.monotonic()
            expires_at = now + normalized_ttl if normalized_ttl is not None else None
            store = self._store(key)
            if store is self._state:
                size = self._entry_bytes(key, value)
                # An entry larger than the whole budget could only be kept by
                # emptying the store and still not fit, so it is not stored;
                # the call that would use it answers stale_state instead.
                if self._state_max_bytes is not None and size > self._state_max_bytes:
                    self._purge_expired(now)
                    # Every reload makes the same entry again and fails the
                    # same way, so the app author needs to hear about it.
                    logger.warning(
                        f"InMemoryCache did not store a server State entry of about {size} bytes, which is"
                        f" larger than its whole state_max_bytes budget of {self._state_max_bytes}. Calls with"
                        f" that token answer stale_state until you raise state_max_bytes or make the State smaller."
                    )
                    return
                self._state_bytes += size
            store[key] = (value, expires_at)
            if expires_at is not None:
                heapq.heappush(self._deadlines, (expires_at, key))
            self._purge_expired(now)
            if self._max_entries is not None:
                while len(self._data) > self._max_entries:
                    self._data.popitem(last=False)
            if self._state_max_bytes is not None:
                # Whatever caller ids a client invents, State stays within its
                # budget: the entry used longest ago goes first.
                while self._state_bytes > self._state_max_bytes:
                    oldest = next(iter(self._state))
                    self._remove(oldest)

    def _purge_expired(self, now: float) -> None:
        """Remove expired entries while the caller holds ``_lock``."""
        deadlines = self._deadlines
        while deadlines and deadlines[0][0] <= now:
            deadline, key = heapq.heappop(deadlines)
            entry = self._store(key).get(key)
            # Only the pair pushed by the key's latest write matches its stored
            # deadline; an older pair must not remove a newer value.
            if entry is not None and entry[1] == deadline:
                self._remove(key)
        # Rewriting one key many times leaves one stale pair per write until
        # its deadline passes. Rebuilding from the live entries keeps the list
        # no larger than about twice the store.
        live = len(self._data) + len(self._state)
        if len(deadlines) > 2 * live + 64:
            self._deadlines = [
                (entry[1], key)
                for store in (self._data, self._state)
                for key, entry in store.items()
                if entry[1] is not None
            ]
            heapq.heapify(self._deadlines)

    def delete(self, key: str) -> None:
        with self._lock:
            self._remove(key)

    def has(self, key: str) -> bool:
        return self.get(key) is not None

    def clear(self) -> None:
        """Drop all entries. Called by ``Citry.clear()``."""
        with self._lock:
            self._data.clear()
            self._state.clear()
            self._state_bytes = 0
            self._deadlines.clear()


# Entries that pages link (compiled Vue code, component JS and CSS, served
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
# How many keys each engine remembers. A forgotten key costs one extra backend
# check on its next render, so this bounds memory without affecting
# correctness.
_STORED_KEY_LIMIT = 4096
# Each remembered key maps to when it was last confirmed and, for a key whose
# value can change (see _store_unless_matched), a mark naming the value seen.
_STORED_KEYS: WeakKeyDictionary[object, OrderedDict[str, tuple[float, str | None]]] = WeakKeyDictionary()
# Renders on several threads write through the same engine's record.
_STORED_KEYS_LOCK = Lock()


def _store_if_missing(owner: object, cache: CitryCache, key: str, value: Callable[[], str]) -> None:
    """
    Make sure ``cache`` holds ``key``, asking the backend at most once per recheck interval.

    ``value`` is called only when the entry must be written, so a large body
    is encoded and sent only then. The entry is written without a TTL: an
    open page can ask for it at any later time. Backend errors propagate, so
    a render never links an entry that failed to store.

    A render on another thread that checked the backend just before a
    delete (a bad entry removed, or ``Citry.clear()``) can record the key as
    stored after it was forgotten. The recheck interval bounds how long that
    wrong record lasts.
    """
    now = time.monotonic()
    # Seen stored recently: trust it and skip the round trip.
    if _recently_confirmed(owner, key, None, now):
        return
    # ``has`` before ``set`` sends the body only when the backend lacks it,
    # including after the backend dropped it.
    if not cache.has(key):
        cache.set(key, value())
    _remember_confirmed(owner, key, None, now)


def _store_unless_matched(owner: object, cache: CitryCache, key: str, value: str, mark: str) -> None:
    """
    Make sure ``cache`` holds ``value`` under ``key``, comparing it with the backend at most once per recheck interval.

    This is ``_store_if_missing`` for a key whose value can change while the
    key stays the same, such as a compatibility key that each class version
    rewrites, or a key named by its inputs rather than its bytes. ``mark``
    names ``value`` (a hash of it), so a different value for the same key is
    compared and written at once, and only a value confirmed recently skips
    the round trip.

    The comparison reads the stored value back, so when a worker running
    another version writes its own value under the same key, this process
    overwrites it at most once per interval. Citry never serves the stored
    value: each worker returns the object built from its own class.
    """
    now = time.monotonic()
    if _recently_confirmed(owner, key, mark, now):
        return
    if cache.get(key) != value:
        cache.set(key, value)
    _remember_confirmed(owner, key, mark, now)


def _recently_confirmed(owner: object, key: str, mark: str | None, now: float) -> bool:
    """Whether ``key`` was confirmed holding the value ``mark`` names within the recheck interval."""
    with _STORED_KEYS_LOCK:
        remembered = _STORED_KEYS.get(owner)
        confirmed = None if remembered is None else remembered.get(key)
        if remembered is None or confirmed is None:
            return False
        # A key in use stays at the recent end, so the limit drops the keys
        # no page links any more.
        remembered.move_to_end(key)
    return confirmed[1] == mark and now - confirmed[0] < _STORED_KEY_RECHECK_SECONDS


def _remember_confirmed(owner: object, key: str, mark: str | None, now: float) -> None:
    """Record that ``key`` holds the value ``mark`` names, dropping the oldest records past the limit."""
    with _STORED_KEYS_LOCK:
        remembered = _STORED_KEYS.setdefault(owner, OrderedDict())
        remembered[key] = (now, mark)
        remembered.move_to_end(key)
        while len(remembered) > _STORED_KEY_LIMIT:
            remembered.popitem(last=False)


def _forget_stored_key(owner: object, key: str) -> None:
    """Make the next store of ``key`` ask the backend again (the entry was removed)."""
    with _STORED_KEYS_LOCK:
        remembered = _STORED_KEYS.get(owner)
        if remembered is not None:
            remembered.pop(key, None)


def _forget_stored_keys(owner: object) -> None:
    """Forget every key remembered for ``owner``, e.g. after ``Citry.clear()`` emptied its cache."""
    with _STORED_KEYS_LOCK:
        _STORED_KEYS.pop(owner, None)

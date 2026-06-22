"""
Cache adapters for common shared stores.

Each adapter wraps a client object you construct yourself, so citry imports
nothing from the host packages::

    import redis
    from citry.contrib.caches import RedisCache
    app = Citry(cache=RedisCache(redis.Redis(host="...")))

    import diskcache
    from citry.contrib.caches import DiskCache
    app = Citry(cache=DiskCache(diskcache.Cache("/var/cache/citry")))

Which to pick:
- ``DiskCache`` shares across worker processes on one host with
no extra service (the usual answer for the multi-worker fragment requirement,
docs/design/dependencies.md section 8.3);
- ``RedisCache`` shares across hosts.
- For a Django project, ``citry.contrib.django.DjangoCache`` reuses the cache
the project already configured.

The protocol is four methods (``citry.CitryCache``),
so adapting any other store takes minutes.
"""

from __future__ import annotations

from typing import Any


class RedisCache:
    """
    Adapt a Redis client (``redis.Redis`` or compatible) to citry's
    ``CitryCache`` protocol. Values are stored as UTF-8 strings; ``ttl``
    becomes the key's expiry (``ex``).

    ``prefix`` is prepended to every key, for sharing a Redis database with
    other uses. (Citry's own keys already start with ``citry:``.)
    """

    def __init__(self, client: Any, *, prefix: str = "") -> None:
        self._client = client
        self._prefix = prefix

    def get(self, key: str) -> str | None:
        value = self._client.get(self._prefix + key)
        if value is None:
            return None
        return value.decode() if isinstance(value, bytes) else str(value)

    def set(self, key: str, value: str, ttl: float | None = None) -> None:
        # Redis expiries are whole seconds; round up so a short ttl never
        # becomes "expire immediately".
        expiry = None if ttl is None else max(1, round(ttl))
        self._client.set(self._prefix + key, value, ex=expiry)

    def delete(self, key: str) -> None:
        self._client.delete(self._prefix + key)

    def has(self, key: str) -> bool:
        return bool(self._client.exists(self._prefix + key))


class DiskCache:
    """
    Adapt a ``diskcache.Cache`` (or compatible) to citry's ``CitryCache``
    protocol. The store is a directory on disk, shared by every worker
    process on the host.
    """

    def __init__(self, cache: Any) -> None:
        self._cache = cache

    def get(self, key: str) -> str | None:
        value = self._cache.get(key)
        return value if isinstance(value, str) else None

    def set(self, key: str, value: str, ttl: float | None = None) -> None:
        self._cache.set(key, value, expire=ttl)

    def delete(self, key: str) -> None:
        self._cache.delete(key)

    def has(self, key: str) -> bool:
        return key in self._cache

---
title: Cache backends
description: Choose where Citry stores cached output and generated files, and share that store between workers and deployments.
---

# Cache backends

Citry keeps cached HTML and some generated files in a cache backend: the
store that holds those values. By default each `Citry` instance keeps its
own store in memory, which is enough for one process.

With several worker processes or hosts, each worker would then have its
own separate store. A page rendered by one worker can ask another worker
for a generated file and get a 404, and cached output is never shared.
Give every worker the same shared backend to fix both.

The backend holds more than [cached rendered output](/performance/caching/):

- the generated scripts that load each page's JavaScript and CSS;
- [Events State](/events/state/) that the server keeps for the browser,
  when you turn that on;
- the compiled code and styles of interactive components, when you pass
  a backend.

Size and protect it for all of these uses.

## Choose a backend

| Backend | Shared between | Good fit |
| --- | --- | --- |
| [`InMemoryCache`][citry.InMemoryCache] | Nothing; one process only | Local development or one worker |
| `DiskCache` | Workers on one host | Several processes, no cache service |
| `RedisCache` | Workers on several hosts | A deployment on several hosts |
| `DjangoCache` | Whatever Django's cache shares | An existing Django application |

The DiskCache and Redis adapters wrap a client you create, so install
`diskcache` or `redis` in your application. `DjangoCache` uses Django's
own cache framework.

## Use the default in-memory store

Every [`Citry`][citry.Citry] instance gets its own in-memory store unless
you pass another backend:

```python
from citry import Citry, InMemoryCache

app = Citry()
assert isinstance(app.cache, InMemoryCache)
```

The store is safe to use from several threads and has no size limit by
default. Set `max_entries` to cap it. When the store is full, it drops
the entry that was used longest ago:

```python
backend = InMemoryCache(max_entries=1_000)
app = Citry(cache=backend)
```

`max_entries` must be a positive `int` or `None`; any other value raises
`ValueError`. The limit counts every value in the store, not only
rendered output.

## Share one store between workers

Use Redis when workers run on different hosts:

```python
import redis

from citry import Citry
from citry.contrib.caches import RedisCache

client = redis.Redis(host="cache.internal")
backend = RedisCache(client, prefix="myapp:")
app = Citry(cache=backend)
```

Use DiskCache when the workers share one host and file system:

```python
import diskcache

from citry import Citry
from citry.contrib.caches import DiskCache

store = diskcache.Cache("/var/cache/citry")
app = Citry(cache=DiskCache(store))
```

In a Django application, wrap one of the project's configured caches:

```python
from django.core.cache import caches

from citry import Citry
from citry.contrib.django import DjangoCache

backend = DjangoCache(caches["default"])
app = Citry(cache=backend)
```

Configure the same backend in every process that renders or serves
Citry output. This matters most for
[HTML fragments](/advanced/html-fragments/), where the browser's request
for a fragment's files may reach a different worker from the one that
rendered it.

## Share cached output between workers

A shared store alone does not let workers reuse each other's cached
output. Each `Citry` instance keeps its rendered-output entries separate
until you give the app two values:

- `namespace`: a name for your application and environment, so apps that
  share one store never read each other's entries;
- `generation`: a value you change on every deploy, such as the release
  commit, so new code never reuses HTML rendered by old code.

```python
import os

from citry import Citry

app = Citry(
    cache=backend,
    extensions_defaults={
        "cache": {
            "namespace": "storefront-production",
            "generation": os.environ["RELEASE_SHA"],
            "ttl": 300,
        },
    },
)
```

Use the same namespace and generation in every worker. Change the
generation whenever code, templates, extensions, helpers, or
configuration can change rendered output. Old entries become unreachable
at once and leave the store when they expire or the store drops them.

Both values are needed. A namespace alone still keeps entries separate
for each `Citry` instance. A generation without a namespace, or an empty
string for either, raises `ValueError` when you create `Citry`.

## Limit memory for interactive page assets

An interactive page loads its compiled component code and styles from
URLs after the HTML arrives, and a page that stays open may request one
much later. Without a configured backend, each `Citry` instance keeps
these files in its own process, up to 64 MiB by default. Past the limit,
it drops the files used longest ago, but never the files of a page it is
still rendering.

If the limit is too small, a page that has been open for a while stops
loading a component, and the browser shows a 404 for a URL containing
`/ext/events/definitions/` or `/ext/events/assets/`. Raise the limit, or
pass `None` to remove it:

```python
app = Citry(vue_asset_max_bytes=256 * 1024 * 1024)
app = Citry(vue_asset_max_bytes=None)
```

The value must be a positive `int` or `None`. Another type raises
`TypeError`, and zero or a negative number raises `ValueError`.

When you pass a backend, Citry stores these files there without an
expiry, and `vue_asset_max_bytes` has no effect. Give the backend enough
room that it does not drop them while pages are still open.

!!! note "A dropped file can return 404 for up to a minute"

    Each process checks whether a shared backend still holds a file at
    most once a minute, not on every render. If the backend drops a
    file, the next render after that minute writes it back. Until then,
    other workers answer 404 for it.

## Limit the size of one stored render

Citry does not store a single rendered result larger than 1,000,000
bytes by default. Change the limit with `max_entry_bytes`:

```python
app = Citry(
    cache=backend,
    extensions_defaults={
        "cache": {
            "max_entry_bytes": 2_000_000,
        },
    },
)
```

`None` removes this limit, but a stored render can never exceed 16 MiB.
Any value other than a positive `int` or `None` raises `ValueError` when
you create `Citry`. A render over the limit still appears on the page; it
is just not stored.

Set the total memory, disk space, and eviction policy of a shared store
in Redis, DiskCache, or Django itself. Citry passes each entry's expiry
to the store, but does not manage the store's total size.

## Clear cached values

[`Citry.clear`][citry.Citry.clear] empties an in-memory backend and stops
this `Citry` instance from finding its existing rendered-output entries.
The built-in shared adapters have no `clear()` method, because the store
may hold other applications' data.

To invalidate every worker after a deploy, change the generation. To
remove a single rendered entry, build its key as shown in
[Cache rendered output](/performance/caching/#update-or-remove-entries).

## Write an adapter for another store

Any object with these four synchronous methods works as a backend; the
[`CitryCache`][citry.CitryCache] protocol describes them:

```python
class ApplicationCache:
    def get(self, key: str) -> str | None: ...

    def set(
        self,
        key: str,
        value: str,
        ttl: float | None = None,
    ) -> None: ...

    def delete(self, key: str) -> None: ...

    def has(self, key: str) -> bool: ...
```

Keys and values are strings. `get()` returns `None` for a missing or
expired entry. `set()` receives the expiry in seconds, or `None` for no
expiry.

Pass the adapter object, or an import string, to `Citry`:

```python
app = Citry(cache=ApplicationCache())
app = Citry(cache="myapp.cache.ApplicationCache")
```

Citry checks for the four methods when you create `Citry` and raises
`TypeError` if one is missing. Errors raised by these methods reach your
code; add retries, or treat errors as misses, inside the adapter if your
application needs that.

## Related pages

- [Cache rendered output](/performance/caching/) covers cache keys,
  expiry, and privacy.
- [HTML fragments](/advanced/html-fragments/) explains why fragment files
  need a shared backend across workers.
- [Events State](/events/state/) covers State kept on the server.

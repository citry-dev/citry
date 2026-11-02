---
title: Cache backends
url: https://citry.dev/v/0.7.0/performance/cache-backends/
description: "Choose where Citry stores cached output and generated files, and share that store between workers and deployments."
---
# Cache backends

With several worker processes or hosts, a page rendered by one worker
can ask another worker for a generated file and get a 404, and cached
output is never shared between workers.

Both happen because Citry keeps cached HTML and some generated files in
a cache backend, the store that holds those values, and by default each
`Citry` instance keeps its own store in memory. That is enough for one
process. For several workers, give them all the same shared backend.

The backend holds more than [cached rendered output](/v/0.7.0/performance/caching/):

- the generated scripts that load each page's JavaScript and CSS;
- [Events State](/v/0.7.0/events/state/) that the server keeps for the browser,
  when you turn that on;
- the compiled code and styles of interactive components, and the
  stylesheets that `css_data()` produces, when you pass a backend.

Size and protect it for all of these uses.

## Choose a backend

| Backend | Shared between | Good fit |
| --- | --- | --- |
| [`InMemoryCache`](/v/0.7.0/reference/citry/#citry-inmemorycache) | Nothing; one process only | Local development or one worker |
| `DiskCache` | Workers on one host | Several processes, no cache service |
| `RedisCache` | Workers on several hosts | A deployment on several hosts |
| `DjangoCache` | Whatever Django's cache shares | An existing Django application |

Citry's DiskCache and Redis classes wrap a client you create, so install
`diskcache` or `redis` in your application. `DjangoCache` uses Django's
own cache framework.

## `InMemoryCache` limits

Every [`Citry`](/v/0.7.0/reference/citry/#citry-citry) instance gets its own in-memory store unless
you pass another backend:


```python
from citry import Citry, InMemoryCache

app = Citry()
assert isinstance(app.cache, InMemoryCache)
```


The store is safe to use from several threads and has no size limit by
default for ordinary entries. Set `max_entries` to cap them. When the store is full, it drops
the entry that was used longest ago:


```python
backend = InMemoryCache(max_entries=1_000)
app = Citry(cache=backend)
```


`max_entries` must be a positive `int` or `None`; any other value raises
`ValueError`. The limit counts every value in the store except Events
State kept on the server, which has its own limit (below).

An entry written with a lifetime is removed once it expires, at the next
write to the store, even if nothing reads it again.

### Server-stored State { #server-stored-state }

Events State kept on the server (`State._storage = "server"`) adds one
entry for every render and every State change. Each lasts 24 hours unless
`State._max_age` sets another lifetime. `InMemoryCache` keeps these
entries apart from everything else, under a budget of 64 MiB by default:


```python
backend = InMemoryCache(state_max_bytes=256 * 1024 * 1024)
app = Citry(cache=backend)
```


When the budget is full, the store drops the State entry used longest
ago. The visitor whose entry was dropped sees their next call fail with
`stale_state`, and the page asks them to reload. Other entries, such as
the scripts and styles that open pages load, never make room for State,
so many State writes cannot push them out.

The budget counts the memory each entry's text takes in Python, plus 256
bytes for the objects that hold it. Text such as emoji takes up to four
bytes per character, so it uses the budget faster. An entry larger than
the whole budget is not stored, so the call that would use it also fails
with `stale_state`, and Citry logs a warning. Reloading makes the same
entry again, so the call keeps failing until you raise
`state_max_bytes`.
`state_max_bytes` must be a positive `int` or `None`; any other value
raises `ValueError`. `None` removes the budget, and Citry then logs a
warning once when it stores such State.

64 MiB holds about 1,000 entries of the largest plain-text size a browser
write can make (64 KiB, the default `State._max_bytes`), or about 100,000
of the few-hundred-byte entries a page view usually writes. Raise it when
many visitors keep pages open for hours, and lower it on a small worker.

The budget keeps one client from filling the worker's memory, but such a
client can still push out other visitors' State by sending many calls.
Those visitors then see a reload prompt. Rate-limit the Events routes if
that matters for your app.

## Share a store

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
[HTML fragments](/v/0.7.0/advanced/html-fragments/), where the browser's request
for a fragment's files may reach a different worker from the one that
rendered it.

## Share cached output { #share-cached-output-between-workers }

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

## Limit asset memory { #limit-memory-for-interactive-page-assets }

Without a configured backend, each `Citry` instance keeps in its own
process the files that pages fetch by URL after the HTML arrives: the
compiled code and styles of interactive components, and the stylesheets
that
[`css_data()`](/v/0.7.0/advanced/js-and-css-dependencies/#send-values-to-css)
produces. `css_data()` makes one small stylesheet for each set of values
it returns, so values that change per request, such as a per-user color,
add a new one each time. A page that stays open may request one of these
files much later.

Together they can use up to 64 MiB by default. Past the limit, Citry
drops the files used longest ago, but never the files of a page it is
still writing out.

If the limit is too small, a page that has been open for a while stops
loading a component or a stylesheet. The browser shows a 404 for a URL
containing `/ext/events/definitions/` or `/ext/events/assets/`, or for a
stylesheet URL containing `/cache/`. Raise the limit, or pass `None` to
remove it:


```python
app = Citry(vue_asset_max_bytes=256 * 1024 * 1024)
app = Citry(vue_asset_max_bytes=None)
```


The value must be a positive `int` or `None`. Another type raises
`TypeError`, and zero or a negative number raises `ValueError`.

When you pass a backend, Citry stores these files there without an
expiry, and `vue_asset_max_bytes` has no effect. Give the backend enough
room that it does not drop them while pages are still open.

## Limit render size { #limit-the-size-of-one-stored-render }

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

[`Citry.clear`](/v/0.7.0/reference/citry/#citry-citry-clear) empties an in-memory backend and stops
this `Citry` instance from finding its existing rendered-output entries.
The built-in shared adapters have no `clear()` method, because the store
may hold other applications' data.

To invalidate every worker after a deploy, change the generation. To
remove a single rendered entry, build its key as shown in
[Cache rendered output](/v/0.7.0/performance/caching/#update-or-remove-entries).

## `CitryCache` adapters { #write-an-adapter-for-another-store }

Any object with these four synchronous methods works as a backend; the
[`CitryCache`](/v/0.7.0/reference/citry/#citry-citrycache) protocol describes them:


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

## Edge cases

### Temporary 404s

Each process checks whether a shared backend still holds a file at most
once a minute, not on every render. If the backend drops a file, the
next render after that minute writes it back. Until then, other workers
answer 404 for it.

## Related pages

- [Cache rendered output](/v/0.7.0/performance/caching/) covers cache keys,
  expiry, and privacy.
- [HTML fragments](/v/0.7.0/advanced/html-fragments/) explains why fragment files
  need a shared backend across workers.
- [Events State](/v/0.7.0/events/state/) covers State kept on the server.
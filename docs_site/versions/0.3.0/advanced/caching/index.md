---
title: Caching
url: https://citry.dev/v/0.3.0/advanced/caching/
description: "Cache complete component subtrees or named template regions with safe variation, expiry, invalidation, and shared backends."
---
# Caching

Citry can cache and replay complete rendered subtrees. Use one of two scopes:

- `Component.Cache` caches every call to one component class.
- `<c-cache>` caches one explicitly named region inside a template.

Both use the cache backend configured on your [Citry](/v/0.3.0/reference/citry/#citry-citry) instance.
That same store also holds derived dependency scripts and, when configured,
server-held Events State. A hit preserves correct client behavior while giving
each replayed component a fresh identity for the current render.

Caching is an optimization. A miss always renders normally, and cached values
must never be the authoritative home of application state.

## Cache a component

Add a nested `Cache` class and set `enabled = True`:


```citry
from citry import Citry, Component

app = Citry()


class ProductCard(Component):
    citry = app

    class Cache:
        enabled = True
        ttl = 300
        version = 1

    class Kwargs:
        product_id: int

    template = """
    <article>{{ product_name }}</article>
    """

    def template_data(self, kwargs, slots):
        product = load_product(kwargs.product_id)
        return {"product_name": product.name}
```


The first `ProductCard(product_id=42)` renders and stores its subtree. Later
calls with the same effective typed kwargs replay it until it expires or is
invalidated. The default variation includes every effective Kwargs value after
defaults, factories, input hooks, and final type validation.

`ttl` is seconds. A positive exact integer or float expires the entry, `None`
means no expiry, and zero bypasses lookup and storage. `enabled = False` also
bypasses caching. A hit does not refresh the original expiry.

### Custom variation

Use `Cache.vary()` when the complete typed kwargs contain objects that should
be reduced to stable identifiers, or when only selected values affect output:


```citry
class ProductCard(Component):
    citry = app

    class Cache:
        enabled = True

        def vary(self, kwargs, slots):
            return {
                "product_id": kwargs["product"].id,
                "locale": kwargs["locale"],
            }

    class Kwargs:
        product: object
        locale: str

    template = """
    <article>{{ product_name }}</article>
    """
```


`kwargs` and `slots` are read-only snapshots. The return value must use Citry's
canonical variation types: `None`, exact booleans, integers, finite floats,
strings, bytes, and exact built-in `list`, `tuple`, or `dict` containers composed
from those values. Dictionary keys must be exact strings. Values may be at most
32 containers deep, 10,000 nodes, and 64 KiB in the canonical key format.

A custom method is a correctness promise. Include every input that can change
the rendered subtree. Convert domain objects to stable IDs; do not use an
arbitrary object's `str()` or `repr()`.

### Components with Slots

The default component variation does not guess what a Slot will render. If an
effective supplied Slot, typed Slot default, factory, or input hook produces
content, caching raises [`CacheKeyError`](/v/0.3.0/reference/cache-keys/#citry-ext-cache-cachekeyerror) unless
the component defines a custom `Cache.vary()`.

Leave personalized or context-sensitive slotted components uncached unless you
can describe every output distinction explicitly:


```citry
from citry import Component, SlotInput


class PersonalizedPanel(Component):
    citry = app

    class Cache:
        enabled = False

    class Slots:
        body: SlotInput | None = None

    template = """
      <section><c-slot name="body" /></section>
    """
```


An optional Slot whose effective typed value is `None` is safe with default
variation. Fallback markup written inside `<c-slot>` belongs to the component
template and does not count as a caller-supplied Slot source.

## Cache a template region

`<c-cache>` is transparent: it adds no HTML wrapper. Give it a stable semantic
`key`, then vary on every caller-dependent value used by the body:


```citry
class AccountPage(Component):
    citry = app
    template = """
    <c-cache
      key="account-menu"
      c-vary="[current_user.id, locale]"
      c-ttl="300"
    >
      <c-account-menu c-user="current_user" c-locale="locale" />
    </c-cache>
    """
```


This creates a separate fragment for each user and locale. The body itself is
not inspected or included in the key. If the body also depends on tenant,
permissions, timezone, feature flags, provide/inject data, or another ambient
value, include that value in `c-vary` too.

The controls are:

- `key`: required exact non-empty string.
- `vary`: one canonical value, defaulting to an empty tuple.
- `ttl`: seconds, `None`, or zero; omitted uses the engine Cache default.
- `version`: exact integer or non-empty string, defaulting to `1`.
- `enabled`: exact boolean, defaulting to `True`.

Literal HTML attributes are strings. Write `c-ttl="300"` and
`c-enabled="False"` for typed values; `ttl="300"` and `enabled="false"` are
invalid strings.

On a hit, Citry skips the fragment body, its child components, data methods,
render hooks, and Slot rendering. For nested caches, a live outer hit therefore
suppresses every inner lookup. Keep the outer TTL no longer than freshness
requirements for anything inside it.

## Configure the backend

Pass `cache=` when you construct [Citry](/v/0.3.0/reference/citry/#citry-citry). It accepts a backend
object, an import string, or `None`:


```python
from citry import Citry, InMemoryCache

# Default: one fresh in-process cache for this Citry instance.
app = Citry()
assert isinstance(app.cache, InMemoryCache)

# Bound the number of values in the in-process store.
backend = InMemoryCache(max_entries=1000)
app = Citry(cache=backend)
assert app.cache is backend

# Or name a class that can be constructed without arguments.
app = Citry(cache="citry.cache.InMemoryCache")
```


The original setting remains on `app.settings.cache`; the live backend is
`app.cache`. A backend implements the [CitryCache](/v/0.3.0/reference/citry/#citry-citrycache) protocol:

- `get(key)` returns a stored string or `None`.
- `set(key, value, ttl=None)` stores a string.
- `delete(key)` removes one key.
- `has(key)` reports whether a key is present.

Citry stores JSON strings and never asks a backend to pickle live Python
objects. Missing protocol methods fail at `Citry` construction.

### Share render entries across workers

[InMemoryCache](/v/0.3.0/reference/citry/#citry-inmemorycache) is thread-safe but process-local. Use a
shared backend for multiple workers, then configure both a namespace and a
deployment generation:


```python
import os

import redis

from citry import Citry
from citry.contrib.caches import RedisCache

backend = RedisCache(redis.Redis(host="cache.internal"), prefix="myapp:")
app = Citry(
    cache=backend,
    extensions_defaults={
        "cache": {
            "namespace": "storefront-production",
            "generation": os.environ["RELEASE_SHA"],
            "ttl": 300,
            "max_entry_bytes": 1_000_000,
        }
    },
)
```


Cross-engine render hits are enabled only when both `namespace` and
`generation` are non-`None`. A namespace without a generation remains local to
one `Citry` instance. Change the generation whenever code, templates,
extensions, helpers, or global configuration can change rendered output.

Other shared adapters are available for one host or a Django application:


```python
import diskcache
from citry.contrib.caches import DiskCache

disk_backend = DiskCache(diskcache.Cache("/var/cache/citry"))
```



```python
from django.core.cache import caches
from citry.contrib.django import DjangoCache

django_backend = DjangoCache(caches["default"])
```


The backend's capacity covers every value in the shared store, including render
artifacts, dependency scripts, and server-held Events State.
`InMemoryCache(max_entries=...)` limits that total entry count.
`max_entry_bytes` is different: it caps one render artifact. An oversized
artifact still renders successfully but is not stored.

## Invalidate cached output

Use a component or fragment `version` when one output family changes. A version
bump selects a new family immediately without finding every old variation:


```citry
class ProductCard(Component):
    citry = app

    class Cache:
        enabled = True
        version = "product-card-v2"
```



```html
<c-cache key="category-nav" version="nav-v3">
  ...
</c-cache>
```


For one exact variation, build its physical key and delete it:


```python
from citry.ext.cache import component_cache_key, fragment_cache_key

component_key = component_cache_key(
    ProductCard,
    vary={"product_id": 42},
    version="product-card-v2",
)
app.cache.delete(component_key)

fragment_key = fragment_cache_key(
    app,
    "account-menu",
    vary=[user_id, locale],
)
app.cache.delete(fragment_key)
```


`component_cache_key()` accepts the already computed semantic variation. It
does not instantiate the component or call `Cache.vary()`. Citry intentionally
has no distributed index for deleting every variant.

`Citry.clear()`, component removal, and template/file resets advance local
invalidation state. `Citry.clear()` also clears a backend that exposes a
callable `clear()`, such as `InMemoryCache`; the shared contrib adapters leave
store-wide clearing to their clients. Coordinate a generation change across
workers for deployment-wide invalidation.

## Security and correctness checklist

Before enabling output caching:

1. Include every caller-dependent dimension in the variation: user, tenant,
   permissions, locale, timezone, flags, experiments, CSRF values, CSP nonces,
   template globals, and provide/inject data are common examples.
2. Cache only output reusable by every caller that shares a key.
3. Treat the backend as trusted application infrastructure. Someone with write
   access can inject HTML that Citry will trust on replay.
4. Use stable scalar identifiers instead of `str()` or `repr()` of arbitrary
   objects.
5. Change the deployment generation for every output-affecting deployment or
   configuration change.
6. Use component or fragment versions for targeted semantic invalidation.
7. Remember that a longer-lived outer hit suppresses all inner cache work.
8. Apply suitable access controls and retention to the backend. Artifacts can
   contain rendered private data, protected Events state, and dependency data.

Physical backend keys and ordinary diagnostics contain opaque digests rather
than raw variation values or authored fragment names. That protects logs from
accidental disclosure, but it does not make cached artifacts public data.

## Inspect Cache policy metadata

Component introspection includes Cache metadata only when explicitly requested:


```python
catalog = app.inspect_components(include_extensions=("cache",))
payload = catalog.to_dict()
assert payload["extension_versions"]["cache"] == 1
```


Version 1 publishes this exact component-policy shape:


```json
{
  "enabled": true,
  "ttl": 60.0,
  "version": {"kind": "string", "value": "card-v2"},
  "variation": "custom",
  "default_variation_slot_source": "not-applicable"
}
```


Integer versions use tagged hexadecimal text, for example
`{"kind": "integer", "value": "0x1"}`. This preserves integers larger than
JSON's portable safe range and keeps integer `1` distinct from string `"1"`.

For default variation, `default_variation_slot_source` is `none` when the
component has a closed, empty Slots schema, or `possible` when future supplied
fills, declared fields, opaque schemas, factories, or input hooks may produce
content. For custom variation it is `not-applicable`. This is static policy
metadata, not a prediction about one future call.

Inspection never calls `Cache.vary()`, executes a default factory, loads an
asset, or renders. It also omits backend namespace, generation, capacity, keys,
and runtime variation values. The `<c-cache>` built-in publishes no misleading
`Component.Cache` entry; its core built-in metadata and Kwargs schema describe
the fragment surface.

## Related pages

- [Performance](/v/0.3.0/advanced/performance/) for `Const`, which reuses stable pieces
  inside ordinary renders rather than caching a whole subtree.
- [Extensions](/v/0.3.0/advanced/extensions/) for extension lifecycle and metadata.
- [Security](/v/0.3.0/security/) for template and Events trust boundaries.
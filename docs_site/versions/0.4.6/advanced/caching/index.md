---
title: Cache rendered output
url: https://citry.dev/v/0.4.6/advanced/caching/
description: "Reuse complete component output or named template regions without mixing data between callers."
---
# Cache rendered output

Cache rendered output when producing the same component subtree costs more
than looking it up. Citry can replay a previous render while giving the
replayed components fresh identities for the current page.

Choose the smallest useful scope:

- `Component.Cache` caches every call to one component class.
- `<c-cache>` caches one named region inside a larger template.

Caching is an optimization. Keep application state in its normal database or
service, and make sure every caller who shares a cache key is allowed to see
the same output.

## Cache a component

Add a nested `Cache` class and enable it:


```citry
from citry import Citry, Component

app = Citry()

PRODUCTS = {
    42: "Travel mug",
    51: "Field notebook",
}


class ProductCard(Component):
    class Kwargs:
        product_id: int

    class Cache:
        enabled = True
        ttl = 300
        version = 1

    citry = app

    def template_data(
        self,
        kwargs: Kwargs,
        slots,
    ):
        return {
            "product_name": PRODUCTS[kwargs.product_id],
        }

    template = """
      <article>{{ product_name }}</article>
    """
```


The first `ProductCard(product_id=42)` renders and stores its subtree. Later
calls with the same effective typed kwargs replay it until it expires or its
key changes.

The default variation includes every typed kwarg after defaults, factories,
input hooks, coercion, and validation. This safe default works well when the
kwargs already consist of stable scalar values.

`Component.Cache` is not available on a transparent component, because it
needs a component boundary to replay. Wrap the relevant template region in
`<c-cache>` instead.

## Reduce objects to stable identifiers

Define `Cache.vary()` when a kwarg contains a domain object or when only part
of the input affects the output:


```citry
from dataclasses import dataclass

from citry import Component


@dataclass(frozen=True)
class Product:
    id: int
    revision: int
    name: str


class ProductSummary(Component):
    class Kwargs:
        product: Product
        locale: str = "en"

    class Cache:
        enabled = True

        def vary(self, kwargs, slots):
            return {
                "product_id": kwargs["product"].id,
                "product_revision": kwargs["product"].revision,
                "locale": kwargs["locale"],
            }

    citry = app

    def template_data(
        self,
        kwargs: Kwargs,
        slots,
    ):
        return {"product_name": kwargs.product.name}

    template = """
      <article>{{ product_name }}</article>
    """
```


The method receives read-only snapshots of the effective kwargs and slots.
Return only stable plain values:

- `None`, exact booleans and integers, finite floats, strings, or bytes;
- exact built-in lists, tuples, or dictionaries containing those values.

Dictionary keys must be exact strings. The complete value may be at most 32
containers deep, 10,000 nodes, and 64 KiB in Citry's canonical key format.

A custom variation is a correctness promise. Include every input that can
change the output. Use a database ID instead of an object's `str()` or
`repr()`, which may be unstable or expose private data. If the record can
change while keeping the same ID, include a revision or update timestamp too.

The default component variation distinguishes an ordinary value from the
same value wrapped in [`Const`](/v/0.4.6/reference/rendering/#citry-const). `<c-cache>` unwraps `Const` from
its own control values. Custom `vary()` methods should generally return plain
values so the intended distinction is obvious.

## Decide how slots affect the key

Citry cannot safely guess what supplied slot content will render. With the
default variation, an effective slot value raises
[`CacheKeyError`](/v/0.4.6/reference/cache-keys/#citry-ext-cache-cachekeyerror). This includes slot defaults,
factories, and values created by input hooks.

An optional slot whose effective value is `None` is safe. Fallback markup
inside `<c-slot>` belongs to the component template and is safe too.

Leave a slotted component uncached unless you can describe every relevant
output difference in a custom `Cache.vary()`:


```citry
from citry import Component, SlotInput


class PersonalizedPanel(Component):
    class Slots:
        body: SlotInput | None = None

    class Cache:
        enabled = False

    citry = app

    template = """
      <section><c-slot name="body" /></section>
    """
```


## Cache one template region

`<c-cache>` adds no HTML wrapper. Give the region a stable semantic key, then
vary it by every value used inside:


```citry-html
<c-cache
  key="account-menu"
  c-vary="[current_user.id, locale]"
  c-ttl="300"
>
  <c-account-menu
    c-user="current_user"
    c-locale="locale"
  />
</c-cache>
```


This produces a separate entry for each user and locale. The body itself is
not inspected or included in the key. Add tenant, permissions, timezone,
feature flags, injected values, or any other input that can change the body.

The controls are:

- `key`: required exact non-empty string;
- `vary`: one canonical value, defaulting to an empty tuple;
- `ttl`: expiry in seconds, `None`, or zero;
- `version`: exact integer or non-empty string, defaulting to `1`;
- `enabled`: exact boolean, defaulting to `True`.

An omitted `ttl` uses the Cache extension default. A positive value expires
the entry after that many seconds, `None` keeps it until invalidation or
eviction, and zero bypasses both lookup and storage. A hit does not restart
the expiry timer.

Literal HTML attributes are strings. Use expressions for typed controls:
`c-ttl="300"` and `c-enabled="False"`. The literal forms `ttl="300"` and
`enabled="false"` are invalid strings for these controls.

## Know what a hit skips

Every component call still creates the boundary and finalizes its inputs.
Input hooks, defaults, factories, coercion, validation, and a custom
`Cache.vary()` therefore run before lookup.

On a component hit, Citry skips its data methods, render hooks, template
nodes, child components, and slot rendering. On a `<c-cache>` hit, it skips
the entire body. A live outer hit also suppresses every cache lookup nested
inside it, so the outer TTL must satisfy the strictest freshness requirement
inside that region.

Component and slot highlighting from the Debug extension bypasses rendered
output caching. This keeps the development overlay accurate.

## Change or remove entries

Increase a component or fragment `version` when one family of output changes:


```citry-html
<c-cache key="category-nav" version="nav-v3">
  <c-category-nav />
</c-cache>
```


The new version makes old entries unreachable; it does not delete them. They
remain until their backend expiry or eviction.

To remove one exact variation, build its physical key and delete it:


```python
from citry.ext.cache import (
    component_cache_key,
    fragment_cache_key,
)

component_key = component_cache_key(
    ProductCard,
    vary={"product_id": 42},
    version=1,
)
app.cache.delete(component_key)

fragment_key = fragment_cache_key(
    app,
    "account-menu",
    vary=[user_id, locale],
)
app.cache.delete(fragment_key)
```


`component_cache_key()` accepts the already-computed variation. It does not
create a component or call its `Cache.vary()` method.

[`Citry.clear`](/v/0.4.6/reference/citry/#citry-citry-clear) advances local invalidation state. It also
clears backends that provide `clear()`, including the in-process backend.
Shared adapters leave store-wide clearing to their underlying clients. Use a
new deployment generation for coordinated invalidation across workers.

## Handle misses and backend failures

An absent, corrupt, incompatible, oversized, or unreplayable render artifact
is treated as a miss. Citry renders normally and replaces the entry when the
new artifact fits the configured size limit. An oversized new render still
succeeds, but is not stored.

Exceptions raised by the backend's `get()` or `set()` methods propagate.
Choose or wrap a backend with the failure policy your application needs.
[Cache backends](/v/0.4.6/advanced/cache-backends/) covers capacity, shared stores,
and deployment settings.

## Check privacy before enabling a cache

Before caching rendered output:

1. Include every caller-dependent value in the variation.
2. Share an entry only among callers allowed to see the same output.
3. Include CSRF values, CSP nonces, template globals, and injected data when
   they affect the rendered subtree.
4. Treat the cache as trusted application infrastructure. Anyone who can
   write to it can inject HTML that Citry trusts during replay.
5. Change the deployment generation after every output-affecting deploy.
6. Apply suitable access controls and retention. Cached values can contain
   private HTML, protected Events state, and dependency data.

Physical backend keys use opaque digests instead of raw variation values and
authored fragment names. This reduces accidental disclosure in logs; it does
not make the stored artifact safe to expose.

## Related pages

- [Cache backends](/v/0.4.6/advanced/cache-backends/) for in-process and shared
  storage.
- [Performance](/v/0.4.6/advanced/performance/) for reusing stable values and pure
  component bodies inside an ordinary render.
- [Security](/v/0.4.6/security/) for template and Events trust boundaries.
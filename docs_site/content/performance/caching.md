---
title: Cache rendered output
description: Store a component's or template region's rendered HTML and reuse it on later requests, keyed by the values that change it.
---

# Cache rendered output

Some components do the same expensive work on every request: a product
card loads its record from the database and renders its children, and
the HTML comes out the same each time. Caching stores that rendered
output and reuses it on later calls with the same key, until the entry
expires.

There are two ways to cache:

- Add a `Cache` class to a component to cache every call to it.
- Wrap part of a template in `<c-cache>` to cache just that region.

The cache key decides which calls share an entry. Every value that can
change the output must be part of it, or one user can see another
user's HTML.

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

The first `ProductCard(product_id=42)` renders and stores its HTML. Later
calls with `product_id=42` reuse it for 300 seconds. When Citry reuses an
entry, the components in it get new IDs for the current page, so they
still work in the browser.

By default the key contains every input in `Kwargs`, after defaults and
validation. That works well when the inputs are plain values such as IDs
and strings.

## Build a stable key

When an input is an object, or only part of it affects the output,
define `Cache.vary()` and return the values that matter:

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

`vary()` receives read-only copies of the inputs and slots. Include
every value that can change the output. Use a database ID rather than an
object's `str()` or `repr()`, which can change between runs or contain
private data. If a record can change while keeping its ID, add a
revision number or update time, as `product_revision` does here.

Return only plain values of these exact types:

- `None`, `bool`, `int`, finite `float`, `str`, or `bytes`;
- `list`, `tuple`, or `dict` of those values, with `str` keys.

Subclasses such as enums, named tuples, or `OrderedDict` are rejected.

## `<c-cache>` regions

`<c-cache>` caches part of a template and adds no HTML of its own. Give
it a fixed `key` that names the region (the name is shared across the
whole app, so two templates with the same `key` share entries), and list in `c-vary` every value
the region uses:

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

This stores a separate entry for each user and locale. Citry does not
look inside the body to build the key, so add anything else that can
change it: the tenant, permissions, time zone, feature flags, or values
passed down with [provide and inject](/concepts/provide-and-inject/).

`<c-cache>` accepts these attributes:

- `key`: required non-empty string that names the region;
- `vary`: one value built from the plain types listed above, by default
  an empty tuple;
- `ttl`: seconds until the entry expires, `None` for no expiry, or `0`
  to skip the cache entirely;
- `version`: integer or non-empty string, by default `1`;
- `enabled`: boolean, by default `True`.

Write typed values as expressions: `c-ttl="300"` and
`c-enabled="False"`. A plain attribute such as `ttl="300"` passes a
string, which Citry rejects.

When you omit `ttl`, the entry uses the app's default, 300 seconds unless
you change it. Reusing an entry does not restart its expiry time.

## Protect private output

Two calls with the same key get the same HTML. Before you enable a
cache:

1. Put every value that depends on the user or request into the key.
2. Share an entry only among users allowed to see the same output.
3. Include CSRF tokens, CSP nonces, `template_globals`, and provided
   values when they appear in the cached HTML.
4. After each deploy that changes output, change the deployment
   generation, a value set up in
   [Cache backends](/performance/cache-backends/#share-cached-output-between-workers)
   that you change on every deploy.
5. Protect the cache store like your database. Anyone who can write to
   it can inject HTML that Citry trusts, and stored entries can contain
   private HTML, Events state, and JavaScript or CSS data.

Citry stores keys as hashes, so logs do not show the raw values or region
names. The stored entries themselves still need protection.

## What still runs

When Citry finds a stored entry, a cached component skips its data methods, render hooks,
template, child components, and slots. A `<c-cache>` region skips its
whole body.

Some work still runs on every call, because Citry needs the inputs to
build the key: input hooks, defaults, factories, type conversion,
validation, and your `Cache.vary()`.

When an outer entry is reused, the cache lookups nested inside it are
skipped too. Give the outer entry an expiry no longer than any content
inside it can tolerate.

## `version` and `clear()` { #update-or-remove-entries }

When the output changes for all entries of one component or region,
raise its `version`:

```citry-html
<c-cache key="category-nav" version="nav-v3">
  <c-category-nav />
</c-cache>
```

Old entries are no longer found. They stay in the store until they
expire or the store drops them.

To remove one entry, build its key and delete it:

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

`component_cache_key()` takes the key values you pass. It does not call
the component's `Cache.vary()` for you.

[`Citry.clear`][citry.Citry.clear] stops this `Citry` instance from
finding its existing entries, and empties stores that have a `clear()` method, such as the
default in-memory one. The shared adapters do not clear the whole store.
To invalidate entries on every worker at once, change the deployment
generation.

## Cache with slots

Citry cannot tell what passed-in slot content will render. With the
default key, a component that receives slot content raises
[`CacheKeyError`][citry.ext.cache.CacheKeyError]. This includes slot
defaults, factories, and slots set by input hooks.

A slot whose value is `None` is fine, and so is fallback content written
inside `<c-slot>` in the component's own template.

Leave a component that receives slot content uncached, unless a custom
`Cache.vary()` can describe every way that content changes the output:

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

## Handle cache failures

When an entry is missing, damaged, in an incompatible format, too
large, or impossible to reuse, Citry treats it as if no entry existed.
It renders normally and stores the new result. A result larger than the size limit still renders but is not
stored. [Cache backends](/performance/cache-backends/#limit-the-size-of-one-stored-render)
explains the limit.

An exception raised by the cache store's `get()` or `set()` reaches your
code. If a store outage should count as a missing entry, wrap the store
in an [adapter](/performance/cache-backends/#write-an-adapter-for-another-store)
that catches the error.

## Edge cases

### Limits on key values

A key value can be at most 32 containers deep, contain at most 10,000
items, and take at most 64 KiB once encoded. Each list, tuple, and
dictionary counts as one item, and so does each value and each
dictionary key inside it. A value that breaks a limit, or uses an
unsupported type, raises [`CacheKeyError`][citry.ext.cache.CacheKeyError]
when the component renders.

### `Const` values in keys

The default component key treats a value wrapped in [`Const`][citry.Const]
as different from the same plain value. `<c-cache>` removes `Const` from
its own attributes. Return plain values from `vary()` so the key is easy
to reason about.

### Transparent components

A component with `transparent = True` cannot use `Cache`, because it has
no HTML of its own for Citry to store and reuse. Wrap its template region in `<c-cache>`
instead.

### The Debug extension

Component and slot highlighting from the Debug extension turns rendered
output caching off, so the overlay always shows the live result.

## Related pages

- [Performance overview](/performance/) compares caching with the other
  ways to speed up rendering.
- [Cache backends](/performance/cache-backends/) covers where entries are
  stored and how to share them between workers.
- [Constant values](/performance/const/) and
  [Pure components](/performance/pure/) reuse work within ordinary
  renders.
- [Security](/security/) covers trust boundaries for templates and
  Events.

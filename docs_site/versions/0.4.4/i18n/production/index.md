---
title: Production and deployment
url: https://citry.dev/v/0.4.4/i18n/production/
description: "Compile standalone catalogs, validate installed artifacts, deliver browser partitions, and cache localized output safely."
---
# Production and deployment

Development and production load standalone catalog packages differently.

In development, Citry reads the package's `.ftl` files. A new engine sees the
current files from a source checkout or editable install. In production, Citry
requires checked generated artifacts and links the package without reopening
its Fluent source.

This source-free package linking reduces production startup work and ensures
the deployed runtime uses the exact catalog that passed the build.

## Compile each standalone package

From a development checkout, run:


```bash
citry --app myproject.engine:app \
  ext run i18n compile my_app_i18n
```


The command writes:


```text
my_app_i18n/_compiled/
├── manifest.json
├── server.json
└── link.json
```


- `server.json` contains the checked standalone catalog runtime artifact.
- `link.json` contains the checked information needed to join the package to
  the application's locale, layer, and fallback graph.
- `manifest.json` records the package identity and hashes every source and
  generated artifact.

The command reads the package through `importlib.resources`, but it must point
to a writable source-tree package while generating files. Compile before
building a wheel or zip archive.

## Include every required resource in the wheel

Every installed package needs:


```text
citry-i18n.toml
_compiled/manifest.json
_compiled/server.json
_compiled/link.json
```


Also include `locales/**/*.ftl` when the installed package should support
development loading or translator access. A production-only wheel may omit
those source files because `server.json` and `link.json` contain the checked
information needed at runtime.

For setuptools, use the exact package-data example in
[Organize catalogs](/v/0.4.4/i18n/catalogs/#create-a-catalog-package). Other build
backends need equivalent rules for the same paths. Keep `__init__.py` free of
registration side effects; Citry loads resources by the configured
import-package name.

Test the source distribution, its rebuilt wheel, and the installed wheel, not
only the source checkout. Start a production `Citry` instance from outside the
repository, resolve a package-owned message, and inspect the built archive for
every path named by `_compiled/manifest.json`. Citry's release checks do this
with the real `citry_ui_i18n` package and require production linking to parse
zero package FTL files. Citry also supports importable zip resources.

## Production rejects stale or incomplete packages

When `Citry(mode="production")` loads a configured catalog package, it checks:

- the exact `citry-i18n.toml` fields and schema version;
- the stable owner and source locale;
- the generated manifest shape;
- every generated artifact hash;
- the link artifact's package and locale records; and
- the compiler result and revision expected by the current runtime.

A missing artifact, edited generated file, malformed record, mismatched owner,
or stale revision stops startup. Citry does not silently fall back to reading
source FTL in production.

This source-free path applies to standalone catalog packages. Application
component `messages` still belong to the application registry and join the
project catalog when the engine inventories those components.

## Keep one catalog revision through a render

A `LocaleContext` records the catalog, formatter, and time-zone data revisions
that can change localized output.

If hot reload or another inventory change makes a context stale, Citry rejects
the operation and asks the caller to create a new context. One response never
mixes text produced from two catalog revisions.

Create request contexts after the application has loaded the current catalog:


```python
from citry.ext.i18n import make_context


context = make_context(app, locale=request.locale)
```


## Vary caches through the public context identity

When cached output depends on i18n, include the context identity through
Cache's ordinary public API:


```citry
class LocalizedPrice(Component):
    class Cache:
        enabled = True
        ttl = 300

        def vary(self, kwargs, slots):
            return {
                "product": kwargs["product"].id,
                "locale": self.component.i18n.context.identity,
            }
```


The identity includes locale, fallback chain, direction, time zone, time-zone
data revision, catalog revision, and formatter revision. Omitting it is an
explicit promise that the cached output is locale-independent.

The cache extension does not have i18n-specific flags or callback arguments.
The two extensions compose by passing one ordinary immutable public value.

## Deliver only browser messages a page needs

Server-only pages ship no i18n browser runtime or browser catalog.

A client-enabled provider records literal `$i18n` and injected `i18n` calls in
the rendered tree. Citry includes those public outputs, their referenced
messages, private terms, and required profile records. It does not send the
complete project catalog.

For static output with no Citry server endpoint, serialization includes the
finite required message set for every configured selectable locale. Dynamic
browser IDs must appear in `Component.I18n.client_messages`.

For a mounted application, the first response includes the current locale's
required data. `switchLocale()` or `ensureMessages()` requests another checked
partition when needed. The request carries the current revision and a bounded
set of public roots. The server rejects unknown private IDs, stale revisions,
unsupported locales, and oversized requests as one operation.

Inserted HTML fragments carry their own browser message requirements. The
provider adds those requirements while the fragment is present and removes
them when the fragment leaves the document.

## Keep locale changes atomic

Before a browser provider commits a switch, it loads and validates every known
message requirement for the target locale. A successful commit replaces the
readonly context and updates the provider's `lang` and `dir`. A failed or stale
request leaves the previous locale active.

Nested client providers recompute from the outside in. Inherited locale fields
follow the parent; explicit child fields stay fixed; a server-only provider is
a hard boundary.

See [Browser i18n](/v/0.4.4/i18n/browser/) for the authoring API and the difference
between browser-owned and server-owned text.

## Production checklist

Before deployment:

1. run the registry-backed project check;
2. compile and verify every standalone catalog package;
3. include descriptors and generated artifacts in wheels, plus locale sources
   when the wheel should support development use;
4. test the installed packages in `mode="production"`;
5. pass request locale and time zone through explicit `LocaleContext` values;
6. include `context.identity` in every cache key whose output is localized;
7. test client-enabled providers in every supported browser; and
8. verify `lang`, `dir`, accessible names, and fallback behavior in at least
   one right-to-left locale.
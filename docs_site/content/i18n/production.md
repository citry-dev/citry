---
title: Production and deployment
description: Compile standalone catalogs, validate installed artifacts, deliver browser partitions, and cache localized output safely.
---

# Production and deployment

In production, Citry does not read the `.ftl` files of a
[catalog package](/i18n/catalogs/). It loads checked files that you
generate before the build. Startup does less work, and the deployed
application runs exactly the catalog that passed your checks.

This page covers compiling and packaging catalogs, testing the installed
packages, and keeping caches and browser translations correct.

`Citry()` runs in production mode by default. With
`Citry(mode="development")`, Citry reads the `.ftl` files directly, so
you can edit translations without compiling.

## Compile each catalog package

From a development checkout, run:

```bash
citry --app myproject.engine:app \
  ext run i18n compile my_app_i18n
```

The command writes three files:

```text
my_app_i18n/_compiled/
├── manifest.json
├── server.json
└── link.json
```

- `server.json` holds the checked messages.
- `link.json` holds what Citry needs to combine the package with the
  application's locales, other packages, and fallbacks.
- `manifest.json` names the package and records a hash of every source
  and generated file.

The package must be a writable folder in your source tree. Compile
before you build a wheel or zip archive.

## Include the compiled files in the wheel

Every installed catalog package needs:

```text
citry-i18n.toml
_compiled/manifest.json
_compiled/server.json
_compiled/link.json
```

Also include `formats.json` if the package has one. Include
`locales/**/*.ftl` when the installed package should also load in
development mode or be translated further. A production-only wheel may
leave the `.ftl` files out.

For setuptools, use the package-data example in
[Organize catalogs](/i18n/catalogs/#include-the-catalog-files-in-your-wheel).
With another build backend, include the same paths.

Keep the package's `__init__.py` free of setup code. Citry finds the
files by the package name you list in `catalogs` and needs no
registration code.

## Test the installed package

Test the built artifacts, not only your source checkout: the source
distribution, the wheel rebuilt from it, and the installed wheel. From
outside the repository, start a `Citry` instance in production mode and
translate a message from the package. Check that the built archive
contains every file listed in `_compiled/manifest.json`.

A catalog package also loads when installed as an importable zip
archive.

## Know what stops startup in production

When a production engine loads a catalog package, it checks:

- the fields and schema version in `citry-i18n.toml`;
- the package owner and source locale;
- the shape of the manifest;
- the hash of every generated file;
- the package and locale records in `link.json`; and
- that the files match what the current Citry compiler produces.

A missing file, an edited generated file, a broken record, a different
owner, or files from an older compile stop startup. Citry never falls
back to reading the `.ftl` files in production. Compile again and
rebuild.

This applies to catalog packages only. Messages in your application's
own components are loaded with the components, as in development.

## Cache translated output safely

A cached render must not be reused for another language. When a cached
component's output depends on i18n, add the locale context's
`identity` to the cache key through `vary()`:

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

The identity covers everything that can change the output: locale,
fallback languages, direction, time zone, time-zone data version,
catalog version, and format version.

Leaving the identity out means you promise the output is the same in
every language.

## Create contexts after a reload

A locale context records the catalog version it was built from. If a
hot reload or another change loads a new catalog, operations on an older
context raise an error that asks you to create a new one. This way one
response never mixes text from two catalog versions.

Create each request's context after the application has loaded its
catalog:

```python
from citry.ext.i18n import make_context


context = make_context(app, locale=request.locale)
```

## Send the browser only the messages it needs

A page without a [client provider](/i18n/browser/) (a
`<c-i18n client>` element) sends no i18n code
or messages to the browser.

With a client provider, the page includes only the messages its browser
code uses, as found in literal `$i18n` calls, `$c-tr` bindings, and
`component.$i18n` or `this.$i18n` calls, plus the messages they include
and the format profiles they need. Citry never sends the whole catalog.

How more messages arrive depends on the setup:

- With Citry mounted in a
  [web framework integration](/web-frameworks/), the first response
  includes what the current locale needs. `switchLocale()` and
  `ensureMessages()` ask the server for more. The server rejects the
  whole request if it names an unknown or private message, an old
  catalog version, an unsupported locale, or too many messages.
- For static output with no Citry server, the page includes the needed
  messages for every selectable locale. List message IDs built at
  runtime in `Component.I18n.client_messages`.

Content that an [Events](/events/) handler renders again brings the messages it
uses. An [HTML fragment](/advanced/html-fragments/) needs its own
client provider.

## Production checklist

Before you deploy:

1. run `citry --app ... check`;
2. compile and verify every catalog package;
3. include the descriptor and compiled files in each wheel, plus the
   `.ftl` files if the wheel should also work in development mode;
4. test the installed packages in production mode;
5. create a locale context for each request from its locale and time
   zone;
6. add `context.identity` to the key of every cache whose output is
   translated;
7. test client providers in every browser you support; and
8. check `lang`, `dir`, accessible names, and fallback text in at least
   one right-to-left locale.

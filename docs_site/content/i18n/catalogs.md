---
title: Organize catalogs
description: Store shared and translated Fluent resources in importable packages with explicit ownership and fallback.
---

# Organize catalogs

A component's `messages` block holds its text in one language. The
translations into other languages need a home of their own, and so do
messages that many components share or that a component library
publishes.

Citry keeps them in a catalog package: an ordinary Python package that
contains Fluent `.ftl` files, one folder per locale, plus a small
descriptor file. This page shows how to create one, add translations,
and control which translation wins when several packages define the same
message.

## Create a package

A catalog package looks like this:

```text
my_app_i18n/
├── __init__.py
├── citry-i18n.toml
├── formats.json        # optional
├── locales/
│   ├── en-US/
│   │   ├── account.ftl
│   │   └── common.ftl
│   └── cs-CZ/
│       ├── account.ftl
│       └── common.ftl
└── _compiled/
    ├── manifest.json
    ├── server.json
    └── link.json
```

The descriptor `citry-i18n.toml` contains exactly three fields:

```toml
schema_version = 1
owner = "my-app"
source_locale = "en-US"
```

- `owner` is a stable name for whoever defines these messages. It is
  separate from the Python package name, so you can move or rename
  modules without changing it.
- `source_locale` is the language the package's original messages are
  written in. The package must contain at least one `.ftl` file in that
  locale's folder.

Locale folders must use the standard spelling, such as `en-US`, not
`EN-us`.

The `_compiled` folder holds files that the compile command generates
for production. While you edit translations, run the engine in
development mode so Citry reads the `.ftl` files directly:

```python
app = Citry(mode="development")
```

`Citry()` runs in production mode by default, and production mode
refuses a package that has no `_compiled` files. See
[Production and deployment](/i18n/production/) for the compile command.

## Add translations

Write each message's `@param` comments only in the source locale:

```fluent
# locales/en-US/account.ftl
# @param {str} $name - User name.
my-app-account-greeting = Hello, { $name }.
```

The translation uses the same variables without repeating the comments:

```fluent
# locales/cs-CZ/account.ftl
my-app-account-greeting = Ahoj, { $name }.
```

A translation may reorder the variables or use different plural
branches. It may not use a variable that the source does not declare.
Citry checks this before it builds the catalog.

A translation file may leave messages out. Citry then uses a fallback
language, as described below; it does not copy source text into every
locale file.

## Order the packages

List the packages in the engine settings, from lowest to highest
priority:

```python
app = Citry(
    extensions_defaults={
        "i18n": {
            "source_locale": "en-US",
            "locales": ("en-US", "cs-CZ"),
            "catalogs": (
                "vendor_checkout_i18n",
                "my_app_i18n",
            ),
        },
    },
)
```

Here `my_app_i18n` may replace a message from `vendor_checkout_i18n` in
the same locale. Messages in your application's own components rank
above all packages and may replace package messages too.

Two packages may not use the same `owner`.

## Which translation wins

Citry first looks for the message in the requested locale, across every
package and the application's components, from highest priority down.
Only then does it move to a fallback locale.

For example:

- the application replaces the English `my-app-account-greeting`;
- a package has both English and Czech versions; and
- the application has no Czech version.

An English request uses the application's version. A Czech request uses
the package's Czech translation. Your English replacement does not hide
an existing Czech translation.

When no locale in the configured fallbacks has the message, Citry uses
the source locale of the package that defined it. Different packages may
have different source locales.

A message's main text and each of its attributes fall back separately.
A locale may translate a button's label but not its `.aria-label`; the
`.aria-label` then comes from the fallback language.

A locale may stay partly translated. Untranslated messages show the
fallback text, and `citry check` warns about each `tr()` call that would
fall back, because plain text cannot carry its own `lang` attribute. See
[Language direction and accessibility](/i18n/direction-and-bidi/#mark-fallback-text-with-its-language)
for how to mark fallback text with its language. A
[`<c-trans>` rich message](/i18n/rich-messages/#translate-all-locales)
is the exception: it needs a translation in every locale that renders
it.

To list every message that falls back in a locale, run:

```bash
citry --app myproject.engine:app \
  ext run i18n coverage --locale cs-CZ
```

Add `--fail-on-missing` to make CI fail when a message falls back to its
source language. See
[Translation workflow and tooling](/i18n/workflow/#find-missing-translations).

## Share common messages

A catalog package may define messages that no component owns:

```fluent
my-app-common-open = Open
my-app-common-close = Close
my-app-common-save = Save
```

Every component registered with the engine can call these IDs, and
Citry checks such calls against the whole catalog.

Keep shared messages for text that really is shared. Text that belongs
to one component reads best beside that component, where translators
can see how it is used.

## Package the files { #include-the-catalog-files-in-your-wheel }

Make sure your build includes the descriptor and the compiled files.
Also include the `.ftl` files if the installed package should load in
development mode or be translated further. Citry checks this setuptools
setup in its own wheel builds:

```toml
[tool.setuptools]
include-package-data = false

[tool.setuptools.packages.find]
include = ["my_app_i18n*"]

[tool.setuptools.package-data]
my_app_i18n = [
    "citry-i18n.toml",
    "formats.json",
    "locales/**/*.ftl",
    "_compiled/*.json",
]
```

With another build backend, include the same paths through its own
package-data setting.

## Publish library text

A component library writes its text in each component's `messages`
block, and shared text in `.ftl` files in its source locale. Its build
can collect these into one catalog package.

Set the package's `owner` to the library's `ComponentLibrary.name`. When
an application lists that package in `catalogs`, Citry uses the package
for those messages and does not load the components' `messages` blocks a
second time.

The application can list its own catalog after the library's package to
replace selected messages. A replaced message still belongs to the
library, so it keeps falling back to the library's source locale.

## Ship named formats

A library can also ship format profiles: named formatting settings such
as `my-app-page-number`, described in [Format values](/i18n/formatting/).
Put them in a `formats.json` file next to `citry-i18n.toml`:

```json
{
  "number": {
    "my-app-page-number": {
      "input": {"notation": "decimal"}
    }
  }
}
```

Each profile name must start with the package's `owner` followed by
`-`. For the owner `my-app`, `my-app-page-number` is valid and
`page-number` is not. This keeps separately installed libraries from
taking the same names.

Citry adds package profiles to the application's profiles when it
creates the engine. A profile name that already exists, in the
application or in another package, stops startup with an error.

Include `formats.json` in the wheel and compile the package again after
any change. Production refuses a compiled package whose `formats.json`
has changed since it was compiled.

## Less common cases

### Startup fails

A development engine still compares an existing
`_compiled/manifest.json` with the current `.ftl` files. After you edit
a package that has compiled files, startup fails with a "does not match
its installed FTL sources" error. Run the compile command again.

### Edits not picked up

A running engine keeps the package list and files it started with.
When your development server reloads, it must create a new engine to
see package edits. A new engine reads the current files, including from
an editable install.

### Duplicate messages

Citry keeps each component's `messages` block and each `.ftl` file as a
separate source. If two
sources at the same priority define the same public message, such as two
files in one package, the error names both locations rather than letting
file order decide. A Fluent term (a phrase starting
with `-`) stays private to the file or block that defines it.

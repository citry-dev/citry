---
title: Organize catalogs
url: https://citry.dev/v/0.4.1/i18n/catalogs/
description: "Store shared and translated Fluent resources in importable packages with explicit ownership and fallback."
---
# Organize catalogs

Component `messages` blocks work well for source text that belongs to one
component. A standalone catalog package holds translations, shared application
messages, or messages published by a reusable library.

Citry loads catalog packages as resources. Importing one does not need to run
registration code or create an extension object.

## Create a catalog package

A package uses this layout:


```text
my_app_i18n/
├── __init__.py
├── citry-i18n.toml
├── formats.json
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


The `_compiled` files are generated for production. During development Citry
can read the `.ftl` files directly.

The descriptor contains exactly three fields:


```toml
schema_version = 1
owner = "my-app"
source_locale = "en-US"
```


`owner` is a stable identity for the messages. It is not the import package
name, so reorganizing Python modules does not need to transfer ownership.

Every package must contain at least one `.ftl` source for its `source_locale`.
Locale directory names must already use canonical spelling, such as `en-US`
rather than `EN-us`.

Make sure your build backend includes the TOML descriptor and generated
`_compiled` files in the wheel. Include the `.ftl` resources too when the
installed package should support development loading or downstream translation
work. A new development engine reads the current files from an editable
install. The configured package topology of an existing engine stays fixed, so
an application reload cycle must create a new engine after a package edit. A
production-only wheel may omit the source files after compilation.

Citry verifies this setuptools recipe in its own wheel builds:


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


If you use another build backend, configure its package-data feature to include
the same paths. The backend changes how files enter the distribution; it does
not change Citry's catalog layout.

## Ship package-owned format profiles

A reusable library may include a `formats.json` beside `citry-i18n.toml`. It
uses the same closed profile shape as the application's Python
`FormatRegistry`, expressed as JSON:


```json
{
  "number": {
    "my-app-page-number": {
      "input": {"notation": "decimal"}
    }
  }
}
```


Every profile name must start with the descriptor's stable owner plus `-`. For
an owner of `my-app`, `my-app-page-number` is valid and `page-number` is not.
This keeps independently installed libraries from claiming generic profile
names.

Package profiles are merged with the application's registry when the engine is
created. A package may not replace an application profile or a profile from
another package; a collision is a startup error. The `formats.json` digest is
part of the package manifest, so production rejects stale compiled artifacts.
Include the file in the wheel and rerun the catalog compile command after any
profile change.

## Configure packages in precedence order

Pass ordinary import-package strings:


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


The sequence runs from lower to higher priority. In this example,
`my_app_i18n` may override a public message from
`vendor_checkout_i18n` in the same locale. Application component messages form
the application layer and may override package messages too.

Two configured packages may not claim the same stable owner.

## Keep one source unit per component or file

Citry does not paste every `.ftl` file into one large resource. It keeps each
component `messages` block and each catalog file as its own source unit.

This matters for two reasons:

- a duplicate public message points to both source locations instead of being
  decided by file order; and
- a private Fluent term remains private to the file or component block that
  defines it.

Use a public namespaced message when several source units need the same text.
For example, put `my-app-common-open` in `common.ftl`, then reference that
public message from another public message.

## Define types in the source locale

The source locale owns each message's `@param` declarations:


```fluent
# locales/en-US/account.ftl
# @param {str} $name - User name.
my-app-account-greeting = Hello, { $name }.
```


Translations use the same variables without repeating their Python types:


```fluent
# locales/cs-CZ/account.ftl
my-app-account-greeting = Ahoj, { $name }.
```


The translation may reorder variables or use a different selector shape. It
may not add an undeclared input. Citry checks references and the effective
interface before building the catalog.

## Understand locale-major fallback

Citry looks for the requested locale before it falls back to another locale.
Within one locale, it checks higher-priority layers before lower-priority
layers.

Consider this setup:

- the application overrides the English `my-app-account-greeting`;
- a package supplies both English and Czech versions; and
- the application has no Czech override.

An English request uses the application's override. A Czech request uses the
package's Czech translation before it considers any English source text. An
English-only application override therefore does not hide an available Czech
translation.

If no configured fallback contains the output, Citry tries the source locale
of the package that owns that message. Different packages may have different
source locales.

Message values and attributes fall back independently. A locale may translate
the visible label while an untranslated `.aria-label` safely comes from an
earlier fallback, provided the call site can represent that language correctly.
See [Language direction and accessibility](/v/0.4.1/i18n/direction-and-bidi/) for the
language-markup rule.

Translation files may be sparse. An omitted output follows the configured
fallback chain and finally its defining owner's source locale; Citry does not
silently copy source text into every locale file. Use
`citry ext run i18n coverage --locale <locale>` to see the exact outputs that
fall back, and add `--fail-on-missing` when a locale must be complete in CI.

## Put common messages outside components

A catalog package may define public messages that no component owns directly:


```fluent
my-app-common-open = Open
my-app-common-close = Close
my-app-common-save = Save
```


Any component registered with the configured engine may call those public IDs.
Citry checks literal keys against the complete project catalog, not only the
calling component's `messages` block.

Use shared messages for genuinely shared concepts. Keep component-specific
copy near its component so translators can find the owning interface and
context.

## Package reusable library messages

A component library authors family-specific source text in each component's
`messages` block and shared text in standalone source-locale FTL. Its build can
collect those source units into a dedicated catalog package. Give the
`ComponentLibrary` and catalog descriptor the same stable owner name; when an
application configures that package, Citry uses the checked package artifact
instead of loading the exported component block a second time as an application
override.

The application adds that package to `catalogs` and may place an application
catalog later in the sequence to override selected public messages.

An override keeps the original message owner and its source fallback. The
application does not become the defining owner merely because it supplies a
higher-priority value.

Compile package artifacts before building a production wheel. See
[Production and deployment](/v/0.4.1/i18n/production/) for the exact command and
validation behavior.
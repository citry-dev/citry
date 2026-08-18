---
title: Locales and context
url: https://citry.dev/v/0.4.0/i18n/locale-context/
description: "Configure supported locales and pass one explicit locale context through a render tree or subtree."
---
# Locales and context

Every localized result depends on a locale context. It contains the selected
locale, fallback chain, writing direction, optional time zone, and the
revisions of the catalog and formatter data used by the render.

You normally create the context once from request data and provide it to the
root component.

When registered components declare `I18n.messages_locale`, Citry can also make
a source-mode context without engine settings. It infers the default from the
unique application source locale, or from the unique library source locale
when the application owns no messages. Configure the locale graph below when
users need selectable translations, when source ownership is ambiguous, or
when the application needs explicit fallback policy.

## Configure the locale graph

The engine configuration accepts these fields:


```python
from citry import Citry

app = Citry(
    extensions_defaults={
        "i18n": {
            "source_locale": "en-US",
            "default_locale": "en-US",
            "locales": ("en-US", "cs-CZ", "ar-EG"),
            "fallbacks": {
                "ar-EG": ("en-US",),
            },
            "catalogs": ("my_app_i18n",),
        },
    },
)
```


`source_locale` names the language used by application source messages.
`default_locale` is used when `make_context()` receives no locale. It defaults
to `source_locale` and must appear in `locales`.

`locales` is an ordered sequence of locales that users may select. A source
locale may be fallback-only, but every default locale must be selectable.

`fallbacks` maps one known locale to an ordered sequence of other known
locales. Citry rejects unknown nodes and cycles when it creates the engine.
After those configured fallbacks, each message may use the source locale of
the catalog package that owns it.

`catalogs` is an ordered sequence of import-package names. See
[Organize catalogs](/v/0.4.0/i18n/catalogs/) for the package layout and precedence
rules.

## Citry canonicalizes locale names

Locale names use Unicode BCP 47 spelling. Citry canonicalizes configured and
requested names through the same Rust implementation. For example, `EN-us`
becomes `en-US` and a recognized deprecated language alias becomes its current
form.

Two inputs that become the same canonical locale are a configuration error.
Catalog directory names are stricter: they must already use the canonical
spelling so a package has one stable resource path for each locale.

Unicode extensions may select data such as a numbering system or calendar.
The complete tag must be one of the configured `locales` or an inferred
source-mode locale before it can be selected:


```python
from citry.ext.i18n import make_context


context = make_context(app, locale="hi-IN-u-nu-deva")
```


The complete canonical locale remains part of the context. Citry does not
silently reduce it to only its language and region.

## Create a context from request data

Pass the same application that owns the components:


```python
from citry.ext.i18n import make_context


context = make_context(
    app,
    locale=request.query_params["locale"],
    time_zone="Europe/Prague",
)
```


An unknown or empty locale raises an error. An invalid IANA time-zone name also
raises an error. Omitting `locale` selects the configured `default_locale` or
the inferred source-mode default; omitting `time_zone` creates a zone-free
context.

`make_context()` returns a new immutable value. It does not change the engine's
default context and does not affect another request.

## Provide the context at the render root

Pass the exact context through Citry's ordinary root-provide channel:


```python
rendered = Page().render(
    provides={"citry_i18n": context},
)
```


Every descendant rendered along that tree sees the context through
`self.i18n.context`, template `tr()` and `fmt`, and the built-in i18n
components.

A separate `render()` call creates a separate root:


```citry
class Summary(Component):
    citry = app

    def template_data(self, kwargs, slots):
        context = self.i18n.context
        standalone = Detail().render(
            provides={"citry_i18n": context},
        )
        return {"standalone": standalone}
```


Passing the context again is intentional. The output of `Detail().render()`
depends on the arguments visible at that call, not on where the function
happened to run.

## Override one subtree

`<c-i18n>` provides another context to its descendants:


```citry-html
<main>
  <c-account-card />

  <c-i18n locale="ar-EG" tag="aside">
    <c-account-card />
  </c-i18n>
</main>
```


With `tag="aside"`, Citry emits a real element with the selected `lang` and
derived `dir` attributes. Without `tag`, a server-only provider is transparent
and adds no HTML wrapper.

The provider accepts `locale`, `direction`, and `time_zone` overrides. Omitted
fields inherit. When the locale changes and direction is omitted, Citry derives
the new direction from the locale.

Client-enabled providers need a real `tag` because the browser uses that
element as the subtree boundary. See [Browser i18n](/v/0.4.0/i18n/browser/).

## Use the context outside a component

Inside components, use `self.i18n`. Outside components, use
`i18n.for_context(context)`:


```python
service = i18n.for_context(context)

heading = service.tr("my-app-account-title")
amount = service.format.currency(
    total,
    "EUR",
    format="account-balance",
)
```


The service exposes `context`, `tr()`, `resolve()`, `format`, and `parse`. Every
operation uses the same explicit context.

## Use context identity in a cache key

Localized output must not share a cache entry with output produced under a
different context. Pass the context's plain immutable identity through Cache's
ordinary `vary()` contract:


```citry
class LocalizedCard(Component):
    class Cache:
        enabled = True

        def vary(self, kwargs, slots):
            return self.component.i18n.context.identity
```


Cache and i18n remain separate extensions. The cache receives an ordinary
public value and does not need an i18n-specific option.
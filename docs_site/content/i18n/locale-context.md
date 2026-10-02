---
title: Locales and context
description: Configure supported locales and pass one explicit locale context through a render tree or subtree.
---

# Locales and context

Each request may need a different language, and sometimes a different
time zone. You choose them per request, then pass that choice into the
render so every component uses it.

Citry carries the choice in a locale context: a read-only value that
holds the selected locale, its fallback languages, the writing
direction, an optional time zone, and the version of the translations it
was built from. A locale is a language code with an optional region,
such as `cs-CZ`.

This page shows how to configure the locales your application supports,
create a context for each request, and pass it to the render. It then
covers changing the language for one part of the page.

## Configure the supported locales

List the locales in the engine's i18n settings:

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

- `source_locale` is the language your application's own messages are
  written in.
- `default_locale` is used when a request does not choose a locale. It
  defaults to `source_locale` and must be listed in `locales`.
- `locales` lists, in order, the locales users may select. The source
  locale may be left out if it only serves as a fallback.
- `fallbacks` says which locales to try, in order, when a message has no
  translation in a given locale. After them, Citry tries the source
  locale of whichever package defined the message.
- `catalogs` lists the packages that hold translations. See
  [Organize catalogs](/i18n/catalogs/).

Citry checks the settings when it creates the engine. A fallback that
names an unknown locale, or fallbacks that form a loop, raise
an error.

## Create a context for each request

Call `make_context()` with the same engine that owns the components:

```python
from citry.ext.i18n import make_context


context = make_context(
    app,
    locale=request.query_params["locale"],
    time_zone="Europe/Prague",
)
```

Leave out `locale` to use the default locale. Leave out `time_zone` when
the page shows no times that depend on a zone.

`make_context()` raises `ValueError` for an empty locale, a locale that
is not in `locales`, or an unknown time-zone name. Validate or map user
input before passing it, or catch the error and fall back to the
default.

Each call returns a new value. It does not change the engine's default
or affect any other request.

## Pass the context to the root render

Provide the context under the key `citry_i18n` when you render the page:

```python
rendered = Page().render(
    provides={"citry_i18n": context},
)
```

Every component in that render then translates and formats with it:
template `tr()` and `fmt`, Python code through `self.i18n`, and the
built-in i18n components.

A component that calls `render()` itself, inside a data method, starts a
new render that does not see the page's context. Pass the context again:

```citry
class Summary(Component):
    citry = app

    def template_data(self, kwargs, slots):
        context = self.i18n.context
        detail = Detail().render(
            provides={"citry_i18n": context},
        )
        return {"detail": detail}
```

This keeps each render's output determined by what you pass to it. See
[Provide and inject](/concepts/provide-and-inject/) for the general rule.

## Show one part of the page in another language

Wrap part of a template in `<c-i18n>` to give it a different locale:

```citry-html
<main>
  <c-account-card />

  <c-i18n locale="ar-EG" tag="aside">
    <c-account-card />
  </c-i18n>
</main>
```

With `tag="aside"`, Citry renders an `<aside>` element with the matching
`lang` and `dir` attributes, here `lang="ar-EG" dir="rtl"`. Without
`tag`, `<c-i18n>` adds no HTML of its own.

`<c-i18n>` also accepts `direction` (`ltr` or `rtl`) and `time_zone`.
Anything you leave out is inherited from the surrounding context. When
you change the locale but not the direction, Citry picks the direction
that suits the new locale.

A locale outside `locales`, any other `direction`, or an unknown time
zone raises `ValueError` during the render.

To let this part of the page switch language in the browser, add
`client` and keep `tag`. See [Browser i18n](/i18n/browser/).

## Translate outside a component

Code outside a component, such as an email builder or a view function,
gets the same operations from the extension:

```python
i18n = app.extensions.get_extension("i18n")
service = i18n.for_context(context)

heading = service.tr("my-app-account-title")
amount = service.format.currency(
    total,
    "EUR",
    format="account-balance",
)
```

The service has `context`, `tr()`, `resolve()`, `format`, and `parse`,
and every operation uses the context you passed.

## Cache translated output per context

A cached render must not be reused for a different language. Return the
context's `identity` from the cache's `vary()` method:

```citry
class LocalizedCard(Component):
    class Cache:
        enabled = True

        def vary(self, kwargs, slots):
            return self.component.i18n.context.identity
```

The identity is a plain value that changes whenever anything in the
context would change the output. See
[Production and deployment](/i18n/production/#cache-translated-output-safely)
for a cache key that combines it with other inputs.

## Rules for less common cases

### Different spellings of the same locale

Citry converts locale names to one standard spelling (BCP 47) before it
compares them. For example, `EN-us` becomes `en-US`, and an outdated
language code becomes its current form. Two entries in `locales` that
turn out to be the same locale are a configuration error.

Folder names inside a catalog package are stricter: they must already
use the standard spelling, such as `en-US`.

### Locales with extra options

A locale can carry Unicode options that pick a numbering system or
calendar, such as `hi-IN-u-nu-deva` for Hindi with Devanagari digits.
That exact name must be listed in `locales` before a request can select
it:

```python
context = make_context(app, locale="hi-IN-u-nu-deva")
```

The context keeps the full name. Citry does not shorten it to the
language and region.

### Components with messages but no i18n settings

When components declare `I18n.messages_locale` and the engine has no
i18n settings, `make_context()` still works. Citry infers the default
locale: the one source locale used by the application's own components,
or, if the application has no messages of its own, the one source locale
used by component libraries. If there is more than one candidate, Citry
raises an error. Configure the settings above to choose explicitly.

Without settings, a request may select any locale that a registered
component's messages are written in. When the engine has neither i18n
settings nor component messages, `make_context()` raises
`I18nNotConfiguredError`.

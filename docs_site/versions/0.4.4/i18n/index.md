---
title: Internationalization
url: https://citry.dev/v/0.4.4/i18n/
description: "Translate component text, format locale-sensitive values, and pass locale context explicitly through a Citry render tree."
---
# Internationalization

Internationalization covers more than replacing one sentence with another.
Citry's built-in i18n extension coordinates:

- translated messages and accessible labels;
- locale fallback;
- `lang`, left-to-right, and right-to-left output;
- numbers, percentages, currencies, dates, times, lists, and units;
- strict parsing of localized form input; and
- optional browser-owned translations inside one subtree.

The extension has three modes:

- with no settings and no message assets, it is dormant;
- a registered component `messages` or `messages_file` asset activates
  server-side source mode; and
- engine settings activate selectable locales, catalog packages, named
  formats, parsing, and optional browser switching.

Source mode needs no application settings and adds no browser code. It exists
so a reusable component can translate its own defaults through the ordinary
`tr()` API without forcing every application to configure i18n.

## Configure the locales your application supports

Give the built-in extension a source locale and an ordered set of selectable
locales:


```python
from citry import Citry

app = Citry(
    extensions_defaults={
        "i18n": {
            "source_locale": "en-US",
            "default_locale": "en-US",
            "locales": ("en-US", "cs-CZ", "ar-EG"),
        },
    },
)
```


Citry checks the complete configuration when it creates the engine. Invalid
locale names, duplicate canonical names, an unknown default locale, and cycles
in the fallback graph are errors.

## Write source messages beside the component

The `messages` asset contains Fluent source for the component. Keep it below
the template, JavaScript, and CSS:


```citry
from citry import Component


class AccountCard(Component):
    class I18n:
        messages_locale = "en-US"

    class Kwargs:
        name: str

    citry = app

    template = """
      <article>
        <h2>{{ tr("my-app-account-greeting", name=name) }}</h2>
      </article>
    """

    messages = """
      # @param {str} $name - User name.
      my-app-account-greeting = Welcome, { $name }.
    """
```


`messages_locale` says which language the component's defining Fluent source
is written in. Defining a message asset makes the engine-wide registered source
catalog available: another registered component may call this public message
ID even when `AccountCard` is not rendered.

`tr()` always returns text, so the template escapes it normally. Citry reads
the message ID, variables, and `@param` types and checks literal calls against
that interface.

The inline block is the defining source. Put translator-owned locales in a
[catalog package](/v/0.4.4/i18n/catalogs/).

## Pass the locale into the render

For selectable locales, create a context from an explicit request value, then
provide that context to the root render:


```python
from citry.ext.i18n import make_context


def render_account_page(locale: str):
    context = make_context(app, locale=locale)

    return AccountPage().render(
        provides={"citry_i18n": context},
    )
```


This rule keeps each render predictable. A component rendered separately
inside `template_data()` starts another tree and does not silently take the
caller's locale. Pass the context to that render when it should use the same
locale.

Inside a component, use `self.i18n`. Outside a component, create a service for
one explicit context:


```python
i18n = app.extensions.get_extension("i18n")
service = i18n.for_context(context)
text = service.tr("my-app-account-greeting", name="Ada")
```


Neither call changes process-wide or task-wide state.

## Choose server-owned or browser-owned text

Use server rendering by default:


```citry-html
<h1>{{ tr("my-app-account-title") }}</h1>
```


The result is ordinary HTML. If the browser later switches locale, it does not
know that this text came from `tr()` and does not rewrite it.

Use `$i18n` only for a control that genuinely needs to change in place:


```citry-html
<c-i18n tag="section" client>
  <h1 x-text="$i18n.tr('my-app-account-title')"></h1>
  <button @click="$i18n.switchLocale('cs-CZ')">Čeština</button>
</c-i18n>
```


For a page-wide language change, send the new locale as a URL, form, cookie, or
other explicit request input and render the page again. This updates all
server-owned content and avoids making initial page interactivity wait for a
large number of Alpine expressions.

## Continue by user need

- [Locales and context](/v/0.4.4/i18n/locale-context/) explains configuration,
  canonical locale names, fallback, and subtree providers.
- [Write messages](/v/0.4.4/i18n/messages/) covers Fluent syntax and typed variables.
- [Organize catalogs](/v/0.4.4/i18n/catalogs/) covers application-wide translations
  and installable catalog packages.
- [Rich messages](/v/0.4.4/i18n/rich-messages/) shows how translators can position
  application-owned links and inline components without writing HTML.
- [Format values](/v/0.4.4/i18n/formatting/) and
  [parse localized input](/v/0.4.4/i18n/parsing/) cover locale-sensitive data.
- [Browser i18n](/v/0.4.4/i18n/browser/) explains `$i18n`, loading, and subtree
  switching.
- [Language direction and accessibility](/v/0.4.4/i18n/direction-and-bidi/) covers
  `lang`, `dir`, fallback language, and bidirectional text.
- [Translation workflow](/v/0.4.4/i18n/workflow/) covers project checks and catalog
  commands.
- [Production and deployment](/v/0.4.4/i18n/production/) covers compiled catalog
  packages, browser partitions, and cache identity.
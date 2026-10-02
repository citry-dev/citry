---
title: Internationalization
description: Translate component text, format locale-sensitive values, and pass locale context explicitly through a Citry render tree.
---

# Internationalization

Internationalization (i18n) lets one application show its pages in
several languages. Citry's built-in i18n extension handles the parts
that differ between languages:

- translated text, including accessible labels such as `aria-label`;
- numbers, currencies, dates, times, lists, and units written the way
  each language writes them;
- reading numbers and dates that users type into forms;
- the `lang` and `dir` attributes, including right-to-left languages
  such as Arabic.

This page walks through the basic setup: write text as messages, add the
languages users can choose, and pick a language for each request. The
other pages in this section cover each part in depth.

## Write messages

A message is a piece of user-visible text with a stable ID. Write
messages in the component's `messages` block, using
[Fluent](https://projectfluent.org/), a translation format designed so
translators can handle each language's grammar. Call a message from the
template with `tr()`:

In these examples, `app` is your `Citry` engine:

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

`messages_locale` says which language the messages are written in. Here
it is `en-US`, a locale: a language code with an optional region.

The `@param` comment declares the type of each variable the message
uses. Citry checks `tr()` calls against it, so a missing or wrongly
typed argument is reported.

`tr()` returns plain text, and the template escapes it like any other
value.

This works without any i18n settings and adds no browser code. Any registered component can call
`my-app-account-greeting`, even when `AccountCard` is not on the page.
[Write messages](/i18n/messages/) covers the Fluent syntax.

## Add languages

To offer more than the source language, list the locales in the
engine's i18n settings:

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

Citry checks these settings when it creates the engine. An invalid
locale name, two names for the same locale, or a default locale missing
from `locales` raises an error.

The translations themselves go in a catalog package: a Python package of
Fluent files, one folder per locale. See
[Organize catalogs](/i18n/catalogs/).

## Choose the language

Read the locale from the request, such as a URL parameter or a cookie.
Build a locale context from it, then pass the context to the root
render. A locale context is a read-only value that holds the selected
locale and everything derived from it, such as the writing direction:

```python
from citry.ext.i18n import make_context


def render_account_page(locale: str):
    context = make_context(app, locale=locale)

    account_page = AccountPage()
    return account_page.render(
        provides={"citry_i18n": context},
    )
```

Every component in that render uses the context. A component that
calls `render()` itself must pass it again. Nothing changes for
other requests, because Citry keeps no global "current locale".

Inside a component, Python code reads the same context through
`self.i18n`, for example `self.i18n.tr(...)`.
[Locales and context](/i18n/locale-context/) covers time zones, a
different language for one part of the page, and use outside a
component.

## Switch in the browser

By default, text is translated on the server and arrives as ordinary
HTML:

```citry-html
<h1>{{ tr("my-app-account-title") }}</h1>
```

To switch the whole page to another language, send the new locale with
the next request, for example in the URL, and render the page again.

When a small part of the page must change language without a reload,
wrap it in `<c-i18n client>` and translate with `$i18n` in Vue
expressions:

```citry-html
<c-i18n tag="section" client>
  <h1 v-text="$i18n.tr('my-app-account-title')"></h1>
  <button @click="$i18n.switchLocale('cs-CZ')">
    Čeština
  </button>
</c-i18n>
```

The switch changes only the Vue-owned text inside that element.
Text rendered on the server with `tr()` stays in its original language. [Browser i18n](/i18n/browser/) explains when to use
each option.

## Continue by task

- [Locales and context](/i18n/locale-context/): configure locales,
  fallback languages, and time zones, and change the language of one
  part of the page.
- [Write messages](/i18n/messages/): Fluent syntax, plural forms, typed
  variables, and labels such as `aria-label`.
- [Organize catalogs](/i18n/catalogs/): store translations and shared
  messages in installable packages.
- [Rich messages](/i18n/rich-messages/): let translators place a link or
  a small component inside a sentence without writing HTML.
- [Format values](/i18n/formatting/) and
  [Parse localized input](/i18n/parsing/): numbers, currencies, dates,
  and times.
- [Browser i18n](/i18n/browser/): translate and switch languages in the
  browser.
- [Language direction and accessibility](/i18n/direction-and-bidi/):
  `lang`, `dir`, and mixed left-to-right and right-to-left text.
- [Translation workflow and tooling](/i18n/workflow/): checks, coverage
  reports, and catalog commands.
- [Production and deployment](/i18n/production/): compile catalogs,
  package them, and cache translated output.

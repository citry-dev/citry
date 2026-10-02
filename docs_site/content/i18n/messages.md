---
title: Write messages
description: Define Fluent messages beside components and call them through typed Citry translation APIs.
---

# Write messages

To make text translatable, move it out of the template into a message: a
piece of text with a stable ID that translators can translate. The
template then asks for the message by ID, and Citry returns the text in
the current language.

Citry writes messages in [Fluent](https://projectfluent.org/), a
translation format in which each language can follow its own grammar,
such as its own plural forms. Citry adds one thing to Fluent: an
`@param` comment that declares the type of each variable, so Citry can
check every call.

This page covers writing messages and calling them. Translations into
other languages go in catalogs, covered in
[Organize catalogs](/i18n/catalogs/).

## Add messages

Put the messages in the component's `messages` block, after the
template, JavaScript, and CSS:

```citry
from citry import Component


class AccountCard(Component):
    class I18n:
        messages_locale = "en-US"

    class Kwargs:
        name: str
        count: int

    citry = app

    template = """
      <article>
        <h2>{{ tr("my-app-account-greeting", name=name) }}</h2>
        <p>{{ tr("my-app-account-count", count=count) }}</p>
      </article>
    """

    messages = """
      # @param {str} $name - User name.
      my-app-account-greeting = Welcome, { $name }.

      # @param {int} $count - Number of accounts.
      my-app-account-count = { $count ->
          [one] One account
         *[other] { $count } accounts
      }
    """
```

Each message starts with its ID, then `=`, then the text. `{ $name }`
inserts a variable, which the caller passes as a keyword argument to
`tr()`.

`I18n.messages_locale` says which language the messages are written in.

A message defined in one component is available to every component
registered with the same engine. Any of them can call
`my-app-account-greeting`, even when `AccountCard` has not rendered.

Messages work without any i18n settings. Citry then translates on the
server into the source language only; it adds no browser code, language
switching, or named formats until you configure them.

## Call a message

In a template, call `tr()` with the message ID and its variables:

```citry-html
<p>{{ tr("my-app-account-greeting", name=account.name) }}</p>
```

In component Python code, call `self.i18n.tr()`:

```python
text = self.i18n.tr(
    "my-app-account-greeting",
    name=account.name,
)
```

Outside a component, get a service for an explicit
[locale context](/i18n/locale-context/):

```python
i18n = app.extensions.get_extension("i18n")
service = i18n.for_context(context)
text = service.tr("my-app-account-greeting", name="Ada")
```

All three return plain text. A template escapes it like any other value.

## Declare variable types

Write one `@param` comment per variable directly above the message:

```fluent
# @param {str} $name - User name shown in the greeting.
my-app-account-greeting = Welcome, { $name }.
```

The text after `-` is optional. It is shown to translators and in the
editor, so use it to say what the value is.

The types are:

| Type | Accepted value |
|---|---|
| `str` | A Python string |
| `int` | An exact Python integer |
| `Decimal` | A finite `decimal.Decimal` |
| `datetime` | An aware Python `datetime`, where the message needs an exact moment in time |
| `Slot` | Content supplied by the application, used in [rich messages](/i18n/rich-messages/) |

Citry checks `tr()` calls against these declarations. A missing
variable, an unknown one, or a value of the wrong type is an error.

Each declaration belongs to one message. Two messages may both use
`$name` with different types.

Write the type name exactly as listed. Citry reads it as text and does
not import anything, so a dotted path such as `decimal.Decimal` is not
accepted.

## Write plural forms

Use a selector, `{ $count -> ... }`, which picks one branch based on a
value. Each language can then choose its right form:

```fluent
# @param {int} $count - Number of unread messages.
my-app-inbox-count = { $count ->
    [one] One unread message
   *[other] { $count } unread messages
}
```

The branch marked `*` is the default. Each translation may use the
branches its own language needs; a language with three plural forms
writes three, and a language with none writes one.

## Translate labels { #translate-labels-such-as-aria-label }

A message can have attributes: related texts, each on its own line
starting with `.`, that describe the same thing. Use them for an
element's visible label and its accessible label or tooltip:

```fluent
# @param {str} $name - User whose actions are available.
my-app-account-actions = Actions
    .aria-label = Actions for { $name }
    .title = Open the actions for { $name }
```

Ask for an attribute with `attr=`, and put the result in an HTML
attribute with a `c-` attribute, whose value Citry evaluates as Python:

```citry-html
<button
  c-aria-label="tr(
    'my-app-account-actions',
    attr='aria-label',
    name=account.name,
  )"
>
  {{ tr("my-app-account-actions") }}
</button>
```

A `{{ }}` expression inside a plain attribute value stays literal text,
so the `c-` form is required.

Citry works out the needed variables for each output separately. Above,
the main text needs none, while `.aria-label` and `.title` need `name`.

The `@param` comments above the message cover the main text and all its
attributes. Do not put a comment between the main text and an
attribute, because that ends the message.

## Name by feature

Give each ID a prefix for your application or package, then one for the
feature or component:

```text
my-app-account-card-greeting
my-app-account-card-actions
my-app-checkout-payment-error
```

A prefix shows where a message is defined and keeps IDs from different
components and packages apart. Do not build the ID from the English
sentence. Translations are stored under the ID, so it must stay the same
when the wording changes.

## Use a messages file

Use `messages_file` when you prefer a separate `.ftl` file:

```citry
class AccountCard(Component):
    citry = app

    messages_file = "account_card.ftl"
```

A component has either `messages` or `messages_file`, not both. They
load, inherit, and reload like a component's other files, such as
`template_file`.

## Reuse text

### Reuse with a term

A Fluent term is a reusable phrase whose name starts with `-`:

```fluent
-product-name = Citry

my-app-welcome = Welcome to { -product-name }.
my-app-about = About { -product-name }
```

A term is private to the `messages` block or `.ftl` file that defines
it. Another component may define its own `-product-name` without a
conflict. To share a phrase across files, use a public message instead.

### Include a message

A message may include another message by its ID:

```fluent
my-app-product-name = Citry
my-app-page-title = { my-app-product-name } account
```

Citry follows these references when it checks variable types and
fallback, and when it sends messages to the browser. Calling
`my-app-page-title` is enough; the message it includes comes along.

## Get the language used

When a translation is missing, Citry falls back to another language.
`tr()` returns only the text. Use `resolve()` when you also need to know
which language was used:

```python
resolved = self.i18n.resolve(
    "my-app-account-greeting",
    name=name,
)

resolved.text
resolved.locale
resolved.direction
resolved.used_fallback
```

Use this to mark fallback text with its own `lang` attribute. A plain
`tr()` call that would fall back to another locale fails `citry check`,
because its text cannot carry a `lang`. See
[Language direction and accessibility](/i18n/direction-and-bidi/#mark-fallback-text-with-its-language).

## Hover for types

When the Citry editor extension knows your application (the `citry.app`
setting), hover a variable name in a `tr()` call to see its type and
description. Go to definition opens the `@param` line, even when the
message is in another component, file, or catalog package. This works in
templates, Python, Vue `$i18n.tr()`, component JavaScript, and
`<c-trans>`. See [VS Code](/ide/vscode/).

## Less common cases

### Missing `@param`

For a simple variable used only on the server, a missing `@param` is a
warning (`citry.i18n.missing-param-type`).
[Translation workflow and tooling](/i18n/workflow/#make-a-missing-type-an-error-or-ignore-it)
shows how to change its severity.

A type is always required when the variable is used in a selector, a
`Slot`, a formatting function, or a browser call, because Citry cannot
check those safely without it.

### `@param` in translations

The message in the source language declares the types. Translations use
the same variables without the comments.

One exception exists: a source-language catalog file may repeat a
component's message with the same `@param` names and types. This lets a
library build its catalog package from its components' `messages`
blocks. Changing a name or type in the repeat is an error.

### Set `messages_locale`

Declare `I18n.messages_locale` on the component that defines `messages`
or `messages_file`. A subclass that inherits those messages also keeps
that language.

An application component may leave it out when the engine settings
declare `source_locale`; it then uses that locale. A reusable library
should always declare it, because it cannot rely on the application's
settings.

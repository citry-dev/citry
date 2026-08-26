---
title: Write messages
url: https://citry.dev/v/0.4.4/i18n/messages/
description: "Define Fluent messages beside components and call them through typed Citry translation APIs."
---
# Write messages

Citry uses Fluent for translated messages. Fluent gives translators stable
message names, attributes for related outputs, selectors for language-specific
grammar, and private terms for reuse inside one source unit.

Citry adds one piece of metadata: a small `@param` declaration that tells the
checker and runtime which Python value type each message variable accepts.

## Add a messages asset to a component

Place `messages` after the component's template, JavaScript, and CSS:


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


Use `messages_file` when the source belongs in a separate `.ftl` file:


```citry
class AccountCard(Component):
    citry = app
    messages_file = "account_card.ftl"
```


`messages` and `messages_file` are mutually exclusive. They load, inherit, and
reload like the other primary component assets.

`Component.I18n.messages_locale` identifies the language of the component's
defining source. Keep it on the component that owns the `messages` or
`messages_file` declaration; an inherited asset keeps its declaration owner's
locale. When engine i18n settings already declare `source_locale`, an
application component may omit the component field and inherit that locale.
Reusable libraries should declare it explicitly.

Defining a message asset activates source-mode server translation even when the
application has no i18n settings. Citry compiles the complete registered source
catalog, so component B may call a public key defined by component A without
rendering A first. No browser catalog, locale switcher, named package format,
or parser is enabled until the application configures those features.

With no explicit engine default, Citry chooses the only application source
locale. If there are no application message owners, it chooses the only
library source locale. Multiple possible application or library source locales
are an error; configure the engine instead of relying on discovery order.

## Call a message from templates and Python

Template `tr()` is the text form of `self.i18n.tr()`:


```citry-html
<p>{{ tr("my-app-account-greeting", name=account.name) }}</p>
```


Inside Python component code:


```python
text = self.i18n.tr(
    "my-app-account-greeting",
    name=account.name,
)
```


Outside a component, use a service with an explicit context:


```python
service = i18n.for_context(context)
text = service.tr("my-app-account-greeting", name="Ada")
```


All three forms return plain text. Template rendering escapes the result.

Use `resolve()` when the caller also needs the locale selected by fallback:


```python
resolved = self.i18n.resolve("my-app-account-greeting", name=name)

resolved.text
resolved.locale
resolved.direction
resolved.used_fallback
```


See [Language direction and accessibility](/v/0.4.4/i18n/direction-and-bidi/) before
putting fallback text into an element whose surrounding language may differ.

## Group related outputs with attributes

A message may contain a main value and related attributes:


```fluent
# @param {str} $name - User whose actions are available.
my-app-account-actions = Actions
    .aria-label = Actions for { $name }
    .title = Open the actions for { $name }
```


Request an attribute explicitly:


```citry-html
<button
  aria-label="{{ tr(
    'my-app-account-actions',
    attr='aria-label',
    name=account.name,
  ) }}"
>
  {{ tr("my-app-account-actions") }}
</button>
```


The `@param` declarations above the message apply to its value and all its
attributes. Fluent does not attach a comment to an individual attribute. Do
not put another top-level comment between the value and an attribute, because
that ends the message.

Citry derives the required subset separately for each output. The main value
above needs no arguments, while `.aria-label` and `.title` require `name`.

## Declare each message's parameter types

The declaration syntax is:


```fluent
# @param {str} $name - User name shown in the greeting.
my-app-account-greeting = Welcome, { $name }.
```


The description is optional but useful to translators. The current accepted
types are:

| Type | Accepted value |
|---|---|
| `str` | A Python string |
| `int` | An exact Python integer |
| `Decimal` | A finite `decimal.Decimal` |
| `datetime` | An aware Python `datetime` where the operation requires an instant |
| `Slot` | An application-owned rich-message fill |

The type belongs to one message. Two unrelated messages may both use `$name`
with different types. Within one message, its value and attributes share one
parameter namespace.

Citry parses the type name from the comment. It does not inspect imports,
evaluate Python, or accept an arbitrary dotted import path.

The defining source writes `@param` declarations. Translations inherit the
interface and must not redeclare it. One exact source-locale override may
repeat the same parameter names and types. This narrow case lets a library
generate its standalone source catalog from co-located component `messages`
blocks; changing a name or type in that repeat is still an error.

With a configured `citry.app`, the editor uses these declarations as the
message-call interface. Hover an argument name in template or Python `tr()`,
browser `$i18n.tr()`, injected component JavaScript `i18n.tr()`, or a literal
`<c-trans>` value or fill to see its type and description. Go to definition
opens the exact `@param` line, even when the message belongs to another
component, file, or catalog package.

A simple server-only scalar without a declaration produces the
`citry.i18n.missing-param-type` warning by default. A concrete type is required
when a selector, rich Slot, browser operation, or formatter needs it to prove
the call is safe.

## Use selectors for grammar

Let the translation choose language-specific forms:


```fluent
# @param {int} $count - Number of unread messages.
my-app-inbox-count = { $count ->
    [one] One unread message
   *[other] { $count } unread messages
}
```


The source and each translation may use the selector shape appropriate for its
language. Translators do not need to copy English branches that their locale
does not use.

## Reuse private terms inside one source unit

Fluent terms start with `-`:


```fluent
-product-name = Citry

my-app-welcome = Welcome to { -product-name }.
my-app-about = About { -product-name }
```


Citry keeps terms private to the component block or `.ftl` source file that
defines them. Another component may define its own `-product-name` without a
conflict. Cross-file reuse needs a public, namespaced message ID.

## Reference another public message

A public message may include another public message:


```fluent
my-app-product-name = Citry
my-app-page-title = { my-app-product-name } account
```


Citry follows these references when it checks argument types, fallback, and
browser message loading. A message required by another message travels with
it; callers do not need to load the dependency separately.

## Name messages for ownership, not English text

Use stable names with an application or package prefix and a feature or
component prefix:


```text
my-app-account-card-greeting
my-app-account-card-actions
my-app-checkout-payment-error
```


This makes a definition traceable and reduces collisions across components and
packages. Do not generate an ID from the English sentence. The ID is part of
the catalog's public contract and should stay stable when the wording changes.
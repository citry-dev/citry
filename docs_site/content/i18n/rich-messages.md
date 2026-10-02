---
title: Rich messages
description: Let translators position application-owned links and inline components without accepting translated HTML.
---

# Rich messages

Some sentences contain a link, an icon, emphasis, or a small component,
such as "Ada accepts the **terms of service**." Each language may need
that link at a different place in the sentence, so you cannot split the
sentence into a text part and a link part.

`<c-trans>` solves this. The message marks where the link goes, and the
template supplies the link itself. Translators move the marker; they
never write HTML, attributes, URLs, or component names.

## Add a slot variable

Add a variable where the content belongs and declare its type as
`Slot`:

```fluent
# @param {str} $account_name - User accepting the terms.
# @param {Slot} $terms_link - Link to the terms page.
my-app-terms-acceptance =
    { $account_name } accepts the { $terms_link }.
```

A `Slot` variable is filled with content from the template, not with
text.

## Fill the message

Pass ordinary values in `c-values`, and each `Slot` as a `<c-fill>` with
the variable's name:

```citry-html
<c-trans
  message="my-app-terms-acceptance"
  c-values="{'account_name': account.name}"
>
  <c-fill name="terms_link">
    <a href="/terms">{{ tr("my-app-terms-name") }}</a>
  </c-fill>
</c-trans>
```

`message` is the message ID. `c-values` holds every variable that is not
a `Slot`; the `c-` prefix makes Citry evaluate it as Python. A name may appear in `values` or as a fill, not both.

Citry reports a missing, unknown, or wrongly typed value or fill. It
checks fixed calls like this one before rendering, and checks values
built at runtime when it renders.

## Move or repeat content

A translation may put the slot anywhere, and may use it more than once:

```fluent
# @param {Slot} $terms_link - Link to the terms page.
my-app-read-terms =
    Read { $terms_link }, then review { $terms_link } again.
```

Citry renders the fill once for each place it appears. If the two places
need different content or behavior, declare two `Slot` variables
instead.

## Text stays escaped

Citry escapes all text that comes from the message:

```fluent
# @param {Slot} $link - Application-owned link.
my-app-safe-message = <unsafe> { $link } & text
```

`<unsafe>` appears on the page as text. Only the content of the fill is
rendered as HTML. A translation therefore cannot add an event handler, an
unsafe URL, an attribute, or a component.

## Less common cases

### Use `tr()` for text

`<c-trans>` is only for messages with `Slot` variables. For a message
that is text only, call `tr()`.

### Where a slot may go

A `Slot` must appear on its own as `{ $terms_link }`. It cannot be the
value a selector chooses on, a formatting function's argument, or part
of a larger expression. Every branch of a selector must use each `Slot`
at least once.

### No browser switching

`<c-trans>` renders on the server. `$i18n.switchLocale()` in the browser
does not change it. Render the page or that part of it again to show
another language.

### Translate all locales

`<c-trans>` adds no element around the message. It wraps each fill in
`<bdi dir="auto">` so the fill's text direction does not affect the
sentence around it. Because there is no wrapping element, fallback text
from another locale could not be marked with its own `lang`.

So `citry check` reports an error
(`citry.i18n.cross-language-fallback`) when a rich message would fall
back to another locale. Add a translation for each selectable locale
that renders it.

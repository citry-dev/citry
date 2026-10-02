---
title: Markup in attributes
description: Pass a small rendered block through a c-* attribute and make the boundary between markup and Python explicit.
---

# Markup in attributes

Sometimes a component takes a piece of HTML as an input, such as a card's
footer. Instead of building that HTML in Python, you can write it as markup
right in the `c-*` attribute. Wrap it in `<>` and `</>`:

```citry-html
<c-Card
  c-footer="<>
    <footer>
      <a c-href='archive_url'>Read the archive</a>
    </footer>
  </>"
/>
```

`<>` and `</>`, called fragment markers, mark the value as markup rather than
Python. Citry renders the
markup and passes the result to `Card` as its `footer` input.

Inside the markup, quote attribute values with the quote character the
outer value does not use. Here the outer value uses double quotes, so the
link uses single quotes: `c-href='archive_url'`. A double quote inside would
end the outer value early, and Citry has no way to escape it.

## Pick attribute or slot

For content that the caller provides, a slot is usually clearer: write the
content between the component's tags, or in a
[`<c-fill>`](/reference/builtins/#c-fill). Use markup in an attribute when the
component treats that content as one of its inputs. See
[Slots](/concepts/slots/).

## Use the caller's data

The markup can use expressions and component tags, like the rest of the
template. Its names come from the template you write it in, not from the
component that receives it:

```citry-html
<c-Card
  c-footer="<>
    <p>Prepared for {{ user.name }}</p>
    <c-HelpLink c-topic='help_topic' />
  </>"
/>
```

Here `user` and `help_topic` come from the component whose template contains
`<c-Card>`, not from `Card`.

## Render the markup

The receiving component gets a [`CitryRender`][citry.CitryRender], not a
plain string. Insert it with `{{ ... }}`. That keeps the markup unescaped and
keeps any JS or CSS the markup needs:

```citry
from citry import CitryRender, Component


class Card(Component):
    class Kwargs:
        footer: CitryRender

    template = """
      <article>
        <c-slot />
        <footer>{{ footer }}</footer>
      </article>
    """
```

The input is not a slot. The component decides where, and whether, to
render it.

## Skip the `<>` markers { #when-the-fragment-markers-are-optional }

Citry also reads a value as markup without `<>...</>` when the value, with
surrounding spaces removed:

1. starts with `<` followed directly by an ASCII letter, and
2. ends with a complete tag.

All of these are read as markup:

```citry-html
<c-Card c-body="<p>One element</p>" />
<c-Card c-body="<p>One</p><p>Two</p>" />
<c-Card c-body="<p>Hello</p> between <strong>tags</strong>" />
<c-Card c-body="<br>" />
<c-Card c-body="<c-Icon />" />
```

The final tag can be a closing tag, a self-closing tag, a `<c-raw>` block, or
a void element such as `<br>`. The markup must still be valid.

A value that starts or ends with plain text is read as Python, and fails:

```citry-html
{# Fails: read as Python #}
<c-Card c-body="Hello <strong>{{ name }}</strong>" />

{# Works #}
<c-Card c-body="<>Hello <strong>{{ name }}</strong></>" />
```

An HTML comment on its own also needs the markers:

```citry-html
<c-Card c-body="<><!-- Keep this comment. --></>" />
```

Use `<>...</>` whenever you write new code. It makes the choice visible and
works for any value.

## Less common rules

- `<>` and `</>` must wrap the whole value, apart from surrounding spaces.
- A value starting with `<` and a space, or with `<<`, also needs the
  markers.
- These attributes always take a Python expression, never markup:
  `c-bind`, `c-if`, `c-elif`, `c-for`, `c-is` on `<c-component>`, `c-name`
  on `<c-slot>` and `<c-fill>`, and `c-required` on `<c-slot>`. To pass
  rendered content there, prepare it in Python.
- That rule covers only those built-in uses. Your own component can have a
  `name` or `required` input that accepts markup.

---
title: Markup in attributes
url: https://citry.dev/v/0.4.6/syntax/nested-templates/
description: "Pass a small rendered block through a c-* attribute and make the boundary between markup and Python explicit."
---
# Markup in attributes

A dynamic `c-*` attribute usually contains a Python expression. It may also
contain a small Citry template:


```citry-html
<c-Card
  c-footer="<>
    <footer>
      <a c-href="archive_url">Read the archive</a>
    </footer>
  </>"
/>
```


The fragment markers `<>` and `</>` tell Citry that `c-footer` contains
markup, not Python. Citry renders that markup using the surrounding template's
data and passes the result to the `Card` component as its `footer` input.

Use a fragment when you write new code. It makes the choice between markup and
Python visible, and it works for one tag, several tags, or plain text.

## The surrounding component renders the value

Markup in an attribute can use the same expressions and component tags as the
template around it:


```citry-html
<c-Card
  c-footer="<>
    <p>Prepared for {{ user.name }}</p>
    <c-HelpLink c-topic="help_topic" />
  </>"
/>
```


Here `user` and `help_topic` belong to the component whose template contains
`<c-Card>`. They do not come from `Card`.

The receiving component gets a [`CitryRender`](/v/0.4.6/reference/rendering/#citry-citryrender), not a plain
string. Inserting it with an expression preserves its markup and any JS or CSS
collected while it rendered:


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


The attribute does not become a slot automatically. The receiving component
decides what the input means and where to render it.

For ordinary caller-provided content, a component body and
[`<c-fill>`](/v/0.4.6/reference/builtins/#c-fill) are usually clearer. Use markup in an
attribute when the component deliberately models that piece of content as an
input.

## When the fragment markers are optional

Citry also recognizes markup without `<>...</>` when the trimmed value:

1. begins with `<` followed immediately by an ASCII letter, and
2. ends at a complete tag boundary.

These all take the markup path:


```citry-html
<c-Card c-body="<p>One element</p>" />
<c-Card c-body="<p>One</p><p>Two</p>" />
<c-Card c-body="<p>Hello</p> between <strong>tags</strong>" />
<c-Card c-body="<br>" />
<c-Card c-body="<c-Icon />" />
```


A closing tag, self-closing tag, `<c-raw>` block, or unclosed-form HTML void
element such as `<br>` can provide the final boundary. The markup still has to
be structurally valid when Citry parses it.

Leading or trailing plain text does not meet this rule:


```citry-html
<c-Card c-body="Hello <strong>{{ name }}</strong>" />
```


Citry tries to read that value as Python, which fails. A fragment fixes it:


```citry-html
<c-Card c-body="<>Hello <strong>{{ name }}</strong></>" />
```


The fragment must wrap the entire non-whitespace value. A space after the
opening `<`, a doubled `<<`, or a standalone HTML comment also needs a
fragment.

For example, a standalone comment without a fragment takes the Python path and
fails to parse:


```citry-html
<c-Card c-body="<!-- Keep this comment. -->" />
```


Wrap it to make the markup boundary explicit:


```citry-html
<c-Card c-body="<><!-- Keep this comment. --></>" />
```


## Some attributes always expect an expression

The following syntax has a fixed structural meaning and never accepts a nested
template value:

- `c-bind`, `c-if`, `c-elif`, and `c-for`
- the dynamic `c-is` input on a built-in dynamic component
- dynamic `c-name` on `<c-slot>` and `<c-fill>`
- dynamic `c-required` on `<c-slot>`

Pass Python to those attributes. If the Python expression needs to produce
rendered content, prepare that value in the component instead.

These restrictions belong to the built-in syntax, not to the normalized input
name alone. A user component may still define an ordinary `c-name` or
`c-required` input that accepts markup.

Read [Attributes](/v/0.4.6/syntax/dynamic-attributes/) for expression-valued inputs and
[Slots](/v/0.4.6/concepts/slots/) for the usual way to pass flexible content into a
component.
---
title: Nested templates in attributes
url: https://citry.dev/v/0.3.1/syntax/nested-templates/
description: "How a c-* attribute can hold a nested template instead of an expression, and how citry decides which one you meant."
---
# Nested templates in attributes

A `c-*` attribute usually holds an expression: citry evaluates the value as
Python and uses the result, as shown in
[Dynamic attributes](/v/0.3.1/syntax/dynamic-attributes/). But sometimes you want to
pass a chunk of markup instead of a computed value. For that, a `c-*` attribute
can hold a nested template: a small piece of HTML that citry renders and passes
along.


```html
<c-Card
  title="My Card"
  c-footer="
    <footer>
      <p>Made with care</p>
    </footer>
  "
/>
```


Here `c-footer` does not evaluate as an expression. Its value is markup, so
citry treats it as a nested template, renders it against the surrounding
component's data, and hands the result to the `<c-Card>` tag. Whitespace around
the tag is fine.

## Wrapping several roots or plain text

A single root tag works on its own, as above. When you want to pass plain text,
or a leading or trailing piece that is not a tag, wrap the value in a fragment,
`<>...</>`. The `<>` and `</>` delimiters are stripped before the inside is
parsed.


```html
<c-Card
  c-body="<>
    <p>First paragraph</p>
    <p>Second paragraph</p>
  </>"
  c-footer="<>Just some text</>"
/>
```


A nested template can contain expressions and other component tags, just like a
normal template. It runs against the same data as the component it sits on.


```html
<c-my-tag c-body="<>Hello {{ name }}</>" />
```



```html
<c-my-tag c-body="<c-icon />" />
```


## How citry decides: expression or template

citry looks at the trimmed attribute value and treats it as a nested template
only when one of these is true:

- It is a fragment: it starts with `<>` and ends with `</>`.
- It starts with `<` immediately followed by an ASCII letter, and it ends with
  either `/>` (a self-closing tag) or a matching `</tag>`.

Anything else is treated as an ordinary expression. The check is strict, and a
few natural-looking values fall through to expression handling:

- Leading or trailing text outside the tag: `hello <span>A</span>` or
  `<span>A</span> world`.
- A space right after the opening `<`: `< THIS IS TEXT >`.
- A doubled `<<`.

These are then parsed as Python, and usually fail because they are not valid
Python. If you meant markup, wrap it in `<>...</>` to force the template path.

## HTML comments inside a value

An HTML comment starts with `<!`, not `<` plus a letter, so a value like
`<!-- x -->` on its own is not recognized as a template. citry treats it as an
expression, and `<!-- x -->` is not valid Python, so it is a parse error. To
include an HTML comment, put it inside a real nested template:


```html
<c-Card c-body="<div><!-- keep me --></div>" />
```


Inside a nested template, a `#` is plain text, not a Python comment. See
[Comments](/v/0.3.1/syntax/comments/) for where each comment kind applies.

## Good to know

- The nested template renders against the data of the component it is written
  on (the parent), not the component receiving the attribute.
- citry does not require a nested template to have a single root tag; several
  root tags parse without error. Use a fragment when you need plain text or a
  non-tag piece at the start or end, and prefer a single root or a fragment for
  clarity.
- The template is compiled the first time it renders and reused after that, so
  repeated renders do not re-parse the markup.

Attribute names like `c-body` and `c-footer` above are ordinary `c-*`
attributes; nothing about the names is special. What makes them nested
templates is that their values are markup. Whether the receiving component
treats them as slots or as plain props is up to that component's API; see
[Components](/v/0.3.1/concepts/components/) and [Slots](/v/0.3.1/concepts/slots/).
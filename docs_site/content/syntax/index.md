---
title: Template basics
description: Learn which parts of a Citry template are HTML, which parts run as Python, and where to find each piece of special syntax.
---

# Template basics

A Citry template turns component data into the page people see. You can insert
names and calculated values, show or hide content, repeat an element for every
item in a collection, set HTML attributes from data, and build a page from
smaller components.

Citry keeps those jobs close to ordinary HTML. `{{ ... }}` inserts a Python
value, `c-*` attributes let Python decide how an element renders, and `<c-*>`
tags place components and built-in behavior in the page.

```citry-html
<!-- heading = "Reading list"
     books = ["Dune", "Kindred"] -->
<section c-class="['shelf', {'has-books': books}]">
  <h1>
    {{ heading }}
  </h1>
  <p c-for="book in books">
    {{ book }}
  </p>
  <p c-empty>
    No books yet.
  </p>
</section>
```

Citry evaluates the Python expressions before the HTML reaches the browser.
This example inserts the heading, adds the `has-books` class, and creates one
paragraph for every book.

When part of the page should respond immediately to a click, keystroke, or
other browser action, use [Alpine](https://alpinejs.dev/){: target="_blank" rel="noopener"}
in the component's HTML. Its `x-data`, `x-show`, and `@click` attributes run after the page loads, without asking
Python to render the page again. Start with
[Alpine in templates](/syntax/alpine/).

## The syntax at a glance

Core features:

- `{{ expression }}`: insert a
  [Python value](/syntax/expressions/)
- `c-title="heading"`: set a Python value as
  [attribute or component input](/syntax/dynamic-attributes/)
- `c-if`, `c-for`: [conditions and loops](/syntax/control-flow/)
- `x-*`, `@event`, `:name`: [Alpine behavior](/syntax/alpine/)
- `<c-Card>`, `<c-slot>`:
  [components](/concepts/components/) and
  [built-in tags](/reference/builtins/)
- `{# ... #}`, `<c-raw>`:
  [comments or literal text](/syntax/comments/)
- `c-body="<>...</>"`:
  [markup through an attribute](/syntax/nested-templates/)

Citry also has attributes for browser and server interaction:

- `$c-props`, `@c-*`, and `:c-*` are covered in
[Client interactivity](/concepts/client-interactivity/) and [Events](/events/)
- `#c-key` and `#c-ignore` guide how an event response
updates existing HTML. See [Event actions](/events/actions/).

## Self-closing tags

Opening and closing tags must match. Standard void elements such as `<input>`
and `<br>` do not need closing tags. Other tags may use the compact
self-closing form too:

```citry-html
<input name="query">
<span />
<c-StatusBadge />
```

When rendered, `<span />` becomes `<span></span>`.

## Expressions

The `{{ ... }}` Python expressions are allowed only
outside of tags:

```citry-html
{# ✅ Valid #}
<p title="Some title">
  {{ content }}
</p>

{# ❌ Invalid #}
<p title="{{ content }}">
</p>

{# ❌ Invalid #}
<p title="Some title" {{ content }}>
</p>

{# ❌ Invalid #}
<{{ tag }} title="Some title">
</{{ tag }}>
```

## Python attributes

To use Python in HTML attributes, prefix the name with `c-`:

```citry-html
{# Static title #}
<p title="My Title">

{# Dynamic title #}
<p c-title="heading.upper()">
```

Static HTML attributes are literal strings.

Citry strips the `c-` prefix from the dynamic attributes, so:

```citry-html
<p c-title="heading.upper()">
```

becomes:

```citry-html
<p title="MY TITLE">
```

!!! note

    Attribute values may use double quotes, single quotes, or HTML's unquoted
    form. We recomment to **always** quote dynamic `c-*` expressions so spaces and operators stay inside the
    value.

## Boolean attributes

A value-less HTML attribute is a bare boolean attribute. On a component tag,
the same spelling passes the Python value `True`:

```citry-html
<input required>
<c-Button compact />
```

## Other

HTML comments, declarations such as `<!doctype html>`, and processing
instructions remain part of the output. Citry does not use Django or Jinja
block syntax, so text such as `{% include "menu.html" %}` stays literal too.

## Choose the next page

Start with [Expressions](/syntax/expressions/) if you want to insert or compute
a value. Continue to [Attributes](/syntax/dynamic-attributes/) when that value
belongs on an HTML element or needs to become a Python input to a component.

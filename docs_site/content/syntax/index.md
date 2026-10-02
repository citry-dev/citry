---
title: Template basics
description: Learn which parts of a Citry template are HTML, which parts run as Python, and where to find each piece of special syntax.
---

# Template basics

A component's template turns its data into the HTML people see. Most of a
template is ordinary HTML. A few additions let Python fill in values, set
attributes, show or repeat content, and place other components.

This page shows those additions in one example, then lists where each one is
explained.

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

Citry runs the Python in this template on the server, before the HTML reaches
the browser. It inserts the heading, adds the `has-books` class, and writes
one paragraph for every book.

## Find the syntax

| You want to | Write | Read |
|---|---|---|
| Insert a Python value as text | `{{ user.name }}` | [Expressions](/syntax/expressions/) |
| Set an attribute or component input from Python | `c-title="heading"` | [Attributes](/syntax/dynamic-attributes/) |
| Show, hide, or repeat content | `c-if`, `c-for` | [Conditions and loops](/syntax/control-flow/) |
| React to clicks and typing in the browser | `@click`, `:title`, `v-*` | [Vue in templates](/syntax/vue/) |
| Pass browser data to a child component | `:status="current"` | [Client interactivity](/concepts/client-interactivity/) |
| Call a Python event handler from the page | `@c-click="save"` | [Events](/events/) |
| Keep a form field in step with server data | `:c-query="refresh"` | [Bind events in templates](/events/bindings/) |
| Place a component or a built-in tag | `<c-Card>`, `<c-slot>` | [Components](/concepts/components/), [Built-in tags](/reference/builtins/) |
| Pass a piece of markup as an input | `c-body="<>...</>"` | [Markup in attributes](/syntax/nested-templates/) |
| Leave a comment | `{# ... #}` | [Comments](/syntax/comments/) |
| Show template-looking text unchanged | `<c-raw>` | [Literal text](/syntax/raw/) |

## Where each part runs

Two kinds of code can appear in a template:

- **Python**, in `{{ ... }}` and `c-*` attributes. It runs on the server each
  time Citry renders the component.
- **JavaScript**, in Vue attributes such as `@click` and `:title`. It runs in
  the browser after the page loads, without asking the server to render again.

Use Python to decide what the page contains. Use Vue when part of the page
should change straight away in response to the user. Start with
[Vue in templates](/syntax/vue/) for that.

## `c-*` attributes { #set-an-attribute }

An ordinary attribute holds fixed text. Put `c-` in front of the name to make
the value a Python expression. Citry evaluates it and removes the `c-`:

```citry-html
<!-- heading = "My title" -->
<p title="Static title">
<p c-title="heading.upper()">
```

The browser receives:

```html
<p title="Static title">
<p title="MY TITLE">
```

`{{ ... }}` does not work inside a tag, so `title="{{ heading }}"` keeps the
braces as literal text. [Attributes](/syntax/dynamic-attributes/) covers
classes, styles, and passing values to components.

## Write valid tags

Opening and closing tags must match; the match ignores case. Void elements
such as `<input>` and `<br>` need no closing tag. Any other tag may close
itself:

```citry-html
<input name="query">
<span />
<c-StatusBadge />
```

`<span />` renders as `<span></span>`.

A value-less attribute on an HTML element stays a bare attribute. On a
component tag, it passes the Python value `True`:

```citry-html
<input required>
<c-Button compact />
```

Attribute values may use double quotes, single quotes, or no quotes. Quote
every `c-*` expression, so spaces and operators stay inside the value.

## Use lowercase `c-`

Citry syntax always starts with a lowercase `c-`. The component name after it
ignores case, so `<c-StatusBadge>` and `<c-statusbadge>` find the same
component.

Built-in tags such as `<c-if>`, `<c-for>`, and `<c-slot>` must be written
in lowercase. `<c-If>` is an error.

## Pass text through

HTML comments, `<!doctype html>`, and processing instructions pass through to
the output unchanged.

Citry has no Django or Jinja block tags. Text such as
`{% include "menu.html" %}` stays in the page as written.

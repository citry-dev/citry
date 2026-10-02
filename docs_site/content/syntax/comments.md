---
title: Comments and literal text
description: Choose whether a comment reaches the browser, and use c-raw when template-looking text must pass through unchanged.
---

# Comments and literal text

Citry has two template comment forms. Use an HTML comment when it should reach
the browser, or a Citry comment when it should stay in the source file.

Use `<c-raw>` for a different job: keeping a whole block of
template-looking text unchanged.

## Keep a comment in the HTML

A normal HTML comment remains in the rendered output:

```citry-html
<!-- The browser receives this comment. -->
<p>Account details</p>
```

This is useful for a note meant for someone inspecting the page source.

An HTML comment counts as rendered content. For example, it cannot sit between
an `if` branch and its `else` branch, because those branches must be adjacent.

## Keep a comment only in the template

A Citry template comment starts with `{#` and ends with `#}`. Citry removes it
before rendering:

```citry-html
{# Replace this copy after the beta. #}
<p>Account details</p>
```

You can put one in ordinary template text or between attributes:

```citry-html
<button
  class="button"
  {# Native behavior, even if browser JavaScript fails. #}
  type="submit"
>
  Save
</button>
```

Inside a control-flow branch, a template comment is safe. It is also safe
between adjacent control-flow branches: the non-rendering comment and its
surrounding formatting whitespace do not break the branch chain. See
[Conditions and loops](/syntax/control-flow/#wrap-several-elements-in-a-condition)
for the exact rule.

Inside `{{ ... }}`, `{# ... #}` is not a comment and causes a parse error.
Inside a quoted static attribute, it is literal text:

```citry-html
<p title="{# This text stays in the title. #}">Details</p>
```

## Comment inside a Python expression

Within `{{ ... }}` or an expression-valued dynamic `c-*` attribute, `#` starts
an ordinary Python comment:

```citry-html
<div c-class="get_classes()  # build the class list">
  {{ user.name  # show the person's name }}
</div>
```

The comment ends at the end of the line, as it does in Python, or earlier
at the end of the expression: the closing `}}` or the attribute's closing
quote. A `#` inside a Python string remains part of the string.

Outside a Python expression, `#` is ordinary text. That includes plain
template text, static attribute values, and markup passed through a nested
template attribute.

## Pass template-looking text through unchanged

Wrap text in `<c-raw>` when Citry must not interpret expressions, component
tags, or comments inside it:

```citry-html
--8<-- "docs_site/snippets/builtin_raw.html"
```

Citry removes the `<c-raw>` wrapper and copies its body to the rendered output
without interpreting it. In this example, `{{ this_stays_as_text }}` is not
evaluated and `<c-Card>` is not rendered as a Citry component.

A raw block at the top level of a component's template still produces that
component's top-level elements. In output with no browser behavior, Citry
adds the component's `data-cid-<id>` attribute to them, as it does to every
other top-level element of a component.

Raw output is not HTML-escaped. The browser will still interpret any HTML in
the copied body. Use `<c-raw>` only for text written and trusted by the template
author. It is not a safe way to display HTML supplied by a user.

Events binding syntax is safe to show inside the block. Citry turns
`@c-click="save"` and `:c-query` into server event bindings only on elements
written in the template itself, so inside `<c-raw>` they stay ordinary
attribute text.

`<c-raw>` has a deliberately small syntax:

- It takes no attributes.
- It needs both opening and closing tags and cannot self-close.
- Raw blocks cannot nest. The first closing tag ends the block.

### Keep raw HTML complete on interactive pages

When anything on the page or fragment has browser behavior, such as Vue
directives or `$component`, the body of `<c-raw>` must be a complete piece of HTML. Vue
takes over that part of the page, so Citry has to know where the raw HTML
starts and ends. Otherwise the render fails with an error that names the
block's line and column and explains the rule, such as "The <c-raw>
block at line 2, column 10 is not a complete HTML fragment":

```citry-html
--8<-- "docs_site/snippets/builtin_raw_complete.html"
```

Void elements such as `<br>` and `<img>` need no closing tag. Output with
no browser behavior anywhere copies the raw body unchanged, as described
above.

To pass an HTML comment through a component input, see
[Markup in attributes](/syntax/nested-templates/#when-the-fragment-markers-are-optional).

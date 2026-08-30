---
title: Comments and literal text
url: https://citry.dev/v/0.4.6/syntax/comments/
description: "Choose whether a comment reaches the browser, and use c-raw when template-looking text must pass through unchanged."
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
[Conditions and loops](/v/0.4.6/syntax/control-flow/#wrap-several-elements-in-a-condition)
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


The comment ends at the end of the line, just as it does in Python. A `#`
inside a Python string remains part of the string.

Outside a Python expression, `#` is ordinary text. That includes plain
template text, static attribute values, and markup passed through a nested
template attribute.

## Pass template-looking text through unchanged

Wrap text in `<c-raw>` when Citry must not interpret expressions, component
tags, or comments inside it:


```citry-html
<c-raw>
  {{ this_stays_as_text }}
  <c-Card>This tag stays as text too.</c-Card>
</c-raw>

```


Citry removes the `<c-raw>` wrapper and copies its body to the rendered output
verbatim. In this example, `{{ this_stays_as_text }}` is not evaluated and
`<c-Card>` is not rendered as a Citry component.

Raw output is not HTML-escaped. The browser will still interpret any HTML in
the copied body. Use `<c-raw>` only for text written and trusted by the template
author. It is not a safe way to display HTML supplied by a user.

Events binding syntax is safe to show inside the block. Citry compiles only
attributes that the template parser identified on real elements, so
`@c-click="save"` and `:c-query` text inside `<c-raw>` remains byte-for-byte
literal.

`<c-raw>` has a deliberately small syntax:

- It takes no attributes.
- It needs both opening and closing tags and cannot self-close.
- Raw blocks cannot nest. The first closing tag ends the block.

To pass an HTML comment through a component input, see
[Markup in attributes](/v/0.4.6/syntax/nested-templates/#when-the-fragment-markers-are-optional).
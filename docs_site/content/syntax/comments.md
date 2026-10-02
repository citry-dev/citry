---
title: Comments and literal text
description: Choose whether a comment reaches the browser, and use c-raw when template-looking text must pass through unchanged.
---

# Comments and literal text

This page covers two jobs. The first is leaving a note in a template, either
for the next person who edits it or for someone reading the page source in
the browser. The second is showing text that looks like template syntax,
such as a code sample with `{{ name }}`, exactly as written.

## Leave a note that stays in the template

A Citry comment starts with `{#` and ends with `#}`. Citry removes it while
rendering, so the browser never receives it:

```citry-html
{# Replace this copy after the beta. #}
<p>Account details</p>
```

It also works between attributes:

```citry-html
<button
  class="button"
  {# Native behavior, even if browser JavaScript fails. #}
  type="submit"
>
  Save
</button>
```

A Citry comment may sit between an `if` branch and its `else` branch, because
it renders nothing. See
[Keep branches next to each other](/syntax/control-flow/#keep-branches-next-to-each-other).

## Leave a note in the page source

An HTML comment passes through to the browser:

```citry-html
<!-- The browser receives this comment. -->
<p>Account details</p>
```

Use it for notes meant for someone reading the page source. Because it is
part of the output, an HTML comment cannot sit between an `if` branch and its
`else` branch.

## Comment inside a Python expression

Inside `{{ ... }}` or a `c-*` attribute, `#` starts a Python comment:

```citry-html
<div c-class="get_classes()  # build the class list">
  {{ user.name  # show the person's name }}
</div>
```

The comment ends at the end of the line, or earlier at the end of the
expression: the closing `}}` or the attribute's closing quote. A `#` inside a
Python string stays part of the string.

## Show template syntax as plain text { #pass-template-looking-text-through-unchanged }

Wrap text in `<c-raw>` when Citry must not read the expressions, component
tags, or comments inside it:

```citry-html
--8<-- "docs_site/snippets/builtin_raw.html"
```

Citry removes the `<c-raw>` tags and copies the content to the output as
written. Here `{{ this_stays_as_text }}` is not evaluated and `<c-Card>` is
not rendered as a component. Event attributes such as `@c-click="save"` and
`:c-query` stay plain text too.

`<c-raw>` takes no attributes and needs a closing tag. It cannot nest: the
first `</c-raw>` ends the block.

!!! warning "`<c-raw>` does not make HTML safe"

    Citry does not escape the content of `<c-raw>`, so the browser still
    reads any HTML in it as HTML. Use it only for text you wrote in the
    template. To show text from a user, insert it with `{{ ... }}`, which
    escapes it.

## Less common comment and raw-text rules

- Inside `{{ ... }}`, `{# ... #}` is not a comment. It is a parse error.
- Inside a plain attribute value, `{# ... #}` and `#` are ordinary text:
  `title="{# note #}"` keeps the text in the title.
- `#` is ordinary text everywhere outside a Python expression, including
  [markup passed in an attribute](/syntax/nested-templates/).
- To pass an HTML comment to a component input, see
  [When you can leave out the fragment markers](/syntax/nested-templates/#when-the-fragment-markers-are-optional).
- When a `<c-raw>` block sits at the top level of a component's template,
  the HTML tags at its top level count as the component's top-level
  elements. On a page without browser behavior, Citry adds the component's
  `data-cid-<id>` attribute to them, as it does to every top-level element.

!!! note "Raw HTML must be complete on pages that use Vue"

    When anything on the page or fragment runs in the browser, such as a Vue
    directive or `$component`, the content of `<c-raw>` must be complete
    HTML. Vue takes over that part of the page and needs to know where the
    raw HTML starts and ends. Otherwise the render fails with an error that
    names the block, such as "The <c-raw> block at line 2, column 10 is not
    a complete HTML fragment":

    ```citry-html
    --8<-- "docs_site/snippets/builtin_raw_complete.html"
    ```

    Void elements such as `<br>` and `<img>` need no closing tag. Pages
    without browser behavior copy the content unchanged.

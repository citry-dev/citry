---
title: Comments and literal text
description: Choose whether a comment reaches the browser, and use c-raw when template-looking text must pass through unchanged.
---

# Comments and literal text

Use this page to leave a note in a template, for the next person who edits
it or for someone reading the page source in the browser. It also shows how to
display text that looks like template syntax, such as a code sample with
`{{ name }}`, exactly as written.

## Citry `{# #}` comments { #write-a-hidden-note }

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
[Keep branches together](/syntax/control-flow/#keep-branches-next-to-each-other).

## HTML `<!-- -->` comments { #write-an-html-comment }

An HTML comment passes through to the browser:

```citry-html
<!-- The browser receives this comment. -->
<p>Account details</p>
```

Use it for notes meant for someone reading the page source. Because it is
part of the output, an HTML comment cannot sit between an `if` branch and its
`else` branch.

## Python `#` comments { #comment-an-expression }

Inside `{{ ... }}` or a `c-*` attribute, `#` starts a Python comment:

```citry-html
<div c-class="get_classes()  # build the class list">
  {{ user.name  # show the person's name }}
</div>
```

The comment ends at the end of the line, or earlier at the end of the
expression: the closing `}}` or the attribute's closing quote. A `#` inside a
Python string stays part of the string.

## `<c-raw>` literal text { #pass-template-looking-text-through-unchanged }

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
first closing tag ends the block.

!!! warning "`<c-raw>` does not make HTML safe"

    Citry does not escape the content of `<c-raw>`, so the browser still
    reads any HTML in it as HTML. Use it only for text you wrote in the
    template. To show text from a user, insert it with `{{ ... }}`, which
    escapes it.

## Keep `<c-raw>` complete { #keep-raw-html-complete }

When any component on the page, or in an HTML fragment you insert into a
page, runs in the browser (it has its own `js`, or uses Vue syntax such as
`@click`), the content of `<c-raw>` must be complete HTML.
Vue takes over that part of the page and needs to know where the raw HTML
starts and ends. Otherwise the render fails with an error that gives the
block's line and column and says it "is not a complete HTML fragment":

```citry-html
--8<-- "docs_site/snippets/builtin_raw_complete.html"
```

Void elements such as `<br>` and `<img>` need no closing tag. On pages
without browser behavior, Citry copies the content unchanged.

## Less common rules

- Inside `{{ ... }}`, `{# ... #}` is not a comment. It is a parse error.
- Inside a plain attribute value, `{# ... #}` and `#` are ordinary text:
  `title="{# note #}"` keeps the text in the title.
- `#` is ordinary text everywhere outside a Python expression, including
  [markup passed in an attribute](/syntax/nested-templates/).
- To pass an HTML comment to a component input, see
  [Skip the `<>` markers](/syntax/nested-templates/#when-the-fragment-markers-are-optional).
- When a `<c-raw>` block sits at the top level of a component's template,
  the HTML tags at its top level count as the component's top-level
  elements, so Citry marks them as belonging to that component.

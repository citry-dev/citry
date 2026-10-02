---
title: Literal text
description: Wrap text in c-raw when text that looks like template syntax must reach the page exactly as written.
---

# Literal text

Sometimes a template must show text that looks like template syntax, such
as a code sample with `{{ name }}` or a `<c-Card>` tag. Citry would
normally evaluate the expression and render the component. Wrap the text
in `<c-raw>` to keep it exactly as written:

```citry-html
--8<-- "docs_site/snippets/builtin_raw.html"
```

Citry removes the `<c-raw>` tags and copies the content to the output as
written. Here `{{ this_stays_as_text }}` is not evaluated and `<c-Card>` is
not rendered as a component. Comments, event attributes such as
`@c-click="save"`, and `:c-query` stay plain text too.

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

## Top-level raw blocks

When a `<c-raw>` block sits at the top level of a component's template,
the HTML tags at its top level count as the component's top-level
elements, so Citry marks them as belonging to that component.

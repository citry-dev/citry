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
not rendered as a component. Comments and event attributes such as
`@c-click="save"` or `:c-query="refresh"` stay plain text too.

`<c-raw>` takes no attributes and needs a closing tag. It cannot nest: the
first closing tag ends the block.

!!! warning "`<c-raw>` does not make HTML safe"

    Citry does not escape the content of `<c-raw>`, so the browser still
    reads any HTML in it as HTML. Use it only for text you wrote in the
    template. To show text from a user, insert it with `{{ ... }}`, which
    escapes it.

## Keep `<c-raw>` complete { #keep-raw-html-complete }

Some components run in the browser: they have their own `js`, or use Vue
syntax such as `@click`. When one of them is on the page, or in an HTML
fragment you insert into a page, the content of `<c-raw>` must be complete
HTML: close every element you open, and write `<` in text as `&lt;`.
Vue needs to know where the raw HTML starts and ends. Otherwise the render
fails with an error that gives the block's line and column and says it "is
not a complete HTML fragment":

```citry-html
--8<-- "docs_site/snippets/builtin_raw_complete.html"
```

Void elements such as `<br>` and `<img>` need no closing tag. On pages
without browser behavior, Citry copies the content unchanged.

## Less common rules

- When a `<c-raw>` block sits at the top level of a component's template,
  the HTML tags at its top level count as the component's top-level
  elements, so Citry marks them as belonging to that component.
- A Vue directive on a component tag fails when that component's template
  has its top-level HTML in `<c-raw>`. See
  [Several root elements](/syntax/vue/#several-root-elements).

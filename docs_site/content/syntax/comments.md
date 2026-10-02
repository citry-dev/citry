---
title: Comments
description: Leave a note in a template, and choose whether the browser receives it.
---

# Comments

Use a comment to leave a note in a template, for the next person who edits
it or for someone reading the page source in the browser. Pick the kind of
comment by who should see it and where it goes:

- A Citry comment, `{# ... #}`, stays in the template. The browser never
  receives it.
- An HTML comment, `<!-- ... -->`, reaches the browser with the page.
- A Python comment, `# ...`, explains one expression inside `{{ ... }}`
  or a `c-*` attribute. The browser never receives it.

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

## Less common rules

- Inside `{{ ... }}`, `{# ... #}` is not a comment. It is a parse error.
- Inside a plain attribute value, `{# ... #}` and `#` are ordinary text:
  `title="{# note #}"` keeps the text in the title.
- `#` is ordinary text everywhere outside a Python expression, including
  [markup passed in an attribute](/syntax/nested-templates/).
- To pass an HTML comment to a component input, see
  [Skip the `<>` markers](/syntax/nested-templates/#when-the-fragment-markers-are-optional).
- Inside `<c-raw>`, comments are ordinary text. See
  [Literal text](/syntax/raw/).

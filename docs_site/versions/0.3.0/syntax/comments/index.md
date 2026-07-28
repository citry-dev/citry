---
title: Comments
url: https://citry.dev/v/0.3.0/syntax/comments/
description: "The three ways to write comments in citry templates, which ones survive to the rendered HTML, and which are stripped."
---
# Comments

Citry gives you three kinds of comments, and the difference between them is
simple: one shows up in the rendered HTML, one is stripped before rendering,
and one lives inside a Python expression. Pick the one that matches what you
want the reader of your page to see.

## HTML comments are kept

A normal HTML comment `<!-- ... -->` is left exactly where you wrote it and
appears verbatim in the final output, just like it would in any HTML file.


```html
<!-- This comment appears in the final HTML -->
<div>Content</div>
```


Reach for this when the comment is meant for someone reading the page source in
their browser.

## Template comments are stripped

A template comment `{# ... #}` is removed before the page is rendered, so it
never reaches the browser. Use it for notes to yourself and your teammates that
should not leak into the output.


```jinja
{# This comment never appears in the rendered HTML #}
<div>Content</div>
```


You can place a template comment in text or between attributes in a tag. It is
not allowed inside `{{ ... }}` (that is a parse error), and inside a quoted
static attribute value it is treated as literal text rather than a comment.

## Expression comments

Inside `{{ ... }}` or a dynamic `c-*` attribute, a `#` is an ordinary Python
comment. It runs to the end of the line and never appears in the output.


```html
<div c-class="get_classes()  # fetch dynamic classes">
  {{ user.name  # display username }}
</div>
```


This is the same `#` you write in regular Python, so it correctly ignores a `#`
that sits inside a string. Expression comments are covered in more depth on the
[Expressions](/v/0.3.0/syntax/expressions/) page.

## Where each form is (and is not) a comment

The three forms only act as comments in the contexts above. Outside those
contexts they are plain text:

- A bare `#` in ordinary text (`# hello`) is literal text, not a comment.
- `{# #}` or `#` inside a quoted static attribute value is literal text.
- A `#` inside a nested template value (for example
  `c-body="<div># this is text</div>"`) is literal text, not a Python comment.

If you want an HTML comment inside a `c-*` attribute, wrap it in a nested
template rather than writing `<!-- -->` as the attribute value on its own:


```html
<c-Card c-body="<div><!-- kept in output --></div>" />
```


## A worked example

The three forms side by side in one component. The HTML comment survives to the
browser, the template comment is stripped, and the expression comment documents
the value without printing anything.


```citry
from citry import Component


class Notice(Component):
    template = """
      <!-- rendered banner, visible in page source -->
      {# internal note: swap copy before launch #}
      <p>{{ message  # the greeting to show }}</p>
    """

    def template_data(self, kwargs, slots):
        return {"message": kwargs["message"]}
```


The rendered output keeps the `<!-- ... -->` line and the `<p>`, and contains no
trace of the `{# ... #}` note or the `# the greeting to show` comment.
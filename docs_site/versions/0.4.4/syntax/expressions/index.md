---
title: Expressions
url: https://citry.dev/v/0.4.4/syntax/expressions/
description: "Insert Python values in a Citry template, prepare names for the template, and understand escaping and sandbox limits."
---
# Expressions

Use `{{ ... }}` to evaluate a Python expression inside a template:


```citry-html
<p>
  Hello, {{ user.name }}
</p>
<p>
  Your total is {{ price * quantity }}.
</p>
```


Citry evaluates both expressions on the server.

[Dynamic attributes](/v/0.4.4/syntax/dynamic-attributes/) use the same expressions,
but without the braces:


```citry-html
<p c-title="user.name">
  Hello, {{ user.name }}
</p>
```


## Placement

The `{{ ... }}` Python expressions are allowed only outside of tags:


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


## Template variables

By default, every field in a component's [`Kwargs`](/v/0.4.4/reference/component/#citry-component-kwargs)
is available by name:


```citry
from citry import Component

class Greeting(Component):
    class Kwargs:
        name: str

    template = "<p>Hello, {{ name }}</p>"
```


Use [`template_data`](/v/0.4.4/reference/component/#citry-component-template-data) when the template needs a
value you first have to prepare in Python.

Here Python counts the items and exposes `count`:


```citry
from citry import Component

class Cart(Component):
    class Kwargs:
        items: list[str]

    def template_data(self, kwargs: Kwargs, slots):
        return {"count": len(kwargs.items)}

    template = "<p>{{ count }} items</p>"
```


Overriding `template_data()` replaces the default mapping. In this example,
`count` is available but `items` is not. Return both when you need both:


```python
return {
    "items": kwargs.items,
    "count": len(kwargs.items),
}
```


Missing variable raises `KeyError`.

!!! note

    If [sandboxing](#sandbox) is disabled, missing variable instead raises `NameError`.

## Python expressions

You can use the familiar expression forms that produce a value:


```citry-html
{{ user.name.upper() }}
{{ items[0] }}
{{ names[1:3] }}
{{ "Member" if user.is_active else "Guest" }}
{{ f"{user.name}: {score}" }}
{{ any_score > 0 and account.is_active }}
```


Literals, calls, attribute access, indexing, slicing, arithmetic,
comparisons, boolean operations, and conditional expressions all work.

An expression must produce a value. Python statements such as `import`,
`return`, `del`, `def`, and an assignment with `=` are not allowed. Async
expressions and `yield` are not supported either.

A Python string may contain `}}`; Citry still finds the real end of the
expression correctly:


```citry-html
<p>{{ "A string containing }} is fine" }}</p>
```


Citry expressions are Python, not Django or Jinja expressions. There are no
template filters, and `|` keeps its Python meaning as the [bitwise OR operator](https://docs.python.org/3/reference/expressions.html#binary-bitwise-operations){: target="_blank" rel="noopener"}.

!!! note

    Comprehensions, lambdas, and assignment expressions with `:=` work too, but
    usually make a template harder to scan. Prepare complicated values in
    `template_data()` instead. A `:=` assignment changes the render context, so a
    name it creates can affect expressions that render later in the same context.

## Python builtins not available

Functions such as `len()`, `range()`, `str()`, and `sum()` are not added to a
template automatically.

This fails with `KeyError: 'len'`:


```citry-html
{{ len(items) }} items
```


Compute the value in `template_data()`, as the `Cart` example above does. You
can deliberately expose a function too:


```python
return {
    "len": len,
    "items": kwargs.items,
}
```


The template can then call `len(items)`, because both names are
available to it.

## Expression results

Expression results follow these rules:

| Type | Result |
|--|--|
| `None` | Empty string |
| Ordinary values | Converted to text and HTML-escaped |
| Composed components <br/> ([`Component()`](/v/0.4.4/reference/component/#citry-component), [`CitryElement`](/v/0.4.4/reference/rendering/#citry-citryelement)) | Behaves as part of template |
| Rendered components <br/> ([`Component().render()`](/v/0.4.4/reference/rendering/#citry-citryelement-render), [`CitryRender`](/v/0.4.4/reference/rendering/#citry-citryrender)) | Behaves as part of template |
| [`Slot`](/v/0.4.4/reference/slots/#citry-slot) | Behaves as part of template |
| [`Markup`](/v/0.4.4/reference/rendering/#citry-markup) or an object with `__html__()` | Inserted as trusted HTML |

Serializing a component turns it into a regular string.
If you then try to insert it into a template, it gets HTML-escaped:


```citry
table = str(
    Table(headers=headers, rows=rows)
)

class Page(Component):
    def template_data(self, kwargs, slots):
        return {"table": table}

    template = "{{ table }}"

page = str(Page())
print(page)
# '&lt;table&gt;...'
```


## Bypass HTML escape

HTML escaping includes quotes, apostrophes, `<`, `>`, and `&`.

[`Markup`](/v/0.4.4/reference/rendering/#citry-markup) and `__html__()` bypass the escaping that
normally protects the page from untrusted content.

`citry.Markup` is exactly
[`markupsafe.Markup`](https://markupsafe.palletsprojects.com/en/stable/escaping/#markupsafe.Markup){: target="_blank" rel="noopener"},
re-exported unchanged. `Markup(value)` trusts the complete value. It does not
sanitize, validate, or escape anything, so use it only when the complete value
is trusted HTML.

Dynamic values must be added through `Markup.format()`, which escapes ordinary
strings. Passing an interpolated string to the constructor trusts the dynamic
part too:


```python
from citry import Markup

user_title = '<img src=x onerror="alert(1)">'

# Wrong: the constructor trusts the interpolated user value.
unsafe_title = Markup(f"<h1>{user_title}</h1>")

# Right: Markup.format() escapes the user value.
safe_title = Markup("<h1>{}</h1>").format(user_title)
```


Citry also trusts the result of an object's `__html__()` method. Return
`Markup` and compose dynamic values through its escaping operations:


```python
from citry import Markup

class MetaTag:
    name: str
    content: str

    def __html__(self) -> Markup:
        return Markup('<meta name="{}" content="{}">').format(
            self.name,
            self.content,
        )
```


To make Ruff's
[`S704`](https://docs.astral.sh/ruff/rules/unsafe-markup-use/){: target="_blank" rel="noopener"}
rule recognize
the Citry import path, add this to your `pyproject.toml`:


```toml
[tool.ruff.lint.flake8-bandit]
extend-markup-names = ["citry.Markup"]
```


This setting extends S704's recognized constructors; enable S704 through your
Ruff lint selection if it is not already enabled.

## Comments in expressions

Inside an expression, `#` starts an ordinary Python comment:


```citry-html
<div c-class="get_classes()  # prepare the class list">
  {{ user.name  # show the person's name }}
</div>
```


The comment ends either at the end of the line, or at the end of the expression region (closing quote or `}}`).
See [Comments and literal text](/v/0.4.4/syntax/comments/).

## Sandbox

All Python expressions run in a security sandbox, whether it's  `{{ ... }}` or `c-` attributes.

The sandbox blocks following:

What | How
--|--
Private attributes `_abc` | Access blocked
Dunder attributes `__abc` | Access blocked
Unsafe functions such as `eval`, `exec`, and `open` | Calling blocked
`str.format()` and `str.format_map()` | Calling blocked (use an f-string instead)

A blocked operation raises [`SecurityError`](/v/0.4.4/reference/rendering/#citry-securityerror).

Read [Security](/v/0.4.4/security/) for the complete sandbox contract and the settings
that control it.
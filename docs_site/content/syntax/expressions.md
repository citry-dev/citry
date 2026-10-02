---
title: Expressions
description: Insert Python values in a Citry template, prepare names for the template, and understand escaping and sandbox limits.
---

# Expressions

Most templates need to show data: a user's name, a total, a list of results.
Write a Python expression inside `{{ ... }}`, and Citry replaces it with the
value when it renders the component on the server:

```citry-html
<p>
  Hello, {{ user.name }}
</p>
<p>
  Your total is {{ price * quantity }}.
</p>
```

This page covers which names a template can use, what Python you can write,
how values turn into HTML, and how to insert HTML you trust.

## Where `{{ }}` works { #where-expressions-go }

`{{ ... }}` works only in the content between tags. To set an attribute from
Python, put `c-` in front of the attribute name and write the expression
without braces (see [Attributes](/syntax/dynamic-attributes/)):

```citry-html
{# ✅ Text content: evaluated #}
<p>{{ content }}</p>

{# ✅ Attribute: use c- and no braces #}
<p c-title="content">Hover me</p>

{# ❌ The title is the literal text "{{ content }}" #}
<p title="{{ content }}"></p>
```

Braces written elsewhere inside a tag also stay as literal text. A tag name
cannot be an expression: `<{{ tag }}>` is a parse error.

## Make values available

Every field of a component's [`Kwargs`][citry.Component.Kwargs] is available
by name:

```citry
from citry import Component

class Greeting(Component):
    class Kwargs:
        name: str

    template = """
      <p>Hello, {{ name }}</p>
    """
```

When the template needs a value you first compute in Python, return it from
[`template_data()`][citry.Component.template_data]:

```citry
from citry import Component

class Cart(Component):
    class Kwargs:
        items: list[str]

    def template_data(self, kwargs: Kwargs, slots):
        return {"count": len(kwargs.items)}

    template = """
      <p>{{ count }} items</p>
    """
```

The returned dictionary replaces the `Kwargs` fields. Here the template can
use `count` but not `items`. Return both when you need both:

```python
return {
    "items": kwargs.items,
    "count": len(kwargs.items),
}
```

A name the template cannot find raises `KeyError`.

## Python in `{{ }}` { #write-expressions }

Any Python expression that produces a value works:

```citry-html
{{ user.name.upper() }}
{{ items[0] }}
{{ names[1:3] }}
{{ "Member" if user.is_active else "Guest" }}
{{ f"{user.name}: {score}" }}
{{ score > 0 and account.is_active }}
```

Statements are rejected: `import`, `return`, `del`, `def`, and assignment with `=`. `await`, async comprehensions, and `yield` are not supported.

These are Python expressions, not Django or Jinja ones. There are no template
filters, and `|` is Python's
[bitwise OR operator](https://docs.python.org/3/reference/expressions.html#binary-bitwise-operations){: target="_blank" rel="noopener"}.

Comprehensions and lambdas work too, but they make a template harder to read.
Compute complicated values in `template_data()` instead.

## Add helper functions

Python builtins such as `len()`, `range()`, `str()`, and `sum()` are not
available in a template. This fails with `KeyError: 'len'`:

```citry-html
{{ len(items) }} items
```

Compute the value in `template_data()`, as the `Cart` example does, or pass
the function itself:

```python
return {
    "len": len,
    "items": kwargs.items,
}
```

To give every template the same helper, add it once to the
`template_globals` of your [`Citry`][citry.Citry] instance. See
[Add render-wide values](/concepts/rendering/#add-values-for-one-whole-render).

## How values render

| Value | What Citry inserts |
|--|--|
| `None` | Nothing |
| Ordinary values | The value as text, HTML-escaped |
| A component, such as `Card(...)` or a [`CitryElement`][citry.CitryElement] | The rendered component |
| A rendered component, such as [`Card(...).render()`][citry.CitryElement.render] or a [`CitryRender`][citry.CitryRender] | The rendered component |
| A [`Slot`][citry.Slot] | The slot's content |
| [`Markup`][citry.Markup] or an object with `__html__()` | The HTML as is, without escaping |

Escaping turns quotes, apostrophes, `<`, `>`, and `&` into HTML entities, so
text from users cannot add tags to the page.

!!! warning "A component turned into a string shows up as escaped text"

    `str(table)` produces an ordinary string. Inserting that string into
    another template escapes it, so the page shows `&lt;table&gt;...` as
    text. Pass the component itself, not its string:

    ```python
    # Escaped: the template receives a plain string
    table = Table(rows=rows)
    return {"table": str(table)}

    # Rendered: the template receives the component
    table = Table(rows=rows)
    return {"table": table}
    ```

## Insert HTML you trust

To insert HTML without escaping, wrap it in [`Markup`][citry.Markup].
`Markup(value)` trusts the whole value. It does not check or clean it.

When the HTML includes data from users, never put that data into the
constructor. Build the HTML with `Markup.format()`, which escapes each
ordinary string you pass to it:

```python
from citry import Markup

user_title = '<img src=x onerror="alert(1)">'

# Wrong: the constructor trusts the user's value.
unsafe_title = Markup(f"<h1>{user_title}</h1>")

# Right: Markup.format() escapes the user's value.
safe_title = Markup("<h1>{}</h1>").format(user_title)
```

Citry also trusts what an object's `__html__()` method returns. Return
`Markup`, and add dynamic values through `format()` the same way:

```python
from citry import Markup

class MetaTag:
    name: str
    content: str

    def __html__(self) -> Markup:
        return Markup(
            '<meta name="{}" content="{}">'
        ).format(self.name, self.content)
```

`citry.Markup` is
[`markupsafe.Markup`](https://markupsafe.palletsprojects.com/en/stable/escaping/#markupsafe.Markup){: target="_blank" rel="noopener"}
itself, so its documentation applies.

!!! tip "Let Ruff flag unsafe `Markup` calls"

    Ruff's
    [`S704`](https://docs.astral.sh/ruff/rules/unsafe-markup-use/){: target="_blank" rel="noopener"}
    rule warns about unsafe `Markup` use. Enable `S704` in your Ruff rule
    selection, then add the Citry import path so the rule recognizes it:

    ```toml
    [tool.ruff.lint.flake8-bandit]
    extend-markup-names = ["citry.Markup"]
    ```

### Keep HTML complete

When any component on the page, or in an HTML fragment you insert into a
page, runs in the browser (it has its own `js`, or uses Vue syntax such as
`@click`), each `Markup` value must be complete HTML:

- close every element it opens;
- do not self-close an element that needs a closing tag, such as `<span/>`;
- write a `<` in text as `&lt;`.

Otherwise the render fails with "A Markup value (trusted HTML from Python)
is not a complete HTML fragment". On pages without browser behavior, Citry
inserts the value unchanged.

## Python `#` comments { #add-a-comment }

Inside `{{ ... }}` or a `c-*` attribute, `#` starts a Python comment:

```citry-html
<div c-class="get_classes()  # prepare the class list">
  {{ user.name  # show the person's name }}
</div>
```

The comment ends at the end of the line or at the end of the expression,
whichever comes first. See [Comments](/syntax/comments/#comment-an-expression).

## Sandbox limits

Every template expression runs in a sandbox that blocks code which could
reach outside the template:

| What | Result |
|--|--|
| Private attributes such as `_name` | Access blocked |
| Dunder attributes such as `__class__` | Access blocked |
| Unsafe functions such as `eval`, `exec`, and `open` | Call blocked |
| `str.format()` and `str.format_map()` | Call blocked; use an f-string |

A blocked operation raises [`SecurityError`][citry.SecurityError]. Read
[Security](/security/) for the full sandbox rules and the settings that
control it.

## Less common rules

- A Python string may contain `}}`. Citry still finds the real end of the
  expression, so `{{ "a }} b" }}` prints `a }} b`.
- An assignment expression with `:=` works, but the name it creates can stay
  visible to expressions that render after it, such as the content of the
  same element. Pick a name that nothing else in the template uses.
- With the sandbox turned off, a missing name raises `NameError` instead of
  `KeyError`.

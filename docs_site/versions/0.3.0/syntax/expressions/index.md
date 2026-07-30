---
title: Expressions
url: https://citry.dev/v/0.3.0/syntax/expressions/
description: "How Citry's {{ }} expression syntax works, which Python is allowed, why builtins like len() are missing, and how expression comments behave."
---
# Expressions

Anywhere in a template you can drop a value into the output with double curly
braces. Whatever is between the braces is a small piece of Python, evaluated
against the data your component exposes, and its result is rendered where you
wrote it.


```html
<p>Hello, {{ user.name }}</p>
```


The same rules apply inside dynamic `c-*` attributes, so once you know how
expressions work here you know how they work there too. See
[Dynamic attributes](/v/0.3.0/syntax/dynamic-attributes/) for the attribute side.

## What you can write

An expression is a single Python expression: something that produces a value.
Attribute access, arithmetic, comparisons, boolean logic, indexing, slicing,
conditional (ternary) expressions, method calls, literals, and f-strings all
work.


```html
<p>{{ user.name }}</p>
<p>{{ price * quantity }}</p>
<p>{{ greeting + ', ' + user.name }}</p>
<p>{{ user.name.upper() }}</p>
<p>{{ 'Member' if user.is_active else 'Guest' }}</p>
<p>{{ items[0] }}</p>
```


These six lines cover the common shapes: attribute access, arithmetic, string
joining, a method call, a conditional expression, and indexing.

More advanced forms work too: list, dict, set, and tuple literals,
comprehensions, lambdas, and the walrus operator (`name := value`). If you need
an inline assignment inside an expression, the walrus operator is the way to do
it.

## What you cannot write

An expression must be a single expression, not a statement. Assignments with
`=`, augmented assignments like `+=`, `del`, `import`, `def`, `class`, and the
`for`, `while`, `if`, `try`, `return`, and `yield` statements are all rejected
when the template compiles. When you reach for one of these, move the logic into
`template_data` (shown below) and pass the finished value into the template.

## Python builtins are not available

This is the surprise most people hit first. Builtin functions like `len()`,
`range()`, `str()`, `int()`, and `sum()` are not available inside expressions.
Names in an expression are looked up in the data your component provides, and
the builtins are not part of that data.

So the natural first attempt fails:


```html
<!-- Renders an error: the name `len` is not available in expressions -->
<p>{{ len(items) }} items</p>
```


You see `KeyError: 'len'`, because `len` is looked up in the render context
(where it does not exist) rather than in Python's builtins.

The fix is to compute the value in plain Python and hand it to the template. A
component's `template_data` method returns the names the template can use, and
it runs as ordinary Python where every builtin is available.


```citry
from citry import Component


class Cart(Component):
    template = """
      <p>{{ count }} items</p>
    """

    def template_data(self, kwargs, slots):
        return {"count": len(kwargs["items"])}
```


Here `template_data` calls `len` itself and exposes the result as `count`. The
template just displays the prepared name.

You can also expose a builtin under a name and call it from the template. If
`template_data` returns `{"max": max}`, then `{{ max(scores) }}` works, because
now `max` really is one of the names in the context.

## How name lookups fail

It helps to know the two ways a name can fail, because the messages differ.

A name that is simply not in the context raises `KeyError`. You can see this
directly with [safe_eval](/v/0.3.0/reference/citry/#citry-citry-2) applied to a bare name:


```python
from citry_core.safe_eval import safe_eval

expr_func = safe_eval("x")
expr_func({})  # raises KeyError: 'x'

expr_func = safe_eval("x")
expr_func({"x": None})  # returns None
```


A present name whose value is `None` resolves fine, as the second call shows. It
is the absence of the name, not a falsy value, that raises.

A name that the sandbox actively blocks fails with `SecurityError` instead. The
sandbox blocks underscore and dunder attribute access (like `obj._secret` or
`__class__`), unsafe builtins such as `eval`, `exec`, and `open` (even when
passed in under a different name), and `str.format` and `str.format_map` (use an
f-string instead). So `KeyError` means "this name is missing" and
`SecurityError` means "this is not allowed", which is a useful distinction when
you are debugging a template.

## Comments in expressions

Inside an expression you can write an ordinary Python `#` comment. Everything
after the `#` to the end of the line is ignored, exactly as in Python.


```html
<div c-class="get_classes()  # fetch dynamic classes">
  {{ user.name  # display username }}
</div>
```


This works in `{{ }}` and in `c-*` expression attributes alike. Note that `#` is
a comment only inside an expression. In plain template text or inside a quoted
static attribute value, `# ...` is just literal text.

For comments that live outside expressions (HTML comments and template
comments), see [Comments](/v/0.3.0/syntax/comments/).
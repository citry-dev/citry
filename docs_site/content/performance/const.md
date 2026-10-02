---
title: Constant values
description: Mark component inputs that never change, so Citry prepares the template parts that use them once and reuses them across renders.
---

# Constant values

Some inputs have the same value in every render, such as a column label
in every table row or a layout setting that is fixed for the whole site.
Citry still evaluates and escapes the template parts that use them on
every render.

Wrap such a value in [`Const`][citry.Const]. Citry then
prepares the template parts that depend only on constant values once,
and reuses them in later renders. Measure a real page first, and mark
only values that repeat.

## Mark a fixed input

Wrap the value where you pass it to the component:

```citry
from citry import Component, Const


class Metric(Component):
    class Kwargs:
        label: str
        value: str

    template = """
      <p>
        <strong>{{ label }}</strong>
        <span>{{ value }}</span>
      </p>
    """


rows = [
    Metric(label=Const("Status"), value="Ready"),
    Metric(label=Const("Status"), value="Waiting"),
]
```

Both rows reuse the prepared `<strong>` content. `value` is an ordinary
input and renders as usual.

Inside the component, `label` is a plain string. Citry removes the
`Const` wrapper before your code and templates see the value.

`Const` is a promise. Citry does not check the value again, so do not
change it afterwards. If you change a marked list or object in place, the
page can show the old output.

## Mark repeated values

Each [`Citry`][citry.Citry] instance keeps the prepared templates for
the 512 most recently used combinations of component and constant
values. [`Citry.clear`][citry.Citry.clear] empties this store.

Mark values that recur across many renders: fixed labels, small layout
choices, and site-wide settings. Do not mark a value that differs on
almost every render, such as `Const(user.id)`. Each new value adds an
entry that is never reused and pushes out useful ones.

## See what runs once

Citry prepares a template part in advance when every value it uses is
constant:

- `{{ expression }}` becomes ready-made escaped text.
- A `<c-if>` chain keeps only the branch that applies.
- A `<c-for>` loop that produces only text is expanded once, up to 1,000
  iterations.
- An attribute expression becomes ready-made attribute text, unless an
  installed extension implements the `on_attrs_resolved` hook to inspect
  or change the final attributes on every render.

Child components and slot content always render again, because they can
create new components or depend on the template that supplied the
content. Constant expressions inside them can still be prepared in
advance.

Keep template expressions free of side effects. Citry may evaluate a
constant expression in a branch that the current render does not show.

## Use template literals

A value written directly on a component tag is the same in every render,
so Citry treats it as constant without `Const`:

```citry-html
<c-Grid columns="3" compact="" />
<c-Grid c-columns="1 + 2" c-breakpoints="[480, 900]" />
```

The same applies to an expression attribute that uses no variables. An
expression attribute whose variables are all constant also passes a
constant result to the child.

Citry marks the result as a whole. In `c-total="add(1, 2)"`, the child's
`total` input is constant when `add` is a constant value too; the
arguments `1` and `2` stay ordinary integers inside the call.

## Mark a default

Wrap a default in `Const` so calls that omit the input get the same
benefit:

```citry
from citry import Component, Const


class Grid(Component):
    class Kwargs:
        columns: int = Const(3)

    template = """
      <div c-style="{'--columns': columns}">
        {{ columns }} columns
      </div>
    """
```

`Grid()` uses the constant default. `Grid(columns=4)` passes an ordinary
value, unless the caller writes `Const(4)`.

## Keep values constant

With the default `template_data()`, every constant input stays constant
in the template, unless the `Kwargs` class converts or copies it. The
`Metric` and `Grid` examples need nothing more.

A custom `template_data()` can return anything, so Citry does not guess.
An output stays constant only when it has the same name as a constant
input and is the exact same object:

```python
def template_data(self, kwargs, slots):
    return {
        "label": kwargs.label,
    }
```

`return kwargs` works the same way. Citry compares the objects with
Python's `is` test, after the `Kwargs` class, the output data class,
and any extension data hooks have run. If one of them converts or
replaces a value, that value loses its mark.

Mark a renamed or computed output yourself, but only when it really is
stable:

```python
def template_data(self, kwargs, slots):
    return {
        "heading": Const(kwargs.label),
        "value": Const(kwargs.value.strip()),
    }
```

## Edge cases

### `True` is not `1`

Values of different types never share a stored entry, even when Python
considers them equal, as it does `True` and `1`.

### Recomputed values

Because Citry uses the `is` test, a recomputed value that Python happens
to reuse, such as a small integer or a short string, counts as the same
object and keeps its mark.

### Skip generators

Preparing the template can use it up and leave
later work with an empty iterator. Pass a list or tuple.

### Custom schemas

Citry keeps `Const` defaults and default factories constant on the
`Kwargs` dataclasses it generates. It does not assume anything about
default factories in schema classes you write yourself, so mark their
results with `Const(...)` in `template_data()` when needed.

### Using marked values

Before Citry receives it, `Const(value)` is a wrapper object that stands
in for the value. An API that needs the real built-in object, or checks
its identity, can reject the wrapper. Use
[`is_const`][citry.is_const] and [`const_value`][citry.const_value] to
unwrap it first:

```python
from citry import Const, const_value, is_const


marked = Const("status")
if is_const(marked):
    plain = const_value(marked)
```

### Nested markers

Citry removes nested markers only when the outer value is marked:
`Const([Const(1)])` reaches the component as `[1]`. It looks inside
built-in lists, tuples, sets, frozensets, and dictionaries, but not
inside your own classes.

An unmarked list keeps its markers, so `[Const(1)]` still contains a
wrapper, and so does a list that component or extension code puts a
marker into. Unwrap it where you use it:

```python
from operator import add

from citry import Const, const_value


items = [Const(1)]
total = add(const_value(items[0]), 2)
```

### Inputs that share data

Citry unwraps markers passed in the same call together, so two inputs
that refer to the same object still do afterwards.

When a marked and an unmarked input share data that Citry must rebuild,
the marked input can get its own cleaned copy. The original stays
unchanged.

### Cyclic data

A marker that contains itself raises `ValueError`. A marked tuple or
frozenset that contains itself can raise it too.

### Unhashable values

A marked value that cannot be hashed, such as an unhashable custom
object, renders normally without the speed-up.

## Related pages

- [Performance overview](/performance/) compares `Const` with the other
  ways to speed up rendering.
- [Pure components](/performance/pure/) reuse a whole component's HTML
  within one page.
- [Cache rendered output](/performance/caching/) reuses whole rendered
  components across requests.
- [Rendering](/concepts/rendering/) explains the full render process.

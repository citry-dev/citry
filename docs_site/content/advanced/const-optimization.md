---
title: Const optimization
description: Mark stable component inputs so Citry can reuse the template work that depends on them.
---

# Const optimization

Use [`Const`][citry.Const] when the same component input appears across many
renders and never changes. Citry can then finish the template work that
depends on that input once and reuse the result.

This is useful for repeated rows with the same label, components with stable
layout choices, and application-wide presentation settings. It is a focused
rendering optimization, not a general cache for component output.

## Mark a stable input

Wrap the value at the point where you pass it to a component:

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

The label is the same for both rows, so Citry can reuse the rendered
`<strong>` content. Each `value` remains ordinary input and renders normally.

`Const` is a promise from your code. Citry does not watch the value for later
changes, so treat the marked value as read-only.

## What Citry can reuse

Citry precomputes a template part when every value needed by that part is
constant:

- `{{ expression }}` becomes reusable escaped text.
- A `<c-if>` chain keeps only its selected branch.
- A `<c-for>` loop that produces only text can be unrolled once, up to 1,000
  iterations.
- Constant attribute expressions become reusable attribute text unless an
  installed extension needs to process the final attributes.

Child component tags and slot or fill content stay live. They may create new
components or depend on the template that supplied the content. Constant
expressions inside those live areas can still be precomputed.

Keep template expressions free of side effects. Citry may evaluate a constant
expression while preparing a branch, even when that branch is not selected in
the current render.

## Let template literals be constant automatically

Values written directly on a component tag cannot vary between renders, so
Citry marks them for you:

```citry-html
<c-Grid columns="3" compact="" />
<c-Grid c-columns="1 + 2" c-breakpoints="[480, 900]" />
```

The same applies to an expression attribute with no variable references. You
only need `Const(...)` for a value passed from Python or forwarded through a
template variable.

## Make a default constant

Mark a typed default when the omitted value should receive the optimization:

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

`Grid()` uses the constant default. `Grid(columns=4)` receives an ordinary
dynamic value unless the caller passes `Const(4)`.

## Know where the marker stops

In templates and ordinary Python operations, a marked value usually behaves
like the value inside it. A few boundaries need care:

- A transformation such as `title.upper()` returns a new, unmarked value.
- A coercing model, including a Pydantic `Kwargs` model, may create a new value
  and remove the marker.
- APIs that require an exact built-in type can reject the proxy. For example,
  `json.dumps()` rejects marked values and `getattr()` rejects a marked
  attribute name. Convert to the required plain value first, or mark the final
  result instead.
- A custom unhashable object that Citry cannot turn into a stable cache key is
  rendered normally.

Do not mark a one-shot generator. Precomputing can consume it, leaving later
work with an exhausted iterator. Use a stable list or tuple instead.

Extensions can also keep attribute processing live by implementing the
`on_attrs_resolved` hook. This preserves the extension's chance to inspect or
change the final attributes.

## Choose values that will repeat

The optimization cache keeps the 512 most recently used combinations on each
[`Citry`][citry.Citry] instance. [`Citry.clear`][citry.Citry.clear] empties it.

Marking `Const(user.id)` when nearly every user has a different ID creates
many entries with little or no reuse. Prefer values such as fixed labels,
small layout choices, and stable configuration that recur across many
renders.

Different types remain different cache inputs. `Const(True)` and `Const(1)`
do not share an entry, even though Python considers those values equal.

## Related pages

- [Cache rendered output](/advanced/caching/) for reusing a complete rendered
  subtree.
- [Rendering](/concepts/rendering/) for the full render and serialization
  process.

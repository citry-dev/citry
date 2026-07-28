---
title: Performance
description: Render the parts of a template that never change once, with Const, and reuse them across renders.
---

# Performance

Most of a template is the same on every render. The wrapper markup, the labels,
the fixed classes: none of it depends on the data that changes from one render
to the next. Citry can render those constant parts once, cache the result, and
on later renders only recompute the parts that actually vary.

You turn this on by promising which inputs stay the same, using
[`Const`][citry.Const].

## Mark an input as constant with `Const`

Wrap a value in `Const(...)` to promise it does not change between renders:

```python
from citry import Const

Card(cols=Const(3))
```

`Const(3)` behaves exactly like `3` everywhere in your template: in arithmetic,
comparisons, attribute access, and string conversion. Citry unwraps it to the
raw value whenever it needs one, so you rarely notice the wrapper is there. It
even keeps the underlying type for type checkers, so `Card(cols=Const(3))`
type-checks against a `cols: int` field.

When an input is marked const, Citry pre-computes every template part that
depends only on constant inputs and stores the result. On the next render with
the same const values, it reuses that result instead of computing it again.

```citry
from citry import Const, Component

class Card(Component):
    template = """
      <p>{{ cols }}</p>
    """

    def template_data(self, kwargs, slots):
        return {"cols": kwargs["cols"]}

# The <p> renders to static text once and is reused on later renders.
Card(cols=Const(3)).render().serialize()  # '<p ...>3</p>'
```

## The per-row loop

The clearest win is a list where each item shares stable parts. Here every row
has the same label markup and only the value changes:

```citry
from citry import Const, Component

class Row(Component):
    template = """
      <tr>
        <td>{{ label }}</td>
        <td>{{ value }}</td>
      </tr>
    """

    def template_data(self, kwargs, slots):
        return {
            "label": kwargs["label"],
            "value": kwargs["value"],
        }

# `label` is the same for every row, so mark it Const.
# `value` varies, so pass it plain.
rows = [Row(label=Const("Name"), value=v) for v in values]
```

The `<td>{{ label }}</td>` part is computed once and reused for every row. Only
`{{ value }}`, which differs per row, is recomputed. Across many rows that saves
the repeated work of rendering the identical label cell.

## What gets pre-computed

When all the inputs a part reads are const, that part is computed ahead of time:

- A `{{ expr }}` whose variables are all const becomes static text.
- A `<c-if>` chain whose conditions are all const is decided ahead of time, and
  only the winning branch is kept.
- A `<c-for>` over a const iterable that unrolls entirely to text is run once and
  baked in (capped at 1000 iterations; past that the loop stays live).
- Const attribute values render to text.

```citry
class Card(Component):
    template = """
      <c-if cond="cols > 2">big</c-if><c-else>small</c-else>
    """

    def template_data(self, kwargs, slots):
        return {"cols": kwargs["cols"]}

Card(cols=Const(3)).render().serialize()  # "big"
Card(cols=Const(1)).render().serialize()  # "small"
```

Some things stay live no matter what: child component tags render a fresh
instance each time, and slot or fill content is re-evaluated per render. Const
expressions inside those live parts still pre-compute where they can.

## Template literals are constant for free

A value written directly in a template cannot change between renders, so Citry
marks it const with no opt-in from you:

```citry
class Page(Component):
    template = """
      <c-Card age="30" />
    """
```

The same applies to boolean attributes (`compact=""` becomes `True`) and to
expression attributes with no variables (`c-age="30"`, `c-items="[1, 2]"`). The
child component pre-computes on those values automatically.

## Constant defaults

To make a default constant, mark it in the typed `Kwargs` class:

```citry
class Card(Component):
    template = """
      <p>{{ cols }}</p>
    """

    class Kwargs:
        cols: int = Const(3)

    def template_data(self, kwargs, slots):
        return {"cols": kwargs.cols}

Card().render()        # uses the const default 3 and pre-computes
Card(cols=5).render()  # the passed value renders normally
```

## When Const does not help (or hurts)

`Const` is a promise you make; Citry trusts it rather than checking it.

- **Do not mark values that change every render.** `Const(user.id)` with a
  different value each time creates a new cache entry per value, so nothing is
  reused. Mark only values that stay the same across many renders.
- **Do not mutate a value after marking it.** If you change the value later, the
  cached output goes stale and the cache key does not update. Treat a marked
  value as read-only.
- **Transformations drop the marker.** `Const("hi")` passed through unchanged
  stays const, but `kwargs["title"].upper()` returns a plain, unmarked value.
  Mark the final form if that is the stable one.
- **Values that render differently are cached separately.** `Const(True)` and
  `Const(1)` render as `"True"` and `"1"`, so they get their own cache entries
  even though they compare equal.

The cache lives on your [`Citry`][citry.Citry] instance and is cleared by
`Citry.clear()`, so there is no global state to reason about across instances.

## Related pages

- [Caching](/advanced/caching/) for caching whole rendered components.
- [Rendering](/concepts/rendering/) for how a render is produced in the first
  place.

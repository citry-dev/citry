---
title: Performance
url: https://citry.dev/v/0.4.3/advanced/performance/
description: "Reuse stable values and pure component bodies when repeated rendering work becomes measurable."
---
# Performance

Citry provides two explicit rendering optimizations for repeated work:

- [`Const`](/v/0.4.3/reference/rendering/#citry-const) marks an individual value that will not change, so
  template work depending only on that value can be prepared once.
- `pure = True` marks an entire component class whose body is deterministic
  and side-effect-free, so equal occurrences within one root render can reuse
  the settled body strings.

Both are promises made by your code. Start without them, measure a real
repeated-render workload, and opt in only where the same work recurs.

## Reuse stable values with `Const`

Use [`Const`](/v/0.4.3/reference/rendering/#citry-const) when the same component input appears across many
renders and never changes. Citry can then finish the template work that
depends on that input once and reuse the result.

This is useful for repeated rows with the same label, components with stable
layout choices, and application-wide presentation settings. It is a focused
rendering optimization, not a general cache for component output.

`Const(...)` describes one value. For a whole component body, see
[Reuse a pure component body](#reuse-a-pure-component-body).

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

## Inspect a marker at an exact-type boundary

Most component code can treat a marked value like the value inside it. When a
library must pass an exact built-in type to another API, use
[`is_const`](/v/0.4.3/reference/rendering/#citry-is-const) to detect the marker and
[`const_value`](/v/0.4.3/reference/rendering/#citry-const-value) to retrieve its value:


```python
from citry import const_value, is_const


if is_const(columns):
    columns = const_value(columns)
```


These helpers are mainly for component and extension authors. Application
templates normally do not need them.

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
[`Citry`](/v/0.4.3/reference/citry/#citry-citry) instance. [`Citry.clear`](/v/0.4.3/reference/citry/#citry-citry-clear) empties it.

Marking `Const(user.id)` when nearly every user has a different ID creates
many entries with little or no reuse. Prefer values such as fixed labels,
small layout choices, and stable configuration that recur across many
renders.

Different types remain different cache inputs. `Const(True)` and `Const(1)`
do not share an entry, even though Python considers those values equal.

## Reuse a pure component body

When a small component appears many times with repeated data, it can opt into
render-local body memoization:


```citry
from citry import Component


class StatusIcon(Component):
    pure = True

    class Kwargs:
        state: str

    template = """
      <span c-class="state">{{ state }}</span>
    """
```


This is a class-level promise: rendering the template body must be a
deterministic, side-effect-free function of its template variables. Citry
still creates each component instance, runs its data and lifecycle hooks, and
gives it a fresh render ID. Within that one root render, a later equal body can
reuse the first body's immutable strings and transparent control-flow shape.
When a body also renders a child or a slot, that live content still renders
again while safe work beside it can be reused. The memo is discarded when the
root render ends.

Do not declare a component pure when its template expressions mutate state,
consume one-shot iterators, read ambient values not present in template data,
or rely on a per-element extension hook running for every occurrence. Body
items that create child components, slot or ownership records, or i18n
capture remain live even when safe sibling items are reused. A subclass must
state `pure = True` again because it can add new behavior.

Purity pays only when equal instances repeat within the same tree. A component
that appears once, or whose inputs are unique every time, should remain on the
ordinary path. Use `Const(...)` when only selected values are stable; use
`pure = True` only when the complete body satisfies the stronger promise.

## Related pages

- [Cache rendered output](/v/0.4.3/advanced/caching/) for reusing a complete rendered
  subtree.
- [Rendering](/v/0.4.3/concepts/rendering/) for the full render and serialization
  process.
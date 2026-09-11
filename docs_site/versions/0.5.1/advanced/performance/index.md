---
title: Performance
url: https://citry.dev/v/0.5.1/advanced/performance/
description: "Reduce component setup or reuse stable template work when repeated rendering becomes measurable."
---
# Performance

Citry provides three explicit rendering optimizations:

- [`simple = True`](/v/0.5.1/reference/component/#citry-component-simple) renders a presentation component
  without its own instance, hooks or browser identity.
- [`Const`](/v/0.5.1/reference/rendering/#citry-const) marks an individual value that will not change, so
  template work depending only on that value can be prepared once.
- `pure = True` marks an entire component class whose body is deterministic
  and side-effect-free, so equal occurrences within one root render can reuse
  the settled body strings.

Start without them, measure a real repeated-render workload, and choose the
contract that fits the component.

## Skip independent setup with simple components

Use `simple = True` for a presentation component that only needs to turn
inputs and optional default content into HTML:


```citry
from citry import Component


class StatusLabel(Component):
    simple = True

    class Kwargs:
        text: str

    template = """
      <span class="status">{{ text }}</span>
    """
```


The surrounding component owns the output. Inputs and data callbacks remain
live on every invocation; equal inputs are not required. Citry rejects
declarations or calls that need an independent instance, including component
hooks, own JS/CSS, named outlets and component-level client bindings.
Use a static `template_data(kwargs, slots)` method if data needs preparation.

The [Simple components](/v/0.5.1/advanced/simple-components/) guide explains the
supported content, inheritance and error rules. This changes the component's
contract, so it is useful only where independent identity and hooks are
unnecessary.

| Choice | What it avoids | What your code promises |
| --- | --- | --- |
| `simple = True` | Independent component setup and ownership records | The component fits the restricted presentation contract |
| `Const(value)` | Repeating template work based only on that value | The marked value will not change |
| `pure = True` | Repeating safe body work for equal data within one root render | The template is deterministic and side-effect-free |

You can combine simple and pure declarations when both contracts apply.
The data callback still runs. Simple bodies with default outlets remain live.

## Reuse stable values with `Const`

Use [`Const`](/v/0.5.1/reference/rendering/#citry-const) when the same component input appears across many
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


The same applies to an expression attribute with no variable references. Citry
also forwards the optimization through a direct expression attribute when all
of that expression's variables are known constant.

Citry evaluates an expression before marking its complete result as the child
input. In `c-total="add(1, 2)"`, the arguments remain ordinary integers. When
every referenced variable, including `add`, is known constant, Citry marks the
evaluated result at the child-input root.

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

## Mark stable output from a custom callback

Citry consumes the markers it adds automatically and an explicit `Const(...)`
at the root of each component input or output. Those values reach component
kwargs, data callbacks, hooks, and template expressions as ordinary Python
values. Citry keeps the optimization metadata separately, so identity checks,
`type()` checks, JSON serialization, path operations, and standard-library
APIs work normally for the values Citry prepares.

The base `template_data` method returns the component kwargs. Citry knows that
this mapping preserves each name and value, so the earlier `Metric` and `Grid`
examples keep their known const inputs without an override.

A custom `template_data` callback can run arbitrary Python, so Citry does not
infer constness from equal values. It does preserve a marked input when the
final output has the same key and is the exact same ordinary object:


```python
def template_data(self, kwargs, slots):
    return {
        "label": kwargs.label,
    }
```


If the caller supplied `label=Const(value)` and the input schema preserves
`value`'s identity, this direct pass-through keeps its promise when the final
output still has that identity. Citry compares after the output schema and data
hooks. The same rule applies to `return kwargs`: each same-key input keeps its
known constness when both schema stages retained the recorded object.

Renamed or replaced outputs are dynamic unless the callback makes a new
promise. Mark them only when the result will stay stable:


```python
def template_data(self, kwargs, slots):
    return {
        "heading": Const(kwargs.label),
        "value": Const(kwargs.value.strip()),
    }
```


Citry uses Python's `is` identity test. Normal singleton and interning behavior
therefore applies: a recomputed immutable value can count as the same object
when Python reuses its identity.

Schemas that validate, coerce, or otherwise transform data do not inherit the
input's optimization by name alone. A same-key field can keep it by retaining
the exact input object; otherwise the final named field needs an explicit
`Const(...)` promise. Citry normalizes marked defaults and factories on its
generated dataclasses, but it does not assume how arbitrary schema-owned
factories behave.

Citry consumes each output marker before a template expression reads its
value.

## Use marker helpers before rendering

[`is_const`](/v/0.5.1/reference/rendering/#citry-is-const) and
[`const_value`](/v/0.5.1/reference/rendering/#citry-const-value) remain useful when your own code handles a
manually marked value before passing it to Citry:


```python
from citry import Const, const_value, is_const


marked = Const("status")
if is_const(marked):
    plain = const_value(marked)
```


The manual marker is a Python proxy until Citry consumes it. Like other proxy
objects, it cannot preserve identity with the wrapped object, and an API that
requires an actual built-in value may reject it. Call `const_value()` before
handing such a value directly to that API.

Citry recursively unwraps a value only when its outermost object is `Const`:
`Const([Const(1)])` reaches component code as `[1]`. This cleanup follows exact
builtin containers. An ordinary container is left alone, so `[Const(1)]` still
contains a marker. Unwrap a manually nested marker at the point where your code
uses it:


```python
from operator import add

from citry import Const, const_value


items = [Const(1)]
total = add(const_value(items[0]), 2)
```


Calling `add(items[0], 2)` would pass the proxy to `add`. This also applies to
a marker inserted into an ordinary container by component or extension code.

Root markers supplied together in one normalization operation are converted
together, preserving aliases between those roots. When marked and unmarked
fields share a graph that must be rebuilt, the marked value can become a
separate cleaned graph; the unmarked original stays unchanged. Citry does not
inspect attributes or contents inside custom objects. Marker cycles encountered
beneath an outer `Const` raise `ValueError`, and a marked graph that requires
rebuilding a cyclic tuple or frozenset may also be rejected. A custom
unhashable object that cannot form a stable cache key renders normally.

Do not mark a one-shot generator. Precomputing can consume it, leaving later
work with an exhausted iterator. Use a stable list or tuple instead.

Extensions can also keep attribute processing live by implementing the
`on_attrs_resolved` hook. This preserves the extension's chance to inspect or
change the final attributes.

## Choose values that will repeat

The optimization cache keeps the 512 most recently used combinations on each
[`Citry`](/v/0.5.1/reference/citry/#citry-citry) instance. [`Citry.clear`](/v/0.5.1/reference/citry/#citry-citry-clear) empties it.

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
still creates each ordinary component instance, runs its data and lifecycle
hooks, and gives it a fresh render ID. A component also declared simple keeps
the simple contract described above. Within one root render, a later equal body can
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

- [Cache rendered output](/v/0.5.1/advanced/caching/) for reusing a complete rendered
  subtree.
- [Rendering](/v/0.5.1/concepts/rendering/) for the full render and serialization
  process.
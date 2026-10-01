---
title: Pure components
description: Reuse a component's rendered body when equal occurrences repeat within one root render.
---

# Pure components

A small component such as a status icon can appear many times on one page
with the same data. Declare [`pure = True`][citry.Component.pure] to let
Citry render the first occurrence and reuse its body for later equal
occurrences in the same render. Start without it, measure a real
repeated-render workload, and opt in only when the component's whole body
can keep the promise described below.

## Declare a pure component

Set the flag on the component class:

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
hooks, and gives it a fresh render ID. A component also declared
[simple](/performance/simple-components/) keeps the simple contract. Within
one root render, a later equal body can reuse the first body's immutable
strings and transparent control-flow shape. When a body also renders a child
or a slot, that live content still renders again while safe work beside it
can be reused. Citry discards the stored bodies when the root render ends.

## Keep impure components on the ordinary path

Do not declare a component pure when its template expressions mutate state,
consume one-shot iterators, read ambient values not present in template data,
or rely on a per-element extension hook running for every occurrence. Body
items that create child components, slot or ownership records, or i18n
capture remain live even when safe sibling items are reused. A subclass must
state `pure = True` again because it can add new behavior.

Purity pays only when equal instances repeat within the same tree. A component
that appears once, or whose inputs are unique every time, should remain on the
ordinary path.

## Choose an optimization

Citry provides three explicit rendering optimizations. Each one avoids
different work and asks your code for a different promise:

| Choice | What it avoids | What your code promises |
| --- | --- | --- |
| [`simple = True`](/performance/simple-components/) | Independent component setup and ownership records | The component fits the restricted presentation contract |
| [`Const(value)`](/performance/const/) | Repeating template work based only on that value | The marked value will not change |
| `pure = True` | Repeating safe body work for equal data within one root render | The template is deterministic and side-effect-free |

Use `Const(...)` when only selected values are stable; use `pure = True` only
when the complete body satisfies the stronger promise. You can combine simple
and pure declarations when both contracts apply. The data callback still
runs, and a simple body with a default outlet stays live.

## Related pages

- [Constant values](/performance/const/) for reusing template work tied to
  individual stable inputs.
- [Simple components](/performance/simple-components/) for skipping
  independent component setup.
- [Cache rendered output](/performance/caching/) for reusing a complete
  rendered subtree across renders.

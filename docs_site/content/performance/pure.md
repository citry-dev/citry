---
title: Pure components
description: Reuse a component's rendered body when equal occurrences repeat within one root render.
---

# Pure components

A small component such as a status icon can appear many times on one page
with the same data. Declare [`pure = True`][citry.Component.pure] to let
Citry render the first occurrence and reuse its body for later occurrences
with the same template data in the same render. Start without it, measure a real
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
hooks, and gives it a fresh render ID. If the component also sets
`simple = True`, the [simple component](/performance/simple-components/)
rules still apply. Within one root render, a later occurrence with the same
template data reuses the HTML Citry already produced for the first one.
Child components and slot content inside the body still render again for
each occurrence. Citry discards the stored HTML when the root render ends.

## When not to declare a component pure

Do not declare a component pure when its template expressions mutate state,
consume one-shot iterators, read ambient values not present in template data,
or rely on a per-element extension hook running for every occurrence. Child
components, slots, and translated text inside the body still render for every
occurrence. A subclass must state `pure = True` again because it can add new
behavior.

Purity pays only when equal instances repeat within the same tree. A component
that appears once, or whose inputs are unique every time, should not declare
it.

## Related pages

- [Performance overview](/performance/) compares `pure = True` with the
  other optimizations.
- [Constant values](/performance/const/) for reusing template work tied to
  individual stable inputs.
- [Simple components](/performance/simple-components/) for skipping
  independent component setup.
- [Cache rendered output](/performance/caching/) for reusing a complete
  rendered subtree across renders.

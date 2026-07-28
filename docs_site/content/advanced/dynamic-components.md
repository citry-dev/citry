---
title: Dynamic components and elements
description: Choose a component or an HTML tag name at render time with c-component c-is and c-element c-is in citry templates.
---

# Dynamic components and elements

Sometimes you do not know until render time which component to show, or which
HTML tag to wrap your content in. Citry gives you two built-in tags for this:
`<c-component>` picks a component, and `<c-element>` picks a plain HTML tag.
Both read their target from a `c-is` attribute, which takes an expression just
like any other [dynamic attribute](/syntax/dynamic-attributes/).

## Pick a component with c-component

Write `<c-component c-is="expr">`. The `expr` is evaluated against your
`template_data`, and its value chooses which component renders in that spot.
Every other attribute is passed to the target as a keyword argument, and the
body (including any fills) becomes the target's slots.

```citry
from citry import Citry, Component

c = Citry()

class Card(Component):
    citry = c
    template = """
        <div class="card">{{ title }}: <c-slot /></div>
    """

    def template_data(self, kwargs, slots):
        return {"title": kwargs.get("title", "untitled")}

class Page(Component):
    citry = c
    template = """
        <c-component c-is="comp" c-title="'Hi'">body</c-component>
    """

    def template_data(self, kwargs, slots):
        # Resolved to a registered component name at render time.
        return {"comp": "card"}

# Page renders roughly:
# <div class="card">Hi: body</div>
```

Because `c-title` is passed straight through, `Card` sees it as a kwarg, and
`body` becomes its default slot. The target's own kwarg and slot validation
still applies, so passing an attribute the target does not expect raises from
the target.

### What c-is accepts

The resolved value of `c-is` on `<c-component>` must be one of two things:

- A **registered component name** as a string, looked up in this component's
  [`citry`][citry.Citry] instance.
- A **component class** (a [`Component`][citry.Component] subclass), used
  directly.

```citry
class Page(Component):
    citry = c
    template = """
        <c-component c-is="comp">body</c-component>
    """

    def template_data(self, kwargs, slots):
        # A Component class works just as well as a name string.
        return {"comp": Card}
```

An already-constructed component instance is not accepted. If you have a
rendered [`CitryElement`][citry.CitryElement] you want to place, print it with
`{{ ... }}` instead, or pass the class and let `<c-component>` construct it. A
falsy or `None` value raises a `TypeError` asking for an `is` value, and an
unregistered name raises [`NotRegistered`][citry.NotRegistered] with a hint to
use `<c-element>` if you meant a plain HTML tag. `<c-component>` never falls
back to rendering an HTML element.

## Pick an HTML tag with c-element

Write `<c-element c-is="expr">`. Here the resolved value is a **tag name
string**, and citry renders a plain HTML element with that name. Every other
attribute becomes an HTML attribute, formatted exactly like a statically
written element: `class` and `style` are normalized, `False` and `None` values
are dropped, and all values are escaped. The body becomes the element's
children.

```citry
class Page(Component):
    citry = c
    template = """
        <c-element c-is="tag" class="x">hello {{ w }}</c-element>
    """

    def template_data(self, kwargs, slots):
        return {"tag": "section", "w": "world"}

# Page renders roughly:
# <section class="x">hello world</section>
```

Any syntactically valid tag name works, including custom elements like
`my-widget` and SVG camelCase names like `clipPath`. The tag name must start
with a letter and contain only letters, digits, hyphens, underscores, or dots.
This is validated because the name lands verbatim in the output, so the check
doubles as an injection guard (attribute values are always escaped).

### Limits of c-element

- **Void elements reject a body.** A void tag (`br`, `img`, and the rest)
  renders compact and self-closing, so giving it a body raises a `ValueError`.
- **Only the default slot is allowed.** `<c-element>` accepts the tag's body
  as its content and nothing more; a named fill raises a `ValueError`.
- **No nested-template attribute values on the dynamic path.** An attribute
  value that is itself a template fragment (for example
  `c-foo="<b>{{ x }}</b>"`) resolves to a [`CitryRender`][citry.CitryRender]
  and raises a `TypeError`. Precompute the value in `template_data` instead, or
  use a static `is="..."` on a plain element.

## The static and dynamic forms

Writing a plain `is` (for example `<c-component is="card">` or
`<c-element is="div">`) is resolved by the citry compiler ahead of time, so it
never touches the runtime machinery described here. The rendered output is the
same. Use the dynamic `c-is` form (or supply `is` through a
[`c-bind` spread](/syntax/dynamic-attributes/)) whenever the target depends on
your data:

```citry
class Page(Component):
    citry = c
    template = """
        <c-component c-bind="{'is': 'card', 'title': 'Spread'}" />
    """
```

The `is` key in the spread selects the target; the remaining keys are passed
through just like written attributes.

## Both tags are transparent wrappers

`<c-component>` and `<c-element>` add no markup of their own beyond the element
they render. [Provide and inject](/concepts/provide-and-inject/) flow straight
through them, so a value provided above a dynamic tag reaches the component it
renders. The names `component` and `element` are reserved on each
[`Citry`][citry.Citry] instance, so you cannot register your own component
under those names.

For choosing markup based on data without swapping the whole tag, see
[Control flow](/syntax/control-flow/); for the attribute syntax `c-is` builds
on, see [Dynamic attributes](/syntax/dynamic-attributes/).

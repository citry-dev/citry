---
title: Dynamic components and elements
url: https://citry.dev/v/0.4.3/advanced/dynamic-components/
description: "Choose a component or an HTML tag at render time with c-component and c-element."
---
# Dynamic components and elements

Sometimes data decides what to show. A dashboard may choose one of several
cards, while an article may choose whether a heading is an `h2` or an `h3`.

Use `<c-component>` to choose a Citry component. Use `<c-element>` to choose a
plain HTML tag. In both cases, `c-is` contains the Python expression that
selects the result.

Their component-name suffix is case-insensitive, so `<c-Component>` and
`<c-Element>` are equivalent spellings. The framework prefix must still be
the exact lowercase `c-`.

## Choose a component

This page chooses a component by its registered name:


```citry
from citry import Component, SlotInput


class Card(Component):
    class Kwargs:
        title: str = "Untitled"

    class Slots:
        default: SlotInput

    template = """
      <article class="card">
        <h2>{{ title }}</h2>
        <c-slot />
      </article>
    """


class Page(Component):
    def template_data(self, kwargs, slots):
        return {"chosen_component": "card"}

    template = """
      <c-component
        c-is="chosen_component"
        c-title="'Hello'"
      >
        This content goes inside the card.
      </c-component>
    """
```


`c-is` selects `Card`. The Python input `c-title` becomes its `title` kwarg,
and the body fills its default slot. The selected component checks its own
[`Kwargs`](/v/0.4.3/reference/component/#citry-component-kwargs) and
[`Slots`](/v/0.4.3/reference/component/#citry-component-slots) declarations as usual.

Browser-side bindings follow the usual component-boundary rules. They do not
become Python kwargs. See
[Client interactivity](/v/0.4.3/concepts/client-interactivity/) for `$c-props`, Alpine
handlers, and Citry event handlers.

### What `c-is` accepts

For `<c-component>`, the expression must produce either:

- a registered component name, such as `"card"`; or
- a [`Component`](/v/0.4.3/reference/component/#citry-component) subclass, such as `Card`.

To pass a class directly, return it from `template_data()`:


```python
def template_data(self, kwargs, slots):
    return {"chosen_component": Card}
```


A component instance is not accepted. Insert an existing
[`CitryElement`](/v/0.4.3/reference/rendering/#citry-citryelement) with `{{ ... }}`, or pass its class and
let `<c-component>` create it. An unknown name raises
[`NotRegistered`](/v/0.4.3/reference/citry/#citry-notregistered). Citry never treats an unknown
component name as an HTML tag.

## Choose an HTML tag

Use `<c-element>` when only the HTML tag changes:


```citry
from citry import Component


class Heading(Component):
    class Kwargs:
        level: int = 2
        text: str

    def template_data(self, kwargs: Kwargs, slots):
        return {
            "tag": f"h{kwargs.level}",
            "text": kwargs.text,
        }

    template = """
      <c-element c-is="tag" class="heading">
        {{ text }}
      </c-element>
    """
```


`Heading(level=3, text="Details")` inserts:


```html
<h3 class="heading">Details</h3>
```


The tag name must start with a letter. The remaining characters may be
letters, digits, hyphens, underscores, or dots. Custom elements such as
`my-widget` and SVG names such as `clipPath` are valid. HTML void-element
identity is ASCII-case-insensitive, so selecting `BR` produces compact
`<BR/>` output and rejects children just like selecting `br`.

`<c-element>` also applies HTML attribute identity to its selector. `IS`,
`c-IS`, and an `Is` key supplied by `c-bind` therefore mean the same thing as
`is` / `c-is`. `<c-component>` inputs remain case-sensitive and use the exact
lowercase selector spellings.

Other attributes use the normal HTML formatting rules. `class` and `style`
are normalized, and `False` and `None` leave an attribute out. Values are
escaped unless they explicitly provide trusted HTML through `__html__()`.
`$c-props` belongs to component boundaries and is not valid on an HTML
element.

### Limits of `c-element`

- Void elements such as `br` and `img` cannot have a body.
- Only the default slot is accepted. A named fill raises `ValueError`.
- A dynamic attribute cannot produce a template fragment. Precompute a plain
  value in `template_data()` instead.

When you already know the tag, write that HTML tag directly. It is clearer
than asking `<c-element>` to select a fixed name.

## Use a fixed or calculated target

Use `is="card"` when the target is written directly in the template. Use
`c-is="chosen_component"` when a Python expression calculates it.

You can also include `is` in a
[`c-bind` mapping](/v/0.4.3/syntax/dynamic-attributes/):


```citry-html
<c-component
  c-bind="{'is': chosen_component, 'title': heading}"
/>
```


`c-bind` is applied in source order with the other attributes. If more than
one value supplies `is`, the rightmost one wins.

Neither built-in adds wrapper HTML. A selected component may have one root,
several roots, text, or no output. Values from
[Provide and inject](/v/0.4.3/concepts/provide-and-inject/) continue through the
selection normally.

For choosing content without changing the whole tag, see
[Control flow](/v/0.4.3/syntax/control-flow/).
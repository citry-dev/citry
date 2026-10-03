---
title: Dynamic components and elements
description: Choose a component or an HTML tag at render time with c-component and c-element.
---

# Dynamic components and elements

Sometimes your data decides what to render. A dashboard picks one of
several card components for each widget. An article picks whether a heading
is an `h2` or an `h3`.

Citry has two built-in tags for this:

- `<c-component>` renders the Citry component you choose;
- `<c-element>` renders the plain HTML tag you choose.

On both, `c-is` holds the Python expression that makes the choice.

## `<c-component>`

Pass a registered component name to `c-is`. Every other attribute becomes
an input of the chosen component, and the body fills its slots:

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

`c-is` chooses `Card`, `c-title` becomes its `title` input, and the body
fills its default slot. `Card` checks its own
[`Kwargs`][citry.Component.Kwargs] and [`Slots`][citry.Component.Slots] as
it would anywhere else.

The expression can also return a [`Component`][citry.Component] class
instead of a name:

```python
def template_data(self, kwargs, slots):
    return {"chosen_component": Card}
```

`<c-component>` adds no wrapper HTML around the result. The chosen
component may render one root element, several, text, or nothing. Values
from [provide and inject](/concepts/provide-and-inject/) reach it as
usual.

## `<c-element>`

Use `<c-element>` when only the tag name changes. Every other attribute
becomes an HTML attribute, and the body becomes the element's content:

```citry
from citry import Component


class Heading(Component):
    class Kwargs:
        text: str
        level: int = 2

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

`Heading(level=3, text="Details")` renders:

```html
<h3 class="heading">Details</h3>
```

Attributes follow the same rules as on a tag you write by hand: `class` and
`style` values are combined into one string, a `False` or `None` value leaves the attribute out,
and values are escaped unless they provide trusted HTML through
`__html__()`.

If the tag never changes, write it directly. `<h2>` is clearer than
`<c-element is="h2">`.

## Compute the choice

Use `is` for a choice written directly in the template, and `c-is` for a
Python expression:

```citry-html
<c-component is="card" />
<c-component c-is="chosen_component" />
```

You can also put `is` in a [`c-bind` mapping](/syntax/attributes/),
together with the other inputs:

```citry-html
<c-component
  c-bind="{'is': chosen_component, 'title': heading}"
/>
```

Citry applies `c-bind` in source order with the other attributes. If more
than one of them sets `is`, the last one wins.

To show or hide content rather than change a whole tag, use
[control flow](/syntax/control-flow/).

## Less common cases

### What `c-is` accepts

The value must be a registered component name, such as `"card"`, or a
`Component` subclass, such as `Card`.

- An unknown name raises [`NotRegistered`][citry.NotRegistered]. Citry
  never treats an unknown component name as an HTML tag; use `<c-element>`
  for that.
- An already created [`CitryElement`][citry.CitryElement], such as
  `Card(title="Hi")`, raises `TypeError`. Insert it with `{{ ... }}`
  instead, or pass its class.

### Vue bindings stay Vue

Vue bindings on `<c-component>` follow the usual rules for a component
tag. They do not become Python inputs. See
[Client interactivity](/concepts/client-interactivity/) for Vue props,
child events, and server-event handlers.

### Valid tag names

A tag name starts with a letter, followed by letters, digits, hyphens,
underscores, or dots. Custom elements such as `my-widget` and SVG names
such as `clipPath` work. Any other value raises `ValueError`.

Void elements are recognized in any letter case, so `BR` renders compact
`<BR/>` and rejects a body, just like `br`.

### Letter case of `is`

`<c-element>` treats its selector like an HTML attribute, so `IS`, `c-IS`,
and an `Is` key in `c-bind` all work. `<c-component>` passes inputs with
their exact names, so there you must write `is` or `c-is` in lowercase.

The tag names themselves ignore letter case after the prefix:
`<c-Component>` and `<c-Element>` work too. The `c-` prefix must be
lowercase.

### `<c-element>` limits

- A void element such as `br` or `img` cannot have a body.
- It accepts only the default slot. A named `<c-fill>` written in the
  template raises `SyntaxError`. A fill whose name is computed at render
  time, such as `<c-fill c-name="...">`, raises `ValueError`.
- An attribute value cannot be a nested template. Compute a plain value in
  `template_data()` instead.
- Vue props belong on component tags, so they are not valid on the HTML
  element.

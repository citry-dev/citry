---
title: HTML attributes
description: Accept an explicit attribute mapping, choose where a component applies it, and merge class and style values safely.
---

# HTML attributes

A page that uses your reusable button often needs to add something to the
`<button>` itself: an `aria-label`, an extra class, or `disabled`. Citry
does not copy unknown inputs onto a component's first element, because a
component can have several root elements, and the attribute could land on
the wrong one.

Instead, the component accepts the attributes as one mapping and decides
which element receives them. This page shows how, and how to combine
`class` and `style` values from several places.

## Accept attributes

Give the component an `attrs` input. In `template_data()`, combine it with
the component's own attributes, then apply the result to the element with
`c-bind`:

```citry
from dataclasses import field
from typing import Any

from citry import Component, merge_attrs


class ActionButton(Component):
    class Kwargs:
        label: str
        attrs: dict[str, Any] = field(default_factory=dict)

    def template_data(
        self,
        kwargs: Kwargs,
        slots,
    ) -> dict[str, object]:
        return {
            "button_attrs": merge_attrs(
                {"class": "action-button", "type": "button"},
                kwargs.attrs,
            ),
            "label": kwargs.label,
        }

    template = """
      <button c-bind="button_attrs">
        {{ label }}
      </button>
    """
```

A page passes the attributes as a Python dictionary:

```citry-html
<c-ActionButton
  label="Save"
  c-attrs="{
    'aria-label': accessible_name,
    'class': {'action-button--quiet': quiet},
    'disabled': unavailable,
  }"
/>
```

[`c-bind`](/syntax/dynamic-attributes/#c-bind-spread) adds every entry of
the merged mapping to the `<button>`. The rendered button keeps the
`action-button` class and also gets `aria-label`, the quiet class when
`quiet` is true, and `disabled` when `unavailable` is true.

You choose the element. A component with two root elements can accept two
mappings, and a form field can put the attributes on its inner `<input>`
rather than on its wrapper.

## Choose who wins

In the example above, the page's mapping comes last in `merge_attrs()`,
so a page can replace `type` while the component's `action-button` class
stays.

Put the component's mapping last when the page must not change an
attribute:

```python
button_attrs = merge_attrs(
    kwargs.attrs,
    {"class": "action-button", "type": "button"},
)
```

Now a page can add classes, but `type` is always `button`.

## Merge mappings

[`merge_attrs()`][citry.merge_attrs] keeps the last value for each
attribute name. For `class` and `style` it keeps every value and combines
them:

```python
from citry import merge_attrs

attrs = merge_attrs(
    {"class": "button", "id": "old"},
    {"class": {"is-active": True}, "id": "save"},
)

assert attrs == {
    "class": "button is-active",
    "id": "save",
}
```

Each attribute keeps the position where it first appeared, even when a
later mapping replaces its value, so the order in the HTML stays
predictable.

## Build class and style

[`normalize_class()`][citry.normalize_class] turns a string, a mapping,
or a list or tuple of those (nested ones work too) into one class string. In a
mapping, a class with a true value is kept. A later false value removes a
class added earlier:

```python
from citry import normalize_class

classes = normalize_class([
    "button button-large",
    {"is-active": True, "button-large": False},
])

assert classes == "button is-active"
```

[`normalize_style()`][citry.normalize_style] does the same for CSS text,
mappings, and lists of them. A later value replaces an earlier one for the
same property. `None` keeps the earlier value, and `False` removes the
property:

```python
from citry import normalize_style

styles = normalize_style([
    "color: red; width: 10rem",
    {"color": "green", "width": False},
])

assert styles == "color: green;"
```

Any other kind of value, such as an integer, raises `TypeError`.

To read inline CSS as a dictionary, use
[`parse_string_style()`][citry.parse_string_style]. It removes CSS
comments, keeps semicolons inside functions such as `url(...)`, and skips a
declaration without a colon.

## Format as HTML

When you need the attributes as text rather than through `c-bind`,
[`format_attrs()`][citry.format_attrs] turns a mapping into an escaped HTML
attribute string:

```python
from citry import format_attrs

attrs = format_attrs({
    "class": ["button", {"is-active": True}],
    "data-id": 42,
    "disabled": True,
    "hidden": False,
})

assert attrs == (
    'class="button is-active" data-id="42" disabled'
)
```

It follows the same rules as attributes in a template:

- `True` writes the attribute name alone, as in `disabled`;
- `False` and `None` leave the attribute out;
- an empty `class` or `style` is left out;
- names and values are HTML-escaped, except a value with an `__html__()`
  method, which is inserted as trusted HTML.

When Vue renders an interactive component, a `True` value on an attribute
that is not a boolean HTML attribute renders as `data-open="true"` rather
than a bare `data-open`. See [Toggle with `c-*`](/syntax/dynamic-attributes/#html-elements).

## Keep Vue in templates

An attribute mapping carries plain HTML attributes only. Citry never runs
a name from the mapping as Vue code. A name that starts with `v-`, `@`,
`:`, `.`, `^`, or `#`, in any letter case, such as `:title` or `@click`,
is Vue syntax. On a page that uses Vue, such a name on an HTML element
raises `TypeError`, unless its value is `None` or `False`. It fails even
when the template writes the same binding on the element. Write Vue
bindings and event listeners directly on the element in the template,
and remove them from the mapping.

Citry's own `@c-` and `:c-` Events bindings are the exception: a mapping
may set them. See [Bind events in templates](/events/bindings/).

Vue bindings written on a component tag, such as `@click` on
`<c-ActionButton>`, do not reach the component's Python `attrs` input. Vue
passes them to the component as props or listeners, or adds them to its
root element by Vue's usual rules for undeclared attributes.

Read
[Client interactivity](/concepts/client-interactivity/#pass-arbitrary-html-attributes-explicitly)
for the component-boundary rules, and
[Attributes](/syntax/dynamic-attributes/) for static, dynamic, and spread
values in templates.

## Less common cases

### Invalid names

An attribute name must be a string. Any other key raises `TypeError`. A
name that is empty or contains whitespace, `=`, `/`, `>`, `<`, or `{#`
raises `ValueError`. `c-bind` checks names the same way when it adds a
mapping to an element.

### Unescaped values

A value with an `__html__()` method is inserted without escaping. Pass one
only when the code that produced it is trusted and escapes its own
content.

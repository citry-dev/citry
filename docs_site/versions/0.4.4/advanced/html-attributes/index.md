---
title: Forward HTML attributes
url: https://citry.dev/v/0.4.4/advanced/html-attributes/
description: "Accept an explicit attribute mapping, choose where a component applies it, and merge class and style values safely."
---
# Forward HTML attributes

A component does not copy arbitrary inputs onto its first HTML element. That
would be ambiguous for a component with several roots, and it could place an
accessibility or browser attribute on the wrong element.

Give a reusable component an explicit attribute mapping, then choose the
element that receives it.

## Accept and apply an attribute mapping

This button combines its own required attributes with values supplied by the
template using it:


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


Pass the mapping as a Python expression:


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


[`c-bind`](/v/0.4.4/syntax/dynamic-attributes/#c-bind-spread) applies
the final mapping to the `<button>`. The component could apply separate
mappings to separate roots, or place the public attributes on a nested input
instead.

The order in `merge_attrs()` is deliberate. Values supplied by the template
come last, so they may replace `type`. The `class` values combine, preserving
the component's own class. Reverse the two mappings when an attribute must stay
under the component's control:


```python
button_attrs = merge_attrs(
    kwargs.attrs,
    {"class": "action-button", "type": "button"},
)
```


Here the caller can add classes, but cannot change `type`.

## Merge mappings from left to right

[`merge_attrs()`](/v/0.4.4/reference/attributes/#citry-merge-attrs) keeps the last ordinary value for each
name. `class` and `style` are different: every contribution is collected and
normalized.


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


A name keeps the position where it first appeared, even when a later mapping
replaces its value. This makes the resulting attribute order predictable.

## Build class and style values

[`normalize_class()`](/v/0.4.4/reference/attributes/#citry-normalize-class) accepts a string, a mapping, or a
nested list or tuple of those forms. A truthy mapping value keeps its name. A
later falsy value removes a class that appeared earlier:


```python
from citry import normalize_class

classes = normalize_class([
    "button button-large",
    {"is-active": True, "button-large": False},
])

assert classes == "button is-active"
```


[`normalize_style()`](/v/0.4.4/reference/attributes/#citry-normalize-style) accepts CSS text, a mapping, or a
nested sequence of either. Later values replace earlier properties. `None`
leaves an earlier value in place, while `False` removes the property:


```python
from citry import normalize_style

styles = normalize_style([
    "color: red; width: 10rem",
    {"color": "green", "width": False},
])

assert styles == "color: green;"
```


Passing another kind of value, such as an integer, raises `TypeError` from the
matching normalizer.

[`parse_string_style()`](/v/0.4.4/reference/attributes/#citry-parse-string-style) turns inline CSS into a
property mapping. It removes CSS comments, keeps semicolons inside functions
such as `url(...)`, and ignores a declaration without a colon.

## Turn a mapping into HTML

[`format_attrs()`](/v/0.4.4/reference/attributes/#citry-format-attrs) formats a mapping as an escaped HTML
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


The formatting rules are:

- `True` produces a bare attribute;
- `False` and `None` leave the attribute out;
- an empty `class` or `style` is left out;
- names and values are HTML-escaped;
- a value with `__html__()` is treated as trusted HTML.

Attribute names must be strings. A non-string key raises `TypeError`.
An empty name, whitespace, `=`, `/`, `>`, `<`, or the template-comment opener
`{#` in a name raises `ValueError`. The same validation applies when `c-bind`
produces an HTML attribute at render time.

Treat `__html__()` values as an escape hatch. Only pass one when the producing
code is trusted and is responsible for its own escaping.

## Keep browser attributes explicit too

Alpine directives and browser event handlers are ordinary HTML attributes
when a component deliberately spreads them onto an HTML element. They do not
fall through a `<c-Component>` tag automatically.

Read
[Client interactivity](/v/0.4.4/concepts/client-interactivity/#pass-arbitrary-html-attributes-explicitly)
for the component-boundary rules, and
[Attributes](/v/0.4.4/syntax/dynamic-attributes/) for static, dynamic, and spread
values in templates.
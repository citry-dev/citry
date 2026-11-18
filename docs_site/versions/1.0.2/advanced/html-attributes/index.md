---
title: HTML attributes
url: https://citry.dev/v/1.0.2/advanced/html-attributes/
description: "Accept an explicit attribute mapping, choose where a component applies it, and merge class and style values safely."
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


[`c-bind`](/v/1.0.2/syntax/attributes/#c-bind-spread) adds every entry of
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

[`merge_attrs()`](/v/1.0.2/reference/attributes/#citry-merge-attrs) keeps the last value for each
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

[`normalize_class()`](/v/1.0.2/reference/attributes/#citry-normalize-class) turns a string, a mapping,
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


[`normalize_style()`](/v/1.0.2/reference/attributes/#citry-normalize-style) does the same for CSS text,
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
[`parse_string_style()`](/v/1.0.2/reference/attributes/#citry-parse-string-style). It removes CSS
comments, keeps semicolons inside functions such as `url(...)`, and skips a
declaration without a colon.

## Format as HTML

When you need the attributes as text rather than through `c-bind`,
[`format_attrs()`](/v/1.0.2/reference/attributes/#citry-format-attrs) turns a mapping into an escaped HTML
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
- names and values are HTML-escaped, including a
  [`Markup`](/v/1.0.2/reference/rendering/#citry-markup) value.

One rule differs from `c-bind`: `format_attrs()` accepts names such as
`onclick`, `innerHTML`, and `srcdoc`, whose values the browser runs or
reads as markup. It also accepts the names Citry uses to find its own
elements, such as `c-render-id`, `data-cid-*`, and `data-ccss-*`, which
can make Citry copy another component's HTML into the page (see
[Names Citry reserves](#names-citry-reserves)). Choose the names in your
own code, never from request data (a query parameter, form field, or
header).

When Vue renders an interactive component, a `True` value on an attribute
that is not a boolean HTML attribute renders as `data-open="true"` rather
than a bare `data-open`. See [`c-*` boolean attrs](/v/1.0.2/syntax/attributes/#html-elements).

## Keep Vue in templates

An attribute mapping carries plain HTML attributes only. Citry never runs
a name from the mapping as Vue code. A name that starts with `v-`, `@`,
`:`, `.`, `^`, or `#`, in any letter case, such as `:title` or `@click`,
is Vue syntax. Rendering a template that spreads such a name raises
`citry.VueCodeError` on every page, including one without Vue, whatever
the value (even `None`). It fails even when the template writes
the same binding on the element. Write Vue bindings and event listeners
directly on the element in the template, and remove them from the
mapping.

Citry's own `@c-` and `:c-` Events bindings are the exception: a mapping
may set them. See [Bind events in templates](/v/1.0.2/events/bindings/).

Vue bindings written on a component tag, such as `@click` on
`<c-ActionButton>`, do not reach the component's Python `attrs` input. Vue
passes them to the component as props or listeners, or adds them to its
root element by Vue's usual rules for undeclared attributes.

Read
[Pass HTML attributes](/v/1.0.2/vue/props-and-events/#pass-arbitrary-html-attributes-explicitly)
for the component-boundary rules, and
[Attributes](/v/1.0.2/syntax/attributes/) for static, dynamic, and spread
values in templates.

## Add event handlers { #write-handlers-in-the-template }

`c-bind` refuses a name that starts with `on`, such as `onclick`, and the
names `innerHTML`, `outerHTML`, and `srcdoc`, in any letter case. The
browser reads those values as code or markup. Citry raises `ValueError`
for these names, also when an extension's `on_attrs_resolved` hook adds
one. A hook may change the value of a handler the template wrote, but it
cannot add one.

Write the handler in the template instead: `@click`, `@c-click` to call a
handler of your component, or `onclick="..."`. A handler you write in the
template is allowed, because you chose its name.

The exception is a `<c-element>` with `c-is` or `c-bind`. It cannot tell a
name you wrote from one passed in as data, so it refuses both. See
[`<c-element>` limits](/v/1.0.2/advanced/dynamic-components/#c-element-limits).

`c-onclick="handler"` sets the attribute to the value of `handler`, and
that value runs as JavaScript, so choose it in your own code. On a page
that uses Vue, it raises `TypeError` when the page renders, so use
`@click` there. A page uses Vue when one of its components has its own
JavaScript (`js`) or uses a Vue directive such as `@click`; see
[When Vue turns on](/v/1.0.2/vue/#when-vue-turns-on) for the full list.

`c-bind` also refuses `ref`, `ref_for`, and `ref_key`. In a component
with its own JavaScript (`js`), Vue reads these names and stores the
element in the component's own value of that name, which could replace a
value the component shows with `v-html`. Citry raises `ValueError` for
them, also when an extension's `on_attrs_resolved` hook adds one.
`c-ref="..."` raises `ValueError` for the same reason: write `ref="name"`
with a plain text value.

!!! warning "Request data can run as code"

    Citry escapes every attribute value, but it does not check what the
    value means. Some attributes hold code or a page the browser loads,
    such as `href`, `src`, `srcdoc`, and inline handlers. `style` can
    also load a resource: Citry does not check its value as CSS, so a
    `url(...)` in it can load an image from another site. When such a
    value comes from request data, such as a query parameter or a form
    field, choose it in your own code or check it before you use it.

## Less common cases

### Invalid names

An attribute name must be a string. Any other key raises `TypeError`. A
name that is empty, or contains whitespace, a control character, a quote,
`=`, `/`, `>`, `<`, a byte-order mark, a lone surrogate, a Unicode
noncharacter, or `{#`, raises `ValueError`. `c-bind` checks names the
same way when it adds a mapping to an element.

### Names Citry reserves

Citry uses some attribute names to find its own elements and
placeholders in the HTML it renders. If request data could choose one of
these names, it could make Citry copy another component's HTML into the
page. So on an HTML element, `c-bind` raises `ValueError` for a key that
is:

- `c-render-id`, `data-cid`, or `data-citry`
- `data-citry-key`, `data-citry-morph`, `data-citry-i18n`, or
  `data-citry-i18n-binding`
- a name that starts with `data-cid-`, `data-ccss-`, `data-cev-`,
  `data-citry-css-`, `data-citry-omit-handler-`, `data-citry-opaque-`,
  `data-citry-runtime-`, `data-citry-security-`, or `data-citry-vue-`

Letter case does not matter, so `DATA-CID-x` is refused too. Rename the
key to a `data-` name of your own. Other `data-` names work.

A name you write in the template, such as `<div data-cid-x>`, is not
checked, because you chose it. A `<c-element>` with `c-is` or `c-bind`
refuses these names whether you wrote them or passed them in, as it does
with handlers. An `on_attrs_resolved` hook may add these names; Citry's
Events extension adds `data-cev-` names that way.

`data-cev-` names, `data-citry-runtime-control`, and
`data-citry-runtime-events` raise `RuntimeError` instead of
`ValueError`, with a message about Events bindings. When i18n is set up,
`data-citry-i18n-binding` also raises `RuntimeError`, with a message that
points you to `$c-tr`.

### Escape `Markup` values

A value with an `__html__()` method, such as `Markup`, is escaped like
any other value, so a `"` in it stays part of the attribute. Citry
first reads its HTML the way a browser would, so an entity such as
`&amp;` still stands for its character instead of showing as `&amp;`.
Static and interactive pages set the same value.
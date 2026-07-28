---
title: HTML attributes
url: https://citry.dev/v/0.3.0/concepts/html-attributes/
description: "Structured class and style values, attribute spreading, and the Python helpers for building attribute dicts."
---
# HTML attributes

Citry gives you two ways to work with HTML attributes. In a template you write
dynamic attributes with `c-*`, structure `class` and `style` as lists and
dicts, and spread a whole dict with `c-bind`. In Python component code you can
build and merge the same attribute dicts with a small set of helper functions.
Both layers follow the same rules, so what you learn in one carries over.

## Dynamic attributes in templates

Any attribute whose name starts with `c-` is dynamic. Its value is evaluated as
a host-language (Python) expression, and exactly one leading `c-` is stripped
from the rendered attribute name. A boolean result follows HTML rules: `True`
renders a bare attribute, `False` or `None` omits it entirely.


```html
<!-- button_type = "primary", is_loading = True -->
<div c-class="'btn ' + button_type">
  <button c-disabled="is_loading">Submit</button>
</div>
<!-- Result: -->
<div class="btn primary">
  <button disabled>Submit</button>
</div>
```


A `c-*` attribute must have a non-empty value. Writing `c-foo` or `c-foo=""`
raises a parse-time `SyntaxError`. The only exceptions are the control-flow
shorthands `c-else` and `c-empty`, which take no value.

Because the value is an ordinary expression, it can carry an inline Python
comment:


```html
<div c-class="get_classes()  # fetch dynamic classes">y</div>
```


## Structured class and style

`class` and `style` are special. Instead of a plain string, their `c-*` value
can be a string, a dict, or a list, and Citry combines the pieces for you
(Vue-style).

For `class`, a dict maps a class name to a truthy or falsy flag, and a list can
mix strings and dicts. For `style`, a dict maps a CSS property (written in
kebab-case, as you would in CSS) to its value.


```html
<!-- is_active = True, color = "red" -->
<div c-class="['btn', { 'active': is_active, 'hidden': False }]"></div>
<div c-style="{ 'color': color, 'background-color': 'blue' }"></div>
<!-- Result: -->
<div class="btn active"></div>
<div style="color: red; background-color: blue;"></div>
```


Unlike other attributes, `class` and `style` from every source are merged
rather than overwritten. See [merging across sources](#merging-across-sources)
below.

## Spreading a dict with c-bind

`c-bind="expr"` spreads an evaluated dict of attributes onto the tag. Booleans
follow the same bare/omitted rules as any dynamic attribute.


```html
<!-- item.id = 123 -->
<div c-bind="{'class': 'btn', 'disabled': True, 'data-id': item['id']}">y</div>
<!-- Result: -->
<div class="btn" disabled data-id="123">y</div>
```


A `c-bind` that resolves to `None` is a silent no-op (matching Vue's
`v-bind="null"`). Any other non-mapping value (an int, a string, a list) raises
a `TypeError`.

On a component tag, these values remain Python component inputs. Citry does
not copy arbitrary attributes to the child's root. Only `$c-props`, Alpine
event handlers, and `@c-*` handlers have special client-boundary behavior.
For `x-show`, `x-model`, `:class`, `class`, or another arbitrary attribute,
pass an explicit mapping kwarg and let the child spread it onto the chosen
root or nested element. See [Client interactivity](/v/0.3.0/concepts/client-interactivity/#pass-arbitrary-html-attributes-explicitly).

## Merging across sources

You can mix a static attribute, one or more `c-bind` spreads, and dynamic
`c-*` attributes on the same tag. For plain keys, source order wins (the last
one written takes effect). For `class` and `style`, the values from every
source are combined.


```html
<div class="default"
     c-bind="{'class': 'from-bind', 'id': 'first'}"
     c-class="'override'"
     c-bind="{'id': 'second'}">y</div>
<!-- Result (classes from all sources merge; id last-one-wins): -->
<div class="default from-bind override" id="second">y</div>
```


## Writing a literal colon-prefixed attribute

Because only one leading `c-` is stripped, `c-:class` renders the literal
`:class` attribute. This is how you emit a client-framework binding (Alpine or
Vue) from a Citry template: Citry evaluates the expression, and the `:class`
name passes through to the browser.


```html
<!-- alpine_binding evaluates to "{ open: isOpen }" -->
<div c-:class="alpine_binding"></div>
<!-- Result: literal :class attribute for the client framework -->
<div :class="{ open: isOpen }"></div>
```


The same one-strip rule means `c-c-foo` renders `c-foo`, not `foo`.

## Building attribute dicts in Python

The same value handling is available as plain functions, exported from
`citry` and usable anywhere in your component code. This is handy when a
`template_data` method assembles attributes before handing them to the
template.

[`format_attrs`](/v/0.3.0/reference/attributes/#citry-format-attrs) turns a dict into an HTML attribute
string. `True` becomes a bare attribute, `False` and `None` are omitted, and a
structured `class`/`style` is normalized. When a structured `class` or `style`
normalizes to an empty string, the attribute is dropped (an empty `class=""`
would read as a boolean attribute under Citry's rules).


```python
from citry import format_attrs

format_attrs({"class": ["btn", {"active": True, "hidden": False}], "disabled": True, "data-id": 3})
# -> 'class="btn active" disabled data-id="3"'

format_attrs({"required": True})   # -> 'required'
format_attrs({"required": False})  # -> ''
format_attrs({"required": None})   # -> ''
format_attrs({"class": {"hidden": False}, "id": "x"})  # -> 'id="x"'  (empty class dropped)
```


[`merge_attrs`](/v/0.3.0/reference/attributes/#citry-merge-attrs) merges attribute dicts left-to-right. Every
key is last-one-wins except `class` and `style`, whose values from all dicts are
collected and combined. A key keeps its first-seen position even when a later
dict overrides it.


```python
from citry import merge_attrs

merge_attrs({"class": "btn", "id": "first"}, {"class": {"active": True}, "id": "second"})
# -> {"class": "btn active", "id": "second"}
```


[`normalize_class`](/v/0.3.0/reference/attributes/#citry-normalize-class),
[`normalize_style`](/v/0.3.0/reference/attributes/#citry-normalize-style), and
[`parse_string_style`](/v/0.3.0/reference/attributes/#citry-parse-string-style) are the pieces underneath.
`normalize_class` produces a space-joined class string, `normalize_style`
produces an inline CSS string, and `parse_string_style` reads an inline CSS
string back into a dict (keeping semicolons inside parentheses intact, so a
`url(data:...)` value survives).


```python
from citry import normalize_class, normalize_style, parse_string_style

normalize_class(["btn btn-lg", {"active": True, "hidden": False}])  # -> 'btn btn-lg active'
normalize_class(["a", "b", {"b": False}])  # -> 'a'   (later falsy removes earlier)
normalize_style(["color: red; width: 100px", {"color": "green", "width": False}])  # -> 'color: green;'
parse_string_style("background: url(data:image/png;base64,abc); color: red")
# -> {"background": "url(data:image/png;base64,abc)", "color": "red"}
```


## Merge rules to remember

- In a `class` list, a later falsy dict entry removes a class added by an
  earlier entry, so `["a", "b", {"b": False}]` normalizes to `"a"`. This is a
  deliberate divergence from Vue.
- In a `style` merge, `None` means "skip, let an earlier value stand", while
  literal `False` removes the property.
- An empty structured `class` or `style` is omitted entirely, never rendered as
  `class=""`.
- Passing a value that is not a string, dict, or list to `normalize_class` or
  `normalize_style` raises a `TypeError`; there is no silent coercion.
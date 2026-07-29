---
title: Dynamic attributes
url: https://citry.dev/v/0.3.1/syntax/dynamic-attributes/
description: "Use c- attributes to compute attribute values from expressions, with boolean, class, style, spreading, and literal-colon rules."
---
# Dynamic attributes

A plain HTML attribute is a fixed string. When you want the value to come from
your data instead, prefix the attribute name with `c-`. Citry evaluates the
value as an expression (the same expressions you use in `{{ }}`, see
[Expressions](/v/0.3.1/syntax/expressions/)) and strips exactly one leading `c-` from
the rendered name.


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


A `c-` attribute must have a non-empty value: both `c-foo` and `c-foo=""` are a
parse-time error. The only value-less `c-` attributes are the control-flow
shorthands `c-else` and `c-empty` (see [Control flow](/v/0.3.1/syntax/control-flow/)).

## Boolean attributes

When a `c-` value evaluates to a boolean or `None`, Citry follows HTML rules:

- `True` renders the attribute bare, with no value (`disabled`).
- `False` and `None` omit the attribute entirely.


```html
<!-- Result depends on the value of `is_loading` -->
<button c-disabled="is_loading">Submit</button>
<!-- is_loading = True  -> <button disabled>Submit</button> -->
<!-- is_loading = False -> <button>Submit</button> -->
```


## Structured class and style

`class` and `style` accept more than a plain string. You can pass a dict or a
list, in the Vue style, and Citry combines them into a final string. Unlike
every other attribute, values from all sources merge instead of overwriting.

For `class`, a dict maps a class name to whether it is enabled, and a list can
mix strings and dicts:


```html
<!-- is_active = True -->
<div c-class="['btn', { 'active': is_active, 'hidden': False }]"></div>
<!-- Result: -->
<div class="btn active"></div>
```


For `style`, a dict maps a CSS property (written kebab-case) to its value:


```html
<!-- color = "red" -->
<div c-style="{ 'color': color, 'background-color': 'blue' }"></div>
<!-- Result: -->
<div style="color: red; background-color: blue;"></div>
```


If a structured `class` or `style` normalizes to an empty string, the attribute
is dropped rather than rendered as `class=""` (an empty `class=""` would read as
a bare boolean attribute under Citry's rules).

One thing to watch: in a `class` list, a later falsy dict entry removes a class
added by an earlier entry. This is a deliberate divergence from Vue.


```python
from citry import normalize_class
normalize_class(["a", "b", {"b": False}])  # -> 'a'  (the later {'b': False} removes 'b')
```


## Spreading a dict with c-bind

Use `c-bind="expr"` to spread a whole dict of attributes onto a tag at once.
Booleans and structured `class`/`style` follow the same rules as above.


```html
<!-- item = {"id": 123} -->
<div c-bind="{'class': 'btn', 'disabled': True, 'data-id': item['id']}">y</div>
<!-- Result: -->
<div class="btn" disabled data-id="123">y</div>
```


You can use `c-bind` more than once and interleave it with static and `c-`
attributes. Attributes apply in source order: plain keys are last-one-wins,
while `class` and `style` merge across every source.


```html
<div class="default"
     c-bind="{'class': 'from-bind', 'id': 'first'}"
     c-class="'override'"
     c-bind="{'id': 'second'}">y</div>
<!-- Result (classes from all sources merge; id last-one-wins): -->
<div class="default from-bind override" id="second">y</div>
```


A `c-bind` that resolves to `None` is a no-op (matching Vue's `v-bind="null"`).
Any other non-mapping value (an int, string, or list) raises a `TypeError`.

## Escaping the prefix with c-:

Because Citry strips only one leading `c-`, a value written as `c-:class` still
carries a leading `:` in the rendered name. This lets you emit a literal
`:class` attribute for a client framework like Alpine or Vue, while still
computing its value from a Citry expression.


```html
<!-- alpine_binding evaluates to "{ open: isOpen }" -->
<div c-:class="alpine_binding"></div>
<!-- Result: literal :class attribute for the client framework -->
<div :class="{ open: isOpen }"></div>
```


The same rule generalizes: `c-c-foo` renders `c-foo`, not `foo`.

## The same rules from Python

The template behavior above is backed by helpers you can call directly from
component code. They are all exported from `citry`:
[normalize_class](/v/0.3.1/reference/attributes/#citry-normalize-class),
[normalize_style](/v/0.3.1/reference/attributes/#citry-normalize-style),
[parse_string_style](/v/0.3.1/reference/attributes/#citry-parse-string-style),
[merge_attrs](/v/0.3.1/reference/attributes/#citry-merge-attrs), and [format_attrs](/v/0.3.1/reference/attributes/#citry-format-attrs).


```python
from citry import format_attrs, merge_attrs

format_attrs({"class": ["btn", {"active": True, "hidden": False}], "disabled": True, "data-id": 3})
# -> 'class="btn active" disabled data-id="3"'

merge_attrs({"class": "btn", "id": "first"}, {"class": {"active": True}, "id": "second"})
# -> {"class": "btn active", "id": "second"}
```


See [HTML attributes](/v/0.3.1/concepts/html-attributes/) for how these fit into
rendering a component's root element.
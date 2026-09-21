---
title: Attributes
description: Compute HTML attributes and component inputs with Python, including boolean values, class and style merging, and c-bind.
---

# Attributes

## `c-` Dynamic attributes

An ordinary attribute contains a fixed value. Add `c-` to turn the value into a Python expression that *generates*
the value:

```citry-html
<!-- kind = "primary", is_loading = True -->
<button
  c-class="'button button-' + kind"
  c-disabled="is_loading"
>
  Save
</button>
```

Citry evaluates each value as a Python
[expression](/syntax/expressions/) and removes the `c-` from the attribute
name. The browser receives:

```html
<button class="button button-primary" disabled>
  Save
</button>
```

Do not add `{{ }}` around the expression. Write `c-title="user.name"`, not
`c-title="{{ user.name }}"`.

A dynamic attribute needs a non-empty value. `c-title` and `c-title=""` are
errors. The bare `c-else` and `c-empty` [control-flow markers](/syntax/control-flow/) are the two
exceptions.

### HTML elements

On an HTML element, Citry turns the result into an HTML attribute. `True`
renders a bare attribute, while `False` and `None` leave it out:

```citry-html
<!-- required = True, disabled = False -->
<input c-required="required" c-disabled="disabled">
<!-- Result: <input required> -->
```

Attribute names and values are HTML-escaped. The value can opt-out of HTML-escaping, see [Bypass HTML escape](/syntax/expressions/#bypass-html-escape).

### ARIA values

If `aria-pressed` renders without a value or disappears, check the type of
the expression's result. A Python `True` renders a bare attribute; `False`
or `None` omits it. For a boolean ARIA state such as `aria-pressed`, return
the strings `"true"` and `"false"`, including when the state is false:

```citry-html
<!-- Wrong: True becomes bare aria-pressed; False omits it. -->
<button c-aria-pressed="selected">Choose</button>

<!-- Use strings to retain both ARIA states. -->
<button c-aria-pressed="'true' if selected else 'false'">
  Choose
</button>
```

For a Python value, use the `c-` expression form shown here. An ordinary
attribute such as `aria-pressed="{{ selected }}"` keeps that text literally.

### Components

On a component tag, an attribute is the [component's Python input](/concepts/inputs-and-validation/). A static value
is a string, while a `c-*` value keeps its Python type:

```citry-html
<c-UserBadge
  label="User Name"
  c-user="user"
  c-enabled="feature_enabled"
/>
```

Which is equivalent to Python:

```python
UserBadge(
    label="User Name",
    user=user,
    enabled=feature_enabled,
)
```

How to read the above:

- `label` receives the literal string `"User Name"`
- `user` receives the Python object
- `enabled` receives the Python boolean

`False` and `None` are still passed to the component; they are not omitted.

### Vue

Vue expressions must remain statically authored template source. Pass their
values through strict-JSON `js_data`, then write the binding directly:

```citry
class Panel(Component):
    class JsData:
        open: bool

    def js_data(self, kwargs, slots):
        return {"open": True}

    template = '<div :class="{ open: open }"></div>'
```

`c-:class` cannot turn a Python-rendered string into executable Vue source.
This keeps browser code reviewable and prevents runtime data from becoming
code.

Read
[Vue in templates](/syntax/vue/) for browser-side attributes and
[Client interactivity](/concepts/client-interactivity/) for values that cross
component boundaries.

### Escape the c- prefix

Citry removes exactly one leading `c-`. When you need to generate
an attribute with the `c-` prefix, you can either:

Add one more `c-`, so `c-c-feature` -> `c-feature`:

```citry-html
<div c-c-feature="enabled"></div>
<!-- Result when enabled is True: <div c-feature></div> -->
```

Or apply the attribute through [`c-bind`](#c-bind-spread), which preserves the keys:

```citry-html
<div c-bind="{'c-feature': enabled}"></div>
<!-- Result when enabled is True: <div c-feature></div> -->
```

## Props and events

Vue bindings on a component tag pass reactive data and browser events across
the component boundary:

```citry-html
<c-ActionButton
  :theme="selectedTheme"
  @click="selected = true"
  @c-save="saveSelection({ selected })"
/>
```

### `:prop`

Declare native Vue props in the child component's JavaScript:

```js
$component({
  props: {
    open: Boolean,
    dense: Boolean,
  },
});
```

Pass each reactive value from the parent with `:` or `v-bind`:

```citry-html
<c-ActionButton :open="open" :dense="true" />
```

The expression runs in the parent's Vue context. The child receives the value
through Vue's normal prop validation and reactivity. See
[Client interactivity](/concepts/client-interactivity/#pass-props-to-a-child).

### `@event`

Vue's event bindings listen for browser or component events:

```citry-html
<div>
  <c-ActionButton @click="open = !open" />
</div>

{# Inside ActionButton #}
<button>
  Click me!
</button>
```

You can access `$event` inside the expression:

```citry-html
<c-ActionButton
  @click="doSomething($event.target.detail)"
/>
```

Read more about [child events](/concepts/client-interactivity/#listen-to-child-events).

### `@c-event`

Vue event handlers run in the browser. Prefix the event name with `c-`, as in
`@c-click`, to trigger a [server event handler](/events/):

- `@click` - Regular Vue `click` event handler
- `@c-click` - Send event to the server

The value of `@c-click` attributes is strict:

- It MUST name the server-side event handler, eg `submit`
- It MAY send extra arguments, eg `submit({ title })`

Read more about [Binding events in templates](/events/bindings/).

```citry-html
<div>
  {# No arguments #}
  <c-ActionButton @c-click="submit" />

  {# With arguments #}
  <c-ActionButton @c-click="submit({ title })" />
</div>
```

## Class and style

### Class

For an HTML `c-class`, its value may contain:

- string - the class string itself, `"btn btn-sm"`
- mapping - keys are class names, values are truthy == include / falsy == omit
- lists / tuples - containing other strings, mappings, or lists

A mapping includes each class whose value is truthy:

```citry-html
<!-- active = True -->
<div
  c-class="[
    'button',
    {'active': active, 'hidden': False}
  ]"
></div>
<!-- Result: <div class="button active"></div> -->
```

A later false mapping entry removes an earlier class of the same name:

```citry-html
<div c-class="['one', 'two', {'two': False}]"></div>
<!-- Result: <div class="one"></div> -->
```

If the structured value contains no classes, Citry omits the attribute.

```citry-html
<div c-class="{'two': False}"></div>
<!-- Result: <div></div> -->
```

`class` and `style` have special merging behavior - you can define both `c-class` and `class` and they merge:

```citry-html
<div class="btn" c-class="['btn-primary']"></div>
<!-- Result: <div class="btn btn-primary"></div> -->
```

### Style

For an HTML `c-style`, you may also pass a string, mapping, or nested sequence.
Write CSS property names in kebab-case:

```citry-html
<!-- color = "crimson" -->
<p
  c-style="[
    {'color': color},
    'font-weight: bold',
  ]"
>
  Important
</p>
<!-- Result:
  <p style="color: crimson; font-weight: bold;"></p>
-->
```

Across merged style values, `None` leaves an earlier property unchanged and
`False` removes it.

```citry-html
<div
  c-style="[
    {'color': 'red', 'font-size': '16px', 'margin': '1rem'},
    {'color': None, 'font-size': False},
  ]"
>
<!-- Result: <div style="color: red; margin: 1rem;"> -->
```

An empty structured style is omitted:

```citry-html
<div c-style="{'color': False}"></div>
<!-- Result: <div></div> -->
```

`class` and `style` have special merging behavior - you can define both `c-style` and `style` and they merge:

```citry-html
<div
  style="color: red;"
  c-style="{'font-size': '1rem'}"
></div>
<!-- Result: <div style="color: red; font-size: 1rem;"></div> -->
```

### Components are exempt

The merging rules above only apply to plain HTML elements (including [`<c-element>`][c-element]). On a component tag,
`class` and `style` are ordinary component inputs. A component decides whether,
and where, to place an input on its own HTML:

```citry-html
{# On an HTML element the two values merge #}
<div class="card" c-class="'selected'"></div>
<!-- Result: <div class="card selected"></div> -->

{# `Card` receives "card" as an ordinary input #}
<c-Card class="card" />
```

See
[passing HTML attributes through a component](/concepts/client-interactivity/#pass-arbitrary-html-attributes-explicitly).

## c-bind spread

Use `c-bind` to apply several values at once:

```citry-html
<!-- item = {"id": 42} -->
<button
  c-bind="{
    'class': ['button', {'selected': True}],
    'disabled': False,
    'data-id': item['id'],
  }"
>
  Choose
</button>
```

The browser receives:

```html
<button class="button selected" data-id="42">
  Choose
</button>
```

`c-bind` accepts any Python mapping. Mapping keys must be
strings and, on HTML elements, valid attribute names. The value of `c-bind`
itself is always an expression.

When `c-bind` evaluates to `None`, it does
nothing. Any other non-mapping value raises `TypeError`. 

Accepted keys are used exactly as written: a key named `c-title` stays
`c-title`. Only a directly authored dynamic attribute loses one `c-` prefix.
In a prepared Vue template, generated `v-*`, `@*`, and `:*` keys are rejected:
Python-rendered strings do not become authenticated Vue source. Author those
bindings directly in the template instead.

```citry-html
<button c-bind="{ 'c-title': title }">
<!-- Result: <button c-title="My Title"> -->

<button c-title="title">
<!-- Result: <button title="My Title"> -->
```

Most structural built-in tags, including [`<c-if>`][c-if] and
[`<c-for>`][c-for], do not accept an attribute spread. Put `c-bind` on the
HTML element or component tag that should receive those values. `<c-slot>` and
`<c-fill>` are the deliberate exceptions: they use a spread to choose a slot
and bind its data. Their accepted keys are documented in
[Spread slot and fill settings](/concepts/slots/#spread-slot-and-fill-settings).

### On HTML elements

Entries are serialized the same way as when you define the attributes directly:

```citry-html
<span
  c-bind="{'style': {'color': 'crimson'}, 'hidden': False}"
></span>
<!-- Result: <span style="color: crimson;"></span> -->

<span
  c-style="{'color': 'crimson'}"
  c-hidden="False"
></span>
<!-- Result: <span style="color: crimson;"></span> -->
```

### On components

The same principle applies to component inputs:

```citry-html
<c-Card
  title="My card"
  c-bind="{
    'disabled': True,
    'id': 'first',
  }"
></c-Card>

<!-- Same as: -->
<c-Card
  title="My card"
  c-disabled="True"
  c-id="'first'"
></c-Card>
```

Write Vue props and event bindings directly on the component call. `c-bind`
contains Python values and does not turn those values into JavaScript source.

### Order and duplicates

You may use `c-bind` more than once and mix it with direct attributes. Sources
are applied from left to right. A later ordinary key replaces an earlier one,
while every HTML `class` and `style` value is merged:

```citry-html
<div
  class="base"
  c-bind="{'class': 'from-data', 'id': 'first'}"
  c-class="'selected'"
  c-bind="{'id': 'last'}"
></div>
```

The browser receives:

```html
<div class="base from-data selected" id="last"></div>
```

Direct duplicate attributes are rejected. That includes static and dynamic
spellings of the same logical name, such as `id` with `c-id`. On a plain HTML
element, `class` with `c-class` and `style` with `c-style` are allowed because
those values merge. Repeated `c-bind` attributes are allowed too.

HTML attribute names use ASCII-case-insensitive identity. For example, `ID`
from one spread and `id` from a later spread are one attribute: the later
value wins, while the first spelling and output position stay in place.
`CLASS` and `class` contributions merge just like lowercase `class` values.
Two explicit full-name variants such as `ID` and `id` are a parse error, as
are `ID` and `c-id`. This rule applies to ordinary HTML and `<c-element>`;
component input names remain case-sensitive Python kwargs. Because
`<c-element>` is itself an HTML boundary, this includes its special selector:
`IS`, `c-IS`, and spread-provided `Is` all resolve the same `is` input.
`<c-component>` still requires exact lowercase `is` / `c-is`.

Component inputs also resolve from left to right, but every input is
last-one-wins, including `class` and `style`. Their special merging behavior
belongs only to HTML output.

### Pass-through attributes

A common need is to pass arbitrary HTML attributes to a component,
and the component then passing them to one (or several) of its children. This feature is known as [Fallthrough attributes](https://vuejs.org/guide/components/attrs){: target="_blank" rel="noopener"} in Vue.

In Citry, whether you can pass extra attributes to a component is decided by the [`Kwargs`][citry.Component.Kwargs] class:

When there is no `Kwargs` class (or set to `None`), you can pass any attributes to the component. They get all collected as `kwargs` input:

```citry
class Card(Component):
    def template_data(self, kwargs, slots):
        return {"attrs": kwargs}

    template = """
      <div c-bind="attrs"></div>
    """

# Render as `<c-Card class="btn" id="3" data-id="3" />`
```

When your component has a `Kwargs` class, you can't pass extra attributes directly. Instead, define an explicit kwarg like `attrs` to collect the attributes as a dictionary:

```citry
class Card(Component):
    class Kwargs:
        title: str
        attrs: dict

    def template_data(self, kwargs: Kwargs, slots):
        return {"attrs": kwargs.attrs}

    template = """
      <div c-bind="attrs"></div>
    """

# Render as
# <c-Card
#   title="My Card"
#   c-attrs="{'class': 'btn', 'id': 3, 'data-id': 3}"
# />
```

For more details, see [Forward HTML attributes](/advanced/html-attributes/).

## `:c-*` State bind

A `:c-*` attribute connects an input field on the page (such as `<input>` or `<input type="checkbox">`) to a field of the component's
server-side [`State`][citry.Component.State]. Citry syncs the two values, so you don't have to.

### One-way binding

First, consider this example with a [dynamic attribute](#c-dynamic-attributes) `c-value`:

```citry-html
{# The control shows the value, but nothing sends edits back #}
<input type="text" c-value="query">
```

- The `query` is taken from `template_data` or `Kwargs`.
- One-way binding - you have to handle to user input yourself.

If you want to take the value from `State` instead of `Kwargs`, you can use the special `:c-*` attribute. The remainder of the attribute name after the `:c-` is the State field, eg `:c-query` connects the field `State.query`.

```citry-html
{# The control shows the value, but nothing sends edits back #}
<input type="text" :c-query>
```

What happens when you use `:c-query`:

1. `:c-query` means "Take the value of `State.query` and set the
  `<input>`'s value to it".
2. Still one-way binding - you have to react to user input yourself.

Notice we didn't need to explicitly set a `value` attribute on `<input>`.
Different inputs use different ways to set or select the value. Citry detects that
you used `:c-*` on an `<input>` element, and automatically chooses the correct approach. For a list of all supported elements, see [Bind controls to State](/events/bindings/#bind-controls-to-state).

For this to work, your State class needs a `query` field:

```citry
class Card(Component):
    class State:
        query: str
```

### Two-way binding

To enable two-way binding, add a value part to the `:c-` attribute, <br/>eg `:c-query` -> `:c-query="refresh"`:

- `:c-query` displays the `State.query` field in the control
- `:c-query="refresh"`
    - displays `State.query`
    - calls the `refresh` [event handler](/events/) on user input
    - updates the `State.query` to the *new* user input when `refresh` is triggered

```citry-html
{# Display only #}
<input :c-query>

{# Update the field and call `refresh` as the user types #}
<input :c-query="refresh">

{# Wait for 300 ms of quiet before each update #}
<input :c-query.debounce.300ms="refresh">
```

The `:c-` attribute needs an element that holds a value: an `<input>`, `<textarea>`,
`<select>`, or a custom element. Anything else is an error when the template
loads. The editor also reports statically known unsupported targets.

`<select multiple>` is supported in both directions. Its State field is a
`list[str]`; Citry reads every selected option and writes the list back by
matching option values. This also works when `multiple` or the binding arrives
through `c-bind`.

Input `type` follows the same phase rule. A type produced by `c-type` or
`c-bind` is checked against the final rendered attributes. A Vue
`:type` is checked whenever it changes in the browser. Unsupported or unknown
types do not leave a half-active binding. See the complete direction matrix in
[Bind controls to State](/events/bindings/#which-elements-you-can-bind).

```citry-html
{# ✅ Binds an HTML control to a State field #}
<input :c-query="refresh">

{# ❌ A <div> has no value to bind #}
<div :c-query="refresh"></div>

{# ❌ Not allowed on a component tag #}
<c-SearchBox :c-query="refresh" />
```

!!! note

    **DO NOT** pass `:c-` attributes to child components. They belong on the HTML elements inside the component that owns the State.
    A child component binds its own State in its own template, so pass reactive
    browser data down through a native [Vue prop](#prop).

After you have set up the two-way binding, check your event handler, `refresh`. The value of `State.query` is already updated to the latest value every time `refresh` is triggered:

```citry
class Card(Component):
    class Events:
        def refresh(self, state):
            print(state.query)  # contains latest value
```

Read [Bind controls to State](/events/bindings/#bind-controls-to-state) for the
full element list and more. See [Keep State between calls](/events/state/) for declaring the State fields.

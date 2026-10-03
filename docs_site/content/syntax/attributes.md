---
title: Attributes
description: Compute HTML attributes and component inputs with Python, including boolean values, class and style merging, and c-bind.
---

# Attributes

Sometimes a button should be disabled while a form saves, a row should get a
`selected` class, or a component needs a Python object as input. In each case an attribute
value comes from your data rather than from fixed text.

Put `c-` in front of the attribute name to make its value a Python
expression. This page starts with that, including `True` and `False` values
and component inputs. It then covers classes and styles, applying many
attributes at once with `c-bind`, Vue's `:prop` and `@event`, and the
special `:c-*`, `#c-key`, and `#c-ignore` attributes.

## `c-*` Python attrs { #c-dynamic-attributes }

An ordinary attribute holds fixed text. With `c-` in front, Citry evaluates
the value as a Python [expression](/syntax/expressions/) and removes the `c-`
from the name:

```citry-html
<!-- kind = "primary", is_loading = True -->
<button
  c-class="'button button-' + kind"
  c-disabled="is_loading"
>
  Save
</button>
```

The browser receives:

```html
<button class="button button-primary" disabled>
  Save
</button>
```

Write the expression without `{{ }}`: `c-title="user.name"`, not
`c-title="{{ user.name }}"`. A `c-` attribute needs a value, so `c-title` and
`c-title=""` are errors. Only the `c-else` and `c-empty` markers from
[Conditions and loops](/syntax/control-flow/) take no value.

Citry HTML-escapes attribute names and values. To insert a value without
escaping, see [`Markup` skips escape](/syntax/expressions/#insert-html-you-trust).

## `c-*` boolean attrs { #html-elements }

On an HTML element, `True` renders a bare attribute, and `False` or `None`
leaves the attribute out:

```citry-html
<!-- required = True, disabled = False -->
<input c-required="required" c-disabled="disabled">
<!-- Result: <input required> -->
```

If an `aria-pressed` attribute disappears or has no value, the expression
returned a boolean. ARIA states need the strings `"true"` and `"false"`,
including when the state is false:

```citry-html
<!-- Wrong: True gives bare aria-pressed; False drops it. -->
<button c-aria-pressed="selected">Choose</button>

<!-- Right: both states keep a value. -->
<button c-aria-pressed="'true' if selected else 'false'">
  Choose
</button>
```

!!! note "Check whether a flag attribute is present, not its value"

    On a page that uses Vue, the same `True` can read differently in the
    browser. Python writes a bare attribute, so `data-open` reads as `""`.
    When Vue renders or updates the component, it writes `"true"` on any
    attribute the element does not treat as a boolean, such as `data-open`,
    or `disabled` on a `div` element. Real boolean attributes, such as
    `disabled` on an `input` element, stay bare either way. In CSS and
    JavaScript, test `[data-open]` or `hasAttribute("data-open")`.

## `c-*` on components

On a component tag, each attribute is one of the
[component's inputs](/concepts/inputs-and-validation/). A plain attribute
passes a string. A `c-` attribute passes the Python value with its type:

```citry-html
<c-UserBadge
  label="User Name"
  c-user="user"
  c-enabled="feature_enabled"
/>
```

This is the same as calling the component in Python:

```python
UserBadge(
    label="User Name",
    user=user,
    enabled=feature_enabled,
)
```

Unlike on HTML elements, `False` and `None` are passed to the component
like any other value.

## `c-class`

`c-class` accepts more than a string. You can give it:

- a string, such as `"btn btn-sm"`
- a dictionary that maps a class name to a condition; the class is added
  when the condition is true
- a list or tuple of strings, dictionaries, or more lists

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

`class` and `c-class` can sit on the same element. Citry joins them:

```citry-html
<div class="btn" c-class="['btn-primary']"></div>
<!-- Result: <div class="btn btn-primary"></div> -->
```

A later `False` entry removes a class added earlier. When no classes remain,
Citry leaves the attribute out:

```citry-html
<div c-class="['one', 'two', {'two': False}]"></div>
<!-- Result: <div class="one"></div> -->

<div c-class="{'two': False}"></div>
<!-- Result: <div></div> -->
```

## `c-style`

`c-style` accepts a string, a dictionary of CSS properties, or a list of
them. Write property names in kebab-case:

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

`style` and `c-style` on the same element are joined too:

```citry-html
<div
  style="color: red;"
  c-style="{'font-size': '1rem'}"
></div>
<!-- Result: <div style="color: red; font-size: 1rem;"></div> -->
```

When several values set the same property, a later `False` removes it and a
later `None` leaves the earlier value alone. An empty style is left out:

```citry-html
<div
  c-style="[
    {'color': 'red', 'font-size': '16px'},
    {'color': None, 'font-size': False},
  ]"
></div>
<!-- Result: <div style="color: red;"></div> -->
```

!!! note "Components receive `class` and `style` as ordinary inputs"

    The joining above happens only on HTML elements, including
    [`<c-element>`][c-element]. On a component tag, `class` and `style` are
    inputs like any other, and the component decides where to put them. See
    [Pass HTML attributes](/concepts/client-interactivity/#pass-arbitrary-html-attributes-explicitly).

## `c-bind` { #c-bind-spread }

When the attributes come from a dictionary, apply them all with `c-bind`:

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

Each entry renders as if you had written it as a `c-` attribute, so `class`,
`style`, `True`, and `False` follow the rules above. On a component tag, the
entries become the component's inputs:

```citry-html
<c-Card
  title="My card"
  c-bind="{'disabled': True, 'id': 'first'}"
/>

<!-- Same as: -->
<c-Card
  title="My card"
  c-disabled="True"
  c-id="'first'"
/>
```

`c-bind` takes any Python mapping with string keys. On HTML elements, each key
must be a valid attribute name. `None` applies nothing, and any other value
that is not a mapping raises `TypeError`.

Keys are used exactly as written. Unlike a `c-` attribute, a key named
`c-title` stays `c-title`:

```citry-html
<button c-bind="{'c-title': title}">
<!-- Result: <button c-title="My Title"> -->
```

### `c-bind` merge order

You can use `c-bind` more than once and mix it with other attributes. Citry
applies them from left to right. A later value replaces an earlier one, except
that every HTML `class` and `style` value is joined:

```citry-html
<div
  class="base"
  c-bind="{'class': 'from-data', 'id': 'first'}"
  c-class="'selected'"
  c-bind="{'id': 'last'}"
></div>
<!-- Result:
  <div class="base from-data selected" id="last"></div>
-->
```

On a component tag, every input works this way, `class` and `style`
included: the last value wins.

Writing the same attribute twice directly on a tag is an error, and that
includes `id` together with `c-id`. The exceptions are `class` with
`c-class` and `style` with `c-style` on HTML elements, and repeated
`c-bind`.

### `c-bind` forwards `kwargs`

A component often accepts extra HTML attributes, such as `id` or `data-*`,
and puts them on one of its own elements. Vue calls these
[fallthrough attributes](https://vuejs.org/guide/components/attrs){: target="_blank" rel="noopener"}.

A component without a `Kwargs` class accepts any input. Pass all of `kwargs`
to `c-bind`:

```citry
class Card(Component):
    def template_data(self, kwargs, slots):
        return {"attrs": kwargs}

    template = """
      <div c-bind="attrs"></div>
    """

# Use as <c-Card class="btn" id="3" data-id="3" />
```

A component with `Kwargs` rejects inputs it does not declare. Declare one
input, such as `attrs`, that collects the extra attributes as a dictionary:

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

# Use as
# <c-Card
#   title="My Card"
#   c-attrs="{'class': 'btn', 'id': 3}"
# />
```

See [HTML attributes](/advanced/html-attributes/) for more.

## Vue `:prop` and `@event`

Attributes that start with `:` or `@` are Vue syntax. They run in the browser
and pass reactive values and event listeners to a child component:

```citry-html
<c-ActionButton
  :theme="selectedTheme"
  @click="selected = true"
  @c-save="saveSelection({ selected })"
/>
```

- `:theme` passes a Vue prop that the child declares in its JavaScript. See
  [Pass props to a child](/concepts/client-interactivity/#pass-props-to-a-child).
- `@click` runs browser code when the child emits `click`. The expression can
  read `$event`. See
  [Listen to child events](/concepts/client-interactivity/#listen-to-child-events).
- `@c-save` calls the Python event handler `saveSelection` on the server. See
  [Bind events in templates](/events/bindings/).
- `v-on="listeners"` adds every listener in a Vue object at once.

[Vue in templates](/syntax/vue/) lists every Vue directive a component tag
accepts.

!!! warning "Python values cannot become Vue bindings"

    Write each Vue binding (`:name`, `@event`, `v-*`) directly in the
    template. Citry never turns a Python value into browser code, so the
    browser code stays visible in the template.

    A name that starts with `v-`, `@`, `:`, `.`, `^`, or `#`, in any
    letter case, is Vue syntax. When Python supplies such a name, through
    a `c-bind` key or a `c-` attribute such as `c-:class` or `c-v-on`, the
    render fails:

    - On a component tag such as `<c-ActionButton>`, rendering the
      template that writes the tag raises `RuntimeError`, even for a
      `None` value.
    - On an HTML element, on a page that uses Vue, the render raises
      `TypeError`, unless the value is `None` or `False`. It fails even
      when the template writes the same binding on the element, such as
      `@click` beside a `c-bind` mapping with an `'@click'` key: remove
      the key from the mapping. You see the error when you turn the
      render into HTML, for example with `str()`. In an Events response,
      the call fails with a server error and the log shows the
      `TypeError`. On a page without Vue, the name is written as a plain
      attribute.

    Citry's own `@c-` and `:c-` Events bindings are the exception: a
    `c-bind` key may set them. See [Bind events in templates](/events/bindings/).
    A `v-on` value containing `{{ ... }}` fails too.

To give Vue a value from Python, return it from `js_data()` and read it in
the binding:

```citry
class Panel(Component):
    class Kwargs:
        open: bool

    def js_data(self, kwargs: Kwargs, slots):
        return {"open": kwargs.open}

    template = """
      <div :class="{ open: open }"></div>
    """

# Use as <c-Panel c-open="True" />
```

## `:c-*` State bindings

A component's [`State`][citry.Component.State] holds values the server keeps
between event calls. A `:c-*` attribute shows a State field in a form field
and, optionally, sends the user's edits back. The text after `:c-` names the
field:

```citry-html
{# Show State.query in the input #}
<input :c-query>

{# Also update State.query and call `refresh` as the user types #}
<input :c-query="refresh">

{# Wait for 300 ms without typing before each call #}
<input :c-query.debounce.300ms="refresh">
```

The State class declares the field, and the handler reads the updated value:

```citry
class Search(Component):
    class State:
        query: str

    class Events:
        def refresh(self, state):
            print(state.query)  # the latest input
```

Citry picks the right way to fill each kind of field: `value` for a text
input, `checked` for a checkbox, the selected options for a `<select>`.
`<select multiple>` binds to a `list[str]`.

`:c-*` works on `<input>`, `<textarea>`, `<select>`, and custom elements.
For a two-way binding on a custom element, name the event it fires when its
value changes with the `.on:<event>` modifier. Other elements are an error
when the template loads:

```citry-html
{# ❌ A <div> has no value to bind #}
<div :c-query="refresh"></div>

{# ❌ Not allowed on a component tag #}
<c-SearchBox :c-query="refresh" />
```

A child component binds its own State in its own template. To share a
browser value with a child, pass it as a
[Vue prop](/concepts/client-interactivity/#pass-props-to-a-child).

Read [`:c-<field>` bindings](/events/bindings/#bind-controls-to-state) for
which input types are supported in which direction, and
[Event state](/events/state/) for declaring State.

## `#c-key` { #c-key }

When an event handler renders a list again, Vue matches old and new items by
position. If the list was reordered, an open panel or a half-typed field can
end up on the wrong row. `#c-key` gives each item a value that Vue uses to
match it instead:

```citry-html
<c-for each="task in tasks">
  <c-TaskRow
    #c-key="task.id"
    c-task="task"
  />
</c-for>
```

The value is a Python expression. Use something that identifies the record
and does not change, such as a database id, and keep keys unique within
the list.

On a page that uses Vue, a component that `<c-for>` repeats must have a
`#c-key`. A missing, `None`, or duplicate key makes the render fail. On an
HTML element the key is optional, and `None` means no key. `0` and `""` are
real keys.

`#c-key` is not an attribute. It never reaches the HTML or the component's
inputs. Write it directly on an HTML element or a component tag. It fails in
`c-bind` and on `<c-if>` or `<c-for>`:

```citry-html
{# Fails when the page renders #}
<article c-bind="{'#c-key': task.id}"></article>

{# Fails when the template loads #}
<c-if cond="task.visible" #c-key="task.id">...</c-if>
```

To let the parent choose the key, accept it as an input and write `#c-key`
in the component's own template:

```citry-html
{# Inside TaskRow; row_key is an input #}
<article #c-key="row_key">
  {{ task.title }}
</article>
```

See [`#c-key` for list items](/events/actions/#keep-list-items-matched-to-their-records)
for how keys behave when a handler renders the list again.

## `#c-ignore` { #c-ignore-keep-contents-that-a-library-manages }

A chart, map, or rich-text editor library changes the elements you give it.
When an event handler renders the component again, Vue resets those elements
to what the template describes and undoes the library's work. Put
`#c-ignore` on the element that holds the library's elements:

```citry-html
<div class="chart" ref="chart" #c-ignore>
  <canvas></canvas>
  <p class="caption">{{ caption }}</p>
</div>
```

The server renders the contents once. After that, the browser keeps those
same elements while the component stays on the page, even when `caption`
changes. The `#c-ignore` element itself still updates: its attributes and
bindings, such as `ref` or `:class`, change as usual. Reach the contents from
component JavaScript through that element, for example
`this.$refs.chart.querySelector("canvas")`.

The contents are rendered once as plain HTML. They can hold HTML, `{{ }}`
expressions, `<c-if>`, `<c-for>`, and `<c-raw>`. A component, a slot, or a
Vue binding inside would never run, and a `ref` inside would never connect,
so the template fails when it loads. Put the `ref` on the `#c-ignore`
element and find the child from there:

```citry-html
{# Fails: @click would never run inside #c-ignore #}
<div #c-ignore>
  <button @click="zoom();">Zoom</button>
</div>

{# Works: the button is outside the kept contents #}
<button @click="zoom();">Zoom</button>
<div ref="chart" #c-ignore>
  <canvas></canvas>
</div>
```

In a list, add `#c-key` too. Otherwise the kept contents stay in place when
rows reorder, and a row can show another row's chart:

```citry-html
<c-for each="chart in charts">
  <div #c-key="chart.id" #c-ignore>
    <canvas></canvas>
  </div>
</c-for>
```

On a page without Vue, `#c-ignore` does nothing and the element renders as
written. The rules still apply, so the template keeps working if the page
later uses Vue.

## Less common rules

### Keep a `c-` prefix

Citry removes exactly one leading `c-`. To output an attribute named
`c-feature`, add a second `c-`, or set the name through `c-bind`, which keeps
keys as written:

```citry-html
<!-- enabled = True -->
<div c-c-feature="enabled"></div>
<div c-bind="{'c-feature': enabled}"></div>
<!-- Both render: <div c-feature></div> -->
```

### Names ignore case

HTML attribute names ignore case, so `ID` and `id` are the same attribute.
When two `c-bind` mappings set `ID` and `id`, the later value wins, and the
attribute keeps the first spelling and position. `CLASS` and `class` values
are joined like any `class`. Writing two spellings directly, such as `ID`
with `id` or `ID` with `c-id`, is a parse error.

This applies to HTML elements and `<c-element>`, where `IS`, `c-IS`, and a
`c-bind` key `Is` all set the `is` input. Component inputs are Python
keyword arguments, so their names keep their case. `<c-component>` requires
lowercase `is` or `c-is`.

### `c-bind` on built-ins

Most built-in tags, including [`<c-if>`][c-if] and [`<c-for>`][c-for], do
not accept `c-bind`. Put it on the HTML element or component tag inside.
`<c-slot>` and `<c-fill>` accept it to choose a slot and pass its data; see
[`c-bind` on slots](/concepts/slots/#spread-slot-and-fill-settings).

### `:c-*` and `type`

When the input's `type` comes from `c-type` or `c-bind`, Citry checks the
binding against the rendered `type`, and the render fails if the binding
cannot use it. When it comes from a Vue `:type`, the browser checks each new
type and reports an error for one it cannot bind. The editor also reports
unsupported elements it can see in the template. See
[Elements you can bind](/events/bindings/#which-elements-you-can-bind).

### Where `#c-ignore` fails

Each of these fails with a message that says what to change:

- A component tag: put `#c-ignore` on an element in the component's
  template.
- `<c-element>`: write a plain HTML tag.
- On or inside `<svg>` or `<math>`: put it on an HTML element around it.
- `<table>`, `<thead>`, `<tbody>`, `<tfoot>`, `<tr>`, or `<colgroup>`: put
  it on a `<div>` around the table, or on a `<td>` or `<th>`.
- An element with no child elements to keep, such as `<br>`,
  `<textarea>`, `<script>`, `<style>`, or `<title>`: remove it.

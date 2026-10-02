---
title: Vue in templates
description: Add immediate browser behavior to Citry component templates with Vue directives and expressions.
---

# Vue in templates

Some parts of a page should react the moment the user acts: a click opens a
panel, typing updates a preview, a button counts up. Waiting for the server to
render again would be slow and unnecessary. For these, write
[Vue](https://vuejs.org/){: target="_blank" rel="noopener"} attributes in the
component's template. They run in the browser.

Citry adds Vue to the page as soon as one component on it uses Vue. You write
Vue's own attributes, such as `@click` and `v-show`, on the HTML in the
template, and define the component's browser data with `$component({...})` in
its JavaScript.

## Add a browser-side counter

Define the values the browser keeps in Vue's `data()` option:

```js
$component({
  data() {
    return { count: 0 };
  },
});
```

The template can read and change `count` directly:

```citry-html
<button type="button" @click="count += 1">
  Add one
</button>
<output v-text="count"></output>
```

Each copy of the component on the page keeps its own `count`.

## Start Vue data from Python

To start the browser data from a Python value, return it from
[`Component.js_data()`][citry.Component.js_data]. Each top-level key becomes
a value the template can read and change, like a `data()` value:

```citry
from citry import Component


class Counter(Component):
    class Kwargs:
        start: int = 0

    def js_data(self, kwargs: Kwargs, slots) -> dict[str, int]:
        return {"count": kwargs.start}

    template = """
      <button type="button" @click="count += 1">
        Add one
      </button>
      <output v-text="count"></output>
    """
```

The values must convert to JSON: strings, numbers, booleans, `None`, lists,
and dictionaries with string keys. Convert dates, model instances, and other
objects first. Name the keys the JavaScript way, such as `itemCount`.

A `js_data()` key must not reuse a name from `data()`, `setup()`, props,
injections, methods, or computed values. Citry reports the clash rather than
picking one.

## Use Vue directives

Vue attributes that start with `v-` are called directives. Vue also has short
forms for listening to events and setting attributes:

| Form | What it does |
| --- | --- |
| `v-text="label"` | Sets an element's text. |
| `v-show="open"` | Shows the element while the expression is true. |
| `v-if="ready"` | Adds or removes the element. |
| `v-for="item in items"` | Repeats the element in the browser. |
| `v-model="query"` | Keeps a form field and a value in step. |
| `@click="open = true"` | Short for `v-on:click="open = true"`. |
| `:disabled="busy"` | Short for `v-bind:disabled="busy"`. |

Modifiers stay in the attribute name. `@keydown.enter.prevent="submit()"`
listens for Enter and stops the browser's default action.

See Vue's
[template syntax guide](https://vuejs.org/guide/essentials/template-syntax.html){: target="_blank" rel="noopener"}
for every directive and modifier.

## Keep Python and Vue expressions apart

Citry runs `{{ ... }}` and `c-*` values as Python on the server. Vue runs
directive values as JavaScript in the browser. Both can sit in one template:

```citry-html
<section c-class="{'has-results': results}">
  <button type="button" @click="open = !open">
    Toggle details
  </button>
  <p v-show="open">{{ details }}</p>
</section>
```

Python sets the class and inserts `details` once. After the page loads, Vue
changes `open`. Define `open` in `data()`, `setup()`, or `js_data()`.

A Vue expression cannot see Python names. A common first attempt inside a
`c-for` loop reads the loop name from Vue, and no item gets a title:

```citry-html
<!-- Wrong: Vue looks for `item` in browser data. -->
<li c-for="item in items" :title="item">{{ item }}</li>

<!-- Right: Python sets `title` for each item. -->
<li c-for="item in items" c-title="item">{{ item }}</li>
```

`citry check` and the editor report the first form. They also report it when
the browser data has its own `item`: then every item shows that one value,
and nothing fails. When Vue needs the value too, for example in a `v-show`
that changes later, send it with `js_data()` or loop with Vue's `v-for`.

## Choose `v-for` or `<c-for>`

Use `v-for` and `v-if` for HTML that the browser adds, removes, or repeats
inside one component:

```citry-html
<ul>
  <li v-for="item in items" :key="item.id" v-text="item.label"></li>
</ul>
```

Use `<c-for>` and `<c-if>` when the loop or condition creates Citry
components. Only Python creates Citry components, so a `v-for` cannot repeat
one.

## Combine `:class` and `:style` with `c-class` and `c-style`

`:class` adds to an element's classes rather than replacing them. Vue joins
it with `class`, and Citry joins it with `c-class` the same way:

```citry-html
<article
  class="card"
  c-class="{'card--done': task.completed}"
  :class="{ 'card--dragging': dragging }"
>
  ...
</article>
```

The card starts as `card card--done`, and Vue adds `card--dragging` while
`dragging` is true. `:style` works the same way with `style` and `c-style`.
Vue applies `:style` last, so it wins when both set the same property.

Every other attribute must be set in one place. Setting it from Python and
from Vue, such as `c-title` with `:title`, fails when the template loads:

```citry-html
<!-- Fails: Python and Vue both set `title`. -->
<a c-title="label" :title="hint">...</a>
```

Keep only `c-title` when Python decides the value. Keep only `:title` when
the browser should change it later, and send the starting value with
`js_data()`.

## Use Vue directives on a component tag

A Citry component tag accepts these Vue directives:

| Directive | What it does on a component tag |
| --- | --- |
| `:name`, `v-bind` | Passes a Vue prop to the child. |
| `@event`, `v-on` | Listens for an event the child emits. `v-on="listeners"` adds every listener in an object. |
| `v-if`, `v-else-if`, `v-else` | Adds or removes the component. |
| `v-model` | Passes a value and updates it when the child asks. |
| `v-show` | Hides or shows the child's root element. |
| A custom directive | Runs on the child's root element. |

### Pass browser data to a child

A child component has its own browser data. Pass it a value from the parent
with a Vue prop:

```citry-html
<c-StatusBadge :status="currentStatus" />
```

`currentStatus` comes from the parent's `data()`, `setup()`, or `js_data()`.
The child declares `status` as a prop. See
[Client interactivity](/concepts/client-interactivity/) for props, events,
and slots.

Content you pass into a child's slot still reads the data of the component
that wrote it. A slot's fallback content reads the child's data.

### Add or remove a component in the browser

`v-if` works on a component tag as on an element, and one chain can mix
both:

```citry-html
<c-OrderSummary v-if="step === 'review'" />
<p v-else-if="step === 'empty'">Your cart is empty.</p>
<c-CheckoutForm v-else />
```

Python still renders every component in the chain, so the browser can switch
between them without asking the server. When Python should decide whether a
component exists at all, use `<c-if>`.

### Bind a value with `v-model`

`v-model` on a component tag passes the value as the `modelValue` prop. It
updates the value when the child emits `update:modelValue`:

```citry-html
<c-SearchField v-model="query" />
```

These are Vue props, not Python inputs, so the child declares them in its
`$component` options, not in `Kwargs`:

```js
$component({
  props: ["modelValue"],
  emits: ["update:modelValue"],
});
```

```citry-html
<input
  :value="modelValue"
  @input="$emit('update:modelValue', $event.target.value)"
/>
```

An argument names a different prop. Modifiers reach the child in a
`<name>Modifiers` prop:

```citry-html
<c-TitleEditor v-model:title.trim="pageTitle" />
```

Here the child declares `title` and `titleModifiers`, and emits
`update:title`. Vue applies `.trim` and `.number` itself. For `.lazy` or a
modifier of your own, the child reads the modifiers prop and decides.

### Apply `v-show` or a custom directive to the child

`v-show` and custom directives act on the element at the root of the child's
template:

```citry-html
<c-StatusBadge
  v-show="expanded"
  v-tooltip:top="statusHelp"
  :status="currentStatus"
/>
```

The component whose template contains the tag registers the custom directive:

```js
$component({
  directives: {
    tooltip: {
      mounted(el, binding) {
        el.title = binding.value;
      },
    },
  },
});
```

If nothing registers the name, Vue skips the directive silently, so check
the spelling when nothing happens.

The child's template must have exactly one root element. Wrap it in one
element, or put the directive on an element around the component tag.

## Repeat a component with `<c-for>`, not `v-for`

A natural first attempt at a list of components is `v-for`:

```citry-html
{# Fails: v-for cannot create Citry components #}
<c-StatusBadge
  v-for="item in items"
  :status="item.status"
/>
```

The template fails to compile with an error that says what to write
instead. Repeat the component with `<c-for>` over a Python value, and pass
each item's data as a Python input:

```citry-html
<c-for each="item in items">
  <c-StatusBadge c-status="item.status" />
</c-for>
```

## Show tab content written in another component { #keep-vue-bound-group-content-inside-the-groups-tag }

The page stops with an error when you pass content into a citry_ui group,
such as `CTabs`, from a separate component, and that content uses Vue data,
handlers, `v-model`, a `ref`, or an `@c-*` binding. For example, `TabLabels`
writes a tab:

```citry-html
<c-CTab value="one"><span v-text="label"></span></c-CTab>
```

and the page passes `TabLabels` into the group:

```citry-html
<!-- label belongs to TabLabels, but the tab list
     that shows the tab is not inside TabLabels -->
<c-CTabs default_value="one" aria_label="Example">
  <c-TabLabels />
</c-CTabs>
```

The group renders the tab inside its own tab list. Vue gives content the data
of the component that wrote it only inside that component, and the tab list
is not inside `TabLabels`. The error names the content, the component that
wrote it, and the line.

Write the content directly inside the group's tag:

```citry-html
<c-CTabs default_value="one" aria_label="Example">
  <c-CTab value="one"><span v-text="label"></span></c-CTab>
  <c-CTabPanel value="one">Details</c-CTabPanel>
</c-CTabs>
```

Alternatively, set `transparent = True` on the component that writes the
content, such as `TabLabels`. A transparent component renders its content in
place, as if the page had written it inside the group's tag.

Content that shows only Python values, such as `{{ title }}`, works from a
separate component.

## Vue features that Citry does not support

Each of these fails with an error that says what to use instead.

### Event modifiers that Vue does not have

Vue has no `.outside`, `.window`, `.document`, `.debounce`, or `.throttle`
event modifier. It would read one as a key name and the listener would never
run, so the template fails when it loads:

```citry-html
{# Fails: Vue has no .outside modifier #}
<div @click.outside="open = false;">...</div>
```

For a click outside, add a `click` listener to `document` in `mounted()` and
remove it in `unmounted()`. For a Python event handler, `@c-*` attributes
accept `.debounce` and `.throttle`; see
[Bind events in templates](/events/bindings/).

### `v-once` and `v-memo`

The template fails when it loads. Compute a fixed value once in `data()`. To
keep an element's contents as the server first rendered them, use
[`#c-ignore`](/syntax/dynamic-attributes/#c-ignore-keep-contents-that-a-library-manages).

### `<Teleport>`, `<Transition>`, `<Suspense>`, and `<KeepAlive>`

When the page uses Vue, `serialize()` or `str()` on the render raises
`ValueError` with an "unsupported Vue helper" message. On a page without
Vue, the tag is written out as plain HTML and does nothing.

## Less common rules for Vue on component tags

### Directives a component tag rejects

The template fails to compile when a component tag has one of these:

| Instead of | Write |
| --- | --- |
| `v-slot` or `#name` | `<c-fill name="...">` inside the component tag |
| `v-html`, `v-text` | A prop or a fill that the child renders |
| `v-if`, `v-else-if`, `v-else`, or `v-show` with an argument or modifiers | The directive without them |
| `.name` or `v-bind.prop` | A prop, `:name="..."` |
| `v-cloak`, `v-pre` | The directive on an element in the child's template |
| `v-once`, `v-memo` | Nothing: they are not supported on elements either |
| `v-If` or another capitalized built-in name | The lowercase name |

It also fails when `v-if`, `v-else-if`, `v-show`, or `v-model` has no
expression, or when `v-else` has one.

### Directives from `c-bind` or with a `c-` prefix

A directive from `c-bind`, or written with a `c-` prefix such as `c-v-if`,
fails when the page renders. Its expression must be written in the template.

### Vue on built-in tags

`<c-element>` renders a plain HTML element, so every Vue directive works on
it. A built-in tag that renders only its content, such as `<c-provide>`,
accepts no Vue syntax.

`<c-slot>` accepts no Vue syntax either. Its attributes other than `name`
and `required` become data that Python passes to the slot content, so a
`v-if` there would never reach the browser. Put `v-if` on a `<template>`
around the slot, or `v-show` on an element around it:

```citry-html
<template v-if="expanded">
  <c-slot name="details" />
</template>
```

### When `v-show` or a custom directive cannot find one root element

The render fails, with an error naming the directive and the child, when the
child's template has several top-level elements, a top-level `v-for`,
`<c-for>`, or `<c-slot>`, only text, or top-level HTML from `<c-raw>`. When
the child's root is another component with such a template, the browser
reports the error instead.

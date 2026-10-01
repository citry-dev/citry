---
title: Vue in templates
description: Add immediate browser behavior to Citry component templates with Vue directives and expressions.
---

# Vue in templates

Use Vue when part of a component should respond immediately in the browser. A
click can open a panel, an input can update a preview, and a button can change
local state without asking Python to render again.

Citry loads one pinned Vue runtime when the page contains an interactive
component. Write native Vue directives on the HTML in the component template,
and register that component's browser state with `$component({...})`.

## Add a browser-side counter

Define local values with Vue's `data()` option:

```js
$component({
  data() {
    return { count: 0 };
  },
});
```

The component template can read and change `count` directly:

```citry-html
<button type="button" @click="count += 1">
  Add one
</button>
<output v-text="count"></output>
```

Each rendered component instance receives its own `count` value.

## Use native Vue directives

Vue directives begin with `v-`. Vue also provides short forms for event and
attribute bindings:

| Form | What it does |
| --- | --- |
| `v-text="label"` | Inserts text into an element. |
| `v-show="open"` | Shows an element when an expression is truthy. |
| `v-if="ready"` | Adds or removes an element. |
| `v-for="item in items"` | Repeats browser-owned markup. |
| `v-model="query"` | Keeps a form control and a value in step. |
| `@click="open = true"` | Short for `v-on:click="open = true"`. |
| `:disabled="busy"` | Short for `v-bind:disabled="busy"`. |

Most of these also work on a Citry component tag. See
[Use Vue directives on a component tag](#use-vue-directives-on-a-component-tag).

Vue modifiers stay in the attribute name. For example,
`@keydown.enter.prevent="submit()"` listens for Enter and prevents the
browser's default action.

Alpine had event modifiers that Vue does not, such as `.outside`,
`.window`, `.document`, `.debounce`, and `.throttle`. Vue would read one
as a key name, and the listener would never run, so the template fails
when it loads with a message that names the Vue way to do the same thing:

```citry-html
{# Fails: Vue has no .outside modifier #}
<div @click.outside="open = false;">...</div>
```

For a click outside, add a `click` listener to `document` in `mounted()`
and remove it in `unmounted()`. For a server event handler, the `@c-*`
bindings accept `.debounce` and `.throttle`; see
[Bind events in templates](/events/bindings/).

See the [Vue template syntax](https://vuejs.org/guide/essentials/template-syntax.html){:
target="_blank" rel="noopener"} for directive forms and modifiers.

A few Vue features do not work in a `Component.template`:

- Vue's built-in helper components `<Teleport>`, `<Transition>`,
  `<Suspense>`, and `<KeepAlive>` stop the template with an
  unsupported-helper diagnostic.
- `v-once` and `v-memo` make the template fail when it loads. Keep a
  value fixed by not changing it, or compute it once in `data()`. To keep
  an element's contents as the server first rendered them, use
  [`#c-ignore`](/syntax/dynamic-attributes/#c-ignore-keep-contents-that-a-library-manages).

## Keep Python and JavaScript expressions separate

Citry evaluates `{{ ... }}` and `c-*` expressions in Python while rendering.
Vue evaluates directive values in JavaScript in the browser:

```citry-html
<section c-class="{'has-results': results}">
  <button type="button" @click="open = !open">
    Toggle details
  </button>
  <p v-show="open">{{ details }}</p>
</section>
```

Here Python decides the class and inserts `details`. Vue owns `open` after the
page loads. Define `open` in `data()`, `setup()`, or Python `js_data()`.

A Vue binding cannot see Python variables. Inside a `c-for` loop the
first attempt often reads the loop variable from Vue, and no item gets a
`title`:

```citry-html
<!-- Vue looks up `item` in browser state, which has none. -->
<li c-for="item in items" :title="item">{{ item }}</li>

<!-- Python sets `title` while it renders each item. -->
<li c-for="item in items" c-title="item">{{ item }}</li>
```

`citry check` and the editor report the first form. They also report it
when the component's browser data has a value named `item`: Vue then shows
that value on every item instead of the loop value, and nothing fails. When
Vue needs the value too, such as for a `v-show` that changes later, send it
to the browser with `js_data()` or loop with Vue's `v-for` instead.

## Combine `:class` and `:style` with `c-class` and `c-style`

A `:class` binding adds to the element's other classes instead of
replacing them. Vue joins it with a static `class`, and Citry joins it
with a `c-class` the same way:

```citry-html
<article
  class="card"
  c-class="{'card--done': task.completed}"
  :class="{ 'card--dragging': dragging }"
>
  ...
</article>
```

The card first shows `card card--done`, and Vue adds `card--dragging`
while `dragging` is true. The classes from `class` and `c-class` come
first. `:style` works the same way with `style` and `c-style`, and the
bound style is applied last, so it wins for a property both set.

Any other attribute has one owner. Setting the same attribute from Python
and from Vue, such as `c-title` together with `:title`, fails when the
template loads, and `citry check` reports it:

```citry-html
<!-- Fails: Python and Vue both set `title`. -->
<a c-title="label" :title="hint">...</a>

<!-- Python decides the title. -->
<a c-title="label">...</a>
```

To let the browser change the title later, keep `:title` and send the
starting value with `js_data()`.

## Seed Vue state from Python

Return JSON-serializable values from
[`Component.js_data()`][citry.Component.js_data]. Citry installs each top-level
key as a reactive member of that component's Vue instance:

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

Use strings, numbers, booleans, `None`, lists, and string-keyed dictionaries
made from those values. Convert dates, model instances, and other Python
objects first. Use JavaScript names such as `itemCount` for the top-level keys.

Local `data()`, `setup()`, props, injections, methods, and computed values must
use different names from `js_data()` keys. Citry reports a collision instead
of choosing one value.

## Choose the right kind of loop

Use `v-for` and `v-if` for browser-owned HTML inside one component:

```citry-html
<ul>
  <li v-for="item in items" :key="item.id" v-text="item.label"></li>
</ul>
```

Use Python `<c-for>` and `<c-if>` when a loop or condition must create Python
Citry component instances. A browser `v-for` may render Vue-owned children,
but it does not run Python or create server component instances.

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

### Add or remove a component in the browser

`v-if` works on a component tag as it does on an element, and one chain
can mix components and elements:

```citry-html
<c-OrderSummary v-if="step === 'review'" />
<p v-else-if="step === 'empty'">Your cart is empty.</p>
<c-CheckoutForm v-else />
```

Python still renders every component in the chain, so the browser can
switch branches without asking the server. When Python should decide
whether a component exists at all, use `<c-if>` instead.

### Bind a value with `v-model`

`v-model` on a component tag passes the value as the `modelValue` prop and
updates it when the child emits `update:modelValue`:

```citry-html
<c-SearchField v-model="query" />
```

These are Vue props, not Python kwargs, so the child declares them in its
`$component` options rather than in `Kwargs`:

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

An argument names another prop, and modifiers reach the child in a
`<name>Modifiers` prop. Vue applies `.trim` and `.number` to the value the
child emits. For `.lazy` or a modifier of your own, the child reads the
modifiers prop and decides:

```citry-html
<c-TitleEditor v-model:title.trim="pageTitle" />
```

Here the child declares `title` and `titleModifiers`, and emits
`update:title`.

### Apply `v-show` or a custom directive to the child's root

`v-show` and a custom directive run on the element the child renders at
its root:

```citry-html
<c-StatusBadge
  v-show="expanded"
  v-tooltip:top="statusHelp"
  :status="currentStatus"
/>
```

The component that writes the tag registers the custom directive in its
own options:

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

If nothing registers that name, Vue skips the directive without an error,
so check the spelling when nothing happens.

The child must render one root element. If its template has several
top-level elements, a `v-for`, `<c-for>`, or `<c-slot>` at the top level,
only text, or HTML from `<c-raw>` there, the render fails with an error that
names the directive and the child. When the child's root is another
component with such a template, the browser reports the error instead. Wrap
the child's template in one element, or put the directive on an element
around the component tag.

### Directives a component tag rejects

A natural first attempt at a list of components is `v-for`:

```citry-html
{# Fails: v-for cannot create Citry components #}
<c-StatusBadge
  v-for="item in items"
  :status="item.status"
/>
```

The template stops compiling, and the error names the directive and what to
write instead. Python creates Citry components, so repeat them with
`<c-for>` over a Python value, and pass each item's data as a Python kwarg:

```citry-html
<c-for each="item in items">
  <c-StatusBadge c-status="item.status" />
</c-for>
```

Other rejected forms include:

| Instead of | Write |
| --- | --- |
| `v-slot` or `#name` | `<c-fill name="...">` inside the component tag |
| `v-html`, `v-text` | A prop or a fill that the child renders |
| `v-if`, `v-else-if`, `v-else`, or `v-show` with an argument or modifiers | The directive without them |
| `.name` or `v-bind.prop` | A prop, `:name="..."` |
| `v-cloak`, `v-pre` | The directive on an element in the child's template |
| `v-once`, `v-memo` | Nothing: they are not supported on elements either |
| `v-If` or another capitalized built-in name | The lowercase name |

The template also stops compiling when `v-if`, `v-else-if`, `v-show`, or
`v-model` has no expression, or when `v-else` has one. A directive passed
through `c-bind`, or written with a `c-` prefix such as `c-v-if`, fails when
the page renders: its expression must be written in the template.

`<c-element>` renders a plain HTML element, so every Vue directive works
on it. A transparent component such as `<c-provide>` renders its content in
place, so its tag accepts no Vue syntax at all.

`<c-slot>` accepts no Vue syntax either. Its attributes other than `name`
and `required` become data that Python passes to the fill, so a `v-if` or
`:item` there would never reach the browser, and the template fails to
compile. The error names what to write instead. For a browser-side
condition, put `v-if` on a `<template>` around the slot, or `v-show` on an
element around it:

```citry-html
<template v-if="expanded">
  <c-slot name="details" />
</template>
```

## Read state inside the component that owns it

The component that authors a Vue expression supplies its names. A child has
its own data, props, setup bindings, and Python-seeded values. With
`currentStatus` declared in the parent's `data()` or `setup()`, pass it to a
child with a native Vue prop:

```citry-html
<c-StatusBadge :status="currentStatus" />
```

A fill keeps the Vue expression context of the template that supplied it. A
slot fallback uses the receiving component's context. See
[Client interactivity](/concepts/client-interactivity/) for props, events,
slots, and server-render callbacks.

### Keep Vue-bound group content inside the group's tag

The page stops with an error when content you pass into a citry_ui group
such as `CTabs` is written in a separate, ordinary component and uses Vue
data, handlers, `v-model`, a `ref`, or a Citry `@c-*` binding. For example,
`TabLabels` writes the tab content:

```citry-html
<c-CTab value="one"><span v-text="label"></span></c-CTab>
```

and the page passes it into the group:

```citry-html
<!-- label is read in TabLabels, but the tab list
     that shows the content is not inside TabLabels -->
<c-CTabs default_value="one" aria_label="Example">
  <c-TabLabels />
</c-CTabs>
```

The group stores the content and renders it inside its own tab list. Vue
gives content its author's data only inside the author's component tree,
and the tab list is not inside `TabLabels`. The error names the content,
the component that wrote it, and the line.

Write the content inside the group's tag, or make the grouping component
transparent:

```citry-html
<c-CTabs default_value="one" aria_label="Example">
  <c-CTab value="one"><span v-text="label"></span></c-CTab>
  <c-CTabPanel value="one">Details</c-CTabPanel>
</c-CTabs>
```

Content that shows only Python values, such as `{{ title }}`, also works
from a separate component.

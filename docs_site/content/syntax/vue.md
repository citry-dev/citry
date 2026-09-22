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

Vue modifiers stay in the attribute name. For example,
`@keydown.enter.prevent="submit()"` listens for Enter and prevents the
browser's default action.

See the [Vue template syntax](https://vuejs.org/guide/essentials/template-syntax.html){:
target="_blank" rel="noopener"} for directive forms and modifiers.

Citry currently compiles component templates to ordinary Vue VNodes. Vue's
built-in helper components are outside that compiled-template contract for now:
`<Teleport>`, `<Transition>`, `<Suspense>`, and `<KeepAlive>` are rejected with
an unsupported-helper diagnostic when they appear in a `Component.template`.

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

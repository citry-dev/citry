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
the component's `js`.

## Add a browser counter

In the component's `js`, call `$component({...})` and return the values the
browser keeps from a `data()` function, as in any Vue component. The
`template` holds the Vue attributes and can read and change `count`
directly:

```citry
from citry import Component


class Counter(Component):
    template = """
      <button type="button" @click="count += 1">
        Add one
      </button>
      <output v-text="count"></output>
    """

    js = """
      $component({
        data() {
          return { count: 0 };
        },
      });
    """
```

Each copy of the component on the page keeps its own `count`.

## Set data from Python

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

This component needs no `js`: the `js_data()` values are enough to turn on
Vue.

The values must convert to JSON: strings, numbers, booleans, `None`, lists,
and dictionaries with string keys. Convert dates, model instances, and other
objects first. Name the keys the JavaScript way, such as `itemCount`.

A `js_data()` key must not reuse a name from `data()`, `setup()`, props,
injections, methods, or computed values. Citry reports the clash rather than
picking one.

## Vue `v-*` directives { #use-vue-directives }

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

Write directive names in lowercase. On an HTML element, `V-IF` or `v-If`
does not work, and the element always shows: Vue reads `V-IF` as a plain
attribute, and `v-If` as a custom directive named `If`. On a component
tag, both fail when the template loads.

See Vue's
[template syntax guide](https://vuejs.org/guide/essentials/template-syntax.html){: target="_blank" rel="noopener"}
for every directive and modifier.

## Tell Python from Vue

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

## `c-*` with `:` bindings { #combine-class-and-style-with-c-class-and-c-style }

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

## Vue on component tags { #use-vue-directives-on-a-component-tag }

A Citry component tag accepts these Vue directives:

| Directive | What it does on a component tag |
| --- | --- |
| `:name`, `v-bind` | Passes a Vue prop to the child. |
| `@event`, `v-on` | Listens for an event the child emits. `v-on="listeners"` adds every listener in an object. |
| `v-if`, `v-else-if`, `v-else` | Adds or removes the component. |
| `v-model` | Passes a value and updates it when the child asks. |
| `v-show` | Hides or shows the child's root element. |
| A custom directive | Runs on the child's root element. |

Other directives, such as `v-for` and `v-slot`, fail on a component tag;
see [Rejected directives](#rejected-directives).

### `:prop` on a child { #pass-data-to-a-child }

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

### `v-if` on a child { #add-or-remove-a-child }

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

### `v-model` on a child { #bind-with-v-model }

`v-model` on a component tag passes the value as the `modelValue` prop. It
updates the value when the child emits `update:modelValue`. Here `query` is
the parent's browser data:

```citry-html
<c-SearchField v-model="query" />
```

`modelValue` is a Vue prop, not a Python input, so `SearchField` declares
it, along with the `update:modelValue` event, in `$component({...})` in its
`js`, not in `Kwargs`:

```citry
from citry import Component


class SearchField(Component):
    template = """
      <input
        :value="modelValue"
        @input="$emit('update:modelValue', $event.target.value)"
      />
    """

    js = """
      $component({
        props: ["modelValue"],
        emits: ["update:modelValue"],
      });
    """
```

An argument names a different prop. Modifiers reach the child in a
`<name>Modifiers` prop:

```citry-html
<c-TitleEditor v-model:title.trim="pageTitle" />
```

Here the child declares `title` and `titleModifiers`, and emits
`update:title`. Vue applies `.trim` and `.number` itself. For `.lazy` or a
modifier of your own, the child reads the modifiers prop and decides.

### `v-show` on a child { #use-v-show-on-a-child }

`v-show` and custom directives act on the element at the root of the child's
template. The parent registers a custom directive in its own `js`. Here
`OrderPanel` registers `tooltip` and uses it on the `StatusBadge` in its
template:

```citry
from citry import Component


class OrderPanel(Component):
    template = """
      <c-StatusBadge
        v-show="expanded"
        v-tooltip:top="statusHelp"
        :status="currentStatus"
      />
    """

    js = """
      $component({
        data() {
          return {
            expanded: true,
            statusHelp: "Updated every hour",
            currentStatus: "shipped",
          };
        },
        directives: {
          tooltip: {
            mounted(el, binding) {
              el.title = binding.value;
            },
          },
        },
      });
    """
```

If nothing registers the name, Vue skips the directive silently, so check
the spelling when nothing happens.

The child's template must have exactly one root element. Wrap it in one
element, or put the directive on an element around the component tag.

## Repeat a component

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

## Customize Vue { #customize-the-vue-app }

Citry creates the Vue app for you, so there is no `createApp()` call to
configure. To add something to every component, such as a directive that
any template can use, write a Vue plugin and register it with
[`Citry.vue.use(plugin, ...options)`](/reference/browser-apis/#citry-vue-use).
Citry installs it with `app.use(plugin, ...options)` on every Vue app it
creates on the page, before the app mounts.

Here a plugin adds a `v-autofocus` directive. Put it in a script file:

```js
// static/vue-plugins.js
Citry.vue.use({
  install(app) {
    app.directive("autofocus", {
      mounted(el) {
        el.focus();
      },
    });
  },
});
```

Load that file with `defer` in the page's `<head>`. It then runs after
Citry's runtime loads and before Citry creates the first Vue app:

```html
<script defer src="/static/vue-plugins.js"></script>
```

Any component template can now write `<input v-autofocus />`. An extension
can add the same script for every page through `ctx.early_scripts`; see
[Add scripts and styles](/advanced/extensions/#add-scripts-and-stylesheets-to-a-page).

In `install(app)`, a plugin can:

- Register a directive for every template with `app.directive()`.
- Register a component with `app.component()`, and use it in a template by
  its name, such as `<my-widget>`. Give it a `render()` function written with
  `Citry.vue.h`. A `template` string does not work, because Citry's browser
  build of Vue cannot compile templates.
- Give a value to every component with `app.provide()`. A component reads it
  with `inject` in `$component({...})`.
- Handle errors from every component with `app.config.errorHandler`, for
  example to send them to an error tracker. Citry passes each error to your
  handler instead of the browser console, so log it there yourself. After
  an error, Citry still stops sending server updates to that app.
- Add a value or function that every template can read with
  `app.config.globalProperties`.

Keep these limits in mind when you write a plugin:

- Call `Citry.vue.use()` before Citry creates its first Vue app. A later
  call throws an `Error`, because that app would run without the plugin.
- A page can run several Vue apps, for example when
  [HTML fragments](/advanced/html-fragments/) add components to it. The
  plugin's `install` runs once for each app, and each app has its own
  `app.provide()` values. For one value that every app shares, create it
  outside `install` and provide that same object.
- `app.config.compilerOptions` has no effect, because Citry compiles
  templates on the server. `app.config.warnHandler` is never called,
  because the Vue build Citry loads leaves out Vue's warnings.
- A plugin cannot add a mixin to components: `$component({...})` rejects
  `mixins` and `extends` with an error. Define the data, methods, and
  computed values in the options directly.
- Citry adds [`$loading`](/reference/browser-apis/#loading) and
  [`$error`](/reference/browser-apis/#error) to `globalProperties`. A plugin
  that sets either name replaces Citry's version, and `$loading()` and
  `$error()` stop working in every template. Give your properties other
  names.
- If the plugin's `install` throws, that Vue app does not start, and the
  error shows as a page error.

## What is not supported

Each of these fails, except where noted below.

### Alpine modifiers { #unknown-modifiers }

`.outside`, `.window`, `.document`, `.debounce`, and `.throttle` are Alpine
modifiers. Citry 0.6.0 replaced Alpine with Vue, which has none of these
modifiers. Citry rejects them when the template loads, and the error says
how to write the same behavior in Vue:

```citry-html
{# Fails: .outside is an Alpine modifier #}
<div @click.outside="open = false;">...</div>
```

For a click outside, add a `click` listener to `document` in the
`mounted()` option of `$component({...})` in the component's `js`, skip
clicks where `this.$el.contains(event.target)`, and remove the listener in
`unmounted()`. For a Python event handler, `@c-*` attributes accept
`.debounce` and `.throttle`; see
[Bind events in templates](/events/bindings/). The
[0.6.0 upgrade guide](/guides/upgrading-to-0-6-0/#rewrite-alpine-modifiers)
covers the rest of the move from Alpine.

### `v-once` and `v-memo`

The template fails when it loads. Compute a fixed value once in `data()`. To
keep an element's contents as the server first rendered them, use
[`#c-ignore`](/syntax/dynamic-attributes/#c-ignore-keep-contents-that-a-library-manages).

### Vue helper components

When the page uses Vue, `serialize()` or `str()` on the render raises
`ValueError` with an "unsupported Vue helper" message. On a page without
Vue, the tag is written out as plain HTML and does nothing.

## Fill group components { #keep-vue-bound-group-content-inside-the-groups-tag }

Some Citry UI components, such as `CTabs`, collect the content you put inside
them and render it in their own layout. If another component writes that
content, and the content uses Vue data, a Vue event listener, `v-model`, a
`ref`, or an `@c-*` binding, the page stops with an error. For example,
`TabLabels` writes a tab that shows its own browser data, `label`:

```citry
from citry import Component


class TabLabels(Component):
    template = """
      <c-CTab value="one">
        <span v-text="label"></span>
      </c-CTab>
    """

    js = """
      $component({
        data() {
          return { label: "Overview" };
        },
      });
    """
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

Write the content directly inside the group's tag, in the page component's
template, and define `label` in that component's `js`:

```citry-html
<c-CTabs default_value="one" aria_label="Example">
  <c-CTab value="one">
    <span v-text="label"></span>
  </c-CTab>
  <c-CTabPanel value="one">Details</c-CTabPanel>
</c-CTabs>
```

Alternatively, set `transparent = True` on the component that writes the
content, such as `TabLabels`. A transparent component renders its content in
place, as if the page had written it inside the group's tag.

Content that shows only Python values, such as `{{ title }}`, works from a
separate component.

## Less common rules

### Rejected directives

A component tag accepts only the directives listed in
[Vue on component tags](#use-vue-directives-on-a-component-tag). The
directives below fail to compile on a component tag, and the error says
what to write instead:

| Directive on a component tag | Write instead |
| --- | --- |
| `v-for` | `<c-for>` around the tag; see [Repeat a component](#repeat-a-component) |
| `v-slot` or `#name` | `<c-fill name="...">` inside the component tag |
| `v-html`, `v-text` | A prop or a fill that the child renders |
| `v-cloak`, `v-pre` | The directive on an element in the child's template |
| `v-c-*`, `v-citry-*` | Another name: Citry keeps these for its own use |

`v-once` and `v-memo` are not supported anywhere in a template, on
elements or on component tags; see [above](#v-once-and-v-memo).

### Directives via `c-bind`

A directive from `c-bind`, or written with a `c-` prefix such as `c-v-if`,
fails when the page renders. Its expression must be written in the template.

### Vue on built-in tags

`<c-element>` renders a plain HTML element, so every Vue directive works on
it. A built-in tag that renders only its content, such as `<c-provide>`,
accepts no Vue syntax.

`<c-slot>` accepts no Vue syntax either, and the template fails to compile.
Its attributes other than `name` and `required` become data that Python
passes to the slot content, so a `v-if` there could never reach the browser.
Put `v-if` on a `<template>`
around the slot, or `v-show` on an element around it:

```citry-html
<template v-if="expanded">
  <c-slot name="details" />
</template>
```

### Several root elements

The render fails, with an error naming the directive and the child, when the
child's template has several top-level elements, a top-level `v-for`,
`<c-for>`, or `<c-slot>`, only text, or top-level HTML from `<c-raw>`. When
the child's root is another component with such a template, the browser
reports the error instead.

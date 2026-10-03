---
title: Component options
description: Give a Citry component browser state, methods, server data, and code that runs after each server render with $component().
---

# Component options

A component that reacts in the browser needs a few things of its own:
values that change when the user acts, methods the template calls, data
from Python to start with, or code that connects a chart to the HTML the
server sent. Put them in the component's `js`, in one call to
`$component({...})`.

`$component()` tells Citry how the component behaves in the browser. It
takes the same object of
[options](https://vuejs.org/api/#options-api){: target="_blank" rel="noopener"}
as a Vue component, and Citry applies it to every rendered copy of the
component.

This page covers the options for one component. To pass values between
components with `props` and `emits`, see
[Props and events](/vue/props-and-events/). To add something to every
component, see [Plugins and the Vue app](/vue/plugins/).

## Call `$component` once { #call-component-once }

Call `$component()` once, at the top level of the component's `js`:

- A `js` with no `$component()` call is fine. Its code runs, and
  [`js_data()`](#seed-browser-data-from-python) values still reach the
  template.
- A second call in the same script is ignored, without an error.
- A call that runs later, for example inside a `setTimeout` or an event
  listener, is too late. The page's Vue app does not start, so no
  component on the page responds, and the browser console shows an error.

Pass a function instead of an object when all you need is code that runs
after each server render; see
[`onServerRender`](#react-after-a-server-render).

## Data and methods { #data-and-methods }

[`data()`](https://vuejs.org/api/options-state.html#data){: target="_blank" rel="noopener"}
holds values that change in the browser,
[`computed`](https://vuejs.org/api/options-state.html#computed){: target="_blank" rel="noopener"}
derives values from them,
[`methods`](https://vuejs.org/api/options-state.html#methods){: target="_blank" rel="noopener"}
holds functions the template calls, and
[`watch`](https://vuejs.org/api/options-state.html#watch){: target="_blank" rel="noopener"}
runs code when a value changes:

```js
$component({
  data() {
    return { query: "" };
  },
  computed: {
    trimmed() {
      return this.query.trim();
    },
  },
  methods: {
    clear() {
      this.query = "";
    },
  },
  watch: {
    trimmed(value) {
      localStorage.setItem("last-query", value);
    },
  },
});
```

The template reads these by name, as in
`<button type="button" @click="clear">`.

Inside these functions, `this` is the component's Vue instance, the object
Vue creates for one rendered copy of the component. It also carries the
[`js_data()`](#seed-browser-data-from-python) values and the
[Events helpers](/reference/browser-apis/#component-events-helpers), such
as `$state`.

## `js_data()` initial data { #seed-browser-data-from-python }

To start the browser data from a Python value, return it from
[`Component.js_data()`][citry.Component.js_data]. Each top-level key
becomes a value Vue tracks, so the page updates when it changes. The
template reads it as `name`, and the
component's JavaScript reads and changes it as `this.name`:

```citry
from citry import Component


class Counter(Component):
    class Kwargs:
        start: int = 0

    def js_data(self, kwargs: Kwargs, slots) -> dict[str, int]:
        return {"count": kwargs.start}

    template = """
      <button type="button" @click="increment">
        Add one
      </button>
      <output v-text="count"></output>
    """

    js = """
      $component({
        methods: {
          increment() {
            this.count += 1;
          },
        },
      });
    """
```

Two counters on one page each get their own `count`. When the server
renders the component again, for example after an
[event handler](/events/) returns it, Citry updates these values in the
browser.

A component that only reads its `js_data()` values in the template needs
no `js`: the `js_data()` values are enough to turn on Vue.

Name the keys the JavaScript way, such as `itemCount`. The values must
convert to JSON, so convert dates, model instances, and other objects
first; see
[JS data must be JSON](/advanced/js-and-css-dependencies/#js-data-must-be-json).

Two kinds of key fail:

- A key that starts with `$` or `_`, or the key `citryId`. Vue and Citry
  already use these names. Rendering the component raises `ValueError`
  naming the component and the key, before any HTML is sent. Rename the
  key, for example `_count` to `count`.
- A key that reuses a name from the same component's `data()`, `setup()`,
  props, injections, methods, or computed values. Python cannot see those
  names, so the browser catches the clash: the component fails when it
  first appears on the page.

## `onServerRender` callback { #react-after-a-server-render }

Some code has to run again each time the server renders the component,
for example to draw a chart into the new HTML or to connect a non-Vue
widget to it. Put it in `onServerRender`:

```js
$component({
  onServerRender({ component }) {
    const canvas = component.$refs.chart;
    if (!(canvas instanceof HTMLCanvasElement)) return;

    // createChart comes from a charting library.
    const chart = createChart(canvas, component.points);
    return () => chart.destroy();
  },
});
```

Mark the element with a matching Vue `ref`:

```citry-html
<canvas ref="chart"></canvas>
```

`component` is the component's Vue instance, and `component.points` is a
`js_data()` value. Reach elements through a `ref`, as above, not through
`component.$el`. A Vue component can render one root element, several,
only text, or nothing, so `$el` is not always the element you expect.
Check the element's type before you use it.

Citry calls `onServerRender` once the component first appears on the
page, and again after each server render that updates it. A change made
only in the browser does not call it.

Return a cleanup function to undo the work. Citry calls it before the next
`onServerRender` call and when the component is removed. Returning
anything other than a function or nothing throws a `TypeError`, which the
browser console shows.

Passing a function, as in `$component(callback)`, is short for passing
`{ onServerRender: callback }`:

```js
$component(({ component }) => {
  component.$refs.input?.focus();
});
```

[Browser APIs](/reference/browser-apis/#on-server-render) lists
everything the callback receives, and how `async` callbacks work.

!!! note "Cleanup for watchers, listeners, timers, and promises"

    When Citry runs the cleanup, it also stops the watchers and effects
    the callback created before it returned, for example with
    `Citry.vue.watchEffect()`, and removes the listeners it added with the
    [`onEvent`](/reference/browser-apis/#on-server-render-on-event) member
    of its argument. Work that starts later, from a timer or after an
    `await`, is not stopped for you. Stop it in your cleanup function.

## What a render keeps { #what-a-render-keeps }

When an event handler returns the component and the server renders it
again, Citry updates the Vue component that is already on the page. It
does not create a new one:

- `data()` and `setup()` values keep what the browser set.
- `js_data()` values take the server's new values, replacing any change
  the browser made to them.
- Computed values update from the new values.
- `onServerRender` runs its cleanup, then runs again.

Vue creates a new component, which starts from `data()` again, when:

- the handler returns a different component in its place; see
  [`Render` another component](/events/actions/#swap-in-a-different-component);
- an element or component around it is created again, for example
  because its `:key` changed in the new render;
- the user reloads the page.

A text field the user is typing in keeps its text through a render in
most cases; see
[Keep typed input](/vue/server-rendering/#keep-what-the-user-typed-across-renders).

## Lifecycle hooks { #lifecycle-hooks }

[Vue's lifecycle hooks](https://vuejs.org/api/options-lifecycle.html){: target="_blank" rel="noopener"},
such as `mounted`, `updated`, and `unmounted`, work as in Vue. Citry also
uses some of them, and runs its own code around yours:

- `mounted` runs first, then the first
  [`onServerRender`](#react-after-a-server-render) call.
- In `beforeUnmount`, Citry first runs the `onServerRender` cleanup and
  removes the component's [`$onEvent`](/reference/browser-apis/#on-event)
  listeners, then calls yours. Vue's `unmounted` hook runs after that.

## Share helpers { #share-helpers }

Code outside `$component()` runs once, when the browser loads the script,
not once for each copy of the component. Use it for constants and helper
functions that every copy shares:

```js
const formatter = new Intl.NumberFormat("en", {
  style: "currency",
  currency: "EUR",
});

$component({
  methods: {
    price(amount) {
      return formatter.format(amount);
    },
  },
});
```

Each component's script runs inside its own function, so its top-level
names do not clash with other scripts on the page.

A value that should differ between copies belongs in `data()`. A
top-level variable is shared, so every copy changes the same one:

```js
// Wrong: all copies on the page share one `count`.
let count = 0;

$component({
  methods: {
    add() {
      count += 1;
    },
  },
});
```

```js
// Right: each copy gets its own `count`.
$component({
  data() {
    return { count: 0 };
  },
  methods: {
    add() {
      this.count += 1;
    },
  },
});
```

## Use `Citry.vue` { #use-citry-vue }

`Citry.vue` is the Vue library the page already loaded, so a component
script can use Vue's functions without an import: `ref`, `reactive`,
`computed`, `watch`, `nextTick`, `h`, and the rest.

Use `this` for the component's own values and methods. Use `Citry.vue`
for Vue's functions, mostly inside `setup()` and in shared helpers:

```js
$component({
  methods: {
    async open() {
      this.expanded = true;
      // Wait until Vue has shown the panel.
      await Citry.vue.nextTick();
      this.$refs.panel.focus();
    },
  },
});
```

`Citry.vue.use()` installs a Vue plugin on every Vue app Citry creates;
see [Plugins and the Vue app](/vue/plugins/#customize-the-vue-app).
[Browser APIs](/reference/browser-apis/#citry-vue) has the reference.

## Use `setup()` { #use-setup }

Vue's
[`setup()`](https://vuejs.org/api/composition-api-setup.html){: target="_blank" rel="noopener"}
works when it is synchronous and returns a plain object. Take the
Composition API functions from [`Citry.vue`](#use-citry-vue):

```js
$component({
  setup() {
    const selected = Citry.vue.ref(null);
    return { selected };
  },
});
```

An `async` `setup()`, or one that returns a render function, fails when
the component first appears, and the page's Vue app stops. Move async
work into a lifecycle hook such as `mounted`.

## `provide` and `inject` { #provide-and-inject }

A component can `provide` a value to every component inside it, which
reads it with `inject`. These are Vue's own options and are separate from
Citry's Python `<c-provide>`. See
[Vue `provide`/`inject`](/concepts/provide-and-inject/#provide-and-inject-in-client-code).

## Reserved names { #names-citry-reserves-on-the-component-instance }

Citry adds a few names to each component's Vue instance. Do not define a
`data()` key, `setup()` value, method, computed value, or injection with
one of these names:

- `$citryPrepared`, which holds the values Python computed for the
  template. Its contents can change between releases, so do not read it.
- `$citryEvents`, which connects `@c-*` attributes to the server.
- `$loading`, `$error`, `$state`, `$sendEvent`, and `$onEvent`, the
  [Events helpers](/reference/browser-apis/#component-events-helpers).
- Names that a Citry extension adds to templates, such as the i18n
  helpers.

If a component uses one of these names, it fails with an error naming it
when it first appears in the browser.

Do not name a prop, `data()` key, or method `citryId` either. Citry adds a
prop with that name to every component and replaces yours without an
error. Vue ignores a prop whose name starts with `$`, also without an
error. The rules for `js_data()` keys are in
[`js_data()` initial data](#seed-browser-data-from-python).

When your JavaScript needs a value from Python, return it from
[`js_data()`](#seed-browser-data-from-python) and read it as `this.name`
or `component.name`.

## Unsupported options { #unsupported-options }

Citry combines your options with the render function it generates from
the component's template, so a few Vue options do not apply:

- `mixins` and `extends` fail with an error that names the component.
  Write the data, methods, and computed values in the options directly.
- A `render` function or `template` option inside `$component()` is
  ignored, without an error. Citry builds the browser's render function
  from the component's Python `template`.

[Browser APIs](/reference/browser-apis/#component) lists every rule.

## Check JS code { #check-js-code }

The Citry editor extension and `citry check` read the code in `js`:

- In `$component()`, `this` has the component's type, including its
  `js_data()` keys, props, `data()`, methods, and computed values. See
  [Vue and component JS](/ide/vscode/#complete-vue-expressions-and-component-javascript).
- Reading `this.name` when the component has no such value is an error
  ([`citry.component-js.unknown-member`](/ide/diagnostics/#citry.component-js.unknown-member)).
  Citry reports it only when it can see all of the component's values in
  the source.
- `citry check --types` also reports TypeScript errors in the code. See
  [`check --types` typing](/advanced/cli/#check-types-with-typescript-and-ty).

## See also

- [Vue in Citry](/vue/) for how Python and Vue share a template.
- [Props and events](/vue/props-and-events/) for `props`, `emits`, and
  `$emit`.
- [Component JS and CSS](/advanced/js-and-css-dependencies/) for
  `js_file`, the JSON rules for `js_data()`, and component CSS.
- [Browser APIs](/reference/browser-apis/) for `$component`,
  `onServerRender`, and `Citry.vue` in full.

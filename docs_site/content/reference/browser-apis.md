---
title: Browser APIs
description: Reference for $component, Citry.vue, server-render callbacks, and component Events helpers.
---

# Browser APIs

Citry uses Vue for component state, rendering, props, events, and lifecycle
hooks. This page covers the browser names Citry adds to that runtime.

## Component JavaScript

<h3 class="doc-heading" id="component"><code>$component</code></h3>

Register the JavaScript that belongs to one component class. Use
`$component` inside `Component.js` or the file named by `Component.js_file`.
A component class may register one Options object or callback.

The object form accepts the Vue Options that Citry can compose safely:

```js
$component({
  props: {
    label: String,
  },
  data() {
    return { open: false };
  },
  methods: {
    toggle() {
      this.open = !this.open;
    },
  },
});
```

Citry composes `data()`, synchronous `setup()`, props, injections, methods,
computed values, and lifecycle hooks with its component wrapper. Native Vue
rules apply to these options. Citry reserves its generated render function and
reports public-name collisions with Python `js_data()` or Events helpers.
`mixins`, `extends`, an authored `render`, asynchronous `setup`, and a `setup`
function that returns a render function are rejected. `setup` must return a
plain bindings object or `undefined` synchronously.

<h3 class="doc-heading" id="on-server-render"><code>onServerRender</code></h3>

Add `onServerRender` when work must run after the initial mount and again after
Citry updates this component in an accepted server render:

```js
$component({
  onServerRender({ component, revision }) {
    const root = component.$refs.root;
    if (!(root instanceof HTMLElement)) return;

    const controller = connectWidget(root);
    console.log("rendered revision", revision);
    return () => controller.disconnect();
  },
});
```

The component template declares the referenced element:

```citry-html
<section ref="root"></section>
```

| Name | Value |
| --- | --- |
| `component` | The live Vue public instance for this Citry component. |
| `revision` | The accepted server revision visible to the component. |

The callback runs when this component mounts and after an accepted server
render updates it. An unrelated Vue update does not call it. The callback may
return a cleanup function or `undefined`. Citry runs cleanup before the next
callback and when the component unmounts. A different return value is an
error.

Effects registered synchronously inside the callback run in a Vue effect scope
that Citry stops at the same time. Asynchronous continuations must arrange
their own cleanup.

The callback form of `$component` is shorthand for `onServerRender`:

```js
$component(({ component, revision }) => {
  console.log(component, revision);
});
```

<h3 class="doc-heading"><code>js_data()</code> members</h3>

Every top-level key returned by
[`Component.js_data()`][citry.Component.js_data] becomes a reactive member of
the live Vue instance. Templates can read it directly, and JavaScript can read
or assign it through `this` or the callback's `component` value.

Citry updates the server-owned keys when an accepted server render updates the
component. A key cannot collide with local Vue data, setup bindings, props,
injections, methods, computed values, or reserved Citry names.

<h3 class="doc-heading" id="citry-vue"><code>Citry.vue</code></h3>

`Citry.vue` is the exact Vue runtime used by the page. Use it when an ordinary
component script needs Composition API helpers without an ES module import:

```js
$component({
  setup() {
    const query = Citry.vue.ref("");
    const normalized = Citry.vue.computed(() => query.value.trim());
    return { query, normalized };
  },
});
```

## Component Events helpers

The following helpers are available to templates and on the live Vue public
instance when the component participates in Citry Events.

<h3 class="doc-heading" id="state"><code>$state</code></h3>

Read the component's reactive public Events State. Assigning a writable whole
field updates the browser immediately and queues that value for the component's
next non-GET event call. State is client input and must be validated on the
server. Nested values and public fields that are not declared client-writable
are read-only. Non-public State names are unavailable. Invalid assignments
throw synchronously and leave the prior value unchanged.

```citry-html
<button @click="$state.count += 1">Add one</button>
<output v-text="$state.count"></output>
```

<h3 class="doc-heading" id="loading"><code>$loading</code></h3>

Return whether the component has a queued or running server call. Pass an event
name to check only that handler. An unknown handler name is an error.

```citry-html
<button :disabled="$loading('save')">
  <span v-if="$loading('save')">Saving...</span>
  <span v-else>Save</span>
</button>
```

<h3 class="doc-heading" id="error"><code>$error</code></h3>

Return the newest retained handler error, or `null`. Pass an event name to read
only that handler. An unknown handler name is an error.

```citry-html
<p v-if="$error('save')" v-text="$error('save').message"></p>
```

A successful call clears its own handler's retained error.

<h3 class="doc-heading" id="send-event"><code>$sendEvent</code></h3>

Call a declared server event from a Vue expression or component method:

```js
const result = await this.$sendEvent("preview", {page: 2});
```

The method returns a Promise for the handler's data result and rejects with a
structured event error. Use declarative `@c-*` bindings when no browser code
needs the returned result.

<h3 class="doc-heading" id="on-event"><code>$onEvent</code></h3>

Subscribe to a server-dispatched event for this component instance:

```js
const stop = this.$onEvent("cart:changed", (detail) => {
  refreshBadge(detail);
});
```

The callback receives the event detail and `stop()` removes that subscription.
Subscriptions are released when the component is unmounted or remounted.
`$onEvent` requires a component Events declaration.

<h3 class="doc-heading" id="citry-events"><code>Citry.events</code></h3>

Use the page-wide API from ordinary scripts or other browser integrations:

```js
const stop = Citry.events.on("cart:changed", (detail) => {
  refreshHeader(detail);
});
await Citry.events.send("render_abc123", "refresh", {page: 2});
```

`send(target, name, args?, opts?)` accepts a current render ID or an Element
inside its mounted component. The returned Promise has the same data and
error behavior as `$sendEvent`. The other methods are:

| Method | Purpose |
| --- | --- |
| `on(name, callback)` | Listen page-wide for a server-dispatched event; the callback receives its detail. |
| `configure({csrf, timeout, url, transport})` | Set defaults used by current and future event calls. |
| `registerTransport(name, {send})` | Register a transport that returns a Citry event result envelope. |
| `applyActions(actions)` | Apply a validated result action list from an intercepted or custom transport. |

Event calls also emit bubbling `citry:events:before`, `after`, `error`,
`swapped`, and `stale` events. Their detail always includes `instance`,
`class`, and `event`; `after` adds `ok`, `error` adds `error`, `swapped` adds
`els`, and `stale` adds `reason`. The `before` event is cancellable with
`preventDefault()`.

The Events guides cover [State](/events/state/), [template
bindings](/events/bindings/), [returned actions](/events/actions/), and
[direct HTTP routes](/events/http/).

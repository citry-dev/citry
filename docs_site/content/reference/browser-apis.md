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
an accepted server render that updates this component:

```js
$component({
  onServerRender({ component, revision, onEvent }) {
    const root = component.$refs.root;
    if (!(root instanceof HTMLElement)) return;

    const controller = connectWidget(root);
    const stop = onEvent("cart:changed", (detail) => refreshBadge(detail));
    console.log("rendered revision", revision);
    return () => {
      stop();
      controller.disconnect();
    };
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
| [`onEvent(name, handler)`](#on-server-render-on-event) | Listens for an event this component's server handler dispatches and returns a function that stops listening. |
| `id` | The component's current server render ID, the value `Citry.events.send()` accepts and the `instance` in `citry:events:*` details. `null` when the component has none. Read-only. |
| `els` | A new array of the component's connected top-level elements each time you read it. |
| `state` | The same object as [`component.$state`](#state), or `null` when the component declares no `Events`. |
| `sendEvent(name, args?, opts?)` | Calls [`component.$sendEvent`](#send-event). |
| `loading(name?)` | Calls [`component.$loading`](#loading). |
| `error(name?)` | Calls [`component.$error`](#error). |
| `i18n` | The same service as [`component.$i18n`](#i18n), or `null` outside a client i18n provider. |

`state`, `sendEvent`, `loading`, `error`, and `i18n` repeat instance helpers,
so code written either way reads the same values. On a component without
`Events`, `loading()` returns
`false`, `error()` returns `null`, and `sendEvent()` returns a rejected
Promise that says the component declares no `Events` class.

The callback runs when this component mounts and after an accepted server
render that updates this component. An unrelated Vue update does not call it.
The callback may return a cleanup function or `undefined`. Citry runs cleanup
before the next callback and when the component unmounts. A different return
value is an error.

Effects registered synchronously inside the callback run in a Vue effect scope
that Citry stops at the same time. Asynchronous continuations must arrange
their own cleanup.

The callback form of `$component` is shorthand for `onServerRender`:

```js
$component(({ component, revision, onEvent }) => {
  console.log(component, revision, onEvent);
});
```

`init` is another name for `onServerRender` in the object form, and receives
the same context. A definition that names both is an error when its script
loads:

```js
$component({
  props: { label: String },
  init({ component, els }) {
    els[0]?.setAttribute("title", component.label);
  },
});
```

<h4 class="doc-heading" id="on-server-render-on-event"><code>onEvent</code> in the callback context</h4>

`onEvent` takes the same arguments as [`$onEvent`](#on-event), but each
listener lasts only as long as the callback run that added it. Citry removes
it before the next callback and when the component unmounts, so a listener
added on every run is never registered twice. Unlike `$onEvent`, calling it
without an `Events` declaration is not an error, but it only receives events
that this component's own Events handlers dispatch:

```js
$component(({ component, onEvent }) => {
  onEvent("cart:changed", (detail) => {
    component.$el.dataset.items = String(detail.count);
  });
});
```

<h3 class="doc-heading" id="js-data-members"><code>js_data()</code> members</h3>

Every top-level key returned by
[`Component.js_data()`][citry.Component.js_data] becomes a reactive member of
the live Vue instance. Templates can read it directly, and JavaScript can read
or assign it through `this` or the callback's `component` value.

Citry updates the server-owned keys when an accepted server render updates the
component. A key cannot collide with local Vue data, setup bindings, props,
injections, methods, computed values, or
[names Citry reserves on the instance](/advanced/vue-runtime/#names-citry-reserves-on-the-component-instance).
Python rejects a key that starts with `$` or `_`, or the key `citryId`, when
the component renders.

<h3 class="doc-heading" id="i18n"><code>$i18n</code></h3>

Read the browser translation service of the nearest client-enabled
`<c-i18n>` provider. Templates use `$i18n`, component JavaScript uses
`this.$i18n` or `component.$i18n`, and the value is `null` outside a client
provider. The service has these members:

| Member | Meaning |
| --- | --- |
| `context` | Readonly locale, fallback, direction, time-zone, and revision data. |
| `status` | Readonly provider loading state. |
| `tr(message, values?, options?)` | Return loaded message text. Use `{ attr: "name" }` for a Fluent attribute. |
| `resolve(message, values?, options?)` | Return frozen `{ text, locale, direction, usedFallback }` metadata. |
| `format` | Named number, percent, currency, date, time, datetime, relative-time, list, and unit formatters. |
| `parse` | Strict number and percent parsers. |
| `ensureMessages(messages)` | Load one message ID or a list before a dynamic synchronous lookup. |
| `switchLocale(locale)` | Switch this provider's subtree to another locale. |
| `subscribe(callback)` | Call back now and after each context change; returns a function that stops the calls. |
| `bind(options)` | Keep a browser-created element translated; returns `refresh()` and `dispose()`. |

```citry-html
<c-i18n tag="section" client>
  <output v-text="$i18n.tr('my-app-status')"></output>
  <button @click="$i18n.switchLocale('cs-CZ')">Čeština</button>
</c-i18n>
```

See [Browser i18n](/i18n/browser/) for `$c-tr`, message loading, and `bind()`.

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
structured event error. An unknown handler name, or a component that declares
no `Events`, also rejects the Promise instead of throwing. Use declarative `@c-*` bindings when no browser code
needs the returned result.

<h3 class="doc-heading" id="on-event"><code>$onEvent</code></h3>

Subscribe to a server-dispatched event for this component instance:

```js
const stop = this.$onEvent("cart:changed", (detail) => {
  refreshBadge(detail);
});
```

The callback receives the event detail and `stop()` removes that subscription.
A listener added from `mounted()`, a method, or a timer lasts until the
component is unmounted or remounted; a server render does not remove it.
Call `$onEvent` once per instance, for example in `mounted()`, so the same
listener is not added twice.

A call made while this component's own `onServerRender` callback is still
executing (not later from a timer or promise it started) belongs to that
callback instead, like the callback's own [`onEvent`](#on-server-render): Citry
removes the listener before it calls the callback again. After the component
is unmounted, `$onEvent` adds nothing. `$onEvent` requires a component Events
declaration.

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
| `registerTransport(name, {send})` | Register a transport that returns a Citry event result envelope. See [custom transports](#custom-event-transports). |
| `applyActions(actions)` | Apply a validated result action list from an intercepted or custom transport. |

#### Custom event transports

A custom transport replaces the browser's `fetch` for event calls. Citry calls
`send(envelope, request)` for each call and expects the result envelope back,
or a Promise for it:

```js
Citry.events.registerTransport("bridge", {
  send(envelope, request) {
    const get = request.method === "GET";
    return bridge.request(request.url, {
      method: request.method,
      headers: request.headers,
      body: get ? undefined : JSON.stringify(envelope),
      signal: request.signal,
    });
  },
});
Citry.events.configure({transport: "bridge"});
```

`request` describes the HTTP request the built-in transport would send. A
`GET` handler carries its arguments in `url` and has no body, so send the
envelope only for other methods:

| Field | Value |
| --- | --- |
| `url` | The event endpoint, with the query string for a `GET` handler. |
| `method` | The HTTP method, usually `POST`. |
| `headers` | A fresh object with the request headers, including the CSRF token on non-`GET` calls. |
| `signal` | An `AbortSignal` that fires when the call times out or Citry cancels it, for example because the component was removed. |

Forward `request.headers` to the server with the envelope. When a handler
returns a render, the server reads the `X-Citry-Vue-App`,
`X-Citry-Vue-Occurrence`, and `X-Citry-Vue-Revision` headers to find the
component the browser is showing. Without them, the call fails with "Vue
Events requires current app, occurrence, and revision headers." A server
bridge that calls `EventsDispatcher.dispatch` itself passes these headers in
`TransportContext.headers`.

Event calls also emit bubbling `citry:events:before`, `after`, `error`,
`swapped`, and `stale` events. Their detail always includes `instance`,
`class`, and `event`; `after` adds `ok`, `error` adds `error`, `swapped` adds
`els`, and `stale` adds `reason`. The `before` event is cancellable with
`preventDefault()`.

`stale` fires when a call's result will not reach the page. Its `reason` says
why:

| `reason` | What happened |
| --- | --- |
| `superseded` | A newer call to the same handler replaced this one. This happens only for a handler declared with `@event(latest_wins=True)`. |
| `retired` | The component was removed or replaced before the call finished. |
| `epoch` | The page accepted a newer result for the component first, so the rest of this one was dropped. |
| `disposed` | The page's Vue app was shut down. |
| `version` | The server no longer accepts the State token this page holds, usually because the app was deployed or its signing secret changed after the page loaded. |

For `version`, the call also rejects with a `stale_state` error, and Citry
asks the user once per page whether to reload. To show your own message
instead, cancel the event:

```js
document.addEventListener("citry:events:stale", (event) => {
  if (event.detail.reason !== "version") return;
  event.preventDefault();
  showUpdateBanner();
});
```

The Events guides cover [State](/events/state/), [template
bindings](/events/bindings/), [returned actions](/events/actions/), and
[direct HTTP routes](/events/http/).

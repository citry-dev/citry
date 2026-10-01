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
each server render that the page applies to this component:

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
| `els` | The component's connected top-level elements. It is one array for the component's lifetime. Citry refills it on each server render and each time you read `els` from the context, so an `els` you destructured earlier follows server renders. It does not follow a change made only in the browser, such as a `v-if` toggle, until the next refill. |
| `state` | The same object as [`component.$state`](#state), or `null` when the component declares no `Events`. |
| `sendEvent(name, args?, opts?)` | Calls [`component.$sendEvent`](#send-event). |
| `loading(name?)` | Calls [`component.$loading`](#loading). |
| `error(name?)` | Calls [`component.$error`](#error). |
| `i18n` | The same service as [`component.$i18n`](#i18n), or `null` outside a client i18n provider or when the app does not configure the i18n extension. |

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

The callback may be `async`. Citry does not wait for it: the page becomes
ready, and later server renders apply, while it is still running. It may
resolve to a cleanup function. If the next callback run or the unmount comes
first, Citry calls that cleanup as soon as the Promise resolves. A rejected
Promise, or one that resolves to anything else, is logged to the console as
a `[Citry]` error and does not stop the page:

```js
$component({
  async onServerRender({ component }) {
    const { createChart } = await import("/static/chart.js");
    const chart = createChart(component.$refs.chart);
    return () => chart.destroy();
  },
});
```

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
added on every run is never registered twice. On a component without an
`Events` declaration, calling `onEvent` is not an error, but the listener
never runs, because only the component's own server handlers dispatch these
events and it has none:

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

Citry updates the server-owned keys each time the page applies a server
render to the component. A key cannot collide with local Vue data, setup bindings, props,
injections, methods, computed values, or
[names Citry reserves on the instance](/advanced/vue-runtime/#names-citry-reserves-on-the-component-instance).
Python rejects a key that starts with `$` or `_`, or the key `citryId`, when
the component renders.

<h3 class="doc-heading" id="i18n"><code>$i18n</code></h3>

Read the browser translation service of the nearest client-enabled
`<c-i18n>` provider. Templates use `$i18n` inside a client provider.
Component JavaScript uses `this.$i18n` or `component.$i18n`, which is
`null` outside a client provider and `undefined` when the app does not
configure the i18n extension. The service has these members:

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

<h3 class="doc-heading" id="citry-vue-use"><code>Citry.vue.use</code></h3>

Install a Vue plugin, such as a store or a global directive, on every Vue app
Citry creates on the page. Citry calls `app.use(plugin, ...options)` on each
app before it mounts:

```js
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

A component template can then use `v-autofocus`. Register a store plugin,
or any other Vue plugin, the same way.

Call it before Citry creates its first Vue app, from a script that runs
after Citry's runtime has loaded; `Citry.vue` does not exist before that.
Three places work:

- A script in the page `<head>` loaded with `defer`. A page that Citry
  renders loads the runtime with an ordinary script and starts its apps
  from a module script, so a deferred script runs between the two:

  ```html
  <script defer src="/static/vue-plugins.js"></script>
  ```

- A script an extension adds to `ctx.early_scripts` in
  `on_dependencies()`. These scripts run after the Vue runtime loads and
  before any component's JavaScript, so on an interactive page the app
  loads them before it creates the Vue app.
- A component's own JavaScript, when the component is in the page's
  first app. The app loads it before creating the Vue app, and the plugin
  then applies to the whole app, not only to that component.

Other calls behave as follows:

- A call after Citry has created a Vue app throws an `Error`, because that
  app would run without the plugin. Move the call earlier.
- A value that is neither a function nor an object with an `install(app)`
  method throws a `TypeError`.
- Registering the same plugin again does nothing, as with `app.use`, even
  when the options differ.
- An error thrown by the plugin's `install` stops that app from starting
  and is reported as a page error.

## Component Events helpers

The following helpers are available to templates and on the live Vue public
instance when the component participates in Citry Events.

<h3 class="doc-heading" id="state"><code>$state</code></h3>

Read the component's reactive public Events State. This is Citry's own object,
filled from the component's `State` class, and is separate from Vue's `data()`
and from any Pinia store. Assigning a writable whole field updates the browser
immediately and queues that value for the component's next non-GET event call.
State is client input and must be validated on the server. Nested values and
public fields that are not declared client-writable are read-only. Non-public
State names are unavailable. Invalid assignments throw synchronously and leave
the prior value unchanged.

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

The optional third argument accepts these options:

| Option | Meaning |
| --- | --- |
| `timeout` | Milliseconds to wait for the server before the call fails. Overrides the page default. |
| `wait` | Accepts only `true`, the default. See below. |

Citry sends the calls from one Vue app one at a time, in the order they were
made, because each server render builds on the one before it. A call cannot
skip ahead, so `wait: false` rejects the Promise with a `TypeError`. To
replace an older call to the same handler, as live search does, declare the
handler with `@event(latest_wins=True)`. An unknown option also rejects,
and the error names it.

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
is unmounted, `$onEvent` adds nothing. On a component without an `Events`
declaration, no server handler can dispatch to it, so `$onEvent` adds nothing
and returns a `stop()` that does nothing.

<h3 class="doc-heading" id="citry-events"><code>Citry.events</code></h3>

Use the page-wide API from ordinary scripts or other browser integrations:

```js
await Citry.events.send("render_abc123", "refresh", {page: 2});
```

The object has five methods, described below.

<h4 class="doc-heading" id="citry-events-send"><code>Citry.events.send</code></h4>

Call a server event on any mounted component:

```js
Citry.events.send(target, name, args?, opts?)
```

`target` is a current render ID or an Element inside the mounted component.
The returned Promise has the same data and error behavior as
[`$sendEvent`](#send-event), and `opts` takes the same
[options](#send-event). The Promise rejects when no mounted component
matches `target`, or when more than one does. As with `$sendEvent`, an
unknown handler name, or `args` that is not a plain object, also rejects the
Promise instead of throwing.

<h4 class="doc-heading" id="citry-events-on"><code>Citry.events.on</code></h4>

Listen page-wide for a server-dispatched event:

```js
const stop = Citry.events.on("cart:changed", (detail) => {
  updateHeader(detail);
});
```

The callback receives the event's `detail`, and the returned function removes
the listener. Unlike [`$onEvent`](#on-event), this listener hears the event
from every component on the page. An empty event name or a callback that is
not a function throws a `TypeError`.

<h4 class="doc-heading" id="citry-events-configure"><code>Citry.events.configure</code></h4>

Set page-wide defaults for event calls:

```js
Citry.events.configure({
  timeout: 45_000,
  transport: "bridge",
});
```

| Option | Meaning |
| --- | --- |
| `csrf` | Where the CSRF token comes from: `{token}` with a string or a function that returns one, or `{cookie}` with a cookie name. `header` names the request header, `X-CSRFToken` by default. |
| `timeout` | Milliseconds before a call rejects. The default is `30000`. A call's own `timeout` option wins. |
| `transport` | The name of a transport added with [`registerTransport`](#citry-events-register-transport). The default is `"fetch"`. |
| `url` | The Events route base URL. Citry normally reads it from the page. |

Each call merges its options into the earlier ones, and Citry reads them when
it sends each call, so later calls use the new values. A new `csrf` value
replaces the earlier one as a whole. The argument and its `csrf` value must
be plain objects, or the call throws a `TypeError`. Citry ignores an unknown
option. When `transport` names a transport that was never registered, each
later event call fails with "Citry Events transport is not registered".

By default Citry reads the `csrftoken` cookie for every transport. Once you
pass `csrf` to `configure`, Citry reads `csrf.cookie` only for the built-in
`fetch` transport, and a custom transport gets a token only from
`csrf.token`.

<h4 class="doc-heading" id="citry-events-register-transport"><code>Citry.events.registerTransport</code></h4>

Add a transport under a name, then select it with
[`configure`](#citry-events-configure):

```js
Citry.events.registerTransport("bridge", {
  send: (envelope, request) => sendThroughHost(envelope, request),
});
```

The transport's `send` method receives one Citry event envelope and a
description of the HTTP request, and returns the result envelope or a Promise
for it. Registering a name again replaces the earlier transport. An empty
name, or an object without a `send` function, throws a `TypeError`.
[Custom event transports](#custom-event-transports) shows a complete
example.

<h4 class="doc-heading" id="citry-events-apply-actions"><code>Citry.events.applyActions</code></h4>

Apply the `actions` array from a result envelope to the current page:

```js
await Citry.events.applyActions(result.actions);
```

Citry validates the array, applies its actions in order, and returns a
Promise. This is useful for custom transports, integration tests, and hosts
that intercept Citry event responses. The Promise rejects when the array is
not a valid action list, when an action targets a component that is no
longer on the page, or when the actions target components in different Vue
apps.

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

#### Events fired around each call

Event calls also emit bubbling `citry:events:before`, `after`, `error`,
`swapped`, and `stale` events. Their detail always includes `instance`,
`class`, and `event`; `after` adds `ok`, `error` adds `error`, `swapped` adds
`els`, and `stale` adds `reason`. The `before` event is cancellable with
`preventDefault()`. Each event bubbles from the calling component's first
element. When that component has no element on the page, for example
because it was removed before the call finished, the event fires on
`document` instead, so a listener on `document` still hears it. `instance`
and `class` then name the component as Citry last saw it.

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

---
title: Browser APIs
description: Reference for $component, Citry.vue, server-render callbacks, and component Events helpers.
---

# Browser APIs

Look up the JavaScript names Citry adds in the browser: what each one is
for, what it takes and returns, and when it fails. Vue still provides
component state, props, events, and lifecycle hooks. This page covers only
what Citry adds on top.

The names fall into four groups:

- **Component JavaScript:** [`$component`](#component),
  [`onServerRender`](#on-server-render), and
  [`js_data()` members](#js-data-members).
- **Events helpers on a component:** [`$state`](#state),
  [`$loading`](#loading), [`$error`](#error),
  [`$sendEvent`](#send-event), and [`$onEvent`](#on-event).
- **Page-wide events API:** [`Citry.events`](#citry-events).
- **Vue and translations:** [`Citry.vue`](#citry-vue),
  [`Citry.vue.use`](#citry-vue-use), and [`$i18n`](#i18n).

## Component JavaScript

<h3 class="doc-heading" id="component"><code>$component</code></h3>

Register the browser code for one component class. Call it in
`Component.js`, or in the file named by `Component.js_file`. Each
component class registers one object of Vue options, or one callback:

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

The object accepts `props`, `inject`, `data()`, a synchronous `setup()`,
`methods`, `computed`, and lifecycle hooks, with Vue's usual rules. Citry
combines them with its own component code.

Citry rejects:

- `mixins` and `extends`;
- a `render` function, because Citry generates the render function from
  the template;
- an `async` `setup`, or a `setup` that returns a render function. `setup`
  must return a plain object of bindings, or `undefined`;
- a public name that is also a [`js_data()`](#js-data-members) key or an
  [Events helper](#component-events-helpers).

The callback form is short for [`onServerRender`](#on-server-render):

```js
$component(({ component, revision, onEvent }) => {
  console.log(component, revision, onEvent);
});
```

<h3 class="doc-heading" id="on-server-render"><code>onServerRender</code></h3>

Run code when the component mounts and again each time the server renders
it, for example to connect a non-Vue widget to the new HTML. Return a
function to clean up:

```js
$component({
  onServerRender({ component, revision, onEvent }) {
    const root = component.$refs.root;
    if (!(root instanceof HTMLElement)) return;

    const controller = connectWidget(root);
    const stop = onEvent("Cart:changed", (detail) => {
      refreshBadge(detail);
    });
    console.log("rendered revision", revision);
    return () => {
      stop();
      controller.disconnect();
    };
  },
});
```

The template declares the element the code uses:

```citry-html
<section ref="root"></section>
```

The callback receives one object with these members:

| Name | Value |
| --- | --- |
| `component` | The live Vue instance of this component. |
| `revision` | The server revision the component now shows. |
| [`onEvent(name, handler)`](#on-server-render-on-event) | Listens for an event this component's server handler dispatches. Returns a function that stops listening. |
| `id` | The component's current render ID, the value `Citry.events.send()` accepts and the `instance` in `citry:events:*` details. `null` when the component has none. Read-only. |
| `els` | The component's top-level elements on the page, as an array. |
| `state` | The same object as [`component.$state`](#state), or `null` when the component declares no `Events`. |
| `sendEvent(name, args?, opts?)` | Calls [`component.$sendEvent`](#send-event). |
| `loading(name?)` | Calls [`component.$loading`](#loading). |
| `error(name?)` | Calls [`component.$error`](#error). |
| `i18n` | The same service as [`component.$i18n`](#i18n), or `null` outside a client i18n provider or when the app does not configure the i18n extension. |

**When it runs.** On mount, and after each server render the page applies
to this component. A Vue update made only in the browser does not call it.

**Cleanup.** The callback returns a cleanup function or `undefined`; any
other value is an error. Citry calls the cleanup before the next run and
when the component unmounts. Vue effects created synchronously inside the
callback stop at the same time. Code that runs later, such as a timer or
a Promise callback, must clean up after itself.

**Async callbacks.** The callback may be `async`. Citry does not wait for
it: the page becomes ready, and later server renders apply, while it runs.
It may resolve to a cleanup function. If the next run or the unmount
happens first, Citry calls that cleanup as soon as the Promise resolves. A
rejected Promise, or one that resolves to anything else, is logged to the
console as a `[Citry]` error and does not stop the page:

```js
$component({
  async onServerRender({ component }) {
    const { createChart } = await import("/static/chart.js");
    const chart = createChart(component.$refs.chart);
    return () => chart.destroy();
  },
});
```

**Without `Events`.** On a component that declares no `Events` class,
`loading()` returns `false`, `error()` returns `null`, and `sendEvent()`
returns a rejected Promise that says the component declares no `Events`
class.

**`els` updates.** `els` is the same array for the component's whole life.
Citry refills it after each server render, and each time you read `els`
from the callback's object, so an `els` you saved earlier still follows
server renders. It does not follow a change made only in the browser, such
as a `v-if` toggle, until the next refill.

**`init`.** `init` is another name for `onServerRender` in the object form
and receives the same object. A definition that names both throws an error
when its script loads:

```js
$component({
  props: { label: String },
  init({ component, els }) {
    els[0]?.setAttribute("title", component.label);
  },
});
```

<h4 class="doc-heading" id="on-server-render-on-event"><code>onEvent</code> in the callback context</h4>

Listen for an event that this component's server handler dispatches, for
as long as the current callback run lasts. It takes the same arguments as
[`$onEvent`](#on-event). Citry removes the listener before the next run
and when the component unmounts, so adding it on every run never adds it
twice:

```js
$component(({ els, onEvent }) => {
  onEvent("Cart:changed", (detail) => {
    els[0]?.setAttribute("data-items", String(detail.count));
  });
});
```

On a component without `Events`, calling `onEvent` is not an error, but
the listener never runs, because no server handler can dispatch to it.

<h3 class="doc-heading" id="js-data-members"><code>js_data()</code> members</h3>

Read server data in the browser. Every top-level key returned by
[`Component.js_data()`][citry.Component.js_data] becomes a reactive member
of the Vue instance. Templates read it directly, and JavaScript reads or
assigns it through `this` or the callback's `component`.

Citry updates these keys each time the page applies a server render to the
component.

A key cannot have the same name as local Vue data, a `setup` binding, a
prop, an injection, a method, a computed value, or one of the
[names Citry reserves on the instance](/advanced/vue-runtime/#names-citry-reserves-on-the-component-instance).
Python raises an error when the component renders with a key that starts
with `$` or `_`, or with the key `citryId`.

## Events helpers { #component-events-helpers }

A component that declares an `Events` class gets these helpers in its
template and on its Vue instance (`this` in Vue options). See
[Server events](/events/) for how to declare handlers.

<h3 class="doc-heading" id="state"><code>$state</code></h3>

Read and change the component's [State](/events/state/) fields in the
browser. This is Citry's own reactive object, filled from the component's
`State` class. It is separate from Vue's `data()` and from any Pinia store.

```citry-html
<button @click="$state.count += 1">Add one</button>
<output v-text="$state.count"></output>
```

Assigning a whole field that the browser may change updates the page at
once, and sends the new value with the component's next event call that is
not a `GET`. Validate it on the server like any user input.

- Nested values, and fields not listed as browser-writable, are read-only.
- Fields that are not public do not appear on `$state`.
- An invalid assignment throws at once and keeps the old value.

When a handler changes State, its response updates these fields even if
the component does not render again. A field the browser changed but has
not sent yet keeps the browser's value.

<h3 class="doc-heading" id="loading"><code>$loading</code></h3>

Check whether a server call is waiting or running, for example to disable
a button. Pass a handler name to check only that handler. An unknown
handler name throws an error.

```citry-html
<button :disabled="$loading('save')">
  <span v-if="$loading('save')">Saving...</span>
  <span v-else>Save</span>
</button>
```

<h3 class="doc-heading" id="error"><code>$error</code></h3>

Read the newest handler error, or `null`, to show it in the template. Pass
a handler name to read only that handler's error. An unknown handler name
throws an error. A successful call clears its own handler's error.

```citry-html
<p v-if="$error('save')" v-text="$error('save').message"></p>
```

<h3 class="doc-heading" id="send-event"><code>$sendEvent</code></h3>

Call a server handler from JavaScript when your code needs the result. When
it does not, use an `@c-*` binding in the template instead.

```js
const result = await this.$sendEvent("preview", {page: 2});
```

It returns a Promise for the data the handler returns. The Promise rejects
with an event error object when the call fails. An unknown handler name,
or a component that declares no `Events`, also rejects the Promise instead
of throwing.

The optional third argument takes these options:

| Option | Meaning |
| --- | --- |
| `timeout` | Milliseconds to wait for the server before the call fails. Overrides the page default. |
| `wait` | Accepts only `true`, the default. |

Calls from one Vue app go to the server one at a time, in order, because
each server render builds on the one before it. A call cannot skip ahead,
so `wait: false` rejects the Promise with a `TypeError`. To let a new call
replace an older call to the same handler, as live search needs, declare
the handler with `@event(latest_wins=True)`. An unknown option also
rejects, and the error names it.

<h3 class="doc-heading" id="on-event"><code>$onEvent</code></h3>

Run browser code when this component's server handler dispatches an event:

```js
const stop = this.$onEvent("Cart:changed", (detail) => {
  refreshBadge(detail);
});
```

The callback receives the event's detail, and `stop()` removes the
listener. A listener added from `mounted()`, a method, or a timer lasts
until the component unmounts or mounts again; a server render does not
remove it. Call `$onEvent` once per instance, for example in `mounted()`,
so the same listener is not added twice.

An empty event name, or a callback that is not a function, throws a
`TypeError`.

A call made while this component's own `onServerRender` callback is
running (not later, from a timer or Promise it started) belongs to that
run instead, like the callback's own [`onEvent`](#on-server-render-on-event):
Citry removes the listener before the next run.

After the component unmounts, `$onEvent` adds nothing. On a component
without `Events`, no server handler can dispatch to it, so `$onEvent` adds
nothing and returns a `stop()` that does nothing.

## Page-wide events API

<h3 class="doc-heading" id="citry-events"><code>Citry.events</code></h3>

Call handlers, listen for events, and change how calls are sent, from
ordinary scripts or other browser code outside a component:

```js
await Citry.events.send("render_abc123", "refresh", {page: 2});
```

The object has five methods.

<h4 class="doc-heading" id="citry-events-send"><code>Citry.events.send</code></h4>

Call a server handler on any mounted component:

```js
Citry.events.send(target, name, args?, opts?)
```

`target` is a current render ID, or an element inside the mounted
component. The Promise and `opts` work as for
[`$sendEvent`](#send-event). The Promise rejects when no mounted component
matches `target`, when more than one does, when the handler name is
unknown, or when `args` is not a plain object.

<h4 class="doc-heading" id="citry-events-on"><code>Citry.events.on</code></h4>

Listen for an event that any component's server handler dispatches:

```js
const stop = Citry.events.on("Cart:changed", (detail) => {
  updateHeader(detail);
});
```

The callback receives the event's `detail`, and the returned function
removes the listener. Unlike [`$onEvent`](#on-event), this listener hears
the event from every component on the page. An empty event name, or a
callback that is not a function, throws a `TypeError`.

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
| `url` | The base URL of the event routes. Citry normally reads it from the page. |

Each call merges its options into the earlier ones. Citry reads them each
time it sends a call, so calls made afterwards use the new values. A new
`csrf` value replaces the earlier one as a whole.

By default Citry reads the `csrftoken` cookie for every transport. Once you
pass `csrf`, Citry reads `csrf.cookie` only for the built-in `fetch`
transport. A custom transport gets a token only from `csrf.token`.

The argument and its `csrf` value must be plain objects, or the call throws
a `TypeError`. Citry ignores an unknown option. When `transport` names a
transport that was never registered, every later event call fails with
"Citry Events transport is not registered".

<h4 class="doc-heading" id="citry-events-register-transport"><code>Citry.events.registerTransport</code></h4>

Send event calls through your own code instead of the browser's `fetch`,
such as a native app bridge. Register the transport under a name, then
select it with [`configure`](#citry-events-configure):

```js
Citry.events.registerTransport("bridge", {
  send: (envelope, request) => sendThroughHost(envelope, request),
});
```

`send` receives the call's message (the envelope) and a description of the
HTTP request, and returns the result envelope or a Promise for it.
Registering a name again replaces the earlier transport. An empty name, or
an object without a `send` function, throws a `TypeError`.
[Custom event transports](#custom-event-transports) shows a complete
example.

<h4 class="doc-heading" id="citry-events-apply-actions"><code>Citry.events.applyActions</code></h4>

Apply the `actions` array from a result envelope to the page. Custom
transports, integration tests, and code that intercepts Citry's responses
use it:

```js
await Citry.events.applyActions(result.actions);
```

Citry checks the array, applies the actions in order, and returns a
Promise. The Promise rejects when:

- the array is not a valid action list;
- an action targets a component that is no longer on the page;
- the actions target components in different Vue apps;
- a `state` action has no `publicState`, the component's public State
  values (this rejects with a `TypeError`).

### Custom event transports

A custom transport replaces `fetch` for event calls. Citry calls
`send(envelope, request)` for each call and expects the result envelope, or
a Promise for it:

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
| `url` | The event route, with the query string for a `GET` handler. |
| `method` | The HTTP method, usually `POST`. |
| `headers` | A new object with the request headers, including the CSRF token on calls that are not `GET`. |
| `signal` | An `AbortSignal` that fires when the call times out or Citry cancels it, for example because the component was removed. |

Send `request.headers` to the server with the envelope. When a handler
returns a render, the server reads the `X-Citry-Vue-App`,
`X-Citry-Vue-Occurrence`, and `X-Citry-Vue-Revision` headers to find the
component the browser shows. Without them the call fails with "Vue Events
requires current app, occurrence, and revision headers." A server bridge
that calls `EventsDispatcher.dispatch` itself passes these headers in
`TransportContext.headers`.

### Events around a call { #events-fired-around-each-call }

Citry fires DOM events around each event call, so other code can show a
spinner, log failures, or react when a result is dropped:

| Event | When | Extra `detail` fields |
| --- | --- | --- |
| `citry:events:before` | Before the call is sent. Calling `preventDefault()` stops the call. | |
| `citry:events:after` | After the call finishes. | `ok` |
| `citry:events:error` | When the call fails. | `error` |
| `citry:events:swapped` | After a render replaced elements. | `els` |
| `citry:events:stale` | When the result will not reach the page. | `reason` |

Every `detail` includes `instance`, `class`, and `event`. Each event
bubbles from the first element of the component that made the call. When
that component has no element on the page, for example because it was
removed before the call finished, the event fires on `document` instead,
so a listener on `document` still hears it. `instance` and `class` then
name the component as Citry last saw it.

`stale` says in `reason` why the result was dropped:

| `reason` | What happened |
| --- | --- |
| `superseded` | A newer call to the same handler replaced this one. This happens only for a handler declared with `@event(latest_wins=True)`. |
| `retired` | The component was removed or replaced before the call finished. |
| `epoch` | The page accepted a newer result for the component first, so the rest of this one was dropped. |
| `disposed` | The page's Vue app was shut down. |
| `version` | The server no longer accepts the State this page holds, usually because the app was deployed or its signing secret changed after the page loaded. |

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

The Events guides cover [State](/events/state/),
[template bindings](/events/bindings/),
[returned actions](/events/actions/), and
[event routes](/events/routes/).

## Vue and translations

<h3 class="doc-heading" id="citry-vue"><code>Citry.vue</code></h3>

Use Vue's Composition API functions in a component script without an
import. `Citry.vue` is the exact Vue runtime the page uses:

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

Install a Vue plugin, such as a store or a global directive, on every Vue
app Citry creates on the page. Citry calls `app.use(plugin, ...options)` on
each app before it mounts:

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

A component template can then use `v-autofocus`.

Call it after Citry's runtime has loaded (`Citry.vue` does not exist
before that) and before Citry creates its first Vue app. Three places
work:

- **A `defer` script in the page `<head>`.** A page Citry renders loads
  the runtime with an ordinary script and starts its apps from a module
  script, so a deferred script runs between the two:

  ```html
  <script defer src="/static/vue-plugins.js"></script>
  ```

- **A script an extension adds to `ctx.early_scripts`** in
  `on_dependencies()`. These run after the Vue runtime loads and before
  any component's JavaScript, so on an interactive page they run before
  the Vue app is created.
- **A component's own JavaScript**, when the component is in the page's
  first app. It runs before the Vue app is created, and the plugin then
  applies to the whole app, not only to that component.

Errors and repeated calls:

- A call after Citry has created a Vue app throws an `Error`, because that
  app would run without the plugin. Move the call earlier.
- A value that is neither a function nor an object with an
  `install(app)` method throws a `TypeError`.
- Registering the same plugin again does nothing, as with `app.use`, even
  when the options differ.
- An error thrown by the plugin's `install` stops that app from starting
  and is reported as a page error.

<h3 class="doc-heading" id="i18n"><code>$i18n</code></h3>

Translate and format text in the browser. `$i18n` is the translation
service of the nearest `<c-i18n>` that has the `client` attribute:

```citry-html
<c-i18n tag="section" client>
  <output v-text="$i18n.tr('my-app-status')"></output>
  <button @click="$i18n.switchLocale('cs-CZ')">Čeština</button>
</c-i18n>
```

Templates use `$i18n` inside such a `<c-i18n>`. Component JavaScript uses
`this.$i18n` or `component.$i18n`. It is `null` outside a client
`<c-i18n>`, and `undefined` when the app does not configure the i18n
extension.

| Member | Meaning |
| --- | --- |
| `tr(message, values?, options?)` | Return loaded message text. Use `{ attr: "name" }` for a Fluent attribute. |
| `format` | Named number, percent, currency, date, time, datetime, relative-time, list, and unit formatters. |
| `switchLocale(locale)` | Switch this provider's part of the page to another locale. |
| `context` | Read-only locale, fallback, direction, time-zone, and revision data. |
| `status` | Read-only loading state of the provider. |
| `resolve(message, values?, options?)` | Return frozen `{ text, locale, direction, usedFallback }` details. |
| `parse` | Strict number and percent parsers. |
| `ensureMessages(messages)` | Load one message ID, or a list, before looking up a message whose ID is computed at runtime. |
| `subscribe(callback)` | Call back now and after each context change. Returns a function that stops the calls. |
| `bind(options)` | Keep an element created by browser code translated. Returns `refresh()` and `dispose()`. |

See [Browser i18n](/i18n/browser/) for `$c-tr`, message loading, and
`bind()`.

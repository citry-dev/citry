---
title: Browser APIs
description: Reference for $component, Citry.vue, server-render callbacks, page-wide settings, and component Events helpers.
---

# Browser APIs

Look up the JavaScript names Citry adds in the browser: what each one is
for, what it takes and returns, and when it fails. Vue still provides
component state, props, events, and lifecycle hooks. This page covers only
what Citry adds on top.

The names fall into six groups:

- **Component JavaScript:** [`$component`](#component),
  [`onServerRender`](#on-server-render), and
  [`js_data()` members](#js-data-members).
- **Events helpers on a component:** [`$state`](#state),
  [`$loading`](#loading), [`$error`](#error),
  [`$sendEvent`](#send-event), and [`$onEvent`](#on-event).
- **Page-wide settings:** [`Citry.configure`](#citry-configure).
- **Page-wide events API:** [`Citry.events`](#citry-events), the
  [`citry:events:*` events](#events-fired-around-each-call), and how to
  [handle out-of-date pages](#out-of-date-pages).
- **Fragments:** [`Citry.fragments.load`](#citry-fragments-load).
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

The callback form is short for [`onServerRender`](#on-server-render):

```js
$component(({ component, revision, onEvent }) => {
  console.log(component, revision, onEvent);
});
```

Citry rejects:

- `mixins` and `extends`;
- an `async` `setup`, or a `setup` that returns a render function. `setup`
  must return a plain object of bindings, or `undefined`;
- a public name that is also a [`js_data()`](#js-data-members) key or an
  [Events helper](#component-events-helpers).

Citry ignores a `render` function or a `template` option, because it
generates the render function from the component's template.

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
| `revision` | A number that identifies the server render the component now shows. It changes when a server render updates the page. |
| [`onEvent(name, handler)`](#on-server-render-on-event) | Listens for an event this component's server handler dispatches. Returns a function that stops listening. |
| `id` | The render ID: the ID Citry gives this rendered component on the page. It is the value `Citry.events.send()` accepts and the `instance` in `citry:events:*` details. `null` when the component has none. Read-only. |
| `els` | The component's top-level elements on the page, as an array. |
| `state` | The same object as [`component.$state`](#state), or `null` when the component declares no `Events`. |
| `sendEvent(name, args?, opts?)` | Calls [`component.$sendEvent`](#send-event). |
| `loading(name?)` | Calls [`component.$loading`](#loading). |
| `error(name?)` | Calls [`component.$error`](#error). |
| `i18n` | The same service as [`component.$i18n`](#i18n), or `null` outside a client i18n provider or when the app does not configure the i18n extension. |

**When it runs.** On mount, and after each server render the page applies
to this component. A Vue update made only in the browser does not call it.

**Order.** Children's callbacks run before their parent's, and siblings
run in the order they first mounted. This holds on the first mount and
after a server render. By the time the first callback runs, every
component mounted by that mount or render has run its `mounted` hook. If
a callback throws, no later callback of that mount or render runs, and
the page's Vue app stops. A rejected `async` callback only logs.

Each callback sees the page as the earlier callbacks left it, after Vue
applied any change they made. If a callback changes state so that Vue
removes a component whose callback has not run yet, that component gets
no callback. A component that a callback adds gets its own first
callback after the others have run.

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

**`els` updates.** `els` stays one array for the component's whole life.
Citry refills it after each server render, so an `els` you saved earlier
stays current. A change made only in the browser, such as a `v-if` toggle,
shows up in `els` after the next server render.

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

<h4 class="doc-heading" id="on-server-render-on-event"><code>onEvent</code> in the callback</h4>

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
[names Citry reserves on the instance](/vue/component-options/#names-citry-reserves-on-the-component-instance).
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
not a `GET` and not to a handler declared with `@event(detached=True)`.
Validate it on the server like any user input.

- Nested values, and fields not listed as browser-writable, are read-only.
- Fields that are not public do not appear on `$state`.
- Assigning an unknown field, a field that is not browser-writable, or a
  nested value throws an `Error` at once. A value that is not plain JSON
  data throws a `TypeError`. Either way the old value stays.

When a handler changes State, its response updates these fields even if
the component does not render again. A field the browser changed but has
not sent yet keeps the browser's value.

<h3 class="doc-heading" id="loading"><code>$loading</code></h3>

Check whether a server call is waiting or running, for example to disable
a button. Returns `true` or `false`. Pass a handler name to check only that
handler. An unknown
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

```text
$sendEvent(name, args?, opts?)
```

`args` must be a plain object; anything else rejects the Promise. For
example:

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
| `wait` | `true`, the default, waits for this app's earlier calls. `false` sends the call at once. Only a handler declared with `@event(detached=True)` accepts it. |

Calls from one Vue app go to the server one at a time, in order, because
each server render builds on the one before it. A handler declared with
`@event(detached=True)` must not render or change State, so a call to it
can skip ahead with `wait: false`
([details](/events/actions/#skip-the-queue-for-a-read-only-call)). For any
other handler, `wait: false` rejects the Promise with a `TypeError`. To let
a new call replace an older call to the same handler, as live search needs,
declare the handler with `@event(latest_wins=True)`. An unknown option
also rejects, and the error names it.

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

## Page-wide settings

<h3 class="doc-heading" id="citry-configure"><code>Citry.configure</code></h3>

Tell Citry where the page's CSRF token comes from. Citry's browser code
sends the token with every request it makes to Citry's routes except
`GET` requests: event calls, and the request that loads messages when
`$i18n` switches locale. A web framework that checks CSRF tokens, such as
Django's `CsrfViewMiddleware`, refuses these requests without it. See
[Protect against CSRF](/security/#protect-event-posts-from-csrf).

Call it in a script that runs after Citry's runtime has loaded, such as a
component's `js`, and before the first event call or language switch.

```js
Citry.configure({
  csrf: {
    token: () => document.querySelector(
      '[name="csrfmiddlewaretoken"]',
    ).value,
  },
});
```

| `csrf` option | Meaning |
| --- | --- |
| `token` | The token: a string, or a function that returns one. Citry calls the function before each request. |
| `cookie` | The name of the cookie to read the token from when `token` is not set. The default is the server's [`_csrf_cookie`](/security/#csrf-names), or `csrftoken`. |
| `header` | The request header that carries the token. The default is the server's [`_csrf_header`](/security/#csrf-names), or `X-CSRFToken`. |

With no `Citry.configure` call, Citry uses the names from the server's
[`_csrf_cookie` and `_csrf_header` settings](/security/#csrf-names), and
without those it reads the `csrftoken` cookie and sends it as
`X-CSRFToken`, which is what Django expects. Each name the call sets
wins over the server's setting, whether the call runs before or after
the page's first app starts. A later call replaces the earlier call's
names as a whole, and a name it leaves out falls back to the server's
setting. An option given as `undefined` counts as left out. Requests
sent afterwards use the new values.
When the token is empty, or the cookie is missing, Citry sends no token
header.

Citry's own requests (event calls sent by the built-in `fetch` transport,
and the message request) send the token only to an address on the page's
own origin: the same scheme, host, and port as the page. A request to any
other address goes without it, even when you set `token` yourself. A
[custom transport](#citry-events-register-transport) gets the token
whatever address it sends to. A page in an iframe sandboxed without
`allow-same-origin` has no origin of its own, so it sends no token.

If your `token` function throws, the request that needed it fails: the
event call rejects, or the language switch fails and the old language
stays.

The call throws a `TypeError` when the argument or `csrf` is not a plain
object, when either has an option not listed here, when `cookie` is empty,
or when `token` is neither a string nor a function. It also throws when
`header` is not a valid header name, or is a name the token cannot use:
`Content-Type` and names that start with `X-Citry-`, which Citry uses for
its own headers, and names the browser does not let a page send, such as
`Cookie`, `Origin`, and names that start with `Sec-` or `Proxy-`.

[`Citry.events.configure`](#citry-events-configure) can set a different
token for event calls. Event calls then use that token, and the request
that loads messages keeps using the `Citry.configure` token.

<h3 class="doc-heading" id="citry-page-nonce"><code>Citry.pageNonce</code></h3>

Get the page's CSP nonce, so that a request your own code sends (htmx,
`fetch()`) can tell the server which page it comes from. Call it after
Citry's runtime has loaded:

```js
const nonce = window.Citry?.pageNonce?.();
const url = new URL("/cards/42", location.href);
const response = await fetch(url, {
  headers: nonce ? {"X-Citry-Page-Nonce": nonce} : {},
  redirect: "error",
});
```

It returns the nonce on the tag that loaded Citry's runtime, or `null`
when that tag has none. The server reads the header with
`page_nonce_from_headers()` and serializes the fragment with that nonce,
so the fragment starts in the tab that asked for it. Send the header only
to your own origin, and build the URL from `location.href`: `fetch()`
resolves a relative path against the page's base URL, which a `<base>`
tag can change. `redirect: "error"` keeps a redirect from passing the
header on to another site. See [Nonces in fragments](/security/#html-fragments),
which also has an htmx snippet.

Citry never adds the nonce to a fragment itself. A fragment starts only
when the server wrote the page's nonce into it.

!!! warning "Experimental"

    `Citry.pageNonce` and the `X-Citry-Page-Nonce` header are
    experimental. They may change in a minor release without a
    deprecation period.

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

```text
Citry.events.send(target, name, args?, opts?)
```

`target` is a current render ID (the `id` in the
[`onServerRender`](#on-server-render) callback), or an element inside the mounted
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
| `csrf` | Where the CSRF token for event calls comes from: `{token}` with a string or a function that returns one, or `{cookie}` with a cookie name. `header` names the request header, `X-CSRFToken` by default. It replaces the page-wide [`Citry.configure`](#citry-configure) setting for event calls only. |
| `timeout` | Milliseconds before a call rejects. The default is `30000`. A call's own `timeout` option wins. |
| `transport` | The name of a transport added with [`registerTransport`](#citry-events-register-transport). The default is `"fetch"`. |
| `url` | The base URL of the event routes. Citry normally reads it from the page. Citry resolves a relative URL against the page's own address and ignores a `<base>` element. |

Each call merges its options into the earlier ones. Citry reads them each
time it sends a call, so calls made afterwards use the new values. A new
`csrf` value replaces the earlier one as a whole.

Without `csrf` here, event calls use the
[`Citry.configure`](#citry-configure) setting. When that setting reads a
cookie, it does so for every transport, including a custom one. Once you pass `csrf`
here, Citry reads `csrf.cookie` only for the built-in `fetch` transport,
and a custom transport gets a token only from `csrf.token`.

The built-in `fetch` transport sends the CSRF token only when the call's
URL is on the page's own origin, as described under
[`Citry.configure`](#citry-configure). It does not follow an HTTP
redirect: when the server answers an event call with one, the call fails
and its Promise rejects. To send the visitor to another page, return
[`actions.Redirect`][citry.ext.events.actions.Redirect] from the
handler.

The argument and its `csrf` value must be plain objects, or the call throws
a `TypeError`. It also throws a `TypeError` for a `csrf.header` that
[`Citry.configure`](#citry-configure) would reject. Citry ignores an
unknown option. When `transport` names a
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

`send` receives the envelope, the JSON object Citry would post to the
event route, and a description of the HTTP request. It returns the JSON
object the server would answer with (the result envelope), or a Promise
for it.
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
- a `redirect` action names a URL that Citry refuses to follow, such as
  one with a scheme other than `http:` or `https:` (for a redirect with
  `wait: false`, Citry logs the error instead);
- an `event` action names a standard DOM event such as `click`, or a
  name that starts with `citry:`, `vue:`, or `vnode-`, in any letter
  case. [`Dispatch` browser events](/events/actions/#notify-browser-code-that-something-happened)
  explains which names Citry refuses. For an action with `wait: false`,
  Citry logs the error instead;
- a `state` action has no `publicState`, the component's public State
  values (this rejects with a `TypeError`).

Pass only actions that your own server returned. A `render` action
inserts HTML and can make Citry load the scripts it names, so never pass
actions that came from another site, from `postMessage`, or from
storage.

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
| `headers` | A new object with the request headers, including the CSRF token on calls that are not `GET`, and the State token in `X-Citry-State-Token` on a `GET` call to a handler that reads State. |
| `signal` | An `AbortSignal` that fires when the call times out or Citry cancels it, for example because the component was removed. |

Send `request.headers` to the server with the envelope. When a handler
returns a render, the server reads the `X-Citry-Vue-App`,
`X-Citry-Vue-Occurrence`, and `X-Citry-Vue-Revision` headers to find the
component the browser shows. Without them the call fails with
`handler_error`, and the server log says the app, occurrence, or
revision header is missing or invalid. A `GET` call to a handler that
reads State carries its State token in `X-Citry-State-Token`, not in
`url`. When the server answers such a call with `invalid_state`, Citry
calls `send` once more, with a copy of the envelope, the token in `url`,
and without that header. The simplest transport sends the
envelope and `request.headers` to `request.url`, Citry's own event
route.

Server code can also run a call itself with
[`EventsDispatcher`][citry.ext.events.EventsDispatcher], passing the
headers in [`TransportContext`][citry.ext.events.TransportContext]. Both
classes are experimental and may change in a minor release. Also,
`EventsDispatcher()` can build a render only as HTML, while Citry's
browser code accepts only Vue renders, so a handler that returns a render
answers `handler_error` when one of Citry's pages calls it this way.

From Citry 1.0.0 on, a custom transport keeps working on every 1.x
release. These stay the same:

- in the browser: the `send(envelope, request)` call, the `url`,
  `method`, `headers` and `signal` fields of `request`, and the
  `X-Citry-Events` and `X-Citry-Vue-*` headers;
- the envelopes of the
  [`citry-events/1` protocol](https://github.com/citry-dev/citry/blob/main/packages/protocol/events/v1/spec.md#versioning){: target="_blank" rel="noopener"},
  which every 1.x server accepts.

### `citry:events:*` events { #events-fired-around-each-call }

Citry fires DOM events around each event call, so other code can show a
spinner, log failures, or react when a result is dropped:

| Event | When | Extra `detail` fields |
| --- | --- | --- |
| `citry:events:before` | Before the call is sent. Calling `preventDefault()` stops the call. | |
| `citry:events:after` | After the call finishes. | `ok` |
| `citry:events:error` | When the call fails. | `error` |
| `citry:events:swapped` | After a render replaced elements. | `els` |
| `citry:events:stale` | When the result will not reach the page. When `reason` is `version`, calling `preventDefault()` stops Citry's reload question (development) or console warning (production). | `reason` |

Every `detail` includes `instance`, `class`, and `event`. Each event
bubbles from the first element of the component that made the call. When
that component has no element on the page, for example because it was
removed before the call finished, the event fires on `document` instead,
so a listener on `document` still hears it. `instance` and `class` then
name the component as Citry last saw it.

`stale` says in `reason` why the result was dropped:

| `reason` | What happened |
| --- | --- |
| `superseded` | A newer call to the same handler replaced this one, so the actions of this call that have not started yet are dropped, delayed ones included. This happens only for a handler declared with `@event(latest_wins=True)`. |
| `retired` | The component was removed or replaced before the call finished. |
| `epoch` | The page accepted a newer result for the component first, so the rest of this one was dropped. This also happens when the call's own Render replaced the component and the page then accepted a newer result for the new component. A delayed redirect is never dropped for this reason. A result from a handler declared with `@event(detached=True)` never counts as newer, and its own actions without a delay are never dropped for this reason. |
| `disposed` | The page's Vue app was shut down. |
| `version` | The page is out of date: the server does not accept its State, or sent a response this page's Citry browser code cannot read. See [Handle out-of-date pages](#out-of-date-pages). |

### Handle out-of-date pages { #out-of-date-pages }

A visitor can keep a page open until the server no longer accepts it.
Their next event call then fails with the error code `stale_state`. In
production Citry shows no message and does not reload the page, so add
a listener that tells the visitor.

A call fails this way when:

- The State token expired. The token is the signed copy of a
  component's State that the page sends back with each call, and it
  expires 24 hours after Citry issued it, by default. This is the
  common case in production: a visitor leaves a tab open for a day and
  then clicks.
- The server no longer holds or accepts the State: server-stored State
  that the cache dropped, a changed signing secret, or a deploy that
  changed the State class (such as a field's type).
- During a deploy, a server on another Citry release sent a token or a
  response this page's browser code cannot read.

Calls from that component keep failing until the visitor reloads the
page. A starting point is a script on every page that shows a message
with a reload button. Load it with the page's other scripts, before the
visitor can click:

```js
function showOutOfDate() {
  // The events fire on every failed call; add one message.
  if (document.getElementById("out-of-date")) return;
  const banner = document.createElement("div");
  banner.id = "out-of-date";
  banner.textContent = "This page is out of date. ";
  const button = document.createElement("button");
  button.textContent = "Reload";
  button.addEventListener("click", () => location.reload());
  banner.append(button);
  document.body.prepend(banner);
}

document.addEventListener("citry:events:stale", (event) => {
  if (event.detail.reason !== "version") return;
  // Stop Citry's own question or warning; the banner says it.
  event.preventDefault();
  showOutOfDate();
});
document.addEventListener("citry:fragments:stale", (event) => {
  event.preventDefault();
  showOutOfDate();
});
```

Let the visitor choose to reload rather than reloading from the
listener. A page that reloads by itself can loop when the cause is still
there, for example when a CDN keeps serving a cached copy of the page
with its expired token.

What Citry does by itself:

- A call made with `$sendEvent` or `Citry.events.send` rejects with an
  error whose `code` is `stale_state`. Its
  `status` is 409 when the server answered and 0 when the browser found
  the problem itself.
- Citry fires `citry:events:stale` with reason `version`, then
  `citry:events:error`, on every failed call.
- Unless a listener calls `preventDefault()`, Citry also reports it
  once per page. When the page runs with `Citry(mode="development")`,
  the browser shows the confirm dialog "This page is out of date. Reload to
  continue?", so you notice the case while you develop. Otherwise Citry
  writes a console warning that starts with "[Citry] This page is out
  of date". When several apps on one page run in different modes, the
  first failure decides which one you get. For a fragment, the page's
  own mode decides; only on a page with no Citry app of its own does
  the mode of the server that wrote the fragment decide.

A [Vue fragment](/advanced/html-fragments/), HTML your server returns
for the browser to insert into an open page, can also come from another
Citry release. That happens during a deploy, when the server process
that answers already runs the new release. When the page cannot read
the fragment, Citry does not mount its Vue components: the fragment's
HTML stays in the page, but its buttons and bindings do nothing, and
Citry writes `[Citry] discarded Vue fragment` to the console. No event
call is involved, so Citry fires `citry:fragments:stale` instead of `citry:events:stale`:

- It fires on the `<script>` tag that holds the fragment's data while
  that tag is in the page, and on `document` otherwise. It bubbles, so a
  listener on `document` always hears it.
- Its `detail` holds `reason`, which is `version`, and `error`, the
  `stale_state` error described above.
- It is cancelable: `preventDefault()` stops Citry's question or
  warning, as for `citry:events:stale`. Citry tells you once per page
  for both events together.

The Events guides cover [State](/events/state/),
[template bindings](/events/bindings/),
[returned actions](/events/actions/), and
[event routes](/events/routes/).

## Fragments

<h3 class="doc-heading" id="citry-fragments-load"><code>Citry.fragments.load</code></h3>

Start a [Vue fragment](/advanced/html-fragments/) from your own script.
Usually you do not need it: Citry starts the fragments it finds in the
page by itself. Call it when Citry refuses to start a fragment on a page
whose Citry script has no CSP nonce, because the fragment names a script
that Citry does not serve itself, such as a `Script(url=...)` dependency
(see [Nonces in fragments](/security/#html-fragments)).

```text
Citry.fragments.load(data)
```

`data` is the parsed JSON of the fragment's
`<script type="application/json" data-citry-vue-fragment>` tag. Insert
the fragment's HTML without that tag first, so the element the fragment
mounts into is in the page:

```js
const html = await (await fetch("/chart-fragment")).text();
const template = document.createElement("template");
template.innerHTML = html;
const block = template.content.querySelector(
  "script[data-citry-vue-fragment]",
);
block.remove();
document.getElementById("chart").append(template.content);
await Citry.fragments.load(JSON.parse(block.textContent));
```

The call returns a Promise that resolves once the fragment's Vue app has
mounted. It rejects with an `Error` when:

- the data is not a fragment;
- it comes from another Citry release (it then also fires
  [`citry:fragments:stale`](#out-of-date-pages));
- the element the fragment mounts into is missing, appears more than
  once, or sits inside another Vue app;
- or a script fails to load.

Citry trusts data passed to this call as it trusts its own server. It
does not run the checks it runs on a fragment it finds in the page:

- **It does not check the nonce.** On a page with a nonce-based CSP,
  Citry still gives the page's nonce to every script and stylesheet the
  fragment loads, so they run under the policy.
- **It does not check the URLs.** The fragment may load scripts from any
  site, and send its server events and its requests for translated
  messages wherever its data says.

So pass only data your own server wrote for this page, never text that
came from a visitor, a URL, or storage that visitors can write to.

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

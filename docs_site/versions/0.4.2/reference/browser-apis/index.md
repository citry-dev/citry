---
title: Browser APIs
url: https://citry.dev/v/0.4.2/reference/browser-apis/
description: "Reference for $component, Citry's Alpine magics, and the public Citry browser methods."
---
# Browser APIs

Citry adds a small browser API around its component boundaries, Alpine
runtime, server events, and client-enabled i18n providers. This page covers the names Citry provides. For
standard Alpine directives and magics, use the
[Alpine documentation](https://alpinejs.dev/){: target="_blank" rel="noopener"}.

## Component JavaScript

<h3 class="doc-heading" id="component"><code>$component</code></h3>

Register the JavaScript that belongs to one component class. Use
`$component` inside `Component.js` or the file named by `Component.js_file`.
Citry binds that registration to the Python component class, then calls its
initializer for every live rendered instance.

The callback form accepts one initializer:


```js
$component(({ els, data, scope }) => {
  console.log(data.name, scope.name);
  els[0].dataset.ready = "true";
});
```


The configuration form adds declared client props:


```js
$component({
  props: {
    name: {
      type: String,
      required: true,
    },
  },
  init: ({ props, scope }) => {
    scope.name = props.name;
  },
});
```


A component class may register exactly one `$component` initializer. Citry
seeds the component scope from `js_data()` first, then runs the initializer
synchronously after the component boundary, parent initialization, and client
props are ready. Do not return a Promise.

Return a function when the initializer creates something that must be cleaned
up. Citry calls it before that instance initializes again and when the
instance leaves the page:


```js
$component(({ els }) => {
  const chart = createChart(els[0]);
  return () => chart.destroy();
});
```


The initializer receives these values:

| Name | Value |
|---|---|
| `id` | The current server render ID. A rerender may replace it. |
| `els` | A stable array containing the instance's current element roots. It is empty for a rootless component. |
| `data` | A fresh instance-local graph parsed from the JSON returned by [`js_data()`](/v/0.4.2/reference/component/#citry-component-js-data), or `null`. |
| `graph` | The current ownership route and source metadata when the instance belongs to a client graph. |
| `props` | The stable, reactive, top-level read-only values declared by the configuration form. The callback form receives an empty object. |
| `scope` | The stable reactive object available to Alpine expressions inside this component. Its top-level server-data keys are seeded before init. |
| `state` | The component's reactive Events State, or `null` when the component declares no Events. |
| `i18n` | The nearest client-enabled i18n service, or `null` outside such a provider. |
| `effect(fn)` | Run a managed reactive effect. It returns an early-stop function and stops automatically before cleanup. |
| `reactive(value)` | Turn an object or array into an Alpine reactive proxy. |
| `provide(key, value)` | Provide a value to rendered descendants during synchronous initialization. |
| `inject(key, default?)` | Read the nearest inherited client value. Missing values throw unless a default was supplied. |
| `unprovide(key)` | Hide an inherited value from rendered descendants during synchronous initialization. |
| `sendEvent(name, args?, opts?)` | Call one of this component's declared server events and return a Promise for its data result. |
| `onEvent(name, callback)` | Listen for server-dispatched events targeting this instance and return an unsubscribe function. |
| `loading(name?)` | Return whether any handler, or one named handler, is queued or running. |
| `error(name?)` | Return the newest retained error, or the retained error for one named handler. |

`$component` is optional when the template only needs server data in Alpine
expressions. Returning `{"count": 0}` from `js_data()` makes `count` available
to `x-text="count"` and `@click="count++"` directly. On a compatible rerender,
Citry refreshes current seeded keys and removes old seeded keys that disappeared,
while preserving unrelated fields added by the callback.

A prop declaration accepts `type`, `required`, and `default`. `type` may be a
constructor or an array of constructors. `required` defaults to `false`. Use a
factory for an object or array default so instances do not share one mutable
value:


```js
props: {
  filters: {
    type: Object,
    default: () => ({}),
  },
}
```


The [Client interactivity](/v/0.4.2/concepts/client-interactivity/) page explains
component boundaries, client props, slot scope, and rootless components. The
[Component JavaScript and CSS](/v/0.4.2/advanced/js-and-css-dependencies/) explains
when component scripts load.

<h3 class="doc-heading" id="component-i18n"><code>$component.i18n</code></h3>

The `i18n` value in a `$component` initializer is the same service exposed as
`$i18n` to Alpine expressions. It is `null` unless the component is below a
client-enabled `<c-i18n>` provider. Use it for browser-created destinations or
other imperative code; use the `$c-tr` template binding for stable text and
HTML attributes.

## Alpine magics

Citry adds the following magics to Alpine expressions inside an active Citry
component. The event-related magics act on the component instance that owns
the expression. The context magics follow Citry's rendered ownership path,
including slots and teleports.

<h3 class="doc-heading" id="i18n"><code>$i18n</code></h3>

Read the nearest client-enabled i18n provider. Access outside one throws an
error. The service has this public shape:

| Member | Meaning |
|---|---|
| `context` | Readonly locale, fallback, direction, time-zone, and revision data. |
| `status` | Readonly provider loading state. |
| `tr(message, values?, options?)` | Return loaded message text. Use `{ attr: "name" }` for a Fluent attribute. |
| `resolve(message, values?, options?)` | Return frozen `{ text, locale, direction, usedFallback }` metadata. |
| `format` | Named number, percent, currency, date, time, datetime, relative-time, list, and unit formatters. |
| `parse` | Strict number and percent parsers. Each returns `{ input, state, value, error, valid }`. |
| `ensureMessages(messages)` | Load one public message ID or a list before a dynamic synchronous lookup. |
| `switchLocale(locale)` | Atomically switch this provider subtree and return a committed or stale result. |
| `subscribe(callback)` | Call back immediately and after context changes; returns an unsubscribe function. |
| `bind(options)` | Keep a browser-created destination translated; returns `refresh()` and `dispose()`. |


```citry-html
<c-i18n tag="section" client>
  <output x-text="$i18n.tr('my-app-status')"></output>
  <button @click="$i18n.switchLocale('cs-CZ')">Čeština</button>
</c-i18n>
```


Ordinary server `tr()` output is plain HTML and does not react to
`switchLocale()`. See [Browser i18n](/v/0.4.2/i18n/browser/) for `$c-tr`, dynamic
message loading, `bind()`, and the exact ownership rules.

<h3 class="doc-heading" id="state"><code>$state</code></h3>

Read the component's reactive public Events State. Assigning a writable field
queues that change for the component's next server call. A field excluded by
`State._public` cannot be read, and a field excluded by `State._model` cannot
be written.


```citry-html
<button @click="$state.count++">Add one</button>
<output x-text="$state.count"></output>
```


State travels through the browser and must be treated as client input. See
[Security](/v/0.4.2/security/#treat-state-as-client-input).

<h3 class="doc-heading" id="loading"><code>$loading</code></h3>

Return whether this component has a queued or running server call. Pass an
event name to check only that handler. An unknown handler name throws an
error.


```citry-html
<button :disabled="$loading('save')">
  <span x-show="!$loading('save')">Save</span>
  <span x-show="$loading('save')">Saving...</span>
</button>
```


<h3 class="doc-heading" id="error"><code>$error</code></h3>

Read retained handler errors as
`{ status, code, message, fieldErrors? }`, or `null` when there is no matching
error. Call `$error()` for the newest retained error across this component's
handlers. Pass a handler name to read only that handler. An unknown handler
name throws an error.


```citry-html
<p
  x-show="$error('save')"
  x-text="$error('save')?.message"
></p>
```


A successful call clears only its own handler's error. A retry leaves that
error visible while the new call is queued or running, then replaces it on
failure or clears it on success. Reading an error does not clear it.

<h3 class="doc-heading" id="send-event"><code>$sendEvent</code></h3>

Call a declared server event from an Alpine expression:


```js
$sendEvent(name, args?, opts?)
```


The method returns a Promise. It resolves with the handler's data result and
rejects with a structured event error. `opts.timeout` overrides the request
timeout. `opts.wait: false` lets a call bypass the component's event queue.


```citry-html
<button
  @click="result = await $sendEvent('preview', { page: 2 })"
>
  Preview page 2
</button>
```


Only imperative calls receive a returned
[`actions.Data`](/v/0.4.2/reference/events/#citry-ext-events-actions-data) value. A declarative `@c-*`
binding starts the same handler but does not expose its Promise result. Return
[`actions.Dispatch`](/v/0.4.2/reference/events/#citry-ext-events-actions-dispatch) when browser code must
observe a result from a declarative call.

<h3 class="doc-heading" id="on-event"><code>$onEvent</code></h3>

Listen for server-dispatched events targeting this component instance:


```js
const stop = $onEvent("cart:changed", (detail) => {
  console.log(detail);
});
```


The return value removes the listener. Use the `onEvent` member inside
`$component` when the subscription should automatically share the component
initializer's cleanup lifetime.

<h3 class="doc-heading" id="provide"><code>$provide</code></h3>

Provide one value to rendered descendants:


```citry-html
<section x-init="$provide('theme', { name: 'dark' })">
  <c-slot />
</section>
```


The key may be a non-empty string or a Symbol. Call `$provide` during
synchronous directive initialization, normally from `x-init`. To change the
value later, provide one reactive object and update its fields.

<h3 class="doc-heading" id="inject"><code>$inject</code></h3>

Read the nearest inherited value. Citry returns the exact value that was
provided. A missing key throws unless you pass a default:


```citry-html
<output x-text="$inject('theme', 'system')"></output>
```


The helper is bound to the element where the magic is read. Its lookup follows
Citry's rendered ownership path rather than relying only on physical DOM
parents.

<h3 class="doc-heading" id="unprovide"><code>$unprovide</code></h3>

Hide an inherited value from rendered descendants:


```citry-html
<section x-init="$unprovide('theme')">
  <output x-text="$inject('theme', 'system')"></output>
</section>
```


Call `$unprovide` during synchronous directive initialization. A nearer
`$provide` can establish the same key again for its own descendants.

See [Provide and inject](/v/0.4.2/concepts/provide-and-inject/) for shadowing, slot
placement, reactive updates, and multi-placement behavior.

## Page-wide APIs

Use these methods from page scripts and integrations rather than from one
component's Alpine expressions.

<h3 class="doc-heading" id="citry-alpine-before-start"><code>Citry.alpine.beforeStart</code></h3>

Register an Alpine plugin before Citry starts its owned Alpine runtime:


```js
Citry.alpine.beforeStart((Alpine) => {
  Alpine.plugin(myPlugin);
});
```


The callback receives Citry's pinned Alpine object. Calling `beforeStart`
after startup has begun throws an error. Do not load a second Alpine build.

<h3 class="doc-heading" id="citry-events-send"><code>Citry.events.send</code></h3>

Call a server event on any interactive component instance:


```js
Citry.events.send(target, name, args?, opts?)
```


`target` is a current render ID or an Element inside the target instance. The
method returns the same kind of Promise as `$sendEvent` and the component
initializer's `sendEvent` member.

<h3 class="doc-heading" id="citry-events-on"><code>Citry.events.on</code></h3>

Listen page-wide for a server-dispatched event:


```js
const stop = Citry.events.on("cart:changed", (detail) => {
  updateHeader(detail);
});
```


The callback receives the event's `detail`. The returned function removes the
listener. Unlike `$onEvent`, this listener is not limited to one component
instance.

<h3 class="doc-heading" id="citry-events-configure"><code>Citry.events.configure</code></h3>

Set page-wide defaults for later event calls:


```js
Citry.events.configure({
  timeout: 45_000,
  url: "/citry/ext/events/",
});
```


| Option | Meaning |
|---|---|
| `csrf` | The token source and request-header name. It accepts `cookie`, `header`, or a `token` string or function. |
| `timeout` | Milliseconds before a call rejects. The default is `30000`. |
| `transport` | The registered transport name. The default is `"fetch"`. |
| `url` | Override the Events route base URL. Normally Citry reads it from the page manifest. |

<h3 class="doc-heading" id="citry-events-register-transport"><code>Citry.events.registerTransport</code></h3>

Register a page-wide event transport under a name:


```js
Citry.events.registerTransport("custom", {
  send: async (envelope) => sendThroughHost(envelope),
});
```


The transport's `send` method receives one Citry event envelope and returns
its result envelope or a Promise for it. Select the transport with
`Citry.events.configure({ transport: "custom" })`.

<h3 class="doc-heading" id="citry-events-apply-actions"><code>Citry.events.applyActions</code></h3>

Apply a valid result envelope's `actions` array to the current page:


```js
await Citry.events.applyActions(result.actions);
```


The method validates the array, applies its actions in order, and returns a
Promise. It is primarily useful for custom transports, integration tests, and
hosts that intercept Citry event responses.

The Events guides cover [State](/v/0.4.2/events/state/), [template
bindings](/events/bindings/), [returned actions](/v/0.4.2/events/actions/), and
[direct HTTP routes](/v/0.4.2/events/http/). [Alpine
runtime](/advanced/alpine-runtime/) covers plugins, CSP, graph markers, and
deployment.<script src="/citry/citry.js"></script><script type="application/json" data-citry-graph>{"delimiters":{"format":"citry:g1"},"graphs":[{"componentClasses":[],"componentExecutionOrderConstraints":[],"componentInstances":[],"fills":[],"graphId":0,"nestedComponents":[],"slotRegions":[],"sourceLocations":[]}],"mode":"production","protocol":"citry-client-graph/1","revision":"16111e302b0b67f45a6c98682743d59aa151d6f7ac93c97d9e3cf1a14dd08fa7"}</script><script type="application/json" data-citry>{"markLoaded": {"js": ["L2NpdHJ5L2V4dC9ldmVudHMvcnVudGltZS5qcw=="], "css": []}, "fetch": {"js": [], "css": []}, "calls": [], "cssInstances": [], "graph": "16111e302b0b67f45a6c98682743d59aa151d6f7ac93c97d9e3cf1a14dd08fa7", "alpineRuntime": "standard"}</script><script src="/citry/ext/events/runtime.js"></script>
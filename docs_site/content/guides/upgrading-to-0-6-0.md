---
title: Upgrade to Citry 0.6.0
description: Move a Citry 0.5.x project from the Alpine browser runtime to the Vue runtime in Citry 0.6.0, step by step.
---

# Upgrade to Citry 0.6.0

Citry 0.6.0 runs component behavior in the browser with Vue instead of
Alpine. Citry compiles each component template to a Vue component on the
server, and the browser runs those components in one pinned Vue runtime.
Most Python components, templates, `c-*` attributes, slots, and Events
handlers keep working. The bulk of the work is on the browser side: every
`x-*` attribute, every Alpine expression, and the `$component` initializer
move to Vue. Some server-side code and templates change too, such as
attributes on component tags, render targets in Events handlers,
`js_data()` key names, lint settings, and extension hooks; each section
below names the change.

You need to act if your project has any of these:

- component JavaScript (`Component.js`, `js_file`, or `$component`);
- `x-*` attributes, or `@event` and `:attr` bindings that relied on Alpine;
- `$c-props` on a component tag;
- Events handlers that return `actions.Render` with a CSS selector as the
  target;
- a custom Events transport, or page scripts that use `Citry.*` globals;
- a component class named `Mark`;
- `LintSettings` or `Component.Lint` with the Alpine rule names;
- an extension that adds page dependencies or routes, or a tool that reads
  `citry.analysis` results;
- `citry-ui` components or the `citry-lsp` language server;
- `#c-ignore` on a component tag, or around content that holds
  components or Vue bindings;
- several worker processes that serve interactive pages, or a proxy or CDN
  in front of Citry's files.

A project that only renders static HTML from Python mainly needs to upgrade
the packages, check its `#c-ignore` markers, rename a component named
`Mark`, check component tags for `:name`, `v-*`, and `ref` attributes the
child read as kwargs, and work through
[Update settings and extensions](#update-settings-and-extensions).

## Upgrade the packages together

Upgrade Citry, its UI library, and the language server in the same step:

```console
python -m pip install -U "citry==0.6.0" "citry-ui==0.3.0" \
  "citry-lsp==0.2.0"
```

Citry 0.6.0 installs `citry-core` 1.8.0 for you. Upgrade `citry-lsp` to
0.2.0, the release that requires Citry 0.6.0. pip lets `citry-lsp` 0.1.7
stay installed next to Citry 0.6.0, but it then fails to start with
`ImportError: cannot import name 'BROWSER_UNKNOWN_COMPONENT_PROP'`, and the
editor shows no Citry diagnostics. `citry-ui` 0.2.x installs next to Citry
0.6.0 too, but its components render with no browser behavior.

## Replace Alpine directives with Vue

The first thing you notice after upgrading is a page that looks right and
does nothing: a menu that does not open, a counter that does not count. Citry
still writes `x-*` attributes into the HTML, but nothing reads them. There is
no error in Python or in the browser console.

Local browser state moves from `x-data` into the component's JavaScript, and
each directive becomes its Vue form:

```citry
class Faq(Component):
    # 0.5.1
    template = """
      <div x-data="{ open: false }">
        <button x-on:click="open = !open">Toggle</button>
        <p x-show="open" x-cloak>Ships in two days.</p>
      </div>
    """
```

```citry
class Faq(Component):
    # 0.6.0: state lives in the Vue component.
    template = """
      <div>
        <button @click="open = !open">Toggle</button>
        <p v-show="open">Ships in two days.</p>
      </div>
    """

    js = """
      $component({
        data() {
          return { open: false };
        },
      });
    """
```

State that Python computes still comes from
[`js_data()`][citry.Component.js_data]. Each key it returns is now a member
of the Vue component, so `this.count` in JavaScript and `count` in a
template both read it.

| 0.5.1 (Alpine) | 0.6.0 (Vue) |
| --- | --- |
| `x-data="{...}"` | `$component({ data() {...} })` or `js_data()` |
| `x-text`, `x-html`, `x-show` | `v-text`, `v-html`, `v-show` |
| `x-model` | `v-model` |
| `x-for` | `v-for` with a `:key` |
| `x-if` | `v-if`, `v-else-if`, `v-else` |
| `x-on:click`, `@click` | `@click` or `v-on:click` |
| `x-bind:class`, `:class` | `:class` or `v-bind:class` |
| `x-ref` and `$refs` | `ref` and `this.$refs` |
| `x-init` | `mounted()` or [`onServerRender`](/reference/browser-apis/#on-server-render) |
| `x-effect` | `watch`, or `Citry.vue.watchEffect` in `setup()` |
| `x-cloak` | Delete it (see below) |

Delete `x-cloak` and its `[x-cloak] { display: none }` rule. Nothing removes
the attribute any more, so that rule hides the element for good. The served
HTML already contains the page's content; see
[what a page shows before Vue starts](/advanced/vue-runtime/#what-a-hydrated-page-shows-before-vue-starts).

[Vue in templates](/syntax/vue/) covers the directives Citry accepts and the
few it rejects, such as `<Transition>` and `<Teleport>`.

### Find the `x-*` attributes you missed

`citry check` and the editor report each `x-*` attribute left on an HTML
element. A leftover `x-cloak` is an error; other `x-*` attributes are
warnings. Run the check before you test the pages:

```console
citry --app myproject.app:app check
```

If another library on the page reads `x-*` attributes, set
`rule_alpine_attribute="ignore"` in `LintSettings` or in the component's
`Lint` class.

### Rewrite Alpine-only event modifiers

Vue has no `.outside`, `.window`, `.document`, `.debounce`, or `.throttle`
modifiers. The template fails when it loads, and the message names the Vue
way to write the listener:

```citry-html
{# Fails: Vue has no .outside modifier #}
<div @click.outside="open = false;">...</div>
```

Write that behavior in a method instead, for example a `mousedown` listener
on `document` that you add in `mounted()` and remove in `unmounted()`. For a
server call, the `@c-*` Events bindings still accept `.debounce` and
`.throttle`; see [Bind events in templates](/events/bindings/).

### End statement listeners with a semicolon

Alpine ran a listener such as `@click="if (ok) save()"` as written. Vue
reads a listener value as an expression unless it contains a `;`, so this
one stops the render with a Vue compile error ("Error parsing JavaScript
expression"). End a statement with `;`, or move it into a method:

```citry-html
{# Fails: Vue reads an `if` statement as an expression #}
<button @click="if (ok) save()">Save</button>

{# Works #}
<button @click="if (ok) save();">Save</button>
```

### Send events to the parent with `$emit`

Alpine's `$dispatch` does not exist. Declare the event in the child and emit
it with Vue's `$emit`:

```citry-html
{# 0.5.1 #}
<button @click="$dispatch('select', 'red')">Red</button>

{# 0.6.0 #}
<button @click="$emit('select', 'red')">Red</button>
```

```js
$component({
  emits: ["select"],
});
```

The parent listens on the component tag with `@select="..."`. A Vue event
reaches only that listener; it does not bubble through the DOM. When page
code outside the parent must hear it, dispatch a DOM `CustomEvent` from an
element you hold in a `ref`.

## Pass browser values to a child as Vue props

`$c-props` is gone, and a template that uses it stops loading with
`'$c-props' was removed; use native Vue ':prop' or 'v-bind' syntax`. Pass
each value as a Vue prop, and declare the props in the child:

```citry-html
{# 0.5.1 #}
<c-Dialog $c-props="{ open }" />

{# 0.6.0 #}
<c-Dialog :open="open" />
```

```js
$component({
  props: {
    open: Boolean,
  },
});
```

The same applies to Citry UI 0.3.0 components: write `:open="open"` on
`<c-CDialog>` instead of `$c-props`. A callback that 0.5.1 passed as a prop
usually becomes an emitted event, as shown above.

## Update attributes on component tags

The attributes on a `<c-Child>` tag now split into Python inputs and Vue
bindings by their spelling:

- **`:name`, `v-bind`, `v-if`, `v-else-if`, `v-else`, `v-model`, `v-show`,
  custom `v-*` directives, and `ref` are Vue bindings.** 0.5.1 passed them to
  the child as Python kwargs. A child that read `kwargs[":class"]` or a `ref`
  kwarg no longer receives it. Pass a plain kwarg or a `c-attrs` mapping
  instead.
- **`@event` listens for an event the child emits.** In 0.5.1 it added a DOM
  listener to every root element of the child. Now the child declares the
  event in `emits` and calls `$emit`. A native event such as `@click` that
  the child does not declare goes to the child's single root element;
  a child with several roots must place it with `v-bind="$attrs"`. See
  [Listen to child events](/concepts/client-interactivity/#listen-to-child-events).
- **`x-on:event` on a component tag stops the render** with
  `Alpine binding 'x-on:click' was removed; use native Vue v-on or @event
  syntax.` Write `@click` instead.
- **Timed and polling Events bindings move inside the child.** A
  `.debounce` or `.throttle` `@c-*` binding, or `@c-poll`, on a component
  tag stops the render. Put it on an element in the child's template.

## Check your `#c-ignore` markers

On an HTML element, `#c-ignore` keeps its contents as the server first
rendered them, and a later render leaves them alone, so a chart or map
library can own them. The contents can hold only HTML, `{{ }}`
expressions, `<c-if>`, `<c-for>`, and `<c-raw>`. Move any component,
slot, Vue binding, or `ref` out of them; the template fails when it loads
with a message that says which. Put a `ref` on the `#c-ignore` element
itself:

```citry-html
<div class="chart" ref="chart" #c-ignore>
  <canvas></canvas>
</div>
```

On a component tag, `#c-ignore` fails when the template loads. Move it
onto the element inside the component's template that the library
manages. On `<table>`, `<tbody>`, `<tr>`, and the other table row
elements it fails too; wrap the table in a `<div #c-ignore>` instead. See
[`#c-ignore`](/syntax/dynamic-attributes/#c-ignore-keep-contents-that-a-library-manages).

## Write Vue bindings in the template, not in Python

In 0.5.1, Python could build Alpine code as a string and write it into an
attribute. An interactive component in 0.6.0 rejects a Python-built Vue
binding, whether it comes from `c-:attr`, `c-@event`, or a `c-bind` mapping
with a `:x`, `@x`, or `v-*` key:

```citry-html
{# Stops the render: Python writes browser code #}
<div c-:class="'{ active: selected }'">...</div>

{# Works: the binding is in the template #}
<div :class="{ active: selected }">...</div>
```

The error names the attribute and says that a Python-resolved attribute
"cannot introduce Vue syntax". Pass the values the binding needs through
`js_data()` or props. A static page that never loads Vue writes such
attributes as plain text, where they do nothing.

### Set each attribute from Python or from Vue

One element can no longer set the same attribute both ways. `c-title`
together with `:title` fails when the template loads, with a message that
the two set the same attribute. Keep one of them. `:class` and `:style` are
the exception: they join `class` and `c-class`, or `style` and `c-style`,
as Vue does. For the same reason, an object `v-bind="..."` or a dynamic
`:[name]` cannot sit on an element that has any `c-*` attribute, and
`:key` cannot sit next to `#c-key`. See
[Combine `:class` and `:style` with `c-class` and `c-style`](/syntax/vue/#combine-class-and-style-with-c-class-and-c-style).

### Keep Vue-bound content inside a group's tag

Content that you pass into a group component, such as Citry UI's `CTabs`,
must be written inside the group's tag when it uses Vue data, handlers,
`v-model`, a `ref`, or a `@c-*` binding. When a separate component writes
that content and the page passes the component in, the render stops with
an error that names the content, the component that wrote it, and the line.
Move the content inside the group's tag, or set `transparent = True` on
the component that writes it, so it renders its content in place. See
[Keep Vue-bound group content inside the group's tag](/syntax/vue/#keep-vue-bound-group-content-inside-the-groups-tag).

## Move `$component` initializers to Vue Options

`$component(callback)` and `$component({ init })` still work, with a
different timing. Citry calls the function after the component mounts,
children before their parent, and again after each server render that
updates this component. A change to local Vue state does not call it. Code
that needs a value before the first render belongs in `data()` or
`setup()`. The function may be `async`: Citry does not wait for it, a
cleanup it resolves to still runs, and a rejection is logged instead of
stopping the page. The function receives a smaller context than in 0.5.1.

The context adds `component` (the live Vue instance) and `revision`. These
0.5.1 values still work: `id`, `els`, `state`, `i18n`, `sendEvent`,
`onEvent`, `loading`, and `error`. The others are gone; reading one gives `undefined`:

| 0.5.1 context value | 0.6.0 replacement |
| --- | --- |
| `data`, `scope`, `props` | The Vue instance: `component.name` or `this.name` |
| `effect(fn)` | `Citry.vue.watchEffect(fn)` inside the callback |
| `reactive(value)` | `Citry.vue.reactive(value)` |
| `provide`, `inject` | The Vue `provide` and `inject` options |
| `unprovide`, `graph` | No replacement |

```js
// 0.5.1
$component(({ data, scope, effect }) => {
  scope.doubled = data.count * 2;
  effect(() => console.log(scope.doubled));
});
```

```js
// 0.6.0
$component({
  computed: {
    // `count` is a js_data() key, so it is an instance member.
    doubled() {
      return this.count * 2;
    },
  },
  onServerRender({ component }) {
    // Citry stops this effect before the next call.
    Citry.vue.watchEffect(() => console.log(component.doubled));
  },
});
```

A callback that reads `props.name` fails with a `TypeError`, because `props`
is `undefined`; read `component.name` instead. The
[Browser APIs reference](/reference/browser-apis/#component) lists every
option `$component` accepts.

### Use Vue provide and inject in the browser

The template helpers `$provide`, `$inject`, and `$unprovide` do not exist in
0.6.0. Provide a value from a component with Vue's `provide` option and read
it in a descendant with `inject`. See
[Provide and inject in client code](/concepts/provide-and-inject/#provide-and-inject-in-client-code).

### Rename names Vue reserves

- A [`js_data()`][citry.Component.js_data] key that starts with `$` or `_`,
  or the key `citryId`, stops the render with a `ValueError` that names the
  component and the key. Rename it, for example `_count` to `count`.
- A component class named `Mark`, or one registered as `mark`, now fails
  when it is defined, with an `AlreadyRegistered` error that says the
  built-in `<c-mark>` reserves the name. Rename the class or give it another `name`. See
  [Built-in tags](/reference/builtins/#targeted-updates).

[Names Citry reserves on the component instance](/advanced/vue-runtime/#names-citry-reserves-on-the-component-instance)
lists the rest.

## Update Events code

- **Address a render with `render:<id>` or `mark:<name>`.** `actions.Render`
  no longer accepts a CSS selector as its `target`, or a `swap` other than
  `"morph"` for an addressed target. Wrap the region in `<c-mark>` and
  target it by name:

  ```citry-html
  <c-mark name="cart-badge">
    <c-CartBadge c-count="cart.count" />
  </c-mark>
  ```

  ```python
  return actions.Render(
      CartBadge(count=cart.count),
      target="mark:cart-badge",
  )
  ```

  `Citry.events.applyActions` follows the same rule for Render and Event
  actions. Each target names one place, so a 0.5.1 selector that matched
  several elements becomes one Render action per target. One response can
  return them all as adjacent Render actions without a delay, as long as
  no target sits inside another. See [Event actions](/events/actions/).
- **Pass `Citry.events.applyActions` only the fields each action
  defines.** It now rejects an action with a field it does not know, a
  value that is not plain JSON such as `undefined`, or an array with gaps
  such as `[a, , b]`, with a `ProtocolValueError` (a `TypeError`), before it
  applies any action. Remove the extra fields from actions your page code
  builds or forwards. A `state` action you build, for `applyActions` or in
  an `on_event_result` hook, must now include `publicState`, the
  component's public State values.
- **Forward `request.headers` from a custom transport.** Citry now calls
  `send(envelope, request)`. A 0.5.1 transport that sends only the envelope
  fails every handler that returns a render, with "Vue Events requires
  current app, occurrence, and revision headers." See
  [custom event transports](/reference/browser-apis/#custom-event-transports).
- **`$onEvent` hears only the server.** A listener added with `$onEvent` or
  the callback's `onEvent` receives the events that this component's server
  handlers dispatch. A DOM event that page code fires inside the component
  no longer reaches it; listen for that with `addEventListener` on an
  element you hold in a `ref`.
- **Remove `wait: false`.** Calls from one app are sent in order, and
  `$sendEvent` or `Citry.events.send` with `wait: false`, or with an option
  it does not know, now rejects. For live search, declare the handler with
  `@event(latest_wins=True)`.
- **Replace whole `$state` fields.** Writing to a nested value, such as
  `$state.tags.push("new")`, now throws "Nested $state values are
  read-only". Assign the whole field: `$state.tags = [...$state.tags, "new"]`.
- **Wait for `citry:ready` before calling `Citry.events.send`.** A call
  made before the page's Vue app mounts rejects instead of waiting.
- **Set security modes on the `Citry` instance.** On a page with Events,
  pass `security_csp` and `security_javascript` to `Citry(...)`. Passing
  a different value to `serialize()` raises `ValueError`, because a later
  server render of that page must keep the same policy.
- **Update `citry:events:stale` listeners.** The event reports
  `superseded`, `retired`, `epoch`, `disposed`, or `version`. A listener
  that checks for `cancelled` or `timeout` never sees them.
- **Stop reading `data-citry-events` script tags.** Pages no longer carry
  them, so page code that parsed them finds nothing. Read Events values
  inside the component through `$state`, `$loading`, and `$error`.

## Replace removed browser globals

| Removed | What to use |
| --- | --- |
| `Citry.alpine.beforeStart(fn)` | [`Citry.vue.use(plugin)`](/reference/browser-apis/#citry-vue-use) called from a `defer` script in `<head>` or a script an extension adds to `ctx.early_scripts`. An Alpine plugin has no direct replacement. |
| `Citry.manager.*` (`loadJs`, `loadCss`, `callComponent`, ...) | Declare assets on the component with `Component.js`, `Component.css`, or `Dependencies`. Interactive fragments load their own assets. |
| `Citry.i18n.provider` | `component.$i18n` or `this.$i18n`; see [Browser i18n](/i18n/browser/). |
| `window.Alpine`, `alpine:init` | The `citry:ready` event on `document`. |
| `/ext/events/runtime-csp.js` route | Nothing. Citry serves one runtime for every CSP mode. |

## Update settings and extensions

Rename the lint settings in `LintSettings` and in any `Component.Lint`:

```python
# 0.5.1
LintSettings(
    rule_unknown_alpine_variable="warning",
    alpine_variables={"theme": str},
)

# 0.6.0
LintSettings(
    rule_unknown_vue_variable="warning",
    vue_variables={"theme": str},
)
```

The old names raise `TypeError` from `LintSettings` and `ValueError` when a
component class with the old `Lint` names is defined. A tool that builds
`TemplateLintInfo` uses the same new names, `rule_unknown_vue_variable` and
`vue_variables`. Keep only the names your Vue expressions still read; an
Alpine magic means nothing to Vue.

Update scripts that filter `citry check --format json` output by code:

| 0.5.1 code | 0.6.0 code |
| --- | --- |
| `citry.alpine.unknown-variable` | `citry.vue.unknown-variable` |
| `citry.component-js.unknown-data-member` | `citry.component-js.unknown-member` |
| `citry.browser.unknown-component-prop` | Removed |

Also check these settings and hooks:

- **`security_csp="strict"`** used to select Citry's Alpine CSP build and
  limit the expressions you could write. It now scans the final HTML for raw
  `<script>` and `<style>` elements, `on*` attributes, and `javascript:` URLs.
  Any Vue expression works, because Citry compiles templates on the server.
  See [Security](/security/#choose-a-csp-compatibility-mode).
- **Components that never start behind a proxy or CDN:** the page shows
  its server-rendered HTML, but the console reports a CORS or Subresource
  Integrity error. When the proxy or CDN serves Citry's files from another
  host, or the page runs in a sandboxed iframe, pass through the
  `Access-Control-Allow-Origin: *` header that Citry's asset routes now
  send. See
  [Keep the CORS header when a proxy or CDN serves Citry's files](/security/#keep-the-cors-header-when-a-proxy-or-cdn-serves-citrys-files).
- **Scripts on an interactive page must be classic JavaScript.** This
  covers a component's `Dependencies` scripts and an extension's
  `ctx.scripts` and `ctx.early_scripts`. A `type="module"` or JSON data
  script, or a script marked `async`, `defer`, or `nomodule`, raises
  `ValueError` when the page or an Events response is serialized, because Citry loads these
  scripts itself, one after another in list order. Scripts in
  `ctx.early_scripts` load before `ctx.scripts`.
- **`@event(methods=...)` and `Events._methods`** accept only GET, HEAD,
  POST, PUT, PATCH, DELETE, and OPTIONS. Any other method raises
  `ValueError` when the class is defined.
- **`URLRoute(methods=...)`** is checked when you build the route. Pass a
  non-empty tuple of uppercase method names, such as `("GET", "POST")`. A
  list raises `TypeError`. An empty tuple raises `ValueError`, and so does
  a lowercase name such as `"get"`, which no framework adapter would
  match.
- **`parameters` in `citry.analysis` results** leaves out `self` or `cls`.
  In the results of `analyze_template_data_source`,
  `analyze_js_data_source`, and `analyze_css_data_source`,
  `parameters[0]`, when present, is the kwargs parameter. A tool that
  skipped the first entry should read from index 0. The Alpine helpers in
  `citry.analysis` are removed; use `VueLintConsumer`, `VueLintFinding`,
  `lint_unknown_vue_variables`, and `VUE_AMBIENT_NAMES` in place of
  `AlpineLintConsumer`, `AlpineLintFinding`,
  `lint_unknown_alpine_variables`, and `ALPINE_AMBIENT_NAMES`.
- **`OnSerializeContext` and `OnDependenciesContext`** gain a
  `selected_render` field, the render being serialized. Code that builds
  these contexts with positional arguments, such as an extension test,
  now fails or passes values to the wrong fields. Build them with
  keyword arguments.
- **`OnDependenciesContext.before_manifest` is now `early_scripts`.**
  Rename `ctx.before_manifest` to `ctx.early_scripts` in your
  `on_dependencies()` hooks; the scripts it holds still run before
  `ctx.scripts`. The old name has no alias, so a hook that still uses it
  raises `AttributeError`, naming `early_scripts`, when the hook runs.
- **Ownership APIs** are removed: the `citry.ownership` and
  `citry.ownership_manifest` modules and the `ownership` parameters of
  `CitryContext` and `CitryElement`. Delete imports of these modules and
  those arguments.
- **`<c-raw>` and `Markup` inside an interactive component** must hold a
  complete HTML fragment: every tag closed, no stray `<`. Otherwise the
  render stops with an error such as "The `<c-raw>` block at line 2,
  column 10 is not a complete HTML fragment", which names the input and
  explains the rule. Static pages do not have this rule.
- **An interactive page template** that writes `<!doctype html>` or
  `<html>` must put its content inside one `<body>` element. Otherwise
  serialization stops with an error such as "Interactive Vue document
  serialization requires one well-ordered body element."

## Share the cache between worker processes

On a deployment with several worker processes, an interactive page can
load without starting: the browser console shows 404 responses for
component code or stylesheets. The worker that rendered the page stored
them in the Citry cache, and another worker, with its own in-memory
cache, answered the request.

Point every worker at one shared cache backend, such as Redis or
DiskCache. Without a configured cache, a single process keeps this code
in memory up to `vue_asset_max_bytes` (64 MiB by default). A page always
finds its own files right after it arrives, but a page left open long
enough to ask for a dropped file gets the same 404, so raise
the limit or configure a cache. See
[Share the cache between worker processes](/web-frameworks/#share-the-cache-between-worker-processes).

## Clean up integrations

- **HTMX:** delete `citry-htmx.js` and `hx-ext="citry-fragments"`. Citry no
  longer writes the markers that helper preserved. See
  [Use Citry with HTMX](/guides/htmx/).
- **`data-cid-*` selectors:** only static output carries these attributes.
  Elements that Vue renders have none, so CSS or scripts that select
  `[data-cid-...]` stop matching. Use a Vue `ref` in component JavaScript.
- **`data-citry-key` selectors:** `#c-key` on an element no longer writes a
  `data-citry-key` attribute. It still keeps rows matched across renders.
- **Render cache:** entries saved by Citry 0.5.x count as misses and are
  saved again on the next render. You do not need to clear the cache.

## Features to adopt after upgrading

- Interactive pages send their content in the served HTML, so search engines
  and readers without JavaScript see it. Tune this with `ssr` and
  `ssr_element_threshold`; see
  [Send page content in the served HTML](/advanced/vue-runtime/#send-page-content-in-the-served-html).
- `simple = "vue"` gives a component its own Vue state and assets without a
  Python component instance; see
  [Simple components](/performance/simple-components/#choose-the-components-browser-identity).
- A component tag accepts `v-if`, `v-model`, `v-show`, and custom
  directives; see
  [Use Vue directives on a component tag](/syntax/vue/#use-vue-directives-on-a-component-tag).
- `<c-mark>` names a region that an Events handler can render again; see
  [Built-in tags](/reference/builtins/#targeted-updates).
- A text field keeps what the user typed when its component renders again,
  until the server sends a different value; see
  [Keep what the user typed across renders](/advanced/vue-runtime/#keep-what-the-user-typed-across-renders).
- `citry check` and the editor report a misspelled `js_data()` member and a
  Vue binding that reads a Python loop variable; see
  [Template linting](/ide/template-linting/).

## Upgrade checklist

1. Install `citry` 0.6.0, `citry-ui` 0.3.0, and `citry-lsp` 0.2.0 in the
   same environment.
2. Run `citry check` to find leftover `x-*` attributes, and replace each
   with its Vue form.
3. Move `x-data` state into `data()` or `js_data()`.
4. Rewrite `.outside`, `.window`, `.document`, `.debounce`, and `.throttle`
   modifiers on plain `@event` listeners; `citry check` reports them.
   End a statement listener such as `if (ok) save()` with `;`.
5. Replace `$dispatch` with `$emit` and declare `emits` in the child.
6. Replace `$c-props` with `:name` props, declared in the child's `props`.
7. Move `c-:attr`, `c-@event`, and Vue keys in `c-bind` into the template,
   set an attribute such as `title` with `c-title` or `:title`, not both,
   and write Vue-bound group content inside the group's tag.
8. Check component tags for `:x`, `v-*`, and `ref` attributes the child read
   as kwargs, and for `x-on:`.
9. Keep `#c-ignore` only on HTML elements whose contents a library
   manages, and move it off component tags.
10. Replace `data`, `scope`, `props`, `graph`, `effect`, `reactive`,
    `provide`, `inject`, and `unprovide` in `$component` callbacks.
11. Replace `$provide`, `$inject`, and `$unprovide` with Vue `provide` and
    `inject`.
12. Rename `js_data()` keys that start with `$` or `_`, and a component
    class named `Mark` or registered as `mark`.
13. Change CSS-selector render targets to `render:<id>` or `mark:<name>`.
14. Forward `request.headers` in custom transports.
15. Set `security_csp` and `security_javascript` on the `Citry` instance
    for pages with Events.
16. Update `citry:events:stale` listeners that check for `cancelled` or
    `timeout`, code that reads `data-citry-events` script tags, calls
    that pass `wait: false` or unknown options, and action lists passed
    to `Citry.events.applyActions`, including `publicState` in any `state`
    action you build.
17. Remove uses of `Citry.alpine`, `Citry.manager`, and `Citry.i18n`.
18. Rename the Alpine lint settings and diagnostic codes.
19. Check that dependency scripts on interactive pages are classic
    JavaScript, build `OnSerializeContext` and `OnDependenciesContext`
    with keyword arguments, rename `ctx.before_manifest` to
    `ctx.early_scripts`, and remove `citry.ownership` imports and
    `ownership=` arguments.
20. Pass `URLRoute(methods=...)` as a tuple of uppercase names, and read
    `parameters` from `citry.analysis` results starting at index 0.
21. On a deployment with several workers, configure a shared cache
    backend, and let a proxy or CDN pass `Access-Control-Allow-Origin`
    through for Citry's files.
22. Remove `citry-htmx.js`, `hx-ext="citry-fragments"`, and `data-cid-*` or
    `data-citry-key` selectors.
23. Open each interactive page and check the browser console for `[Citry]`
    errors.

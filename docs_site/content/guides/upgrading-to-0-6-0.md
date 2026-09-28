---
title: Upgrade to Citry 0.6.0
description: Move a Citry 0.5.x project from the Alpine browser runtime to the Vue runtime in Citry 0.6.0, step by step.
---

# Upgrade to Citry 0.6.0

Citry 0.6.0 runs component behavior in the browser with Vue instead of
Alpine. Citry compiles each component template to a Vue component on the
server, and the browser runs those components in one pinned Vue runtime. Your
Python components, templates, `c-*` attributes, slots, and Events handlers
keep working. What changes is the browser side: every `x-*` attribute, every
Alpine expression, and the `$component` initializer move to Vue.

You need to act if your project has any of these:

- component JavaScript (`Component.js`, `js_file`, or `$component`);
- `x-*` attributes, or `@event` and `:attr` bindings that relied on Alpine;
- `$c-props` on a component tag;
- a custom Events transport, or page scripts that use `Citry.*` globals;
- `LintSettings` or `Component.Lint` with the Alpine rule names;
- an extension that adds page dependencies;
- `citry-ui` components or the `citry-lsp` language server.

A project that only renders static HTML from Python needs to upgrade the
packages and nothing else.

## Upgrade the packages together

Upgrade Citry, its UI library, and the language server in the same step:

```console
python -m pip install -U "citry==0.6.0" "citry-ui==0.3.0" citry-lsp
```

Citry 0.6.0 installs `citry-core` 1.8.0 for you. Upgrade `citry-lsp` to the
release that requires Citry 0.6.0. pip lets `citry-lsp` 0.1.7 stay
installed next to Citry 0.6.0, but it then fails to start with
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

Because a leftover `x-*` attribute raises no error, search for them before
you test the pages:

```console
grep -rnE '\bx-[a-z]+' --include='*.py' --include='*.html' .
```

### Rewrite Alpine-only event modifiers

Vue has no `.outside`, `.window`, `.document`, `.debounce`, or `.throttle`
modifiers. Citry compiles an unknown modifier as a key name, so the listener
never runs:

```citry-html
{# Never runs: "outside" is not a key the user can press #}
<div @click.outside="open = false">...</div>
```

Write that behavior in a method instead, for example a `mousedown` listener
on `document` that you add in `mounted()` and remove in `unmounted()`. For a
server call, the `@c-*` Events bindings still accept `.debounce` and
`.throttle`; see [Bind events in templates](/events/bindings/).

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

## Move `$component` initializers to Vue Options

`$component(callback)` and `$component({ init })` still work: Citry calls the
function after the component mounts and after each server render that updates
this component. A change to local Vue state does not call it. The function
receives a smaller context than in 0.5.1.

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
- A component named `mark` now fails when its class is defined, with an
  `AlreadyRegistered` error that says the built-in `<c-mark>` reserves the
  name. Rename the class or give it another `name`.

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
  actions. See [Event actions](/events/actions/).
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
- **Replace whole `$state` fields.** Writing to a nested value, such as
  `$state.tags.push("new")`, now throws "Nested $state values are
  read-only". Assign the whole field: `$state.tags = [...$state.tags, "new"]`.
- **Wait for `citry:ready` before calling `Citry.events.send`.** A call
  made before the page's Vue app mounts rejects instead of waiting.

## Replace removed browser globals

| Removed | What to use |
| --- | --- |
| `Citry.alpine.beforeStart(fn)` | For a custom directive, the Vue `directives` option in `$component`. An Alpine plugin has no direct replacement. |
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
component class with the old `Lint` names is defined. Keep only the names
your Vue expressions still read; an Alpine magic means nothing to Vue.

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
- **`OnDependenciesContext.before_manifest`** raises `RuntimeError` on an
  interactive page. Append those tags to `ctx.scripts` instead.
- **`<c-raw>` and `Markup` inside an interactive component** must hold a
  complete HTML fragment: every tag closed, no stray `<`. Otherwise the render
  stops with `opaque HTML must be a self-contained strict fragment`.
- **An interactive page template** that writes `<!doctype html>` or
  `<html>` must put its content inside one `<body>` element. Otherwise
  serialization stops with an error such as "Interactive Vue document
  serialization requires one well-ordered body element."

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

## New in 0.6.0 you may want

- Interactive pages send their content in the served HTML, so search engines
  and readers without JavaScript see it. Tune this with `ssr` and
  `ssr_element_threshold`; see
  [Send page content in the served HTML](/advanced/vue-runtime/#send-page-content-in-the-served-html).
- `simple = "vue"` gives a component its own Vue state and assets without a
  Python component instance; see
  [Simple components](/advanced/simple-components/#choose-the-components-browser-identity).
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

1. Install `citry` 0.6.0, `citry-ui` 0.3.0, and the `citry-lsp` release that
   requires Citry 0.6.0 in the same environment.
2. Search for `x-*` attributes and replace each with its Vue form.
3. Move `x-data` state into `data()` or `js_data()`.
4. Rewrite `.outside`, `.window`, `.document`, `.debounce`, and `.throttle`
   modifiers on plain `@event` listeners.
5. Replace `$dispatch` with `$emit` and declare `emits` in the child.
6. Replace `$c-props` with `:name` props, declared in the child's `props`.
7. Move `c-:attr`, `c-@event`, and Vue keys in `c-bind` into the template.
8. Check component tags for `:x`, `v-*`, and `ref` attributes the child read
   as kwargs, and for `x-on:`.
9. Replace `data`, `scope`, `props`, `effect`, `reactive`, `provide`, and
   `inject` in `$component` callbacks.
10. Replace `$provide`, `$inject`, and `$unprovide` with Vue `provide` and
    `inject`.
11. Rename `js_data()` keys that start with `$` or `_`, and a component named
    `mark`.
12. Change CSS-selector render targets to `render:<id>` or `mark:<name>`.
13. Forward `request.headers` in custom transports.
14. Remove uses of `Citry.alpine`, `Citry.manager`, and `Citry.i18n`.
15. Rename the Alpine lint settings and diagnostic codes.
16. Move `before_manifest` tags to `scripts`.
17. Remove `citry-htmx.js`, `hx-ext="citry-fragments"`, and `data-cid-*` or
    `data-citry-key` selectors.
18. Open each interactive page and check the browser console for `[Citry]`
    errors.

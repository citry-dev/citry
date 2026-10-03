---
title: Upgrade to Citry 0.6.0
description: Move a Citry 0.5.x project from the Alpine browser runtime to the Vue runtime in Citry 0.6.0, step by step.
---

# Upgrade to Citry 0.6.0

Use this guide to move a project from Citry 0.5.x to 0.6.0. In 0.6.0,
components run in the browser with Vue instead of Alpine. Your Python
components, templates, `c-*` attributes, slots, and Events handlers mostly
keep working. Most of the work is in browser code: `x-*` attributes,
Alpine expressions, and component JavaScript move to Vue.

Work from the top. The first sections affect almost every project with
browser behavior. Later sections apply only if you use that feature, and
each starts with what you see when you skip it. The
[checklist](#upgrade-checklist) at the end lists every step.

A project that only renders static HTML from Python, with no browser
behavior, usually needs only these steps: upgrade the packages,
[check component tag attributes](#update-attributes-on-component-tags),
[check `#c-ignore`](#check-your-c-ignore-markers),
[rename a component named `Mark`](#rename-reserved-names), and work
through [Settings and extensions](#update-settings-and-extensions).

## Upgrade the packages { #upgrade-the-packages-together }

Upgrade Citry, its UI library, and the language server in one step:

```console
python -m pip install -U "citry==0.6.0" "citry-ui==0.3.0" \
  "citry-lsp==0.2.0"
```

Citry 0.6.0 installs `citry-core` 1.8.0 for you.

pip lets older versions stay installed next to Citry 0.6.0, but they break:

- `citry-lsp` 0.1.7 fails to start with
  `ImportError: cannot import name 'BROWSER_UNKNOWN_COMPONENT_PROP'`, and
  the editor shows no Citry diagnostics. `citry-lsp` 0.2.0 is the release
  for Citry 0.6.0.
- `citry-ui` 0.2.x components render, but their browser behavior does not
  work.

## Rewrite Alpine syntax { #replace-alpine-directives-with-vue }

**What you see:** the page looks right but does nothing. A menu does not
open, a counter does not count, and there is no error in Python or in the
browser console. Citry still writes `x-*` attributes into the HTML, but
nothing reads them.

Move local browser state from `x-data` into the component's JavaScript, and
write each directive in its Vue form:

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
    # 0.6.0: the state lives in the Vue component.
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

Delete `x-cloak` and its `[x-cloak] { display: none }` CSS rule. Nothing
removes the attribute any more, so the rule would hide the element for
good. You do not need it: the served HTML already shows the page's
content; see
[what a page shows before Vue starts](/advanced/vue-runtime/#what-a-hydrated-page-shows-before-vue-starts).

[Vue in templates](/syntax/vue/) lists the directives Citry accepts and the
few it rejects, such as `<Transition>` and `<Teleport>`.

### Find leftover `x-*`

Run `citry check` before you test the pages. It reports each `x-*`
attribute left on an HTML element, and so does the editor. A leftover
`x-cloak` is an error; other `x-*` attributes are warnings.

```console
citry --app myproject.app:app check
```

If another library on the page reads `x-*` attributes, turn the warning
off with `rule_alpine_attribute="ignore"` in `LintSettings` or in the
component's `Lint` class.

### Rewrite Alpine modifiers

**What you see:** the template fails to load, and the error names the Vue
way to write the listener.

Vue has no `.outside`, `.window`, `.document`, `.debounce`, or `.throttle`
modifiers:

```citry-html
{# Fails: Vue has no .outside modifier #}
<div @click.outside="open = false;">...</div>
```

Write that behavior in a method instead. For example, add a `mousedown`
listener to `document` in `mounted()` and remove it in `unmounted()`.

To slow down calls to the server, the `@c-*` Events bindings still accept
`.debounce` and `.throttle`; see [Bind events in templates](/events/bindings/).

A key modifier such as `.enter` works only on `keydown`, `keyup`, and
`keypress` listeners. On another event, such as `@click.enter` or
`@input.enter`, the template fails to load, because that event has no key:
Vue would ignore the modifier and run the listener on every click or input
event. Remove the modifier, or listen to `keydown` if you meant the key.

### End statements with `;`

**What you see:** the render stops with a Vue compile error, "Error parsing
JavaScript expression".

Alpine ran a listener such as `@click="if (ok) save()"` as written. Vue
reads a listener as an expression unless it contains a `;`. End a
statement with `;`, or move it into a method:

```citry-html
{# Fails: Vue reads an `if` statement as an expression #}
<button @click="if (ok) save()">Save</button>

{# Works #}
<button @click="if (ok) save();">Save</button>
```

### Use `$emit` { #use-emit }

**What you see:** `citry check` reports `$dispatch` as an unknown
variable, and clicking throws an error in the browser console, because
Alpine's `$dispatch` does not exist in Vue.

Emit the event with Vue's `$emit`, and declare it in the child's `emits`:

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
reaches only that listener; it does not bubble up through the page. When
page code outside the parent must hear it, dispatch a DOM `CustomEvent`
from an element you hold in a `ref`.

## Replace `$c-props` { #replace-c-props }

**What you see:** the template stops loading with
`'$c-props' was removed; use native Vue ':prop' or 'v-bind' syntax`.

Pass each value as a Vue prop, and declare the props in the child:

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
`<c-CDialog>`. A callback that 0.5.1 passed as a prop usually becomes an
emitted event; see [Use `$emit`](#use-emit).

## Update `$component` { #move-component-initializers-to-vue-options }

`$component(callback)` and `$component({ init })` still work, but they run
at a different time and receive less.

**When it runs.** Citry calls the function after the component mounts,
children before their parent, and again after each server render that
updates this component. A change to local Vue state does not call it. Code
that needs a value before the first render belongs in `data()` or
`setup()`.

**What it receives.** The context still has `id`, `els`, `state`, `i18n`,
`sendEvent`, `onEvent`, `loading`, and `error`, and adds `component`, the
live Vue component, and `revision`. Reading any other 0.5.1 value gives
`undefined`, so a callback that reads `props.name` fails with a
`TypeError`. Replace those values:

| 0.5.1 context value | 0.6.0 replacement |
| --- | --- |
| `data`, `scope`, `props` | The Vue component: `component.name` or `this.name` |
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
    // `count` is a js_data() key, so it is a component member.
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

The function may be `async`. Citry does not wait for it, still runs a
cleanup function it resolves to, and logs a rejection instead of stopping
the page. The [Browser APIs reference](/reference/browser-apis/#component)
lists every option `$component` accepts.

### Replace `$provide`

**What you see:** code that calls `$provide`, `$inject`, or `$unprovide`
fails, because these template helpers do not exist in 0.6.0.

Provide a value from a component with Vue's `provide` option, and read it
in a descendant with `inject`. See
[Provide in the browser](/concepts/provide-and-inject/#provide-and-inject-in-client-code).

### Rename reserved names { #rename-reserved-names }

- **A [`js_data()`][citry.Component.js_data] key that starts with `$` or
  `_`, or the key `citryId`,** stops the render with a `ValueError` that
  names the component and the key. Rename it, for example `_count` to
  `count`.
- **A component class named `Mark`, or one registered as `mark`,** fails
  when the class is defined, with an `AlreadyRegistered` error that says
  the built-in `<c-mark>` reserves the name. Rename the class or give it
  another `name`. See [Built-in tags](/reference/builtins/#targeted-updates).

[Reserved names](/advanced/vue-runtime/#names-citry-reserves-on-the-component-instance)
lists the rest.

## Update Events code

### Change render targets

**What you see:** `actions.Render` with a CSS selector as its `target`
raises `ValueError`, saying that the target must be `render:<id>`,
`mark:<name>`, or `None`.

A render target now names one place: `mark:<name>` for a region you wrap
in `<c-mark>`, or `render:<id>` for one rendered component. Wrap the region
and target it by name:

```citry-html
<c-mark name="cart-badge">
  <c-CartBadge c-count="cart.count" />
</c-mark>
```

```python
badge = CartBadge(count=cart.count)
return actions.Render(badge, target="mark:cart-badge")
```

A `mark:` or `render:` target accepts only `swap="morph"`. A 0.5.1
selector that matched several elements becomes one Render action per target. One
response can return them all, one after another, as long as no target sits
inside another. `Citry.events.applyActions` follows the same rule for
Render and Event actions. See [Event actions](/events/actions/).

### Keep the root component

**What you see:** the browser reports an error that names both
components, and the page stays as it was.

A handler can still return a different component to replace the calling
one, and the old component's browser state is still lost. But it cannot
replace the outermost component of a page or HTML fragment. Move the part
that changes into a child component, or into a `<c-mark>` region. Props,
listeners, and a `ref` that the parent wrote on the old component's tag do
not reach the new one. See
[Swap in a component](/events/actions/#swap-in-a-different-component).

### Nested `$state` writes

**What you see:** writing to a nested value, such as
`$state.tags.push("new")`, throws "Nested $state values are read-only".

Assign the whole field instead:
`$state.tags = [...$state.tags, "new"]`.

### Remove `wait: false`

**What you see:** `$sendEvent` or `Citry.events.send` rejects.

Calls from one app are now sent in order, and an unknown option, or
`wait: false`, makes the call reject. For live search, where only the
newest call matters, declare the handler with `@event(latest_wins=True)`.

### Wait for `citry:ready`

**What you see:** a call made while the page loads rejects.

A call made before the page's Vue app mounts now rejects instead of
waiting. Listen for the `citry:ready` event on `document` first.

### Forward request headers

**What you see:** every handler that returns a render fails with "Vue
Events requires current app, occurrence, and revision headers."

Citry now calls a custom transport as `send(envelope, request)`. Send
`request.headers` with the request. See
[custom event transports](/reference/browser-apis/#custom-event-transports).

### Set security on `Citry`

**What you see:** on a page with Events, `serialize()` raises `ValueError`
when you pass it a different `security_csp` or `security_javascript`.

Pass `security_csp` and `security_javascript` to `Citry(...)` instead.
A later server render of the same page must use the same policy, so
`serialize()` cannot choose a different one.

### Clean up `applyActions`

**What you see:** `applyActions` throws a `ProtocolValueError` (a
`TypeError`) and applies none of the actions.

It now rejects an action with a field it does not know, a value that is
not plain JSON such as `undefined`, or an array with gaps such as
`[a, , b]`. Remove the extra fields from actions your page code builds or
forwards. A `state` action you build, for `applyActions` or in an
`on_event_result` hook, must now include `publicState`, the component's
public State values.

### Listen for DOM events

**What you see:** a `$onEvent` listener no longer fires for an event that
page code dispatches inside the component.

`$onEvent`, and the callback's `onEvent`, now hear only the events that
this component's server handlers dispatch. For a DOM event that page code
fires, call `addEventListener` on an element you hold in a `ref`.

### Key filters need a keyboard event

**What you see:** a `@c-*` binding such as `@c-click.enter`, or a `:c-*`
binding such as `:c-query.enter`, fails when the template loads, saying
that only keyboard events have a key.

`.enter` and `.escape` on a `@c-*` binding now need `keydown`, `keyup`, or
`keypress`, as they do on a Vue listener. Citry 0.5.1 accepted them on any
event name, where a click never matched and a custom event matched only
when its object had a `key`. Listen to the keyboard event instead:

```citry-html
<input @c-keydown.enter="search" />
```

A `:c-*` binding checks the key of its update event: by default `input`
or `change`, or the event named in `.on:`. Citry 0.5.1 accepted `.enter`
on any of them, and on the default events the binding never sent. Name a
keyboard update event:

```citry-html
<input :c-query.on:keydown.enter="search" />
```

### One `.on:` per binding

**What you see:** a `:c-*` binding that names two update events, such as
`:c-query.on:keyup.on:change`, fails when the template loads, and the
error names both events.

Citry 0.5.1 used the last one. Keep the event you want:

```citry-html
<input :c-query.on:change="search" />
```

### One key per binding

**What you see:** a binding with two key filters, such as
`@c-keydown.enter.escape`, or an element with two `@c-*` bindings for one
event, such as `@c-keydown.enter` and `@c-keydown.escape`, fails when the
template loads, and the error names both.

Citry 0.5.1 used the last key filter of a binding and ran every binding
for an event. To react to either key, call the handler from one Vue
listener:

```citry-html
<input @keydown.enter.escape="$sendEvent('search')" />
```

### Update stale listeners

**What you see:** a listener that checks for `cancelled` or `timeout`
never matches.

The event now reports `superseded`, `retired`, `epoch`, `disposed`, or
`version`.

### Stop reading Events tags

**What you see:** page code that parsed these tags finds nothing.

Pages no longer carry them. Inside the component, read Events values
through `$state`, `$loading`, and `$error`.

### Reload open pages

**What you see:** events from a page that was open during the upgrade fail
with a `stale_state` error.

Citry 0.6.0 cannot read the server-side State that 0.5.x saved. Reload
the page; pages opened after the upgrade are not affected.

## Component tag attributes { #update-attributes-on-component-tags }

**What you see:** a child component no longer receives a kwarg it read,
a listener on a component tag stops firing, or the render stops with an
error that names the attribute.

The attributes on a `<c-Child>` tag now split into Python inputs and Vue
bindings by how they are spelled:

- **`:name`, `v-bind`, `v-if`, `v-else-if`, `v-else`, `v-model`, `v-show`,
  custom `v-*` directives, and `ref` are Vue bindings.** 0.5.1 passed them
  to the child as Python kwargs. A child that read `kwargs[":class"]` or a
  `ref` kwarg no longer receives it. Pass a plain kwarg or a `c-attrs`
  mapping instead.
- **`@event` listens for an event the child emits.** In 0.5.1 it added a
  DOM listener to every root element of the child. Now the child declares
  the event in `emits` and calls `$emit`. A native event such as `@click`
  that the child does not declare goes to the child's single root element;
  a child with several root elements must place it with
  `v-bind="$attrs"`. See
  [Listen to child events](/concepts/client-interactivity/#listen-to-child-events).
- **`x-on:event` stops the render** with `Alpine binding 'x-on:click' was
  removed; use native Vue v-on or @event syntax.` Write `@click` instead.
- **A `.debounce` or `.throttle` `@c-*` binding, or `@c-poll`, stops the
  render.** Put it on an element inside the child's template.

## Move Python bindings

**What you see:** the render stops with an error that names the attribute
and says that a Python-resolved attribute "cannot introduce Vue syntax".

In 0.5.1, Python could build Alpine code as a string and write it into an
attribute. An interactive component in 0.6.0 rejects a Vue binding built
in Python, whether it comes from `c-:attr`, `c-@event`, or a `c-bind`
mapping with a `:x`, `@x`, or `v-*` key:

```citry-html
{# Stops the render: Python writes browser code #}
<div c-:class="'{ active: selected }'">...</div>

{# Works: the binding is in the template #}
<div :class="{ active: selected }">...</div>
```

Pass the values the binding needs through `js_data()` or props. A static
page that never loads Vue writes such attributes as plain text, where they
do nothing.

### Set attributes once

**What you see:** the template fails to load, with a message that
`c-title` and `:title` set the same attribute.

One element can no longer set an attribute both ways, such as `c-title`
together with `:title`. Keep one of them. `:class` and `:style` are the
exception: they combine with `class` and `c-class`, or `style` and
`c-style`, as in Vue.

For the same reason, an object `v-bind="..."` or a dynamic `:[name]`
cannot sit on an element that has any `c-*` attribute, and `:key` cannot
sit next to `#c-key`. See
[`c-*` with `:` bindings](/syntax/vue/#combine-class-and-style-with-c-class-and-c-style).

### Inline group content

**What you see:** the render stops with an error that names the component
that wrote the tab, the line, the Vue code it uses, such as
`v-text="label"` on `<span>`, and `CTabs` as the component that moves the
content.

Citry UI's `CTabs` collects the `<c-CTab>` and `<c-CTabPanel>` tags
inside it and moves their content into the `CTabs` template. Other Citry
UI components that collect item tags, such as `CStepper` and `CTimeline`,
work the same way. Content that uses
Vue data, handlers, `v-model`, a `ref`, or a `@c-*` binding must therefore
be written in the component that holds `<c-CTabs>`. The error appears when
a separate component placed inside `<c-CTabs>` writes that content. Move
the tags into the component that holds `<c-CTabs>`, or set
`transparent = True` on the component that writes them and define their
Vue data in the component that holds `<c-CTabs>`. See
[Vue data inside `CTabs`](/syntax/vue/#keep-vue-bound-group-content-inside-the-groups-tag).

## Check `#c-ignore` { #check-your-c-ignore-markers }

**What you see:** the template fails to load, with a message that says
what `#c-ignore` cannot hold or where it cannot go.

`#c-ignore` on an HTML element keeps its contents as the server first
rendered them, so a chart or map library can own them. In 0.6.0, the
contents can hold only HTML, `{{ }}` expressions, `<c-if>`, `<c-for>`, and
`<c-raw>`. Move any component, slot, Vue binding, or `ref` out of them. A
`ref` can go on the `#c-ignore` element itself:

```citry-html
<div class="chart" ref="chart" #c-ignore>
  <canvas></canvas>
</div>
```

`#c-ignore` also fails on these tags:

- **A component tag.** Move it onto the element inside the component's
  template that the library manages.
- **`<table>`, `<tbody>`, `<tr>`, and the other table row elements.** Wrap
  the table in a `<div #c-ignore>` instead.
- **`<c-element>`, in both the `is` and `c-is` forms.** Write the element
  as a plain tag, such as `<section #c-ignore>`.

See
[`#c-ignore`](/syntax/dynamic-attributes/#c-ignore-keep-contents-that-a-library-manages).

## Fix rejected HTML

These rules apply only to components that run in the browser. Static pages
are not affected.

### Close `<c-raw>` tags

**What you see:** the render stops with an error such as "The `<c-raw>`
block at line 2, column 10 is not a complete HTML fragment".

Inside an interactive component, `<c-raw>` content and `Markup` values
must each be a complete HTML fragment: every tag closed, and no stray
`<`. The error names the input
and explains the rule.

### One `<body>` per page

**What you see:** serialization stops with an error such as "Interactive
Vue document serialization requires one well-ordered body element."

An interactive page template that writes `<!doctype html>` or `<html>`
must put its content inside one `<body>` element.

## Removed browser globals { #replace-removed-browser-globals }

**What you see:** page code throws because `Citry.alpine` or another
removed global is `undefined`, an `alpine:init` listener never runs, or a
request for `runtime-csp.js` returns 404.

| Removed | What to use |
| --- | --- |
| `Citry.alpine.beforeStart(fn)` | [`Citry.vue.use(plugin)`](/reference/browser-apis/#citry-vue-use), called from a `defer` script in `<head>` or a script an extension adds to `ctx.early_scripts`. An Alpine plugin has no direct replacement. |
| `Citry.manager.*` (`loadJs`, `loadCss`, `callComponent`, ...) | Declare assets on the component with `Component.js`, `Component.css`, or `Dependencies`. Interactive fragments load their own assets. |
| `Citry.i18n.provider` | `component.$i18n` or `this.$i18n`; see [Browser i18n](/i18n/browser/). |
| `window.Alpine`, `alpine:init` | The `citry:ready` event on `document`. |
| `/ext/events/runtime-csp.js` route | Nothing. Citry serves one runtime for every CSP mode. |

## Share the cache { #share-the-cache-between-worker-processes }

**What you see:** with several worker processes, an interactive page shows
its HTML but never starts, and the browser console shows 404 responses for
component code or stylesheets.

The worker that rendered the page stored those files in the Citry cache,
and another worker, with its own cache in memory, answered the request.
Point every worker at one shared cache backend, such as Redis or
DiskCache.

Without a configured cache, a single process keeps this code in memory, up
to `vue_asset_max_bytes` (64 MiB by default). A page always finds its own
files right after it loads. A page left open long enough to ask for a file
that was dropped gets the same 404, so raise the limit or configure a
cache. See
[Share the cache](/web-frameworks/#share-the-cache-between-worker-processes).

## Proxies and CDNs { #proxies-and-cdns }

**What you see:** the page shows its server-rendered HTML, but components
never start, and the browser console reports a CORS or Subresource
Integrity error.

Citry's asset routes now send `Access-Control-Allow-Origin: *`. When a
proxy or CDN serves Citry's files from another host, or the page runs in a
sandboxed iframe, make sure the proxy or CDN passes that header through.
See
[Keep the CORS header](/security/#keep-the-cors-header-when-a-proxy-or-cdn-serves-citrys-files).

## Settings and extensions { #update-settings-and-extensions }

### Rename lint settings

**What you see:** `LintSettings` raises `TypeError`, or defining a
component whose `Lint` class uses the old names raises `ValueError`.

Rename the settings in `LintSettings` and in any `Component.Lint`:

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

A tool that builds `TemplateLintInfo` uses the same new names. Keep only
the names your Vue expressions still read; an Alpine helper such as
`$dispatch` means nothing to Vue.

### Rename diagnostic codes

**What you see:** a script that filters `citry check --format json` output
by code stops matching.

| 0.5.1 code | 0.6.0 code |
| --- | --- |
| `citry.alpine.unknown-variable` | `citry.vue.unknown-variable` |
| `citry.component-js.unknown-data-member` | `citry.component-js.unknown-member` |
| `citry.browser.unknown-component-prop` | Removed |

### Strict CSP mode

**What you see:** with `security_csp="strict"`, rendering raises
`ValueError`: "Citry found N strict-CSP incompatibility issue(s)",
followed by a list of the problems.

`security_csp="strict"` used to select Citry's Alpine CSP build and limit
the expressions you could write. It now checks the final HTML for raw
`<script>` and `<style>` elements, `on*` attributes, and `javascript:`
URLs. Any Vue expression works, because Citry compiles templates on the
server. See [Security](/security/#choose-a-csp-compatibility-mode).

### Classic scripts only

**What you see:** serializing a page or an Events response raises
`ValueError` about a script.

A component's `Dependencies` scripts, and an extension's `ctx.scripts` and
`ctx.early_scripts`, must be classic JavaScript on an interactive page.
Citry loads these scripts itself, one after another in list order, so it
rejects a `type="module"` or JSON data script, and a script marked
`async`, `defer`, or `nomodule`. Scripts in `ctx.early_scripts` load before
`ctx.scripts`.

### `ctx.early_scripts`

**What you see:** an `on_dependencies()` hook raises `AttributeError`,
naming `early_scripts`.

Rename `ctx.before_manifest` to `ctx.early_scripts`. The scripts it holds
still run before `ctx.scripts`. The old name has no alias.

### Keyword hook contexts

**What you see:** code that builds `OnSerializeContext` or
`OnDependenciesContext` with positional arguments, such as an extension
test, fails or passes values to the wrong fields.

Both gain a `selected_render` field, the render being serialized. Build
them with keyword arguments.

### Check HTTP methods

**What you see:** defining an Events class or building a `URLRoute` raises
an error.

- `@event(methods=...)` and `Events._methods` accept only GET, HEAD, POST,
  PUT, PATCH, DELETE, and OPTIONS. Any other method raises `ValueError`
  when the class is defined.
- `URLRoute(methods=...)` is checked when you build the route. Pass a
  non-empty tuple of uppercase method names, such as `("GET", "POST")`. A
  list raises `TypeError`. An empty tuple raises `ValueError`, and so does
  a lowercase name such as `"get"`, which no framework adapter would match.

### `citry.analysis` results

**What you see:** a tool that reads `citry.analysis` results skips the
kwargs parameter.

In the results of `analyze_template_data_source`,
`analyze_js_data_source`, and `analyze_css_data_source`, `parameters` now
leaves out `self` or `cls`. `parameters[0]`, when present, is the kwargs
parameter, so a tool that skipped the first entry should read from index 0.

The Alpine helpers in `citry.analysis` are removed. Use
`VueLintConsumer`, `VueLintFinding`, `lint_unknown_vue_variables`, and
`VUE_AMBIENT_NAMES` in place of `AlpineLintConsumer`,
`AlpineLintFinding`, `lint_unknown_alpine_variables`, and
`ALPINE_AMBIENT_NAMES`.

### Removed Python APIs

**What you see:** an `ImportError`, or a `TypeError` for an unexpected
argument.

- **`TemplateNode`** is removed. Compiled templates never contained it, so
  delete any import of it or `isinstance` check against it. An extension
  that built one in `on_template_compiled` should instead add the nested
  template's markup to the template source in `on_template_loaded`, so it
  compiles with the rest of the template.
- **The ownership APIs** are removed: the `citry.ownership` and
  `citry.ownership_manifest` modules, and the `ownership` parameters of
  `CitryContext` and `CitryElement`. Delete the imports and those
  arguments.

## Clean up integrations

- **HTMX:** delete `citry-htmx.js` and `hx-ext="citry-fragments"`. Citry
  no longer writes the markers that helper kept, and inserted fragments
  start on their own. See [Use Citry with HTMX](/guides/htmx/).
- **`data-cid-*` selectors:** only static output carries these
  attributes. Elements that Vue renders have none, so CSS or scripts that
  select `[data-cid-...]` stop matching. Use a Vue `ref` in component
  JavaScript.
- **`data-citry-key` selectors:** `#c-key` on an element no longer writes
  a `data-citry-key` attribute, so selectors for it stop matching.
  `#c-key` still keeps rows matched across renders.
- **Render cache:** entries saved by Citry 0.5.x count as misses and are
  saved again on the next render. You do not need to clear the cache.

## New features to try

- Interactive pages send their content in the served HTML, so search
  engines and readers without JavaScript see it. Tune this with `ssr` and
  `ssr_element_threshold`; see
  [What the server sends](/advanced/vue-runtime/#send-page-content-in-the-served-html).
- `simple = "vue"` gives a component its own Vue state and assets without
  a Python component instance; see
  [Simple components](/performance/simple-components/#give-a-simple-component-its-own-vue-state).
- A component tag accepts `v-if`, `v-model`, `v-show`, and custom
  directives; see
  [Vue on component tags](/syntax/vue/#use-vue-directives-on-a-component-tag).
- `<c-mark>` names a region that an Events handler can render again; see
  [Built-in tags](/reference/builtins/#targeted-updates).
- A text field keeps what the user typed when its component renders
  again, until the server sends a different value; see
  [Keep typed input](/advanced/vue-runtime/#keep-what-the-user-typed-across-renders).
- `citry check` and the editor report a misspelled `js_data()` member and
  a Vue binding that reads a Python loop variable; see
  [Template linting](/ide/template-linting/).

## Upgrade checklist

1. Install `citry` 0.6.0, `citry-ui` 0.3.0, and `citry-lsp` 0.2.0 in the
   same environment.
2. Run `citry check` to find leftover `x-*` attributes, and replace each
   with its Vue form.
3. Move `x-data` state into `data()` or `js_data()`.
4. Rewrite `.outside`, `.window`, `.document`, `.debounce`, and
   `.throttle` modifiers on plain `@event` listeners. End a statement
   listener such as `if (ok) save()` with `;`.
5. Replace `$dispatch` with `$emit`, and declare `emits` in the child.
6. Replace `$c-props` with `:name` props, declared in the child's `props`.
7. Replace `data`, `scope`, `props`, `graph`, `effect`, `reactive`,
   `provide`, `inject`, and `unprovide` in `$component` callbacks.
8. Replace `$provide`, `$inject`, and `$unprovide` with Vue `provide` and
   `inject`.
9. Rename `js_data()` keys that start with `$` or `_`, and a component
   class named `Mark` or registered as `mark`.
10. Change CSS-selector render targets to `mark:<name>` or `render:<id>`,
    and move a replaced outermost component's changing part into a child
    or a `<c-mark>` region.
11. Forward `request.headers` in custom transports.
12. Replace nested `$state` writes with whole-field assignments, remove
    `wait: false` and unknown call options, and wait for `citry:ready`
    before calling `Citry.events.send`.
    Move `.enter` and `.escape` from a `@c-*` binding on any other event to
    a `keydown` or `keyup` binding, and give a `:c-*` binding that uses
    them `.on:keydown` in place of `.lazy` or its other `.on:` event.
    Keep one `.on:` event and one key filter on each binding, and one
    `@c-*` binding per event on each element.
13. Set `security_csp` and `security_javascript` on the `Citry` instance
    for pages with Events.
14. Update action lists passed to `Citry.events.applyActions`, including
    `publicState` in any `state` action you build, `$onEvent` listeners
    for page DOM events, `citry:events:stale` listeners that check for
    `cancelled` or `timeout`, and code that reads `data-citry-events`
    script tags.
15. Check component tags for `:x`, `v-*`, and `ref` attributes the child
    read as kwargs, and for `x-on:`, timed `@c-*` bindings, and `@c-poll`.
16. Move `c-:attr`, `c-@event`, and Vue keys in `c-bind` into the
    template, set an attribute such as `title` with `c-title` or `:title`
    but not both, and write Vue-bound group content inside the group's
    tag.
17. Keep `#c-ignore` only on HTML elements whose contents a library
    manages, and move it off component tags, table row elements, and
    `<c-element>`.
18. Close every tag in `<c-raw>` and `Markup` inside interactive
    components, and put an interactive page's content inside one
    `<body>`.
19. Remove uses of `Citry.alpine`, `Citry.manager`, `Citry.i18n`,
    `window.Alpine`, and `alpine:init`.
20. On a deployment with several workers, configure a shared cache
    backend, and let a proxy or CDN pass `Access-Control-Allow-Origin`
    through for Citry's files.
21. Rename the Alpine lint settings and diagnostic codes, and fix any
    output that `security_csp="strict"` now rejects.
22. Check that dependency scripts on interactive pages are classic
    JavaScript, rename `ctx.before_manifest` to `ctx.early_scripts`, and
    build `OnSerializeContext` and `OnDependenciesContext` with keyword
    arguments.
23. Pass `URLRoute(methods=...)` as a tuple of uppercase names, read
    `parameters` from `citry.analysis` results starting at index 0, and
    remove `TemplateNode`, `citry.ownership` imports, and `ownership=`
    arguments.
24. Remove `citry-htmx.js`, `hx-ext="citry-fragments"`, and `data-cid-*`
    or `data-citry-key` selectors.
25. Open each interactive page, reloading pages opened before the
    upgrade, and check the browser console for `[Citry]` errors.

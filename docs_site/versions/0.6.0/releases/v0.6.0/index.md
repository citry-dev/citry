---
title: v0.6.0
url: https://citry.dev/v/0.6.0/releases/v0.6.0/
description: "What changed in citry v0.6.0."
---
# v0.6.0

Citry 0.6.0 replaces Alpine with Vue. Most Python components, templates,
`c-*` attributes, slots, and Events handlers keep working, but browser code
moves to Vue and some Python code changes too, such as lint settings,
`js_data()` key names, and extension hooks.
[Upgrade to Citry 0.6.0](https://citry.dev/guides/upgrading-to-0-6-0/)
walks through every step.

## Highlights

- Write Vue directives, bindings, props, events, and slots in component
  templates, and Vue Options or Vue's Composition API (`Citry.vue`) in
  component JavaScript.
- Citry compiles each component to Vue on the server and sends one pinned
  Vue runtime only to the pages that need it, so you need no Node.js or
  frontend build step.
- Interactive pages send their content in the served HTML, so search
  engines and readers without JavaScript see it, and Vue takes over that
  HTML instead of building the page again.
- An Events handler can render one region of the page again: wrap it in
  `<c-mark name="cart-badge">` and return
  `actions.Render(CartBadge(count=n), target="mark:cart-badge")`, or target
  one rendered component with `render:<id>`.
- `citry check --types` type-checks component JavaScript and Vue
  expressions with TypeScript, Python template expressions with ty, and
  each `c-*` input against the child's `Kwargs`, reporting findings as the
  editor does; it needs `citry-lsp`, Node.js, and TypeScript's `tsc`.
- `simple = "vue"` gives a component its own Vue state and assets without a
  Python component instance.

## Upgrading from 0.5.x

- **Upgrade the packages together:** install `citry-ui` 0.3.0 and
  `citry-lsp` 0.2.0 with Citry 0.6.0, because older versions fail to start
  or lose their browser behavior
  ([guide](https://citry.dev/guides/upgrading-to-0-6-0/#upgrade-the-packages-together)).
- **Alpine syntax becomes Vue:** rewrite `x-*` attributes, Alpine-only
  modifiers, `$dispatch`, and `$c-props` with their Vue forms; `citry check`
  lists the `x-*` attributes you missed
  ([guide](https://citry.dev/guides/upgrading-to-0-6-0/#replace-alpine-directives-with-vue)).
- **Component tag attributes become Vue bindings:** `:name`, `v-*`, and
  `ref` on a component tag no longer reach the child as kwargs,
  `#c-ignore` works only on plain HTML elements, not on component tags or
  `<c-element>`, and Vue slot syntax such as `<template #title>` inside a
  component tag fails when the template loads; fill the slot with
  `<c-fill name="title">`
  ([guide](https://citry.dev/guides/upgrading-to-0-6-0/#update-attributes-on-component-tags)).
- **Vue names from Python data stop the render:** a `c-bind` key, a `c-*`
  attribute such as `c-@click`, or an `on_attrs_resolved` hook that sets
  an attribute name starting with `v-`, `:`, `.`, `^`, `@`, or `#` now
  raises the new `citry.VueCodeError`, a `TypeError`, when the template
  renders, on every page. If a script you load yourself, such as Alpine,
  read these names on an HTML element, spread the long form, such as
  `x-on:click`
  ([guide](https://citry.dev/guides/upgrading-to-0-6-0/#move-python-bindings)).
- **Component JavaScript moves to Vue Options:** the `$component` callback
  gets a smaller context, and `js_data()` keys that start with `$` or `_`
  must be renamed
  ([guide](https://citry.dev/guides/upgrading-to-0-6-0/#move-component-initializers-to-vue-options)).
- **Events code:** render targets are `mark:<name>` or `render:<id>`
  instead of CSS selectors, custom transports must forward
  `request.headers`, and a `state` action you build, for
  `Citry.events.applyActions` or an `on_event_result` hook, needs a
  `publicState` object. `.enter` and `.escape` on a `@c-*` binding work
  only on `keydown`, `keyup`, or `keypress`, and on a `:c-*` binding only
  with `.on:keydown`, `.on:keyup`, or `.on:keypress`. A `:c-*` binding
  that names two `.on:` events, a binding with two key filters, and a
  second `@c-*` binding for the same event on one element now fail
  ([guide](https://citry.dev/guides/upgrading-to-0-6-0/#update-events-code)).
- **Handlers that return a different component:** a handler can no longer
  replace the outermost component of a page or HTML fragment with a
  different component; move the part that changes into a child component
  or a `<c-mark>` region. Replacing any other calling component still
  works, and the old component's browser state is still lost
  ([docs](https://citry.dev/events/actions/#swap-in-a-different-component)).
- **Page scripts and selectors:** `Citry.alpine`, `Citry.manager`, and
  `Citry.i18n` are removed, and Vue-rendered elements carry no
  `data-cid-*` or `data-citry-key` attributes
  ([globals](https://citry.dev/guides/upgrading-to-0-6-0/#replace-removed-browser-globals),
  [selectors](https://citry.dev/guides/upgrading-to-0-6-0/#clean-up-integrations)).
- **Deployment and security:** several worker processes need a shared
  cache backend, and a proxy or CDN may need to pass Citry's CORS header
  through
  ([cache](https://citry.dev/guides/upgrading-to-0-6-0/#share-the-cache-between-worker-processes),
  [proxy](https://citry.dev/guides/upgrading-to-0-6-0/#proxies-and-cdns)).
- **Lint settings and diagnostic codes:** the Alpine names become Vue
  names, such as `rule_unknown_vue_variable` and
  `citry.vue.unknown-variable`, and `citry.csp.incompatible-browser-code`
  is removed: Vue expressions compile on the server and never need
  `unsafe-eval`
  ([guide](https://citry.dev/guides/upgrading-to-0-6-0/#update-settings-and-extensions)).
- **Extensions and Python tools:** dependency scripts on interactive pages
  must be classic JavaScript, `OnSerializeContext` and
  `OnDependenciesContext` gain `selected_render`, `ctx.before_manifest`
  becomes `ctx.early_scripts`, `URLRoute` checks `methods`,
  `citry.analysis` results leave `self` out of `parameters`,
  `citry.analysis.lint_csp_compatibility` and `CspCompatibilityFinding` are
  removed, and the `TemplateNode` class is removed
  ([guide](https://citry.dev/guides/upgrading-to-0-6-0/#update-settings-and-extensions)).
- **Subclasses name the parent class to add inputs:** a nested `Kwargs`,
  `Slots`, `State`, `TemplateData`, `JsData`, or `CssData` on a subclass
  now replaces the parent's class, like any nested Python class, so write
  `class Kwargs(Parent.Kwargs):` to keep the parent's fields. Citry warns
  with `NestedSchemaReplacedWarning` when a subclass leaves out a parent's
  fields. A replacing `State` also drops the parent's `_public`, `_model`,
  and `_max_age`, and Citry warns. A component whose parents declare
  different `Kwargs`, or that replaces a `State` with
  `_storage = "server"` without setting `_storage`, raises `ValueError`
  when defined. `Events`, `Dependencies`, and other settings
  classes still add to the parent's
  ([guide](https://citry.dev/guides/upgrading-to-0-6-0/#name-the-parent-class)).
- **HTML returned from `on_render` shows as text:** `on_render()` now
  escapes a plain `str` it returns or yields, as `{{ }}` does, so user
  input in it cannot add a script. Wrap HTML in `Markup` or return a
  component. The extension hooks `on_component_rendered()` and
  `on_slot_rendered()` follow the same rule; wrap their HTML in `Markup`
  ([guide](https://citry.dev/guides/upgrading-to-0-6-0/#wrap-html-returned-from-on-render)).
- **`Markup` in an attribute is escaped:** a `Markup` value in an HTML
  attribute is now escaped like any other value, so a `"` in it can no
  longer end the attribute and add another one. An entity such as
  `&amp;` still reads as its character
  ([guide](https://citry.dev/guides/upgrading-to-0-6-0/#markup-attribute-values)).

## Other additions

- A component tag accepts `v-if`, `v-else-if`, `v-else`, `v-model`,
  `v-show`, and custom directives.
- `onServerRender({ component, revision, onEvent })` runs after mount and
  after each server render of the component, and it may be `async`.
- `Citry.vue.use(plugin)` installs a Vue plugin on every Vue app Citry
  creates.
- A text input, `<textarea>`, or `<select>` keeps what the user typed when
  its component renders again, until the server sends a different value.
- Interactive pages served through Citry's routes link their stylesheets
  and preload their scripts in `<head>`, so they are styled from the first paint, and browser assets
  are minified.
- Interactive fragments load their own assets, so HTMX pages no longer
  need the `citry-htmx.js` helper or `hx-ext="citry-fragments"`.
- `citry check` and the editor report misspelled component members, Vue
  bindings that read Python loop variables, undeclared emitted events,
  leftover `x-*` attributes, invalid HTML attribute values
  (`rule_invalid_attribute_value`), and `js_data()` values Citry cannot
  prove it can send as JSON.
- A translation catalog may leave messages out: `citry check` now warns,
  instead of failing, when a `tr()` call or a message in
  `I18n.client_messages` would show text from a fallback language. Set
  `LintSettings(rule_i18n_cross_language_fallback="error")` to require
  complete translations; a `<c-trans>` message still needs every
  translation.
- `citry check --types` checks `c-class`, `c-style`, and bound attributes
  such as `:style` against their expected types, which can report existing
  bindings such as `:aria-expanded="String(open)"`.
- Interactive pages start inside an iframe sandboxed without
  `allow-same-origin`, because Citry's asset routes send
  `Access-Control-Allow-Origin: *`.
- A Content Security Policy needs no nonce or hash for a page's app data,
  which the browser reads as JSON without running it, and
  `csp_script_hashes` lists only the scripts the browser runs.
- `Citry(vue_asset_max_bytes=...)` caps the memory a process without a
  configured cache spends on compiled component code (default 64 MiB).
- Render-cache entries saved by 0.5.x count as misses and are saved again,
  so you do not need to clear the cache.

## Fixes

- `parse_string_style()`, `normalize_style()`, and `merge_attrs()` no longer
  drop text that looks like a CSS comment inside a quoted value or after a
  backslash, such as `content: "/* note */"`, matching Vue.
- `class Kwargs(Parent.Kwargs):` on a subclass now keeps the parent's
  field defaults, and a nested data class such as `Kwargs` can list a
  required field after one with a default.
- `$state` and State bindings now show the State an Events handler changed
  when the handler returns nothing, returns data, or renders only a
  `<c-mark>` region, instead of keeping the old values until the component
  renders again.
- On Python 3.10, an i18n catalog package without `__init__.py` now loads
  instead of failing with a `TypeError`.
- Events handlers declared with `PUT`, `DELETE`, or another non-POST
  method now work, and each still rejects other methods and checks CSRF.
- `GET` Events calls reject arguments with unpaired surrogates instead of
  silently replacing characters.
- `citry check` no longer reports every template variable as undeclared
  when `template_data()`, `js_data()`, or `css_data()` runs several `if`
  checks before it returns.
- `citry check` no longer reports the keys of a `template_data()` written
  as a `@staticmethod` or `@classmethod` as undeclared, and checks the
  value types of a `js_data()` written that way.
- `citry check` no longer reports browser names such as `Document` or
  `btoa` as unknown in component JavaScript.
- `citry check` no longer reports `citry.js-data.unsupported-type` for a
  `js_data()` value that reads a `Kwargs` field annotated with a type
  alias of a `Literal`.
- In an app without i18n settings, `citry check` no longer reports
  "Unknown i18n format profile" for a formatter call in component
  JavaScript or one guarded by `self.i18n.configured`, matching the
  editor; an unguarded Python call is still reported.
- `citry check` no longer crashes with a traceback when a component's
  `messages` fail to compile, for example a selector variable that is not
  declared as a number with `@param`. It reports
  `citry.i18n.catalog-invalid` instead, and the JSON output gives the line
  and column inside the `messages` block.
- Fallback text that runs in the other direction, such as English on an
  Arabic page, no longer reorders the surrounding sentence when the
  browser translates it with `$i18n.tr()`, `$c-tr`, `i18n.bind()`, or
  `resolve()`. The browser now adds the same direction marks the server
  adds, and `resolve().direction` matches the server.

- `citry create` now rejects a name whose file would be a Python keyword,
  such as `citry create class`, instead of writing a module nobody can
  import.
- A Flask mount prefix written with a trailing slash, such as
  `prefix="/citry/"`, now serves Citry's routes instead of sending every
  Citry request to your app. A FastAPI or Flask prefix without a leading
  `/` raises Citry's `ValueError` without changing the app.
- Server-side State is now stored under `citry:state:` cache keys, so a
  State token can only refer to State that Citry stored. After the
  upgrade, events from a page opened earlier fail with a `stale_state`
  error until the page is reloaded.
- A component that declares `Dependencies` with an empty `css` list no
  longer makes a fragment raise `RuntimeError` when no web integration is
  mounted.
- An `on_render` or `on_component_rendered` hook that returns
  `str(result)` with extra HTML no longer writes the component's
  `data-cid-*` attribute twice on one tag.
- An extension hook that returns a value of the wrong type, such as an
  `on_component_rendered()` that returns a number, an `on_serialize()`
  that returns something other than a `str`, or an `on_event_result()`
  that returns something other than a list of actions, now raises a
  `TypeError` that names the hook and the extension, before the next
  extension runs. Before, the error blamed the next extension or appeared
  later without naming the extension, and `serialize()` returned whatever
  `on_serialize()` gave.
- An attribute that an `on_dependencies()` hook adds to a script or
  stylesheet in one render no longer appears in later renders of the same
  component.
- mypy and pyright now accept `self.events.url()`, and it is listed in
  the API reference.
- `enable_hot_reload(engine, mode="restart")` from `citry.contrib.django`
  now restarts the Django dev server when a component file changes.
- `enable_hot_reload` now notices component files under `Citry(dirs=...)`
  outside Django's template folders. Point `dirs` at your component
  folders, since the reloader checks every file under them.
- A component that keeps rendering itself, such as a tree node whose data
  lists the node among its own children, now fails quickly with a
  `RecursionError` naming the component instead of running until the
  process runs out of memory. Pass `Citry(max_component_depth=...)`
  (default 2000) if a page really nests deeper.
- An element with an empty `class` or `style`, such as
  `<p class c-class="name">` or `<p style="" c-style="styles">`, no
  longer raises `TypeError: Invalid class value: True` (or
  `Invalid style value: True`) when it also has a `c-class`, `c-style`,
  `c-bind`, or other `c-*` attribute. The empty attribute adds nothing to
  the value from Python. With no Python value, the element keeps the empty
  attribute.
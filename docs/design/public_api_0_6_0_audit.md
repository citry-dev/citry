# Public API audit: citry 0.5.1 to 0.6.0

This document lists every public surface that citry 0.5.1 shipped and says
what happens to it in the 0.6.0 candidate on the `vue-pr-api` branch. It
answers one question for the maintainer: did the move from Alpine to Vue
break anything users relied on, and if so, was that on purpose?

It is an internal design record. It names removed APIs on purpose, because
its job is to account for them.

## 1. Summary

### What was checked

Five audits compared citry 0.5.1 with the branch, one per area:

- the browser JavaScript API (globals, `$component`, template helpers, DOM
  events, data attributes);
- the Python API (`citry.__all__`, `Component`, render entry points,
  exceptions, every non-underscore submodule);
- settings, the extension API, the CLI, the language server, and
  diagnostic codes;
- template syntax (`<c-*>` tags, `c-*` attributes, `#c-*` flags, Alpine
  directives, Events bindings, i18n syntax);
- HTTP routes and the Events wire protocol, i18n, and citry-ui.

The sources for 0.5.1 were:

- the `citry==0.5.1` wheel and sdist from PyPI, installed into a clean
  virtual environment and unpacked for reading;
- the `citry@0.5.1` git tag;
- the published 0.5.1 docs snapshot in `docs_site/versions/0.5.1/`;
- the `citry-ui@0.2.2`, `citry-lsp@0.1.7`, and `citry-core@1.7.1` tags.

The branch was audited at commit `2db4ba42`. The statuses below were then
updated for the fixes committed afterwards (`2db4ba42..566c128a`), each
checked against the code and, where noted, by running it. The maintainer
then decided every question in section 6, and the commits after
`566c128a` implement those decisions. Each decision in section 6 ends with
a **Status** line naming its commits. Where a row in section 3 or 5 still
cites a decision number, that Status line is the current answer.

### Method

Each audit diffed public names and signatures between the two versions
(`inspect.signature` dumps for Python, an AST comparison for every citry-ui
component, `--help` output for every CLI command), read the source for
behavior changes, and ran small throwaway renders on both versions where
behavior was in doubt. Rows marked "(checked by rendering)" were confirmed
that way; those scripts were temporary and not kept. Browser behavior after
Vue mounts was not executed by the audits unless a row says so; the
restored browser behavior is covered by the end-to-end tests listed in
section 4.

### Did 0.6.0 break the public API?

Yes. Most breaks are deliberate removals of Alpine or of Citry's browser
ownership graph (the record 0.5.1 kept of which component owned which DOM
nodes). The rest are seven consequences of running components on Vue:

1. `wait: false` on `$sendEvent` / `Citry.events.send` rejects with a
   `TypeError`, because each app sends its calls one at a time (0.5.1
   sent such a call outside the queue).
2. A custom Events transport is called as `send(envelope, request)` and
   must forward the request headers.
3. Writing a nested `$state` value throws.
4. Components that Vue renders carry no `data-cid-*` attributes.
5. `Markup` and `<c-raw>` content inside an interactive component must be
   a strict fragment (HTML whose tags all open and close inside it).
6. Alpine-only event modifiers such as `.outside` fail when the template
   loads, with a message that names the Vue alternative.
7. `#c-ignore` keeps an element's contents as the server first rendered
   them, and those contents may not hold components or Vue bindings.

All seven are recorded in the CHANGELOG and the upgrade guide.
`OnDependenciesContext.before_manifest` is renamed to `early_scripts`
(decision 6.8); under that name it works on interactive pages, which it
did not at the time of the audit.

What still works as in 0.5.1:

- `citry.__all__` has the same 191 names. 179 behave as in 0.5.1: 178 are
  untouched, and `URLRoute` is back to its 0.5.1 type. Of the other 12,
  six only gained optional parameters or trailing fields, and six changed
  incompatibly: the Alpine lint names (`LintSettings`,
  `TemplateLintInfo`), the ownership parameters (`CitryContext`,
  `CitryElement`), and the new `selected_render` field
  (`OnSerializeContext`, and `ExtensionManager` through its
  `on_serialize` method).
- Every public member of `Component` keeps its signature. `MyComp(**kwargs)`
  still returns a `CitryElement`.
- The CLI (`citry check`, `format`, `list`, `inspect`, `create`, `watch`,
  `ext ...`) and the language server options are unchanged.
- Every extension hook name, config dataclass, and built-in extension is
  the same.
- Every citry-ui component keeps the same Python `Kwargs`, `Slots`, and
  callback names.
- Every HTTP route URL is kept, except the Alpine CSP runtime route.
- The template grammar is byte-identical. All syntax changes come from
  validation of what the grammar already parses.

What was removed deliberately: Alpine itself (`x-*` directives, Alpine
magics, `Citry.alpine`, `$c-props`), the browser ownership graph and its
Python modules, Python-built browser code (`c-:attr`, `c-bind` keys that
spell Vue bindings), and a set of `$component` callback fields that have no
Vue meaning. Section 5 lists each one with its replacement.

What was broken by accident and is now restored:

- the `$component` / `onServerRender` context fields `id`, `els`, `state`,
  `sendEvent`, `loading`, `error`, and `i18n` (`els` is one array for the
  component's lifetime, refilled on each server render and on each read
  of the getter; a destructured reference does not see changes made only
  in the browser until the next refill);
- `$component({ init })`;
- `citry:events:stale` with `reason: "version"` and the one-time reload
  prompt after a deploy, which reaches `document` listeners when the
  calling component has no elements left (a component that is unmounted
  reports `retired` instead, because its call is cancelled);
- the component id in `citry:events:*` details after the component is
  gone (the last known `instance` and `class`);
- `URLRoute.methods` as a tuple on every route;
- Vue definition bundles and stylesheets served correctly by any worker
  that shares the configured cache;
- `$sendEvent` on a component without Events rejecting as in 0.5.1, and
  `$loading()` / `$error()` there returning `false` / `null`;
- interactive components whose class name contains `_`;
- the `$i18n` entry on the browser API reference page.

Four changes that failed silently or confusingly now fail with a clear
message: old Alpine lint setting names name their replacement, `#c-ignore`
on a component tag raises, `#c-ignore` on an element says why and what to
do instead, and the `v-once` / `v-memo` hint on a component tag no longer
points at an element. `URLRoute(methods=...)` now rejects a value that is
not a non-empty tuple of uppercase method names when the route is built.

Section 6 lists the questions still open for the maintainer.

## 2. Counts per area and status

Statuses:

- **unchanged**: same name, signature, and behavior.
- **changed-compatible**: code written for 0.5.1 keeps working; the
  surface gained options, fields, or behavior.
- **changed-incompatible**: the surface still exists, but some 0.5.1 code
  that uses it fails or behaves differently.
- **removed**: the surface is gone.
- **restored**: the branch had lost 0.5.1 behavior and it works again.
- **new**: not in 0.5.1.

Rows were counted by a script from the tables in section 3, one per table
row. A row
that groups several names (for example "13 exception classes") counts once.
Where an original report gave a row two statuses ("removed / new" for a
module that lost some names and gained others), this document assigns one:
`changed-incompatible` when public names were removed from a surface that
still exists, `removed` only when the whole surface is gone. A few surfaces
appear in two areas because two audits covered them from different angles
(`LintSettings`, `TemplateLintInfo`, `citry.analysis`, `URLRoute`,
`OnSerializeContext`, `OnDependenciesContext`, `$i18n`, the callback
`i18n` field, the `runtime-csp.js` route); they are counted in each area,
so the grand total counts them twice.

| Area | unchanged | changed-compatible | changed-incompatible | removed | restored | new | Rows |
|---|---|---|---|---|---|---|---|
| Browser JavaScript | 8 | 9 | 9 | 20 | 9 | 6 | 61 |
| Python API | 14 | 19 | 27 | 4 | 1 | 8 | 73 |
| Settings, extensions, CLI, LSP | 41 | 11 | 9 | 6 | 1 | 14 | 82 |
| Template syntax | 39 | 16 | 13 | 17 | 0 | 6 | 91 |
| HTTP, protocol, i18n, citry-ui | 19 | 16 | 9 | 9 | 4 | 6 | 63 |
| **Total** | **121** | **71** | **67** | **56** | **15** | **40** | **370** |

"restored" means 0.5.1 behavior that the branch had lost and that works
again now. A restored row is compatible with 0.5.1 for the part that was
restored; its note says what, if anything, still differs.

## 3. Inventory by area

Path shorthand used in the tables:

- `P/` = `packages/py/citry/citry/`
- `C` = `P/_vue/client.js` (the browser script that creates Citry's Vue
  apps and connects them to Events)
- `EV` = `packages/js/citry-client/src/citry-events-vue.ts` (built into
  `P/_vue/events.js`)
- `E51` = `packages/js/citry-client/src/citry-events.ts` at `citry@0.5.1`
- `M51` = `P/ext/dependencies/client/citry.js` at `citry@0.5.1`
- `I51` = `packages/js/citry-client/src/citry-i18n.ts` at `citry@0.5.1`
- `v051/` = `docs_site/versions/0.5.1/`
- `RB` = `docs_site/content/reference/browser-apis.md` on the branch
- `U/` = `packages/py/citry_ui/citry_ui/`

A 0.5.1 column path without a tag prefix means the same path at the
`citry@0.5.1` tag. Branch line numbers come from the audit baseline
`2db4ba42` and may have moved by a few lines in rows that later commits
touched; file names are current.

Terms used below:

- **Hydration**: Vue adopts the HTML the server already sent instead of
  building the page again in the browser.
- **Occurrence**: one rendered instance of a component on a page; Citry
  tracks each by a render ID.
- **Strict fragment**: HTML in which every tag that opens also closes
  inside the same piece, with no bare `<`.
- **Epoch guard**: the Events bridge numbers each call and drops a response
  that arrives after a newer call's response.

### 3.1 Browser JavaScript

`packages/js/citry-client` is `"private": true` in both versions, so no
TypeScript types were ever published.

#### Window globals and `Citry.*`

| Surface | 0.5.1 | 0.6.0 branch | Status | Notes / replacement |
|---|---|---|---|---|
| `window.Citry` namespace | M51:8540, E51:876 | C:6-14 | changed-compatible | Still created on demand. Rejects a non-object `Citry` global. |
| `Citry.events.send(target, name, args?, opts?)` | E51:6759 | C:77-79, 3574-3583 | changed-compatible | Target is a render ID or element; `render:<id>` also accepted. Rejects when a target matches several apps, and before the app mounts (wait for `citry:ready`). `opts` keeps only `timeout`; `wait` is ignored (decision 6.1). |
| `Citry.events.on(name, fn)` | E51:6786 | C:80-86 | unchanged | Adds argument type checks. |
| `Citry.events.configure({csrf, timeout, transport, url})` | E51:6797 | C:87-93 | changed-compatible | All four fields honored. Throws on a non-plain object (0.5.1 accepted `null`). |
| `Citry.events.registerTransport(name, {send})` | E51:2512-2526 | C:94-99; EV:100-117 | changed-incompatible | Called as `send(envelope, request)`. A transport that drops `request.headers` fails every handler that returns a render. Now a Breaking CHANGELOG entry. |
| `Citry.events.applyActions(actions)` | E51:6816-6827 | C:43-76, 150-229 | changed-incompatible | CSS-selector targets and non-`morph` swaps rejected; unknown fields, sparse arrays, and non-plain objects rejected (C:150-199); Render/State actions need a mounted target; fires `citry:events:*` with `event: "__external__"` for mounted targets. |
| `Citry.events._internal`, `_decorate`, `_loadingFor`, and other underscore names | E51:6829-6870 | none | removed | Private. |
| `Citry.alpine.beforeStart(fn)` | M51:617-624; v051 `advanced/alpine-runtime` | none | removed | Documented plugin hook. No public way to install a Vue plugin on Citry's apps (decision 6.2). |
| `Citry.alpine._install`, `_register`, `_magic`, `_morph`, ... | M51:625-680 | none | removed | Private. |
| `globalThis.Alpine` | M51:325, 434 | none | removed | Alpine is gone. |
| `Citry.manager.*` (`registerComponent`, `registerComponentData`, `callComponent`, `decorateContext`, `loadJs`, `loadCss`, ...) | M51:8541-8566 | none | removed | Named in the 0.5.1 django-components guide. Fragments load their own assets. Dead Python that emitted `Citry.manager.registerComponentData` was deleted (`f817b31d`, `49a8d6c7`). |
| `Citry.manager.ownership.*` | M51:8567-8587 | none | removed | Belonged to the ownership graph. |
| `Citry.i18n.provider(element, parent)` | I51:2186 | none | removed | Undocumented wiring. |
| `Citry.vue` | none | C:9-13; RB | new | The page's pinned Vue runtime. |
| `Citry.fragments.load`, `window.Vue`, `window.CitryVueEvents`, `window.CitryVueFragments`, `window.__citryRuntime` | none | `citry-fragments.ts:106-119`; `P/_vue/*.js`; C:4568 | new | Undocumented globals. `window.Vue` is `Citry.vue`. The rest are implementation globals users could come to depend on. |

#### `$component(...)` and the callback context

| Surface | 0.5.1 | 0.6.0 branch | Status | Notes / replacement |
|---|---|---|---|---|
| `$component(fn)` callback form | M51:7595-7640; v051 `reference/browser-apis` | C `runCallback`; RB | changed-incompatible | Shorthand for `onServerRender`. Runs after mount and after each accepted server render of this component. Receives the restored fields below, but not `data`, `scope`, `props`, `graph`, `effect`, `reactive`, `provide`, `inject`, `unprovide`. |
| `$component({props, init})` config form | M51:7605-7630 | C `registerTypeOptions` | restored | The object is Vue Options; `init` runs as `onServerRender`. Naming both throws; a non-function `init` throws. Before the fix Vue dropped `init` silently. |
| Returned cleanup function | M51:7632-7640 | C `runCallback` | unchanged | A non-function return other than `undefined` now throws. |
| field `id` (render ID) | M51:7595 | C `runCallback` getter | restored | Reads the occurrence's current render ID, or `null`. |
| field `els` | M51:7140, 7594 | C `runCallback` | restored | One array of the component's connected top-level elements for the component's lifetime, refilled on each server render and on each read of the getter. A destructured reference does not see changes made only in the browser until the next refill. |
| field `data` | M51:7595 | none | removed | `js_data()` keys are instance members (`component.<key>`). |
| field `graph` | M51:7596 | none | removed | Ownership graph concept. |
| field `props` | M51:7609 | none | removed | Vue props on `component`. |
| field `scope` | M51:7139 | none | removed | The Vue instance replaces the Alpine scope. |
| field `state` | E51:6686 | C `runCallback` getter | restored | `component.$state`, or `null` for a component without Events, as in 0.5.1. |
| field `i18n` | I51:2201-2203 | C `runCallback` getter | restored | `component.$i18n`, or `null` outside a client i18n provider. |
| field `effect(fn)` | M51:7159-7177 | none | removed | `Citry.vue.watchEffect` inside the callback; Citry stops its effect scope with the run. |
| field `reactive(value)` | M51:7150-7158 | none | removed | `Citry.vue.reactive`. |
| fields `provide`, `inject`, `unprovide` | M51:7141-7149 | none | removed | Vue `provide` / `inject` Options. No Vue equivalent of `unprovide`. |
| field `sendEvent(name, args?, opts?)` | E51:6693-6701 | C `runCallback` | restored | Calls `component.$sendEvent`; rejects on a component without Events, as in 0.5.1. |
| field `onEvent(name, fn)` | E51:6702-6705 | C `runCallback` | changed-incompatible | Bound to the run. Hears only events this component's server handlers dispatch. The runtime calls listeners directly, so events fired by page code do not reach them, and `stopPropagation()` no longer blocks delivery. Works without Events, where 0.5.1 threw. In CHANGELOG. |
| field `loading(name?)` | E51:6687-6689 | C `runCallback` | restored | `component.$loading`; `false` without Events. |
| field `error(name?)` | E51:6690-6692 | C `runCallback` | restored | `component.$error`; `null` without Events. |
| `onServerRender({component, revision, onEvent, ...})` | none | C:1705-1737; RB | new | |
| `js_data()` keys as instance members | none | RB | new | |

#### Template helpers and directives

| Surface | 0.5.1 | 0.6.0 branch | Status | Notes / replacement |
|---|---|---|---|---|
| `$state` | E51:5195-5198 | C:1153-1230 | changed-incompatible | A nested write (`$state.items.push(x)`) throws "Nested $state values are read-only". 0.5.1 changed only the local copy. In CHANGELOG. |
| `$loading(name?)` | E51:5200-5212 | C:1779, 3750-3756 | unchanged | Same meaning; `false` on a component without Events. Outside any Citry component it throws, as in 0.5.1 (E51:1794-1805). |
| `$error(name?)` | E51:5214-5223 | C:1780, 3757-3762 | unchanged | Same error shape; `null` on a component without Events. Outside any Citry component it throws, as in 0.5.1. |
| `$sendEvent(name, args?, opts?)` | E51:5225-5257 | C `$sendEvent` | changed-incompatible | `timeout` works. Without Events it rejects, as in 0.5.1 (restored). `opts.wait: false` is still silently ignored and every call from an app is sent one at a time (decision 6.1). |
| `$onEvent(name, fn)` | E51:5259-5270 | C:1803-1810 | changed-incompatible | The runtime calls listeners directly, so events fired by page code do not reach them. On a component without Events it returns an unsubscribe function that does nothing, as in 0.5.1 (restored). In CHANGELOG. |
| `$provide`, `$inject`, `$unprovide` | M51:7086-7096 | none | removed | Vue `provide` / `inject`. |
| `$i18n` | I51:2208 | `citry-i18n-vue.ts:715-760`; RB `#i18n` | changed-compatible | Vue instance member with the same ten members. The reference entry is back on RB (restored in the HTTP/i18n area). |
| `$c-tr:...` binding | I51:2207 | `P/_i18n_directives.py` | unchanged | Same syntax. |
| `$root` override (graph-aware) | M51:3508-3515 | none | removed | Vue's `$root` is the app root. |
| `$c-props` component attribute | M51:21, 241 | none | removed | Vue props. |
| Citry's Alpine directives (`x-citry-boundary`, `x-citry-fill-source`, `x-citry-tr`) | M51:474, 3503 | none | removed | Generated internally. |
| Alpine (`x-*`, stock magics, `alpine:init`, `alpine:initialized`) | v051 `syntax/alpine` | none | removed | Closest startup event: `citry:ready`. |

#### DOM events

| Surface | 0.5.1 | 0.6.0 branch | Status | Notes / replacement |
|---|---|---|---|---|
| `citry:events:before` (cancelable) | E51:2602-2607 | EV:576, 915; C:3374-3401 | changed-compatible | Same detail. Also fires for mounted `applyActions` with `event: "__external__"`. |
| `citry:events:after` `{ok}` | E51:2603 | EV:763, 776 | unchanged | |
| `citry:events:error` `{error}` | E51:2753 | EV:552, 772 | changed-compatible | Same envelope. |
| `citry:events:swapped` `{els}` | E51:4596 | EV:480; C:3393 | changed-compatible | The host fills `els` with the live Vue root elements. |
| `citry:events:stale` `{reason}` | E51:2037, 3636-3640 | EV (stale sites); C `dispatchLifecycleEvent` | changed-incompatible | Reasons: `superseded`, `retired`, `epoch`, `disposed` (new), `version` (restored). `cancelled` and `timeout` stay removed: a timed-out call is aborted, so no late response arrives. Cancelable only for `version`. When the calling component is gone, the event starts at `document` with `instance` and `class` set to `null`. |
| Version-skew reload prompt (default action of `stale` / `version`) | E51:2024-2045, 2175 | EV `stale_state` branch; C `promptReload` | restored | On a `stale_state` error the bridge fires a cancelable `stale` with `reason: "version"` before `error`; if nobody cancels it, the page asks once per page to reload. The call still rejects with the server's error. |
| Server `Dispatch` `CustomEvent` | E51:4440-4492 | C:3364-3372 | changed-compatible | Same delivery for server results. `applyActions` Event actions with a CSS-selector target are rejected. |
| `citry:ready` `{appId, revision}` | none | C:3852 | new | Documented. |
| `citry:rendered` `{appId, revision}` | none | C:3470 | new | Undocumented. Fires only after a declarative `@c-*` call settles. |

#### Data attributes and build variants

| Surface | 0.5.1 | 0.6.0 branch | Status | Notes / replacement |
|---|---|---|---|---|
| `data-cid-<id>` on component roots | v051 django-components guide DJC-052/094; `troubleshooting` | on static components only; absent on Vue-owned components (checked by rendering) | changed-incompatible | Selectors stop matching interactive components. The upgrade guide says so (decision 6.3). |
| `data-cid`, `data-cev-*`, `data-citry-root`, other Alpine markers | E51:5276-5278 | none on Vue components | removed | Listed as reserved in 0.5.1, not as a read API. |
| `data-citry-key`, `data-citry-css-class` | M51 | still emitted by Python for some output | unchanged | Internal markers. Element `#c-key` no longer writes `data-citry-key` (template area). |
| Standard vs CSP Events bundle | v051 `advanced/alpine-runtime` | one runtime; templates compiled on the server | changed-compatible | Strict CSP no longer limits expression syntax. |
| npm package `citry-client` | `"private": true` | same | unchanged | Never published. |

### 3.2 Python API

#### `citry.__all__`

0.5.1 exports 191 names and the branch exports 190: `TemplateNode` is
removed (decision 6.18), and every other name is still there. The rows
below are the 13 names that changed, the removed name, and one row for the
rest.

| Surface | 0.5.1 | 0.6.0 branch | Status | Notes / replacement |
|---|---|---|---|---|
| 177 other names in `citry.__all__` | `P/__init__.py` | same | unchanged | Same signatures and public members. |
| `citry.TemplateNode` (also `citry.nodes.TemplateNode`) | `P/nodes/__init__.py` | not defined | removed | The template compiler never generated it. An extension that built one should add the markup to the template source in `on_template_loaded`. Decision 6.18. |
| `citry.Citry(...)` | `P/citry.py:130` | `P/citry.py:130, 170-171` | changed-compatible | Adds keyword params `ssr=True`, `ssr_element_threshold=0`. Methods unchanged. |
| `citry.CitrySettings` | `P/settings.py` | `P/settings.py` | changed-compatible | Gains `ssr`, `ssr_element_threshold`. |
| `citry.CitryRender.serialize()` / `serialize_result()` | `P/citry_render.py:236, 309` | `P/citry_render.py:364, 441` | changed-compatible | New keyword `ssr`. Constructor gains keyword-only `render_target`, `owner_citry`. |
| `citry.CitryTemplate` | `P/citry_template.py:47` | same | changed-compatible | New fields `prepared_generate` (inserted after `generate`), `prepared_standalone_bodies`. Built by the engine. |
| `citry.RenderFrame` | `P/citry_render.py:158` | `P/citry_render.py:229` | changed-compatible | New trailing field `prepared_occurrence`. |
| `citry.URLRoute` | `P/util/routing.py:156` | `P/util/routing.py` | restored | The branch had widened `methods` to allow `None`; it is a tuple again on every route (`04084529`). A value that is not a non-empty tuple of uppercase method names now raises when the route is built. |
| `citry.Extension` | `P/extension.py` | `P/extension.py:950, 954` | changed-compatible | New hooks `browser_plugin()`, `prepare_browser_render(ctx)`. |
| `citry.CitryContext` | `P/citry_context.py:65` | `P/citry_context.py:60` | changed-incompatible | `ownership` param and attribute removed; `.js_data` slot added. Positional callers past `sandboxed` shift. Engine-built. |
| `citry.CitryElement` | `P/citry_element.py:63` | `P/citry_element.py:87` | changed-incompatible | `ownership_invocation_id`, `ownership_graph`, `forward_ownership_invocation` removed; `prepared_call_metadata` added; binding record type changed. `render()` unchanged. |
| `citry.LintSettings` | `P/settings.py:97` | `P/settings.py:97` | changed-incompatible | `rule_unknown_alpine_variable` and `alpine_variables` renamed to `rule_unknown_vue_variable`, `vue_variables`; two new rules. An old name raises `TypeError` that names the replacement on every Python version (`a2d0f7c5`). |
| `citry.TemplateLintInfo` | `P/_linting.py:166` | same | changed-incompatible | Same renames; `alpine_variables` of `AlpineVariableInfo` becomes `vue_variables` of `VueVariableInfo`. |
| `citry.OnSerializeContext` | `P/extension.py:528` | `P/extension.py:534` | changed-incompatible | New required field `selected_render` inserted before `html`. Readers unaffected. In CHANGELOG. |
| `citry.ExtensionManager.on_serialize` | `P/extension.py` | same | changed-incompatible | New positional param `selected_render`. Internal dispatcher on a documented class. |

#### `Component` class

All 40 public members keep their signatures and defaults. The behavior
changes:

| Surface | 0.5.1 | 0.6.0 branch | Status | Notes / replacement |
|---|---|---|---|---|
| `Component.simple` | `P/component.py:653` | `P/component.py:715` | changed-compatible | New value `"vue"`. |
| `Component.js_data()` contract | `P/component.py:1136` | `P/component.py:1205`; `P/component_render.py:2668-2727` | changed-incompatible | Keys become Vue instance members. A key starting with `$` or `_`, or `citryId`, raises `ValueError` at render. In CHANGELOG. |
| `Component.Lint` nested class | `P/component.py` | `P/component.py:915-918` | changed-incompatible | Old Alpine names still removed, but the `ValueError` now names the replacement (`a2d0f7c5`; run). |
| Component name `mark` | allowed | `P/component_registry.py:29, 159` | changed-incompatible | Reserved for `<c-mark>`. A class named `Mark` fails at definition with `AlreadyRegistered`. In CHANGELOG (decision 6.10). |
| Kwargs unknown-key error | `P/component.py` | `P/component.py:131-164` | changed-compatible | Adds a "Did you mean" hint. |
| `x-*` attributes in templates | acted on by Alpine | rendered unchanged, nothing acts on them (checked by rendering) | changed-incompatible | Silent. Only `x-on:` on a component tag raises (decision 6.5). |

#### Render and serialize entry points

| Surface | 0.5.1 | 0.6.0 branch | Status | Notes |
|---|---|---|---|---|
| `CitryElement.render(...)` | `P/citry_element.py:130` | `P/citry_element.py:140` | unchanged | |
| `Citry.render_template(...)` | `P/citry.py:329` | `P/citry.py:333` | unchanged | |
| `CitryRender.serialize` / `serialize_result` | see above | see above | changed-compatible | `ssr=` added. |
| `citry.serialize.serialize_render`, `serialize_render_result` | `P/serialize.py` | same | changed-compatible | `ssr=` added. |
| `SerializedRender(html, security)` | `citry.__all__` | same | unchanged | |
| `SerializedSecurity(scripts, csp_script_hashes)` | same | same | unchanged | `csp_script_hashes` now lists the Vue bootstrap script. |
| `SerializedScriptSecurity(...)` | same | same | unchanged | |
| `Slot`, `SlotContext`, `SlotData`, `SlotFunc` | same | same | unchanged | |

#### Exceptions

| Surface | 0.5.1 | 0.6.0 branch | Status | Notes |
|---|---|---|---|---|
| 13 exception classes in `citry.__all__` | `P/__init__.py` | same | unchanged | Same classes, bases, signatures. |
| `CacheKeyError`, `EventError`, `PreviewError`, `citry.ext.*.errors.*` | | | unchanged | |
| `citry.component_render.CacheArtifactError` re-export | `P/component_render.py` | not re-exported | removed | Still defined in `citry.ext.cache`. |
| `ValueError` for reserved `js_data` keys | none | `P/component_render.py:2705-2727` | new | |
| Template errors for Vue directives on component tags and `<c-slot>` | none | `P/client_directives.py:232, 286` | new | Messages suggest what to write instead. |
| `RuntimeError` for `x-on:` on a component tag | none | `P/nodes/__init__.py:1672-1675` | new | |

#### Public submodules

| Surface | 0.5.1 | 0.6.0 branch | Status | Notes / replacement |
|---|---|---|---|---|
| Unchanged modules (`citry.attrs`, `autodiscovery`, `cache`, `command`, `commands.*`, `component_graph`, `component_like`, `components.provide`, `components.error_fallback`, `constants`, `contrib.*`, `ext`, `ext.cache` package parts, `ext.debug`, `ext.dependencies.{routes,scripts}`, most of `ext.events.*`, `ext.i18n` modules other than those listed below, `ext.preview.*`, `library_component`, `lifecycle`, `provide`, `reload`, `util.{css,exception,id,logger,misc,routing}`) | | | unchanged | Same names and signatures. |
| `citry.ownership` (28 names) | `P/ownership.py` ("This module is internal.") | gone | removed | Binding records moved to `citry.client_directives`. No replacement for the graph. |
| `citry.ownership_manifest` (7 names) | `P/ownership_manifest.py` | gone | removed | The Vue app JSON replaces the manifest. |
| `citry.browser_render` | none | `P/browser_render.py` | new | Browser plugin types and helpers. |
| `citry.components.mark` | none | `P/components/mark.py` | new | |
| `citry.ext.events.renderers` | none | `P/ext/events/renderers.py` | new | Render encoders. |
| `citry.analysis` Alpine names (`ALPINE_AMBIENT_NAMES`, `AlpineLintConsumer`, `AlpineLintFinding`, `lint_unknown_alpine_variables`, `BrowserComponentMember`, `BrowserComponentPropsUse`, `BrowserScopeWrite`, `browser_component_members`, `browser_component_prop_uses`, `browser_component_scope_writes`) | `P/analysis.py:3873` | not present | changed-incompatible | Replaced by `VUE_AMBIENT_NAMES`, `VueLintConsumer`, `VueLintFinding`, `lint_unknown_vue_variables`, `BrowserComponentMemberReference`, `BrowserComponentPropSite` and friends. `browser_component_scope_writes` has no counterpart. |
| `citry.analysis` changed literals and fields | | | changed-incompatible | `BrowserBinding.kind` `x-data`/`x-for` to `v-for`/`v-slot`; `BrowserExpression.host` `alpine` to `vue`; `BrowserComponentSourceAnalysis` drops `scope_writes`, adds `component_calls`, `public_names`, `sections`, `member_references`. |
| `citry.analysis` new keyword params and trailing fields | | | changed-compatible | For example `lint_unknown_component_js_members(severity=)`, `BrowserExpression.python_bindings`. |
| `citry.analysis` new names | | | new | 18 names including `VueLintConsumer`, `lint_vue_python_variables`, `mark_literal_findings`. |
| `citry.nodes` ownership re-exports (`ComponentTagClientBindingRecord`, `current_ownership_graph`, ...) | `P/nodes/__init__.py` | removed | changed-incompatible | Documented node classes (`Node`, `IfNode`, ...) unchanged. |
| `citry.nodes` call metadata | | | changed-incompatible | `physical_parent_region_id` becomes `direct_parent_execution`. Internal. |
| `citry.citry_render` | | | changed-incompatible | Physical-region parts removed; prepared render parts added. Internal render-assembly types changed; no user-facing effect. |
| `citry.component_render` | | | changed-incompatible | Ownership helpers and incidental re-exports removed; prepared-render helpers added. Internal render-assembly types changed; no user-facing effect. |
| `citry.serialize` | | | changed-incompatible | Ownership manifest names removed; `RenderDecoration`, `RenderFrame`, `escape_to_str`, `format_attrs` re-exports added. |
| `citry.client_directives` | | | changed-compatible | New binding records and message helpers. |
| `citry.components` | | | changed-compatible | Exports `make_mark_component`. |
| `citry.components.dynamic`, `.js_css` | | | unchanged | |
| `citry.constness` | | | changed-compatible | `ConstPrecomputeAdapter`, `precompute_const_parts(adapter=)`. |
| `BUILTIN_COMPONENT_NAMES` | | `P/component_registry.py:29` | changed-incompatible | Adds `"mark"`. |
| `citry.ext.cache.artifact` | | | changed-incompatible | Region parts replaced by 15 typed parts; `CachedRenderArtifact.ownership` removed. Old cache entries become misses. |
| `citry.ext.cache.replay` | | | new | Only underscore names. |
| `citry.ext.cache.extension` | | | unchanged | |
| `citry.ext.dependencies` / `.types` / `.extension` | | `P/ext/dependencies/emission.py:71, 92` | changed-incompatible | `OnDependenciesContext` gains required `selected_render`. |
| `citry.ext.dependencies.emission` | | | changed-incompatible | Ownership names and `emit_dependencies(ownership_artifact=)` removed; Vue key constants added. |
| `citry.ext.events.EventsDispatcher` | `P/ext/events/dispatcher.py:369` | `:366, 379` | changed-compatible | Keyword-only `render_encoders`, `preferred_renderer`. |
| `citry.ext.events.bindings` | | | changed-incompatible | `DATA_CEV_*`, `CevAttr`, `BINDING_SPEC_ENCODING` removed; `RUNTIME_*_ATTR` added; `class_id` param dropped. |
| `citry.ext.events.emission` | | | changed-incompatible | `emit_events_dependencies`, runtime path constants, ownership names removed; `build_manifest` drops `client_graph_revision`; `build_events_manifest` added. |
| `citry.ext.events.extension` | | | changed-incompatible | `emit_events_dependencies` re-export gone. |
| `citry.ext.events.routes` | | `P/ext/events/routes.py` | changed-incompatible | `CSP_RUNTIME_PATH`, `EVENTS_CSP_RUNTIME_SRC` removed; `DEFINITION_PATH`, `STYLE_ASSET_PATH`, `EVENT_ROUTE_METHODS` added. |
| `citry.ext.events.results` | | | changed-compatible | Render encoder classes; `encode_actions(render_encoder=, render_context=)`. |
| `citry.ext.events.schemas` | | | unchanged | Only incidental imports gone. |
| `citry.ext.i18n.extension` | | | changed-compatible | Re-exports browser plugin types; sends i18n data inside the Vue app data on interactive pages. |
| `citry.ext.i18n.emission`, `.bindings`, `.components` | | `P/ext/i18n/emission.py`, `bindings.py`, `components.py` | changed-compatible | `emission` adds `vue_plugin_js` and `prepared_i18n_payload` and serves the Vue plugin; `bindings` evaluates values as Vue expressions; the provider host template uses `$component`. No public name removed. |
| `citry.ext.preview.*` | | | unchanged | |
| `citry.util.html` | | | changed-compatible | `script_json` added. |
| `citry.extension` re-exports | | | changed-incompatible | Re-exports `LintSettings`, `OnSerializeContext`, `OnRenderCacheStageContext` with their changes. |
| Other re-exporting modules (`host_templates`, `slots`, `tag_rules`, `assets`, `introspection`, `citry_context`, `citry_element`, `citry_template`, `settings`, `component`) | | | changed-incompatible | Re-export the section's changed classes. |

### 3.3 Settings, extensions, CLI, LSP

#### `Citry(...)` and `CitrySettings`

| Surface | 0.5.1 | 0.6.0 branch | Status | Notes / replacement |
|---|---|---|---|---|
| `extensions=()` | `P/settings.py:325` | `P/settings.py:369` | unchanged | |
| `extensions_defaults=None` | `:326` | `:370` | unchanged | |
| `dirs=()` | `:327` | `:371` | unchanged | |
| `cache=None` | `:328` | `:372` | changed-compatible | Now also stores compiled Vue definitions and stylesheets. Several workers need a shared backend (CHANGELOG). The default in-memory cache keeps them without limit (decision 6.15). |
| `sandbox_expressions=True` | `:329` | `:373` | unchanged | |
| `autodiscover=True` | `:330` | `:374` | unchanged | |
| `mode="production"` | `:331` | `:375` | unchanged | |
| `template_globals=None` | `:332` | `:376` | unchanged | |
| `lint=None` | `:333` | `:377` | changed-incompatible | Two `LintSettings` fields renamed. |
| `id_generator=None` | `:335` | `:379` | unchanged | |
| `secret=None` | `:336` | `:380` | unchanged | |
| `event_result_resolvers=()` | `:337` | `:381` | unchanged | |
| `event_payload_codecs=()` | `:338` | `:382` | unchanged | |
| `security_csp="off"` | `:339` | `:383` | changed-compatible | Same values. `"strict"` scans final HTML instead of selecting the Alpine CSP build; `"off"` no longer needs `unsafe-eval`. Any mode other than `"off"` turns off hydration. In CHANGELOG. |
| `security_javascript="allow"` | `:340` | `:384` | changed-compatible | `"omit"` removes the Vue runtime. Values other than `"allow"` turn off hydration. |
| `security_script_integrity="off"` | `:341` | `:385` | changed-compatible | `"citry"` turns off hydration. |
| Per-call `serialize(security_csp=..., security_javascript=...)` | `P/citry_render.py:236` | `P/_vue/serialization.py:1113-1120` | changed-incompatible | On an Events page a differing override raises. In CHANGELOG. |
| `ssr=True` | none | `P/settings.py:386` | new | |
| `ssr_element_threshold=0` | none | `P/settings.py:387` | new | |

No 0.5.1 default changed.

#### `LintSettings`, `Component.Lint`, `TemplateLintInfo`

| Surface | 0.5.1 | 0.6.0 branch | Status | Notes / replacement |
|---|---|---|---|---|
| `rule_unknown_template_variable="error"` | `P/settings.py:127` | `:134` | unchanged | |
| `rule_i18n_missing_param_type="warning"` | `:128` | `:135` | unchanged | |
| `template_variables={}` | `:129` | `:136` | unchanged | |
| `rule_unknown_alpine_variable="error"` | `:130` | none | removed | Use `rule_unknown_vue_variable`. The error names it (`a2d0f7c5`). |
| `alpine_variables={}` | `:131` | none | removed | Use `vue_variables`. The error names it. |
| `rule_unknown_vue_variable="error"` | none | `:137` | new | |
| `vue_variables={}` | none | `:138` | new | |
| `rule_unknown_component_js_variable="error"` | `:132` | `:139` | unchanged | |
| `component_js_globals={}` | `:133` | `:140` | unchanged | |
| `rule_unknown_component_js_member="error"` | none | `:141` | new | |
| `rule_vue_python_variable="warning"` | none | `:142` | new | |
| `Component.Lint` with the old names | `P/component.py` | `P/_linting.py` | changed-incompatible | Raises a `ValueError` that now names the replacement (checked by rendering). |
| `TemplateLintInfo` fields and JSON keys | `P/_linting.py:166-244` | `P/_linting.py:166-178` | changed-incompatible | Renamed; a 0.5.1 dict no longer passes `from_dict()`. |
| `citry.analysis` exports | `P/analysis.py` | same file | changed-incompatible | See 3.2. |

#### Extension API

| Surface | 0.5.1 | 0.6.0 branch | Status | Notes / replacement |
|---|---|---|---|---|
| Registration, `extensions_defaults`, `Extension.name`, `class_name`, nested `Config` | `P/extension.py` | `P/extension.py:650` | unchanged | |
| `Extension.urls` / `URLRoute(methods=...)` | `P/util/routing.py:187` | `P/util/routing.py` | restored | `methods` is always a tuple again. The branch had admitted `None`. |
| `validate_config_fields`, `inspect_component`, `inspect_template_namespace` | | `:728, 788, 810` | unchanged | |
| Lifecycle hooks (`on_extension_created`, `on_component_class_created`, ...) | | `:833-847` | unchanged | |
| Render hooks (`on_component_input`, `on_component_data`, ...) | | `:852-893` | unchanged | |
| `export_render_cache`, `render_cache_bypass_reason` | | `:905, 935` | unchanged | |
| `stage_render_cache(ctx)` | | `:910`; context `:303-311` | changed-incompatible | Context gains required `parent_ids`, `provided_render_ids`. Hooks that read it are unaffected; code that builds it by hand breaks. |
| `on_serialize(ctx)` | `:930` | `:939` | changed-incompatible | `selected_render` inserted before `html`, so positional construction breaks; hooks that read it are unaffected. A user hook turns off hydration. |
| Template/asset hooks (`on_template_loaded`, ..., `on_files_reset`) | | `:974-1027` | unchanged | A user `on_js_loaded` turns off hydration. |
| Custom hooks via `ExtensionManager.emit` | | `:1593` | unchanged | |
| `ExtensionCommand`, `ExtensionManager.commands`, `get_extension_command` | | | unchanged | `command.py` is byte-identical. |
| The other 28 context classes | | `:92-553` | unchanged | |
| `on_dependencies` / `OnDependenciesContext` | `P/ext/dependencies/emission.py:74-108` | `:70-106` | changed-incompatible | `selected_render` added before `strategy`. `before_manifest` renamed to `early_scripts`; the old name raises `AttributeError` that names the replacement. In CHANGELOG (decision 6.8). |
| `Component.on_dependencies` | `P/component.py` | `:1274` | changed-compatible | Overriding it turns off hydration. |
| `EventsExtension.on_dependencies` | `P/ext/events/extension.py:438` | none | removed | Internal to a built-in extension. |
| `Extension.browser_plugin()` | none | `P/extension.py:950` | new | Undocumented. The only extension-facing way to add browser code (decision 6.2). |
| `Extension.prepare_browser_render(ctx)` | none | `P/extension.py:954` | new | Undocumented. |
| Debug extension config | `P/ext/debug.py:136-190` | `:97-150` | changed-compatible | Same config; implementation changed. |

#### CLI

`--help` for every command matches, except the program description.

| Surface | 0.5.1 | 0.6.0 branch | Status | Notes |
|---|---|---|---|---|
| `citry` description | "...Alpine.js..." | "...Vue..." | changed-compatible | Text only. |
| `citry --version`, `-h` | | same | unchanged | |
| Leading `--app module:attr` | `P/__main__.py:45-63` | same | unchanged | |
| `citry check [--static] [--format]` | | same | unchanged | JSON schema version stays 1; codes changed (below). |
| `citry format ...` | | same | unchanged | |
| `citry list` | | same | unchanged | |
| `citry inspect --json [component]` | | same | changed-compatible | Lint records carry renamed keys. |
| `citry create [--path] name` | | same | unchanged | |
| `citry watch [--path]` | | same | unchanged | |
| `citry ext list` | | same | unchanged | |
| `citry ext run events openapi` | | same | unchanged | |
| `citry ext run i18n {extract,check,compile,inspect,coverage}` | | same | unchanged | |
| `citry ext run preview {serve,render}` | | same | unchanged | |
| `citry-lsp [--tcp] [--ws] [--host] [--port]` | 0.1.7 | same | unchanged | |

#### LSP, editor, formatter, diagnostic codes

| Surface | 0.5.1 / citry-lsp 0.1.7 | 0.6.0 branch | Status | Notes / replacement |
|---|---|---|---|---|
| LSP `initializationOptions` (`app`, `standardFormatting`, `envFile`, `embeddedFormatting`) | `citry_lsp/server.py:124-168` | unchanged | unchanged | |
| VS Code settings | `packages/editors/vscode/package.json` | no diff | unchanged | |
| Formatter options | `P/_formatter.py` | identical | unchanged | |
| citry-lsp version and dependency | 0.1.7, `citry>=0.5.1` | `version = "0.1.7"`, `citry>=0.6.0` (`cebde4fe`) | changed-incompatible | Released 0.1.7 fails to import with citry 0.6.0. The branch now requires citry 0.6.0 and analyzes the restored callback fields, but the version number is not bumped (decision 6.11). |
| Worker record field `client_writable` | none | `citry_lsp/project.py:365` | new | citry and citry-lsp need matching versions. |
| `citry.alpine.unknown-variable` | `P/_diagnostic_catalog.py:19` | none | removed | Now `citry.vue.unknown-variable`. In CHANGELOG. |
| `citry.component-js.unknown-data-member` | `:22` | none | removed | Now `citry.component-js.unknown-member`. In CHANGELOG. |
| `citry.browser.unknown-component-prop` | `:26` | none | removed | Checked `$c-props` keys. In CHANGELOG. |
| `citry.browser.missing-component-prop`, `incompatible-component-prop` | | `:28-29` | changed-compatible | Check Vue props. |
| `citry.browser.unknown-server-event` | | | changed-compatible | Text says "Vue expression". |
| `citry.csp.incompatible-browser-code` | | | changed-compatible | Checks the configured policy. |
| `citry.template.marker-name-invalid` | none | `:18` | new | |
| `citry.js-data.public-name-collision` | none | `:20` | new | |
| `citry.vue.unknown-variable` | none | `:21` | new | |
| `citry.vue.python-variable` | none | `:22` | new | |
| `citry.component-js.unknown-member` | none | `:25` | new | |
| All other codes | | | unchanged | Same severity and surfaces. |

### 3.4 Template syntax

The Pest grammar, `P/tag_rules.py`, `P/_i18n_directives.py`, and
`P/attrs.py` are byte-identical between `citry@0.5.1` and the branch. Every
change below comes from validation in `crates/citry_template_parser/src/parser.rs`,
`P/client_directives.py`, `P/nodes/__init__.py`, and `P/_vue/`.

#### Text, expressions, comments

| Surface | 0.5.1 | 0.6.0 branch | Status | Notes / replacement |
|---|---|---|---|---|
| `{{ expr }}` Python text expression | v051 `syntax/expressions` | same | unchanged | Vue `{{ }}` is not available; use `v-text`. |
| `{{ }}` only outside tags | same | same | unchanged | |
| Expression sandbox | same | same | unchanged | |
| No Python builtins in scope | same | same | unchanged | |
| Expression result table | same | same for static pages | unchanged | |
| `Markup` / `__html__()` inserted verbatim | same | interactive components require a strict fragment (`crates/citry_html_transform/src/output_scanner.rs:515`) | changed-incompatible | `Markup("<div>")` raises inside an interactive component (checked by rendering). In CHANGELOG (decision 6.13). |
| `{# ... #}` comments | v051 `syntax/comments` | same | unchanged | |
| `#` comments inside expressions | same | same | unchanged | |
| HTML comments, `<!doctype>`, processing instructions | v051 `syntax` | an interactive page template needs one well-ordered `<body>` (`P/_vue/document.py:187`) | changed-incompatible | In CHANGELOG. |
| Self-closing and void tags, case rules | same | same | unchanged | |
| Markup in attributes (`c-x="<>...</>"`) | v051 `syntax/nested-templates` | same (checked by rendering) | unchanged | |
| Attributes that never accept markup | same | same | unchanged | |

#### Built-in `<c-*>` tags

| Surface | 0.5.1 | 0.6.0 branch | Status | Notes / replacement |
|---|---|---|---|---|
| `<c-if>`, `<c-elif>`, `<c-else>` | v051 `reference/builtins` | same | unchanged | |
| `<c-for each>` | same | same | unchanged | |
| `<c-empty>` | same | same | unchanged | |
| `<c-slot>` | same | Vue directive forms are a parse error (`parser.rs:1969`) | changed-compatible | 0.5.1 turned `:item` into slot data silently. |
| `<c-fill>` | same | same | unchanged | |
| `<c-component is>` | same | `P/components/dynamic.py` | changed-compatible | Cannot select `mark`. |
| `<c-element is>` | same | same file | changed-incompatible | Vue bindings must be on the tag; Vue attributes arriving through `c-bind` raise in interactive renders. |
| `<c-provide>` | same | same | unchanged | |
| `<c-cache>` | same | same Kwargs | unchanged | |
| `<c-error-fallback>` | same | same | unchanged | |
| `<c-i18n ...>` | same | same Kwargs | unchanged | |
| `<c-trans>` | same | same | unchanged | |
| `<c-css />`, `<c-js />` | same | same tags | unchanged | Output format changed. |
| `<c-raw>` | v051 `syntax/comments` | static pages unchanged; inside an interactive component the body must be a strict fragment | changed-incompatible | Unbalanced tags, `<c-X/>`, or a bare `<` raise (checked by rendering). The content does appear in the served HTML (see the correction below). |
| User component named `mark` | allowed | reserved (`P/component_registry.py:159`) | changed-incompatible | In CHANGELOG. |

Correction to the template audit: its `<c-raw>` note said raw text produced
no server HTML in an interactive render. A re-check by rendering (temporary
audit notes, not kept) shows the raw content in the served HTML:
`<main><p></p><!--[-->{{ a }} @c-click="save" <b>bold</b><!--]--></main>`.
The CHANGELOG line "`<c-raw>` contents and trusted `Markup` are included as
written" is accurate.

#### `c-*` attribute directives

| Surface | 0.5.1 | 0.6.0 branch | Status | Notes / replacement |
|---|---|---|---|---|
| `c-<name>="expr"` | v051 `syntax/dynamic-attributes` | same | unchanged | |
| `c-c-<name>` | same | interactive renders write `True` as `"true"` | changed-compatible | |
| `c-if`/`c-elif`/`c-else` | same | same | unchanged | |
| `c-for`/`c-empty` | same | same | unchanged | |
| `c-bind="mapping"` | same | same for Python data | unchanged | |
| `c-bind` keys spelling browser code (`:x`, `@x`, `v-*`) on elements | passed through as Alpine | static: inert text; interactive: raises (`P/_vue/capture.py:1083`) | changed-incompatible | In CHANGELOG. |
| `c-bind` keys `@click` / `$c-props` on a component tag | worked | raise (`P/nodes/__init__.py:1745`, `P/client_directives.py:346`) | removed | Write `:prop` / `@event` / `v-on="obj"` on the tag. |
| `c-:attr="python_string"` | worked | static: inert; interactive: raises | removed | In CHANGELOG. |
| `c-@event="python_string"` | worked | same as above | removed | |
| `c-x-*` | worked | inert `x-*` attribute | removed | |

#### `#c-*` flags

| Surface | 0.5.1 | 0.6.0 branch | Status | Notes / replacement |
|---|---|---|---|---|
| `#c-key` on an element | rendered `data-citry-key` | used as the Vue key; `data-citry-key` not written | changed-compatible | In CHANGELOG. The hint for misplaced `#c-key` now explains the Vue meaning (`90d1b663`). |
| `#c-key` on a component tag | same | used for occurrence identity | changed-compatible | |
| `#c-key` rules (structural tags, `None`, falsy values) | same | same | unchanged | |
| `#c-ignore` on an element | rendered `data-citry-morph="ignore"` | raises `TypeError` the first time the component renders, static or interactive (`P/_vue/capture.py`) | removed | The message names the element, says Vue updates every element it renders, and suggests a Vue `ref`. In CHANGELOG and the upgrade guide. |
| `#c-ignore` on a component tag | same | raises `TypeError` when the template compiles (at first render), on static and interactive pages (`d2b9540a`; checked by rendering) | removed | Was accepted silently with no effect on the audited branch. In CHANGELOG. |
| `#c-*` flags cannot arrive through `c-bind` | same | same code | unchanged | |

#### Alpine directives on HTML elements

| Surface | 0.5.1 | 0.6.0 branch | Status | Notes / replacement |
|---|---|---|---|---|
| `x-data` | v051 `syntax/alpine` | inert attribute, no diagnostic | removed | `$component({ data() {...} })` or `js_data()`. Silent (decision 6.5). |
| `x-text`, `x-html`, `x-show`, `x-if`, `x-for`, `x-model`, `x-bind:*`, `x-on:*`, `x-init`, `x-effect`, `x-ref`, `x-cloak`, `x-transition`, `x-teleport`, `x-ignore`, `x-id` | same | inert attributes | removed | Vue equivalents. `x-cloak` stays on the element, so an app rule `[x-cloak]{display:none}` hides content for good. |
| `@event="js"` on an element | Alpine `x-on` | Vue `v-on` | changed-incompatible | Names resolve on the Vue instance; a single statement without `;` fails to compile. In CHANGELOG. |
| Alpine-only modifiers (`.outside`, `.window`, `.document`, `.debounce`, `.throttle`, `.camel`, `.dot`) | Alpine | accepted, no diagnostic | changed-incompatible | The modifier compiles into a key filter, so the listener never runs. In CHANGELOG as "have no effect" (decision 6.6). |
| `:attr="js"` on an element | Alpine `x-bind` | Vue `v-bind` | changed-incompatible | Scope changes as for `@event`. |
| Alpine loops cannot clone Citry components | same | `v-for` on a component tag is a parse error | changed-compatible | Hint suggests `<c-for>`. |
| Runtime auto-loads on `x-`/`@`/`:` attributes | same | Vue loads on Vue syntax | changed-compatible | `x-*` alone loads nothing. |
| Unknown Alpine variable check | same | Vue rules | changed-compatible | |

#### Client bindings on a component tag

| Surface | 0.5.1 | 0.6.0 branch | Status | Notes / replacement |
|---|---|---|---|---|
| `$c-props="{ js }"` | v051 `syntax/dynamic-attributes` | parse error naming `:prop` (`parser.rs:1714`) | removed | In CHANGELOG. |
| `c-$c-props="python"` | v051 `concepts/client-interactivity` | parse error | removed | |
| `$c-props` through `c-bind` | same | runtime error | removed | |
| `$c-props` on a non-component tag / case variants | same | any spelling errors | removed | |
| `@event` on a component tag | DOM listener on every child root | Vue component listener (emits / fallthrough) | changed-incompatible | Multi-root child needs `v-bind="$attrs"` or `$emit`. In CHANGELOG. |
| `x-on:event` on a component tag | same as `@event` | raises (`P/nodes/__init__.py:1672`) | removed | In CHANGELOG. |
| `:x`, `v-*`, `ref` on a component tag as Python kwargs | were kwargs | now Vue bindings; `x-*` other than `x-on:` stays a kwarg | changed-incompatible | In CHANGELOG. |
| Forward Alpine attrs through `c-attrs` + `c-bind` | v051 `concepts/client-interactivity` | `:class` key rejected in interactive renders | removed | Vue fallthrough with `inheritAttrs: false`. |
| Fill content keeps its call site's browser scope | same | same rule for Vue | changed-compatible | New limit for group components (in CHANGELOG). |
| Python slot content starts with an empty Alpine scope | same | not applicable | changed-compatible | |

#### Events bindings

| Surface | 0.5.1 | 0.6.0 branch | Status | Notes / replacement |
|---|---|---|---|---|
| `@c-event` with modifiers on an element | v051 `events/bindings` | same syntax; argument object is a Vue expression | changed-compatible | |
| `@c-poll.Ns` on an element | same | same | unchanged | |
| `@c-*` on a component tag | same | kept | changed-compatible | |
| Timed `@c-*` on a component tag | accepted (checked by rendering) | raises (`P/_vue/direct_capture.py:1650`) | removed | In CHANGELOG (decision 6.7). |
| `@c-poll` on a component tag | accepted (checked by rendering) | raises (`P/_vue/direct_capture.py:1625`) | removed | In CHANGELOG (decision 6.7). |
| `@c-poll` / `@c-*` through `c-bind` | accepted (checked by rendering) | docs say unsupported | changed-incompatible | Not run on the branch. |
| `:c-field` State binding | same | same | unchanged | |
| Binding-shaped text inside `<c-raw>` stays literal | same | same | unchanged | |

#### i18n syntax

| Surface | 0.5.1 | 0.6.0 branch | Status | Notes / replacement |
|---|---|---|---|---|
| `tr(...)`, `fmt` | `P/ext/i18n/extension.py:1136` | `:1180` | unchanged | |
| `$c-tr:...="{ js }"` | v051 `i18n/browser` | same parser; values evaluated by Vue | changed-compatible | |
| `c-$c-tr`, `$c-tr` via `c-bind` | same | same code path | unchanged | Not run. |
| `$i18n.*` in browser expressions | same | Vue global | changed-compatible | |
| `<c-i18n client>` boundary | same | kept | unchanged | |

#### Browser helpers used in template attributes

| Surface | 0.5.1 | 0.6.0 branch | Status | Notes / replacement |
|---|---|---|---|---|
| `$state`, `$loading()`, `$error()`, `$sendEvent()`, `$onEvent()` | v051 `events/bindings` | Vue instance members | changed-compatible | Details in 3.1. |
| `$provide()`, `$inject()`, `$unprovide()` | v051 `syntax/alpine` | not defined | removed | |
| Alpine magics (`$el`, `$refs`, `$dispatch`, `$store`, `$watch`, `$nextTick`, `$id`, `$data`, `$root`) | Alpine | Vue has some with different meanings; no `$dispatch`, `$store`, `$id` | changed-incompatible | |

#### HTML attribute rules

| Surface | 0.5.1 | 0.6.0 branch | Status | Notes |
|---|---|---|---|---|
| `True` to bare attribute, `False`/`None` omitted | same | same in server HTML; Vue writes `"true"` for non-boolean attributes | changed-compatible | |
| Bare attribute on a component tag is `True` | same | same | unchanged | |
| `class`/`style` merging | same | `P/attrs.py` identical | unchanged | |
| Components exempt from merging | same | same | unchanged | |
| Duplicate-attribute and case rules | same | same | unchanged | |
| `format_attrs`, `merge_attrs`, `normalize_class`, `normalize_style`, `parse_string_style` | v051 `reference/attributes` | identical | unchanged | |
| Pass-through attributes | same | same | unchanged | Vue-syntax keys rejected (see `c-bind`). |

#### Python node classes

| Surface | 0.5.1 | 0.6.0 branch | Status | Notes |
|---|---|---|---|---|
| `Node`, `ComponentNode`, `ElementAttrsNode`, ... (13 classes) | v051 `reference/nodes` | identical signatures (checked by rendering) | unchanged | Some return typed prepared values in interactive renders. The 14th 0.5.1 class, `TemplateNode`, is removed (section 3.2, decision 6.18). |

#### New syntax

| Surface | 0.6.0 branch | Status | Notes |
|---|---|---|---|
| Vue directives on elements (`v-*`, `:x`, `@x`, `v-model`, `v-for` with `:key`, `<template v-if>`, ...) | `docs_site/content/syntax/vue.md` | new | |
| Vue bindings on component tags (`:prop`, `v-bind`, `@event`, `v-on`, `v-if` chains, `v-model`, `v-show`, custom directives, `ref`) | `P/client_directives.py:315-360` | new | |
| Parse errors with hints for unsupported directives | `parser.rs:1865, 1969` | new | The `v-once`/`v-memo` hint on a component tag no longer suggests moving the directive to an element (`90d1b663`). |
| Rejected Vue helpers (`<Teleport>`, `<Transition>`, `<Suspense>`, `<KeepAlive>`) | `P/_vue/compiler.py` | new | `v-once` on an element fails with "unsupported raw-text or cached construct" (decision 6.14). |
| `<c-mark name="...">` | `P/components/mark.py` | new | |
| `citry.vue.python-variable` lint | `P/_diagnostic_catalog.py:22` | new | |

### 3.5 HTTP routes, protocol, i18n, citry-ui

#### Routes

| Surface | 0.5.1 | 0.6.0 branch | Status | Notes / replacement |
|---|---|---|---|---|
| `GET {prefix}/citry.js` | `P/ext/dependencies/routes.py:142` | same route; serves `P/_vue/runtime.js` | changed-compatible | Same URL, now the Vue runtime. Adds `Access-Control-Allow-Origin: *`. |
| `GET {prefix}/cache/{class_id}.{script_type}` | `:139` | same | changed-compatible | Adds the CORS header. |
| `GET {prefix}/cache/{class_id}.{vars_hash}.{script_type}` | `:133` | same | changed-compatible | Only CSS variables now; `js_data()` travels in the app JSON. The dead JS-variable paths were removed (`f817b31d`, `49a8d6c7`). |
| `GET {prefix}/asset/{file_name}` | `:141` | same | changed-compatible | Adds the CORS header. |
| `POST {prefix}/ext/events/call` | `P/ext/events/routes.py:233-239` | `:260-266` | unchanged | |
| `GET {prefix}/ext/events/runtime.js` | `:240` | serves `P/_vue/runtime.js` | changed-compatible | |
| `GET {prefix}/ext/events/runtime-csp.js` | `:92, 241-246` | absent | removed | One runtime serves every CSP mode. In CHANGELOG. |
| `{prefix}/ext/events/e/{class_id}/{event}` | `methods=("GET","POST")` | `methods=EVENT_ROUTE_METHODS` = `("GET","HEAD","POST","PUT","PATCH","DELETE","OPTIONS")` (checked by rendering) | changed-compatible | PUT/PATCH/DELETE handlers are reachable; the handler still answers 405 for methods it does not declare. In CHANGELOG Fixed. |
| `{prefix}/ext/events/e/{class_id}` (view events) | `P/ext/events/view_events.py:192` | `:193-199` | unchanged | |
| `GET {prefix}/ext/events/definitions/{digest}.js` | none | `P/ext/events/routes.py` | new | Compiled Vue definitions, stored through the configured cache (`01fe448a`). |
| `GET {prefix}/ext/events/assets/{digest}.css` | none | same | new | Same storage. |
| Definition and stylesheet storage across workers | 0.5.1 class scripts were rebuilt on a miss; variable scripts used `citry.cache` | `P/_vue/events.py` `_store_asset` / `_load_asset` | restored | Any worker that shares the cache backend serves the assets; bytes are checked against the digest. With each worker's own default cache another worker answers 404, which the CHANGELOG now states. |
| `GET {prefix}/ext/i18n/runtime.js` | `P/ext/i18n/routes.py:52` | serves the Vue i18n plugin | changed-compatible | Requires the Vue runtime. |
| `POST {prefix}/ext/i18n/messages` | `:53` | unchanged file | unchanged | |
| Preview routes | `P/ext/preview/routes.py:77-79` | unchanged file | unchanged | |

#### Wire protocol, request headers, and data embedded in the page

| Surface | 0.5.1 | 0.6.0 branch | Status | Notes / replacement |
|---|---|---|---|---|
| Protocol id `citry-events/1` | `packages/protocol/events/v1/spec.md` | same | unchanged | Stays at 1 (pre-1.0 rule). |
| Call `capabilities.swaps` / `actions` | `call.schema.json` | same | unchanged | |
| Call `capabilities.renderers` | none | `call.schema.json:49-67` | new | Omitted means `html-fragment/1`. |
| Result render action | `{action,target,swap,html}` | legacy, `html-fragment/1`, or `vue-prepared/1` | changed-compatible | Old clients get the legacy shape. `prepared` is typed only as `object`. |
| Render `target` values | any CSS selector | `render:<id>`, `mark:<name>`, or none; addressed targets need `swap="morph"` | changed-incompatible | In CHANGELOG. The spec still documents selectors and every swap (decision 6.9). |
| Manifest field `clientGraphRevision` | required | removed and rejected | removed | |
| Manifest in `<script data-citry-events>` | emitted | merged into the Vue app JSON | changed-incompatible | The spec, schema description, and protocol README now describe the app JSON (`115410c5`). Golden result fixtures still contain `data-citry-events` (decision 6.9). In CHANGELOG. |
| Reference package `citry_events` and JS types | `packages/protocol/events/v1/python`, `js` | adds renderer types | changed-compatible | `RenderAction` stays the union. |
| Client-graph protocol `citry-client-graph/1` | present | deleted | removed | Also `citry_core._rust.client_graph`. |
| `<script data-citry-graph>` and ownership comments | emitted | none | removed | |
| i18n manifest `<script data-citry-i18n>` | `P/ext/i18n/emission.py:90` | still for non-interactive renders; in the app JSON for Vue renders | changed-compatible | |
| `X-Citry-Events` request header | `P/ext/events/csrf.py` | unchanged | unchanged | |
| Cross-site checks | same | unchanged | unchanged | |
| Browser CSRF default (`csrftoken` / `X-CSRFToken`) | same | present | unchanged | Checked by string presence. |
| `X-Citry-Vue-App`, `-Occurrence`, `-Revision` headers | none | `P/_vue/events.py` | new | A custom transport must forward them. |
| `Accept: text/html` compatibility responses | same | always HTML-fragment encoded | changed-compatible | |
| `Access-Control-Allow-Origin: *` on asset responses | none | `P/_owned_resource.py` | new | In CHANGELOG. |

#### Framework integrations and route table

| Surface | 0.5.1 | 0.6.0 branch | Status | Notes / replacement |
|---|---|---|---|---|
| `citry.contrib.{asgi,wsgi,django,flask,fastapi,caches}` | `P/contrib/*.py` | same names; the `methods is not None` guards were removed again | unchanged | |
| `citry.URLRoute.methods` | `tuple[str, ...] = ("GET",)` | same (`04084529`) | restored | Tested by `test_events_route_methods.py`. |
| `citry.ext.events.routes` constants | `CSP_RUNTIME_PATH`, `EVENTS_CSP_RUNTIME_SRC` | removed; new constants added | changed-incompatible | Undocumented. |
| `get_event_url()`, `component.events.url()` | `P/ext/events/routes.py:115, 161` | same | unchanged | |
| `EventsDispatcher()` | no-arg | keyword-only encoder params | changed-compatible | |
| `RenderEncoder`, `RenderEncodingContext`, `HtmlFragmentRenderEncoder` | none | `P/ext/events/results.py` | new | |
| `emit_events_dependencies` | public name | removed | removed | Undocumented. |
| `citry.ext.events.bindings.CevAttr` | public name | removed | removed | Undocumented. |
| HTMX helper `citry-htmx.js`, `hx-ext="citry-fragments"` | v051 `guides/htmx` | not needed | removed | In CHANGELOG. |
| Fragments on a page that loaded `citry.js` | runtime adopted fragment manifests | one Vue app per fragment | changed-compatible | Same insertion contract. |

#### i18n: Python and templates

| Surface | 0.5.1 | 0.6.0 branch | Status | Notes / replacement |
|---|---|---|---|---|
| `citry.ext.i18n` exports | `P/ext/i18n/__init__.py`, `config.py`, `api.py` | unchanged files | unchanged | The emission, bindings, components, and extension modules changed; see the next rows and 3.2. |
| `Component.I18n`, `messages`, `messages_file` | `P/ext/i18n/extension.py` | same declarations | unchanged | |
| `self.i18n.tr/resolve/format/parse/context` | `P/ext/i18n/api.py` | unchanged | unchanged | |
| `citry i18n` commands | `P/ext/i18n/commands.py` | unchanged | unchanged | |
| `tr()`, `fmt`, `<c-trans>`, `<c-i18n>` | `P/ext/i18n/components.py` | same tags and inputs; the provider host template uses `$component` | changed-compatible | |
| `$c-tr:...`, `c-$c-tr`, `$c-tr` via `c-bind` | `P/_i18n_directives.py` | values are Vue expressions | changed-compatible | |

#### i18n: browser

| Surface | 0.5.1 | 0.6.0 branch | Status | Notes / replacement |
|---|---|---|---|---|
| `$i18n` in template expressions | Alpine magic | Vue global property | changed-compatible | Same ten members. |
| `$component(({ i18n }) => ...)` | v051 `reference/browser-apis` | restored context field (`c4ec2da0`) | restored | Also `component.$i18n` / `this.$i18n`. |
| `bind()` cleanup through `control.registerCleanup` | v051 `i18n/browser` | return a cleanup from the callback | changed-incompatible | |
| `Citry.i18n.provider` | `citry-i18n.js:2603` | removed | removed | Undocumented. |
| Alpine provide key `citry_i18n`, `x-citry-tr` | `citry-i18n.js:2621-2631` | removed | removed | Undocumented. |
| `$i18n` entry on `reference/browser-apis.md` | present | restored (RB `#i18n`, and the `i18n` context field row) | restored | Counted here as the docs entry; the API row is `$i18n` above. |

#### citry-ui (`citry-ui@0.2.2` to 0.3.0)

| Surface | 0.2.2 | 0.6.0 branch | Status | Notes / replacement |
|---|---|---|---|---|
| Component families and exports | 77 families, 727 names | identical | unchanged | |
| Python `Kwargs`, `Slots`, detail classes, `Literal` aliases (156 classes) | `U/components/*/*.py` | identical | unchanged | |
| Client inputs and callback props (`api.yml`) | same | identical names and types | unchanged | |
| How client inputs are passed | `$c-props="{ open }"` | `:open="open"` | changed-incompatible | Breaking entry in the citry-ui CHANGELOG. |
| `attrs` and part mappings | accepted Alpine attributes | reject `v-`, `:`, `.`, `^`, `@`, `#` names (`U/components/_attrs.py:77-107`) | changed-incompatible | Breaking entry. |
| `CMultiSelect` inline `on*` handlers | accepted | rejected | changed-incompatible | Breaking entry. |
| Bound content from a separate component in group components | rendered, bindings inert | raises | changed-incompatible | Breaking entry in both changelogs. |
| Documented JS methods | none | none | unchanged | |
| Dependency floor | `citry>=0.4.2` | `citry>=0.6.0` | changed-incompatible | In the citry-ui CHANGELOG. |

## 4. Restored items

| What | Where | Tests |
|---|---|---|
| Callback context fields `id`, `els`, `state`, `sendEvent`, `loading`, `error`, `i18n` on `$component(fn)` and `onServerRender`; `els` is one array for the component's lifetime, refilled on each server render and on each getter read (a destructured reference does not follow browser-only changes until the next refill) | `P/_vue/client.js` `runCallback`; `liveRootElements` moved to module scope (`c4ec2da0`, plus the in-place `els` update in the current working tree) | `packages/py/citry/tests/e2e/test_vue_component_context_e2e.py`: `test_initializer_context_exposes_the_instance_helpers_under_their_0_5_1_names`, `test_initializer_context_on_a_component_without_events_matches_0_5_1` |
| `$component({ init })` runs as `onServerRender`; `init` beside `onServerRender` throws | `P/_vue/client.js` `registerTypeOptions` | `test_init_option_runs_as_the_server_render_initializer`, `test_init_option_beside_on_server_render_is_rejected` |
| `citry:events:stale` with `reason: "version"`, cancelable, and the one-time reload prompt; the event starts at `document` when the calling component is gone | `citry-events-vue.ts` (`stale_state` branch, `promptReload` host hook); `P/_vue/client.js` `promptReload`, `dispatchLifecycleEvent` | `test_stale_state_after_a_deploy_asks_once_to_reload`, `test_cancelling_the_version_notification_suppresses_the_reload_prompt`; `packages/js/citry-client/test/vue-events.test.mjs` ("a stale_state answer reports a cancelable version notification before the error", "a cancelled version notification skips the reload prompt, and other errors never prompt") |
| `$sendEvent` on a component without Events rejects; `$loading` / `$error` there return `false` / `null` | `P/_vue/client.js` instance setup | `test_initializer_context_on_a_component_without_events_matches_0_5_1` |
| `URLRoute.methods` is always a tuple; the per-event route declares the standard methods | `P/util/routing.py`, `P/ext/events/routes.py` `EVENT_ROUTE_METHODS`, `P/contrib/{asgi,django,wsgi}.py` (`04084529`) | `packages/py/citry/tests/test_events_route_methods.py` (`test_every_route_declares_a_method_tuple`, `test_per_event_route_declares_the_standard_methods`, `test_per_event_put_and_delete_reach_the_handler`) |
| Vue definition bundles and stylesheets shared through the configured cache | `P/_vue/events.py` `_store_asset`, `_load_asset` (`01fe448a`); docs in `docs_site/content/web-frameworks.md`; CHANGELOG Breaking line on multi-worker caches | `packages/py/citry/tests/test_vue_asset_sharing.py` (seven tests: shared worker, restarted worker, evicted entry, separate default caches, unknown digest, tampered bytes, two engines on one cache) |
| Interactive components whose class name contains `_` | `P/_vue/events.py` tag name mapping (`96455b02`) | `packages/py/citry/tests/test_vue_events.py::test_interactive_component_class_name_with_underscore_renders` |
| Editor tooling and analyzer know the restored fields and `init` | `crates/citry_template_parser/src/browser.rs`, `P/analysis.py`, `packages/py/citry_lsp/citry_lsp/engine.py` (`cebde4fe`) | `packages/py/citry/tests/test_browser_analysis.py`, `packages/py/citry_lsp/tests/test_engine.py` |
| `$i18n` reference entry | `docs_site/content/reference/browser-apis.md` (`c4ec2da0`) | Docs guards |

Fixes for surfaces that failed silently (still removed, now loud):

| What | Where | Tests |
|---|---|---|
| `LintSettings` and `Component.Lint` with the old Alpine names raise an error that names the Vue setting | `P/settings.py` `_REPLACED_LINT_SETTINGS`, `LintSettings.__new__`; `P/_linting.py` (`a2d0f7c5`) | `packages/py/citry/tests/test_citry.py`, `test_component.py` |
| `#c-ignore` on a component tag raises when the template compiles | `P/nodes/__init__.py` (`d2b9540a`) | `packages/py/citry/tests/test_meta_attrs.py` and neighbors |
| `#c-ignore` on an element raises a `TypeError` that names the element and suggests a Vue `ref` | `P/_vue/capture.py` (current working tree) | `test_meta_attrs.py`, `test_vue_metadata_contracts.py` |
| `URLRoute(methods=...)` rejects a value that is not a non-empty tuple of uppercase method names when the route is built | `P/util/routing.py` `_validate_route_methods` (current working tree) | `test_contrib_request.py` |
| The `v-once` / `v-memo` hint on a component tag says to remove the directive | `parser.rs`, `P/client_directives.py` (`90d1b663`) | `crates/citry_template_parser/tests/tag_parser_client_directives.rs`, `test_vue_component_directives.py` |

## 5. Deliberate removals

Every removal below is listed in the CHANGELOG Unreleased section and in
`docs_site/content/guides/upgrading-to-0-6-0.md`, except where a row says
otherwise. The reason is one of two: the surface only made sense with
Alpine or the ownership graph, or Vue already provides the same thing.

| Removed | Reason | Replacement |
|---|---|---|
| Alpine `x-*` directives, Alpine magics, `alpine:init` events, `globalThis.Alpine` | Alpine is gone | Vue directives; `citry:ready` |
| `Citry.alpine.*` | Alpine-only | `Citry.vue.use(plugin)` for app-wide Vue plugins (decision 6.2) |
| `Citry.manager.*`, `Citry.manager.ownership.*` | Alpine dependency manager and ownership graph | Fragments load their own assets |
| `Citry.i18n.provider`, `citry_i18n` provide key, `x-citry-tr` | Alpine wiring | `component.$i18n`; not in CHANGELOG by design (undocumented) |
| Callback fields `data`, `scope`, `props`, `graph`, `effect`, `reactive`, `provide`, `inject`, `unprovide` | Vue replaces each concept | `component`, Vue Options, `Citry.vue.watchEffect`, `Citry.vue.reactive` |
| `$provide`, `$inject`, `$unprovide` in templates | Vue has provide/inject | Vue `provide` / `inject` Options |
| `$root` graph override | Alpine-only | Vue `$root` (different meaning) |
| `$c-props` in every spelling | Vue has props | `:prop`, `v-bind="obj"` |
| `x-on:` on a component tag | Alpine spelling | `@event`, `v-on:event` |
| `c-:attr`, `c-@event`, `c-x-*`, `c-bind` keys spelling Vue bindings | Vue templates are compiled on the server, so Python cannot write browser code | Write the binding in the template, pass values with `js_data()` or props |
| Forwarding Alpine attrs through `c-attrs` | Alpine-only | `inheritAttrs: false` + `v-bind="$attrs"` |
| Timed `@c-*` and `@c-poll` on component tags | No component-level timer in the Vue model | Put the binding on an element in the child (decision 6.7) |
| `#c-ignore` on component tags, and Vue-only content inside `#c-ignore` | A component or binding renders through Vue, which updates it | `#c-ignore` on the element inside the component's template (decision 6.4) |
| `data-cid`, `data-cev-*`, `data-citry-root`, `data-citry-graph`, `data-citry-key` markers | Alpine and ownership markers | Vue `ref`; `data-cid-*` still on static output (decision 6.3) |
| `citry.ownership`, `citry.ownership_manifest`, ownership params on `CitryContext` and `CitryElement` | Ownership graph removed | None needed |
| `citry.analysis` Alpine names | Alpine-only | `Vue*` equivalents |
| `LintSettings` / `Component.Lint` / `TemplateLintInfo` Alpine names | Alpine-only; an alias would carry Alpine magic names into Vue scope | `rule_unknown_vue_variable`, `vue_variables` |
| Diagnostic codes `citry.alpine.unknown-variable`, `citry.component-js.unknown-data-member`, `citry.browser.unknown-component-prop` | Alpine or `$c-props` concepts | `citry.vue.unknown-variable`, `citry.component-js.unknown-member` |
| `ext/events/runtime-csp.js` route and its constants | One runtime serves every CSP mode | `ext/events/runtime.js` or `citry.js` |
| `emit_events_dependencies`, `CevAttr`, `DATA_CEV_*`, `EventsExtension.on_dependencies` | Alpine Events runtime | `build_events_manifest`, `browser_plugin` |
| `clientGraphRevision`, `citry-client-graph/1` protocol, `citry_core._rust.client_graph` | Ownership graph removed | None needed |
| `citry-htmx.js` helper | Citry no longer writes comment markers | Delete it |
| `citry.component_render.CacheArtifactError` re-export | Incidental re-export | Import from `citry.ext.cache` |
| `citry:events:stale` reasons `cancelled` and `timeout` | A timed-out call is aborted, and `disposed` covers most cancellations | `disposed`; rejection of the call |
| `citry_core.html_transform.scan_alpine_html`, `analyze_component_members` | Alpine-only | In the citry-core CHANGELOG |
| `citry.TemplateNode` | The compiler never generated it, and no built-in code built one (decision 6.18) | Delete imports and `isinstance` checks; an extension that built one adds the markup to the template source in `on_template_loaded` |

## 6. Maintainer decisions

### 6.1 `wait: false` on `$sendEvent` and `Citry.events.send`

- **Question:** 0.5.1 documented `opts.wait: false` to send a call outside
  the queue (for example live search). The branch copies only `timeout`
  (`P/_vue/client.js` `eventSend`, the `{timeout: opts.timeout}` lines) and
  sends every call from an app one at a time. The option is ignored with no
  error.
- **Options:** (a) reject unknown `opts` keys, including `wait`, with an
  error saying calls are sent one at a time; (b) restore it with a second
  bridge path that skips the queue, relying on the existing `epoch` guard
  for out-of-order responses; (c) leave it ignored and document that.
- **Recommendation:** (a) now, (b) later if users ask. A silently ignored
  documented option is the worst of the three.
- **Evidence:** `P/_vue/client.js` `eventSend` (`{timeout: opts.timeout}`);
  0.5.1 option in `docs_site/versions/0.5.1/reference/browser-apis/`. Not in
  the CHANGELOG or upgrade guide.
- **Status:** decided: support it if safe, else reject. Rejected: two calls
  in flight would drop each other's renders, because a render applies only
  on the app revision the call was sent from, and each call carries the
  State token the previous one returned. `wait: false` and unknown option
  keys reject with a `TypeError`; the error points at
  `@event(latest_wins=True)` (`ddd553e6`). Proper support is tracked in
  [#155](https://github.com/citry-dev/citry/issues/155).

### 6.2 A public way to install a Vue plugin on Citry's apps

- **Question:** 0.5.1 had `Citry.alpine.beforeStart(fn)`. The branch
  creates each Vue app internally; the only plugin mechanism is
  `Extension.browser_plugin`, which relies on the private `__citryRuntime`
  global and is undocumented.
- **Options:** (a) a public `Citry.vue.onAppCreate((app) => app.use(plugin))`
  accepted only before the first app mounts; (b) document
  `Extension.browser_plugin` / `prepare_browser_render` in
  `advanced/extensions.md`; (c) both.
- **Recommendation:** (a) for page authors, then (b) for extension authors.
  Pinia, UI kits, and global directives have no path today.
- **Evidence:** 0.5.1 hook at M51:617-624; branch `P/_vue/client.js`
  `registerBrowserPlugin` on `__citryRuntime`; `P/extension.py:950-954`.
- **Status:** option (a) as `Citry.vue.use(plugin, ...options)`, applied to
  every app Citry creates; a call after the first app starts throws
  (`ddd553e6`, `457c060f`, editor types `4544c1e0`). Documented in
  `reference/browser-apis.md`.

### 6.3 `data-cid-*` markers on interactive components

- **Question:** static output keeps `data-cid-<id>`; components that Vue
  renders carry none (checked by rendering). 0.5.1 told django-components
  users to switch selectors to `data-cid-*`.
- **Options:** (a) add the attribute in the compiled Vue render output
  (a compiler output change); (b) keep it static-only and say so.
- **Recommendation:** (b). This is now documented: the CHANGELOG Breaking
  Events list says elements that Vue renders carry no `data-cid-*`
  attributes, the upgrade guide says the same, and the django-components
  guide row DJC-052 limits the marker to output without browser behavior.
  Only the decision itself remains to confirm.
- **Evidence:** `CHANGELOG.md` Unreleased; `docs_site/content/guides/upgrading-to-0-6-0.md`;
  `docs_site/content/guides/migrate-from-django-components.md` row `#djc-052`.
- **Status:** option (b) accepted; covered by the upgrade guide.

### 6.4 Element-level `#c-ignore`

- **Question:** `#c-ignore` on an element raises the first time the
  component renders, including on static pages that never become Vue
  apps. The message now names the element and points at a Vue `ref`, and
  the CHANGELOG and the upgrade guide ("Remove `#c-ignore`") cover it.
  Open: whether 0.6.0 needs a real replacement for keeping a third-party
  widget subtree (chart, map) out of updates.
- **Options:** (a) keep the rejection and the `ref` pattern (mount the
  widget into an empty element in `mounted()`); (b) on static pages keep
  the 0.5.1 output and reject only in interactive renders; (c) build a
  lifecycle step that keeps a server-rendered subtree untouched.
- **Recommendation:** (a) for 0.6.0, with (c) as a tracked follow-up. (b)
  would make the same template valid or invalid depending on whether the
  page happens to be interactive.
- **Evidence:** `P/_vue/capture.py` (element error); `P/nodes/__init__.py`
  (component-tag error); `docs/design/vue_migration.md` notes that the
  subtree primitive is deferred.
- **Status:** option (c). On an element in an interactive component the
  server sends the contents as an HTML block that the browser keeps
  unchanged for the component's life; static pages render them as
  written; Vue-only content inside fails when the template loads; the
  component-tag error stays and names the fix (`763a578e`, `40de8c59`,
  `33d5a762`, `deb56390`, `50f14b1f`, `0751132d`, `6a78eec3`).

### 6.5 A diagnostic for leftover `x-*` attributes

- **Question:** every `x-*` attribute renders as inert HTML with no error.
  An `x-cloak` plus an app rule `[x-cloak]{display:none}` hides content
  permanently.
- **Options:** (a) a parse or `citry check` error for known Alpine
  directives on HTML elements, with an escape hatch for third-party
  libraries that read `x-*`; (b) a warning only; (c) rely on the upgrade
  guide.
- **Recommendation:** (a) or (b). The upgrade guide has a "Find the `x-*`
  attributes you missed" section, but a check catches what people miss.
- **Evidence:** no `x-` check in `P/_linting.py`, `P/analysis.py`, or
  `packages/py/citry_lsp/`; inert output checked by rendering.
- **Status:** a warning for `x-*` (`citry.template.alpine-attribute`) and
  an error for `x-cloak` (`citry.template.alpine-cloak`), with
  `rule_alpine_attribute="ignore"` as the escape hatch (`1cced7eb`,
  `16553057`, `ad2b0b78`).

### 6.6 Alpine-only event modifiers

- **Question:** `.outside`, `.window`, `.document`, `.debounce`, and
  `.throttle` on a plain `@event` compile into a key filter, so the
  listener never runs, and nothing reports it. The CHANGELOG says they
  "have no effect".
- **Options:** (a) a compile error that lists the modifiers Vue accepts;
  (b) a warning; (c) leave as is.
- **Recommendation:** (a). A listener that never fires is hard to debug,
  and these modifiers are almost always migration leftovers. If (a) lands,
  reword the CHANGELOG line, which today understates the effect.
- **Evidence:** checked by rendering (temporary audit notes, not kept);
  CHANGELOG "have no effect" line.
- **Status:** option (a): a compile error naming the Vue alternative, and
  the CHANGELOG line reworded (`763a578e`).

### 6.7 Timed `@c-*` and `@c-poll` on component tags

- **Question:** these worked in 0.5.1 and now raise. The errors are clear.
- **Options:** (a) keep the rejection; (b) support them by attaching the
  timer to the child occurrence.
- **Recommendation:** (a) for 0.6.0; it is in the CHANGELOG and the guide.
  Revisit if users report it.
- **Evidence:** `P/_vue/direct_capture.py:1625, 1650`.
- **Status:** option (a); the Python and browser messages now show the
  element form to move into the child (`c6230150`, `ddd553e6`).

### 6.8 `OnDependenciesContext.before_manifest` (now `early_scripts`)

- **Question:** an extension that adds tags to `before_manifest` now fails
  on interactive pages (`P/_vue/events.py:631-635`).
- **Options:** (a) keep the rejection (in CHANGELOG, "add them to
  `ctx.scripts`"); (b) treat `before_manifest` entries as leading
  `scripts` in prepared Vue serialization, which keeps old extensions
  working.
- **Recommendation:** (b) is one place to change and removes a break with
  no Vue reason; (a) is acceptable because the CHANGELOG names the fix.
- **Evidence:** `P/_vue/events.py:631-635`; `P/ext/dependencies/emission.py:97-101`.
- **Status:** option (b): entries become the leading prepared scripts
  (`22b90c45`). The field was later renamed from `before_manifest` to
  `early_scripts`, because "manifest" named the Alpine-era ownership JSON
  that 0.6.0 removes; the CHANGELOG and upgrade guide tell extension
  authors to rename it. A hook that still reads the old name raises
  `AttributeError` naming `early_scripts` (`_REPLACED_DEPENDENCY_FIELDS`
  in `P/ext/dependencies/emission.py`).

### 6.9 The Events protocol contract

- **Question:** `packages/protocol/events/v1/spec.md` still defines CSS
  selectors as targets ("a non-empty CSS selector, applied with
  `querySelectorAll`") and every non-`morph` swap, while the branch server
  and client reject them. Golden result fixtures
  (`tests/happy_render.result.json`, `baseline_swap.result.json`,
  `batch_two.result.json`) still contain `data-citry-events`.
- **Options:** (a) update the v1 spec, schemas, and fixtures in place to
  the branch contract (allowed by the pre-1.0 rule); (b) keep them as the
  protocol's general contract and document Citry's browser as a client
  that supports a subset.
- **Recommendation:** (a), so the reference validator and the product agree.
- **Evidence:** `packages/protocol/events/v1/spec.md:495-505`;
  `P/ext/events/actions.py:176-208`.
- **Status:** option (a). The spec, schema, both validators, and the
  fixtures define `render:<id>` and `mark:<callerRenderId>:<name>`, and a
  `vue-prepared/1` render requires `morph`; protocol version 1 is kept
  (`a77f0346`, `b7c6fab1`, browser fallback check `91ff8480`).

### 6.10 The reserved component name `mark`

- **Question:** a class named `Mark` fails at definition.
- **Options:** (a) keep the reservation (in CHANGELOG); (b) let a user
  registration shadow the built-in.
- **Recommendation:** (a). The error is clear and the rename is trivial;
  shadowing would make `<c-mark>` mean different things in different apps.
- **Evidence:** `P/component_registry.py:29, 159`.
- **Status:** option (a); documented in the builtins reference and the
  upgrade guide (`7c919585`).

### 6.11 citry-lsp version and upper bound

- **Question:** the branch requires `citry>=0.6.0` but keeps
  `version = "0.1.7"`, the number already on PyPI. citry-lsp imports private
  `citry._*` modules.
- **Options:** version 0.2.0 or 0.1.8; with or without an upper bound such
  as `citry>=0.6.0,<0.7.0`.
- **Recommendation:** 0.2.0 with `<0.7.0`, since the worker protocol and
  private imports tie it to a citry minor version.
- **Evidence:** `packages/py/citry_lsp/pyproject.toml:10, 33`.
- **Status:** version 0.2.0 with `citry>=0.6.0` and no upper bound; the VS
  Code extension accepts the 0.2 line (`e6c8abe3`, `3eeb3f8e`).

### 6.12 `@event(methods=...)` and the per-event route

- **Question:** `@event(methods=...)` accepts any token, but the per-event
  route admits only `EVENT_ROUTE_METHODS`. A handler declared with a
  non-standard method is registered but never reachable.
- **Options:** (a) validate `methods` against the standard tuple at
  declaration; (b) widen the route.
- **Recommendation:** (a), so the error appears when the class is defined.
- **Evidence:** `P/ext/events/handlers.py:120` `validate_methods_value`;
  `P/ext/events/routes.py` `EVENT_ROUTE_METHODS`.
- **Status:** option (a) (`3a4e876f`, `ebf1ce31`).

### 6.13 `<c-raw>` and `Markup` inside interactive components

- **Question:** both must be strict, self-contained HTML fragments inside
  an interactive component; static pages accept anything.
- **Options:** (a) keep the rule and document it on the syntax pages;
  (b) accept loose fragments by wrapping them in an element Vue leaves
  alone.
- **Recommendation:** (a); it is in the CHANGELOG. Add a sentence to
  `docs_site/content/syntax/comments.md` and the expressions page if not
  there.
- **Evidence:** `crates/citry_html_transform/src/output_scanner.rs:515`;
  the correction in 3.4.
- **Status:** option (a); the error names the input and the rule, and the
  syntax pages document it (`c6230150`, `1e761d20`, `7c919585`).

### 6.14 `v-once` on an element

- **Question:** `v-once` on an element fails with "unsupported raw-text or
  cached construct", which does not name the directive.
- **Options:** (a) a parse-time error naming `v-once` / `v-memo`, like the
  component-tag hint; (b) support it.
- **Recommendation:** (a), reusing `_ONCE_MEMO_HINT`.
- **Evidence:** `P/_vue/compiler.py:444`; `P/client_directives.py`
  `_ONCE_MEMO_HINT`.
- **Status:** option (a); the error names the directive and points at
  `#c-ignore` (`c6230150`).

### 6.15 Default in-memory cache growth

- **Question:** the default in-memory cache now stores every Vue
  definition bundle and stylesheet with no TTL, so a long-running process
  with many distinct components keeps all of them.
- **Options:** (a) accept (the set is bounded by the app's components and
  their versions); (b) give the default cache a size limit; (c) store Vue
  assets in a separate bounded store and use the shared cache only when one
  is configured.
- **Recommendation:** (a), with a sentence in
  `docs_site/content/advanced/cache-backends.md`. A size limit can evict an
  asset an open page still needs, which is what the fix avoided.
- **Evidence:** `P/_vue/events.py` `_store_asset` ("No TTL").
- **Status:** option (c). Without a configured cache, Vue assets live in a
  per-process store bounded by `vue_asset_max_bytes` (64 MiB); with a
  cache, each process asks the cache about each asset at most once a
  minute
  (`6e3872e5`). The same growth in the dependencies extension is
  [#154](https://github.com/citry-dev/citry/issues/154).

### 6.16 Example projects pin `citry>=0.5.0`

- **Question:** every starter and demo under `examples/` declares
  `citry>=0.5.0` (for example `examples/starters/fastapi/pyproject.toml`)
  but uses Vue syntax.
- **Recommendation:** raise the floor to `citry>=0.6.0` after 0.6.0 is on
  PyPI, in the post-release batch, since a lockfile cannot resolve it
  before then.
- **Status:** raised to `citry>=0.6.0` and `citry-lsp>=0.2,<0.3` now; the
  locks are refreshed after publication, a step added to the release
  checklist (`e076be6e`).

### 6.17 README demo links

- **Question:** `README.md:177-181` links to `tree/citry%400.6.0/...`,
  which 404s until the tag exists.
- **Recommendation:** keep them; they are correct from the moment the
  release is tagged. Check them in the post-release verification.
- **Status:** kept; the release checklist now opens them after tagging
  (`e076be6e`).

### 6.18 The `TemplateNode` node class

- **Question:** `citry.TemplateNode` rendered a nested template string as
  body content. The template compiler never generates it: a template-valued
  `c-*` attribute compiles to `TemplateHtmlAttr`, inside an
  `ElementAttrsNode` on an HTML element or in a `ComponentNode`'s
  attributes. Its docstring said an extension could build one in
  `on_template_compiled`, but no built-in code did. On this branch the
  `simple=True` check still read `_generator`, a single cached value that
  both nested template classes had replaced with one cache per render
  mode.
- **Recommendation:** remove it before 0.6.0 rather than keep an untested
  public class.
- **Status:** removed, with a CHANGELOG line and an upgrade guide line that
  point an extension at `on_template_loaded`. The `simple=True` check that
  read the missing attribute also broke `TemplateHtmlAttr`; that is fixed
  in the same change. The regression never shipped (0.5.1 is not
  affected), so the CHANGELOG has no fix entry.

## 7. CHANGELOG reconciliation

Each "Not in CHANGELOG" item from the five audits was checked against the
root `CHANGELOG.md` Unreleased section and the upgrade guide on the
`vue-pr-api` branch after the restoration commits.

Covered now:

- Lint setting renames on `LintSettings`, `Component.Lint`,
  `TemplateLintInfo`, with an example.
- The reserved `mark` name.
- `citry.analysis` Alpine names; the ownership modules and parameters.
- `OnSerializeContext` and `OnDependenciesContext` gaining
  `selected_render`.
- `x-*` removal (the guide explains finding leftovers).
- The `runtime-csp.js` route and `security_csp="strict"` meaning.
- Removed diagnostic codes and their replacements.
- citry-lsp 0.1.7 and citry-ui 0.2.x needing an upgrade together.
- `$component({ init })` and the callback fields (now "still work").
- `citry:events:stale` reasons, including `version`, and the removed
  `cancelled` / `timeout`.
- `Citry.manager`, `Citry.alpine`, `Citry.i18n`, `window.Alpine`.
- Nested `$state` writes throwing; `$onEvent` and `onEvent` hearing only
  server events; `Citry.events.send` before `citry:ready` rejecting.
- `data-cid-*` absent on elements that Vue renders.
- The `registerTransport` signature, under Breaking.
- `applyActions` selector and swap rejection.
- `$c-props`, `x-on:` on component tags, Vue bindings on component tags
  replacing kwargs, `@event` on component tags following Vue.
- `c-:attr`, `c-@event`, and `c-bind` keys spelling Vue bindings.
- Timed `@c-*` and `@c-poll` on component tags.
- `#c-ignore` on elements and component tags raising (CHANGELOG and
  upgrade guide).
- `data-citry-key` no longer written.
- `<c-raw>` / `Markup` strict fragments, one `<body>`, `v-once`.
- Alpine-only modifiers, now a load-time error.
- `data-citry-events` script tags no longer emitted.
- The HTMX helper no longer needed.
- A shared cache required for several workers (CHANGELOG and upgrade
  guide).
- The per-event route admitting PUT/PATCH/DELETE (Fixed).
- `applyActions` rejecting unknown fields and lists with gaps.
- `URLRoute(methods=...)` validation when the route is built.
- `$onEvent` on a component without Events needs no entry: it returns an
  unsubscribe function that does nothing, as in 0.5.1 (restored).

Added after the maintainer's decisions: `wait: false` rejection,
`Citry.vue.use`, async initializers, `#c-ignore` keeping its contents,
the `x-*` lint rules, Alpine-only modifier errors, `@event` method checks,
`vue_asset_max_bytes`, citry-lsp 0.2.0, and the `TemplateNode` removal.
The CHANGELOG lists the `early_scripts` rename, the one change to that
field since 0.5.1.

Still missing from the root CHANGELOG:

- Security and hook settings that turn off hydration
  (`security_csp` other than `"off"`, `security_javascript` other than
  `"allow"`, `security_script_integrity="citry"`, custom
  `on_dependencies` / `on_serialize` / `on_js_loaded`). Documented in
  `advanced/vue-runtime.md`; the upgrade guide links it once.
- `OnRenderCacheStageContext` gaining `parent_ids` and
  `provided_render_ids`.
- The new `Extension.browser_plugin` / `prepare_browser_render` hooks and
  `citry.browser_render` module (pending decision 6.2 on documenting them).
- The Events protocol additions (`renderers` capability, `vue-prepared/1`
  render actions) and `clientGraphRevision` removal. These are protocol
  details a user of the Python package does not act on; leaving them out
  may be right.
- `ext/i18n/runtime.js` now serving a Vue plugin, and `/cache/...` routes
  no longer carrying `js_data()` scripts. Internal to the page; likely
  fine to leave out.
- New undocumented globals (`Citry.fragments`, `window.Vue`,
  `window.CitryVueEvents`, `window.CitryVueFragments`,
  `window.__citryRuntime`) and the `citry:rendered` event. These should be
  documented or made private rather than listed.

The auxiliary changelogs cover their packages: citry-ui lists the
`$c-props` switch and the `attrs` / `CMultiSelect` / group-content
rejections as Breaking; citry-core lists `scan_alpine_html` and
`analyze_component_members` removal and the new helpers; citry-lsp states
the citry 0.6.0 requirement and the restored fields. The VS Code extension
has no entry.

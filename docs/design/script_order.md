# Component script order

Status: proposal for review (issue
[#145](https://github.com/citry-dev/citry/issues/145)). Nothing here is
built yet. The recommendation targets 0.9.0, which the maintainer plans
as the last release with breaking changes before 1.0.

## What this decides

A Citry component can ship JavaScript: its own `js`, the files listed in
its nested `Dependencies` class, and the `onServerRender` callback it
registers through `$component({...})`. When a page holds several such
components, the browser has to run their code in some order. This document
decides which parts of that order Citry promises for 1.0, which parts it
leaves open, and what happens when one script fails.

The question matters now because the two directions are not symmetric.
Dropping an ordering promise after 1.0 breaks pages that rely on it,
whether the docs stated the promise or not. Adding a way to run some
scripts out of order is gentler, but not free either (see Option 2).

Downloading scripts in parallel while still running them in order is a
separate question, and it is already solved by
[#137](https://github.com/citry-dev/citry/issues/137) (see "What Citry
does today").

## The problem in one example

One component sets a global, and a second component reads it when its
script first runs:

```citry
class Theme(Component):
    js = """
    window.appTheme = { accent: "teal" };
    """

class Badge(Component):
    js = """
    const accent = window.appTheme.accent;
    $component({
      onServerRender({ component }) {
        component.$el.style.color = accent;
      },
    });
    """
```

```citry-html
<c-theme />
<c-badge />
```

Today this works: `Theme`'s script runs before `Badge`'s because `Theme`
renders first, and Citry runs component scripts in that order. If Citry
let each script run as soon as it arrived, `Badge` could run first and
fail with a `TypeError` because `window.appTheme` is still undefined. It
would fail on some page loads and not others, depending on network
timing.

The example is fragile on purpose. A `Dependencies` file, or an import in
a future ES-module model, is the better way to share `appTheme`. But users
write code like this, and whatever Citry promises decides whether it keeps
working.

## Four layers of "order"

"Script order" mixes four things that happen at different times. The rest
of the document keeps them apart.

1. **Script evaluation.** The browser runs a script file. For a
   component's `js`, this is also when `$component({...})` registers the
   component's Vue options with Citry. Code outside `$component()` runs
   once per page, not once per copy of the component
   (`docs_site/content/vue/component-options.md:244-247`).
2. **Vue hooks.** `setup()`, `created`, `mounted` and the rest run once
   per component instance, in the order Vue gives them.
3. **`onServerRender` callbacks.** Citry calls this per instance after the
   instance first mounts and again after each server render that updates
   it.
4. **Async work the user starts.** A callback that returns a Promise keeps
   running after Citry moves on.

## What Citry does today

Line numbers are on `main` at `c6bf31ead`. In this section `client.js`
means `packages/py/citry/citry/_vue/client.js`, and test paths are under
`packages/py/citry/tests/`.

Two words used below:

- A **standalone page** is HTML Citry writes when no web integration
  serves Citry's files (`citry.mounted_prefix` is not set), so every
  script is written inline in the page. The browser's parser runs them in
  tag order.
- On a **mounted page**, a web integration (for example the FastAPI one)
  serves Citry's files, and Citry's browser code adds each script itself
  as a `<script src>` element, one after another
  (`_vue/serialization.py:1215`, `:1265`). A full HTML document served by
  such an app is a mounted page.
- A **fragment** is HTML that a page inserts after it has loaded, which
  starts its own small Vue app.

Labels in the "Status" column:

- **Promised**: a public docs page states it.
- **Tested**: a test checks it.
- **Built, untested**: the code does it, nothing checks it.
- **Open**: no rule exists. The result depends on timing or on code that
  was not written to decide it.

### Script evaluation

| Behavior | Evidence | Status |
|---|---|---|
| The server writes the page's scripts in this order: scripts with `kind="core"` (Citry's runtime and extension early scripts), then `kind="extra"` (by default, `Dependencies` files), then `kind="component"` and `kind="variables"` (component `js` and the
browser variables from `js_data()`). Inside each group, components appear in the order Citry first meets them while rendering, parent before children. | `_bucket` (`ext/dependencies/emission.py:1045-1053`), `_resolve_records` docstring (`emission.py:512-516`); records collected in `ext/dependencies/extension.py:204-257`, whose comment says the order "approximates document order"; tests `test_deps_emission.py::test_nested_url_dependencies_emit_once_in_first_seen_order`, `e2e/test_document_e2e.py::test_component_and_dependency_assets_execute_in_bucket_order` | `Dependencies` before component `js` is promised (`docs_site/content/advanced/dependency-files.md:9-13`). `ctx.scripts` "in the order they run" and early scripts first are promised (`advanced/extensions.md:264`, `:291-297`). Tested |
| Files listed in one `Dependencies` class load in the order listed. | `docs_site/content/advanced/dependency-files.md:37` | Promised. But Citry keeps only the first copy of a file several components list (`emission.py:707`), which can break the listed order across components (see below) |
| An extension's or component's `on_dependencies` hook can reorder or add scripts after Citry builds the list. | `emission.py:287`, `:672`; `_vue/events.py:1028` | Promised as a feature (`advanced/extensions.md:264-296`) |
| On a mounted page, scripts run one at a time. Citry adds the next `<script src>` only after the previous one fired `onload`. | `loadTypeScript` (`client.js:3049-3084`), loop in `primeInitialAssets` (`client.js:3171-3174`); test `e2e/test_vue_dynamic_element_e2e.py::test_initial_script_preloads_overlap_fetch_but_keep_serial_execution` | Tested |
| On a standalone page, the scripts are tags in the page and the browser runs them in order. Citry checks afterwards that each component registered its options. | `_vue/serialization.py:1298-1324`, `client.js:3152-3161` | Tested (the bucket-order test above runs on this path) |
| On a mounted page, downloads overlap: Citry adds `<link rel="preload">` before the serial loop for each script whose only attributes are `integrity`, `crossorigin`, `referrerpolicy` or `fetchpriority`. Other scripts are fetched only when their turn comes. | `createAssetPreloadBatch` (`client.js:2658-2728`, filter at `:2697`); server-side hints `_vue/serialization.py:173-215`; tests above and `::test_initial_script_with_custom_attribute_falls_back_to_serial_element` | Tested |
| A component's script runs at most once per page. An extension's script runs once per Vue app, so a page plus a fragment runs it twice. A script whose component failed to register can run again when the app restarts. | `scriptRecordKey` (`client.js:2891-2893`), key removed at `client.js:3072`; tests `e2e/test_fragment_e2e.py::test_fragment_reuses_a_component_script_the_page_already_loaded`, `test_external_prepared_asset_integrity_is_optional_and_identity_is_app_scoped` | Once per page is promised (`vue/component-options.md:246`, `advanced/js-and-css-dependencies.md:11`). Tested |
| All component scripts of the first render run before Vue creates the app. | `client.js:3256-3265` | Promised (`reference/browser-apis.md:634-637`) |
| On the Vue path, page scripts must be plain scripts that run in order. `async`, `defer`, `nomodule` and `type="module"` are rejected. | `_serialization_security.py:567-580`, `normalizeAssetSource` (`client.js:2828-2844`); test `test_browser_render.py::test_prepared_browser_scripts_require_synchronous_classic_execution` | Promised (`advanced/extensions.md:291-297`). Tested |
| Browser plugin registration scripts run before component scripts on a mounted page, but after them on a standalone page. | `_vue/serialization.py:1324` appends them after the manifest scripts | Built, untested |
| On a page without the Vue runtime (`deps_strategy="simple"`), Citry writes plain `<script>` tags in the same order, and the browser's own rules apply, including any `async` or `defer` the user adds. | `emission.py:294-317` | Tested for the written order |

The order is "the order Citry first meets each component while
rendering", not "HTML order". The two usually agree, with these
exceptions:

- All `extra` scripts run before all `component` scripts, so a
  `Dependencies` file of a component lower on the page runs before the
  `js` of a component higher on the page.
- When two components list the same file, only the first copy counts.
  If component `X` lists `[a.js]` and renders first, and component `A`
  lists `[b.js, a.js]`, then `a.js` runs before `b.js`, against `A`'s
  listed order.
- A component inside a slot fill is met when the receiving component
  renders that slot, after the receiver itself. This follows from the
  code; no test checks it. Nested `render()` calls, replays from the
  render cache and other render paths are not tested either.

### `onServerRender` and Vue hooks

| Behavior | Evidence | Status |
|---|---|---|
| Vue hooks follow Vue: `setup` and `created` run parent first, `mounted` runs child first. Citry wraps these hooks but does not reorder them. | `typeOptions` (`client.js:2287-2591`) | Open (Vue's behavior, no Citry test) |
| The first `onServerRender` runs after `mounted`, in the order the `mounted` hooks ran: children before their parent, and siblings in Vue's order. Every `mounted` hook of that render pass runs before the first callback, because each callback is queued as a Promise task and the built-in `onOccurrenceMounted` is synchronous. | `options.mounted` (`client.js:2534-2556`), `onOccurrenceMounted` (`client.js:4335-4342`) | "Children before their parent" is promised (`guides/upgrading-to-0-6-0.md:241-243`). One test checks it for one parent and one child on a hydrated page (`e2e/test_vue_events_default_e2e.py::test_static_physical_document_shell_hydrates_with_csr_parity` asserts `["leaf", "page"]`). Sibling order is not promised or tested |
| After a server render, callbacks run in this order: (1) every component the response lists as updated, which includes new ones, in response order; (2) remounted components; (3) kept components that mount for the first time, for example when a `v-if` turns on, parent first; (4) components that a browser plugin's update names. Citry awaits each callback's synchronous part before the next. | `applyEnvelope` (`client.js:5441-5465`); new components must be in `updatedIds` (`client.js:5032-5034`); first mounts (`client.js:5414-5415`) | Open. Not documented, not tested, and not the first-mount rule |
| A callback that returns a Promise is not awaited. A rejection is logged and the page keeps going. | `runCallback` (`client.js:4826-4840`); test `e2e/test_vue_component_context_e2e.py::test_async_initializer_runs_beside_the_page_and_its_cleanup_still_runs` | Promised (`reference/browser-apis.md:128-133`). Tested |

### Fragments and server renders

- On a server render, Citry loads new compiled templates first, then new
  component scripts one at a time, then new stylesheets in parallel
  (`client.js:3943-3959`). The first load of a mounted page runs
  stylesheets, then scripts, then compiled templates
  (`client.js:3165-3174`, `3262-3265`). A standalone page writes the
  compiled templates as inline scripts before the component scripts
  (`_vue/serialization.py:1299-1304`). A script that reads computed
  styles while it runs sees these differences. None is documented.
- Separate fragments start on their own
  (`packages/js/citry-client/src/citry-fragments.ts:47-110`). They have no
  order relative to each other, to the page's own startup, or to its
  server renders. They share the per-URL cache, so a component script
  still runs once. Open.

### Failures

| Behavior | Evidence | Status |
|---|---|---|
| A script that fails to load stops startup (or the server render) before later scripts are added, on a mounted page. This includes a third-party or extension script, such as an analytics file an ad blocker refuses. | `loadTypeScript` `onerror` (`client.js:3076-3079`); test `e2e/test_vue_dynamic_element_e2e.py::test_extension_script_loader_retries_and_restarts_same_app_id` | Tested |
| A script that never finishes loading leaves the app waiting. There is no timeout. | `loadTypeScript` | Built, untested |
| A component script that loads but never calls `$component({...})`: on a mounted page, startup stops and later scripts are not added. On a standalone page, every tag has already run, and startup then stops with "initial Citry Vue type Options were not emitted before bootstrap". | `client.js:3071-3074`, `3153-3155`; test `e2e/test_vue_dynamic_element_e2e.py::test_initial_preloaded_later_script_does_not_execute_after_first_registration_failure` | Tested (mounted path) |
| A script that throws while it runs still fires `onload`. If it threw after registering its options, or it registers nothing (a `Dependencies` file), the next script runs as if nothing happened. On a standalone page, each tag runs on its own, so the same holds. | `client.js:3071-3075`: the `onload` handler checks only the registration | Built, untested |
| A synchronous `onServerRender` that throws stops the app. On the first mount, the other queued callbacks still run, because each is its own task. After a server render, the loop stops at the throw. | `client.js:2547-2550`, `5462-5474` | Built, untested |

### Ways one script can depend on another today

- `Dependencies` files, which run before every component's `js`.
- An extension's `ctx.early_scripts`, which run before those.
- `provide` / `inject` between Vue components.
- The `citry:ready` event and `whenReady`, which wait once, at startup,
  for the first-mount callbacks (`client.js:4641`, `4857-4867`).
- A global set by a script that renders earlier, relying on the order
  above.

There is no way to declare "this script needs that one" and no ES-module
output. The ES-module design ([`esm.md`](esm.md),
[#35](https://github.com/citry-dev/citry/issues/35)) is parked research.

## How other frameworks handle it

- **The browser itself.** Classic scripts the parser finds run in document
  order. A script with a `src` added by code is async by default, unless
  the code sets `script.async = false`, which runs such scripts in
  insertion order. `type="module"` scripts run after parsing, in document
  order. `async` scripts and `import()` give no order (WHATWG HTML,
  "Scripting").
- **htmx and Turbo** recreate each `<script>` in swapped content with
  `async = false`, so swapped scripts run in the order they appear (htmx
  2.0.4 `duplicateScript`; Turbo 8.0.12 `activateScriptElement`). Both
  chose ordered execution for content inserted after load, which is
  Citry's case for server renders and fragments.
- **Livewire** runs a component's `@script` once per instance, before
  Alpine initializes that component, and loads `@assets` once per page
  before those scripts
  ([Livewire JavaScript docs](https://livewire.laravel.com/docs/javascript)).
- **Astro islands** hydrate independently, so sibling islands have no
  order. A nested island waits for its nearest server-rendered parent
  island, so a parent always hydrates first
  ([`astro-island.ts` at astro@5.0.0](https://github.com/withastro/astro/blob/astro@5.0.0/packages/astro/src/runtime/server/astro-island.ts)).
  Astro also saw Lit components break when they started before
  hydration finished
  ([withastro/astro#10633](https://github.com/withastro/astro/issues/10633)).
- **Vue and Nuxt** hydrate depth-first: `setup` parent first, `mounted`
  child first. Lazy hydration (Vue 3.5 `hydrateOnVisible`, Nuxt delayed
  hydration) gives up sibling order, as an opt-in per component.
- **Stimulus and Phoenix LiveView** promise order only inside one
  controller or hook, nothing across them
  ([Stimulus lifecycle](https://stimulus.hotwired.dev/reference/lifecycle-callbacks),
  [LiveView JS interop](https://hexdocs.pm/phoenix_live_view/js-interop.html)).
- **Web components** upgrade in tree order once defined; code that needs
  another element waits on `customElements.whenDefined()`.

The pattern: frameworks that run scripts arriving with server HTML keep
them in order (htmx, Turbo, Livewire). Frameworks that run components out
of order make it an opt-in per component (Vue, Nuxt) or build a readiness
signal for the parent-child case (Astro, web components).

## Options

### Option 1: document today's order

Keep today's behavior. Publish the order rules from "What Citry does
today" as the 1.0 contract, decide the rows marked open, and add the
missing tests.

- Breaking impact: none for pages that work today.
- Cost: scripts keep running one at a time. What that costs is not
  measured (see "What would show this wrong").

### Option 2: add an opt-in for unordered scripts

Option 1, plus a way to mark a script as independent so it runs as soon
as it arrives. One shape: component `js` and `Dependencies` entries accept
an `order="any"` flag, and Citry starts the Vue app only once every
script, ordered or not, has run.

- Breaking impact: none on the day it ships. But when a library marks its
  own script as unordered in a minor release, apps that read the
  library's globals from their own scripts can break. The flag should
  therefore be documented as safe only for scripts nothing else reads.
- Cost: a new public flag, its docs, and its error cases. The gain is
  unknown until measured.
- Does not need to ship in 0.9.0. It can arrive in a 1.x release.

### Option 3: make unordered the default

Run each script as soon as it is ready. A script that needs another one
says so, through a `depends_on` list on the component or through `import`
in an ES-module model (#35). Citry orders only along declared edges and
rejects cycles at startup.

- Breaking impact: high. Every page that shares a global between
  component scripts, like the example above, can break on some loads and
  not others. Tests on a fast local machine may pass while users see the
  failure.
- Cost: a dependency-declaration API, cycle and missing-dependency checks,
  and a migration for every existing page. It also needs the ES-module
  design, which is parked.
- Must ship before 1.0 or wait for 2.0.

### Option 4: promise less than today

Keep running scripts in order in practice, but publish only "`Dependencies`
before component `js`" and call the rest unspecified, to keep the freedom
to choose Option 3 later.

- Breaking impact: none now. But users rely on observed order whatever
  the docs say, and the docs already promise more than this (the
  `extensions.md` and `dependency-files.md` rows above), so this option
  would also mean taking back published text.

## Recommendation for 0.9.0

Choose **Option 1** now and keep Option 2 open for 1.x. Concretely:

1. **Promise the evaluation order, with its exceptions.** Publish:

   > On one page, Citry runs scripts in this order: Citry's own scripts
   > and extension early scripts, then `Dependencies` files, then each
   > component's `js`. Inside each group, components run in the order
   > Citry first renders them, which puts a parent before the components
   > in its template. Each component script runs once per page.

   Then state the exceptions listed above: the groups follow each
   script's `kind`; `on_dependencies` hooks can reorder the list; a file
   several components list runs at its first position; extension scripts
   run once per Vue app; and on a standalone page browser plugin scripts
   run after component scripts. Do not promise HTML order. Before
   publishing, make the plugin-script position the same on both page
   kinds (run them before component scripts), so the promise needs one
   fewer exception.
2. **Promise that a render's scripts finish before its components
   start.** All component scripts of the first render run before Vue
   creates the app. All new component scripts of a server render run
   before any callback of that render. Both hold today.
3. **Give `onServerRender` one order.** In 0.9.0, run callbacks after a
   server render in the same order as on the first mount: children before
   their parent, siblings in the order Vue mounts them. Neither the order
   of elements on the page nor the order of occurrences in the response
   gives this order: Teleport and keyed rows that Vue reorders make the
   page order differ from the component tree.
   - The parent of each component is known: the client already follows
     `$parent` links to check that each occurrence's parent matches its
     Vue parent (`validateMountedParents`, `client.js:4869-4878`).
   - Sibling order is not. Vue 3 has no public list of a component's
     children, so the walk needs either Vue's internal vnode tree
     (`instance.subTree`, including Teleport, Suspense and KeepAlive
     children) or a mount-order index Citry records itself in `mounted`.
     The implementation must pick one; depending on Vue internals is a
     maintenance cost.
   - Use one failure rule as well: when a synchronous callback throws,
     Citry runs no further callbacks of that pass and stops the app. On
     the first mount this means one ordered loop over the mounted
     components instead of one independent task per instance
     (`client.js:2543-2554`).
   - Promise sibling order in the docs for the first time, and add
     browser tests for siblings, slot fills and repeated components, on
     hydrated pages and on pages Vue mounts without hydrating.
4. **Make a component script that does not finish stop the app; leave
   the others as they are.** On the Vue path, every component `js` is
   inline code that Citry wraps in a function it writes
   (`ext/dependencies/types.py:212`, `:255-259`) and publishes as a
   bundle (`_vue/events.py:1092-1104`), loaded by URL on a mounted page
   and written inline on a standalone page. In 0.9.0:
   - For `kind="component"` scripts only, the wrapper calls the
     original function inside a `try` (nesting it, so a leading
     `"use strict"` and function hoisting keep working), records any
     error for that component, and records that the script finished.
     It then reports a caught error again with `reportError`, so the
     page's `error` event and error-monitoring tools still see it.
   - A new check covers every component script, not only those that
     call `$component` (today's registration checks run only for
     scripts with `registersOptions`, `_vue/events.py:1111-1115`). A
     script that did not record "finished", because it threw or failed
     to parse, stops startup, or the server render that loaded it, with
     an error that names the component and carries the original error
     when there is one. On a mounted page the check runs in each
     script's `onload`; on a standalone page it runs before the app
     starts.
   - For `Dependencies` files, extension scripts and third-party files,
     keep today's behavior: the browser reports a throw and the next
     script runs. See "Alternatives for item 4" for why.
   - Pages without the Vue runtime (`deps_strategy="simple"`) are
     unchanged: the browser runs those scripts on its own.
5. **Leave fragments unordered** relative to each other, to the page's
   startup and to its server renders, and say so. Inside one fragment,
   the rules above apply.
6. **Measure before Option 2.** See "What would show this wrong".

### Alternatives for item 4

- **Stop the page for any script that throws.** On a standalone page the
  browser runs every tag on its own, so Citry cannot keep later scripts
  from running; it could only refuse to start the app. A cross-origin
  script loaded without CORS reports only "Script error." with no file or
  error object, and a page-wide `error` listener can blame the wrong file
  when another script or a timer throws in between. Users also cannot add
  a `try` to a CDN file or an analytics script. Rejected for those
  reasons.
- **Stop only in development mode.** This keeps production pages limping
  along, which is friendlier to visitors, but it makes development and
  production behave differently, and a broken component then fails later
  and less clearly. Worth considering if the maintainer prefers it.
- **Fail only the component whose script threw** and start the rest of
  the app. Citry has no way to start an app with a component type
  missing today; this needs a design of its own.

The recommended form works because the wrapper is part of the script's
own bytes, so it needs no page-wide `error` listener and blames the
right component. A script that fails to parse never runs the wrapper,
and the missing "finished" record catches that case too.

### Why not Option 3

It breaks pages on some loads and not others, in components far from the
script that changed. It needs an API and the ES-module design, which do
not exist yet. And its gain is not measured: #145 says the ~14 ms it
observed was the time the scripts took to load one after another, not an
estimate of what unordered execution saves.

What unordered execution could save, now that downloads overlap: the
short wait between one script's `onload` and the next insertion; the run
time of later scripts that are already downloaded while an earlier one
is still arriving; and a full network round trip for each script that
gets no preload hint. On the first load, every script also waits for all
stylesheets. Scripts still run on one main thread, so none of this
removes the scripts' own run time. This is reasoning from how browsers
work, not a measurement.

## Security

Item 4 changes the code Citry writes around component scripts, so it
touches the page's scripts (Mechanism 7 in `CLAUDE.md`).

- **Who supplies the value.** The component author writes the script.
  The error text comes from the browser running it.
- **Where the error appears.** In the browser console and in Citry's
  startup error. The error text must be written as text, never as HTML.
- **Integrity and CSP hashes.** On the Vue path, Citry computes the
  `integrity` hash and any CSP hash over the bytes it serves, which
  already include the wrapper and the `$component` rewrite. A wider
  wrapper changes those bytes; the hashes must still be computed after
  it. External and third-party scripts are not wrapped, which is one
  reason item 4 leaves them alone.
- **The "finished" records** live where page code could write them.
  A page script that forges one only hides its own component's
  failure; it gains nothing it could not do by catching the error
  itself. The records must be kept per app and keyed by component, so
  a name such as `__proto__` reaches only its own entry.
- **The CSP nonce** is unchanged: Citry keeps applying it to every
  script it adds (`client.js:2875-2887`) and keeps refusing a nonce from
  the manifest (`client.js:2829`).

## Error modes

- **A script fails to load** (network error, blocked by CSP or an ad
  blocker, integrity mismatch). Unchanged: on a mounted page, startup or
  the server render stops before later scripts run, with `Citry Vue type
  script failed to load: <url>`. Whether a third-party file such as
  analytics should be allowed to fail without stopping the app is a
  separate question; it is listed under the decisions below.
- **A script never finishes loading.** Unchanged: the app waits. A
  timeout is out of scope here.
- **A component script never calls `$component({...})`.** Unchanged: it
  stops startup.
- **A component script throws while it runs, or fails to parse.**
  Proposed: startup (or the server render) stops with an error naming
  the component, on both page kinds. On a standalone page, later tags
  have already run by then.
- **A `Dependencies`, extension or third-party script throws.**
  Unchanged: the browser reports it, and the next script runs.
- **A synchronous `onServerRender` throws.** Proposed: no further
  callbacks of that pass run, and the app stops, on first mount and after
  a server render alike.
- **An async `onServerRender` rejects.** Unchanged: logged, the page
  keeps going.
- **A fragment's host is removed while its scripts load.** Unchanged: a
  script already added still runs and stays in the per-URL cache.
- **Two fragments bring the same new component script.** Unchanged: it
  runs once, and both wait for it.
- **A user adds `async`, `defer` or `type="module"` to a script on the
  Vue path.** Unchanged: rejected when the page is serialized.

## Migration notes

For most users nothing changes. These notes go in the 0.9.0 upgrade
guide.

- **A component script that throws now stops the page.** If a page worked
  while a component's `js` logged an uncaught error, it now fails to
  start, and the error names the component. Fix the script, or catch the
  error inside it when the failure is expected (for example, a missing
  optional browser API).
- **Callbacks after a server render run in a new order:** children before
  parents, siblings in order, the same as on the first mount. Code that
  relied on one component's callback running before another's should
  share the value through `provide` / `inject`, or read it inside the
  callback that needs it.
- **Sharing a global between component scripts keeps working** when the
  component that sets it renders first. A `Dependencies` file is the
  clearer place for shared setup.

## What would show this wrong

- **The measurement.** On a test page, compare ordered execution with
  preloads against unordered execution. Vary the number of script files
  (8, 32 and 128), not the number of components, and include a page whose
  first script arrives slowly and a page whose scripts get no preload
  hint. If unordered execution saves more than about 10 ms, or more than
  10% of the time from first byte to `citry:ready`, Option 2 is worth
  building soon. If it saves more than half of that time, reconsider
  Option 3 before 1.0. The thresholds are a starting proposal for the
  maintainer to set.
- **The callback order.** If finding sibling order needs Vue internals
  that change between Vue minor releases, or walking the tree on every
  server render measurably slows large updates, keep today's order and
  document it instead.
- **The throw rule.** If the example apps or the docs site ship a
  component script that throws on some browsers but still works (for
  example, feature detection that throws), stopping startup is too harsh.
  A search of those scripts before the change would show this.
- **The first-render order.** If a browser test shows a slot-fill
  component's script running before its receiver's, or a cached render
  changing the order, item 1's wording is wrong and must change before
  it ships.

## Decisions for the maintainer

1. Option 1 now, Option 2 possibly later: yes or no.
2. One `onServerRender` order and failure rule for first mount and
   server render (item 3): yes, or keep today's order and document it.
3. A throwing component script stops startup (item 4): yes, or
   development mode only, or no.
4. Run browser plugin scripts before component scripts on standalone
   pages too (item 1): yes or no.
5. Separate follow-up: should a failed third-party or extension script
   (for example, blocked analytics) stop the app, as it does today?
6. The measurement thresholds in "What would show this wrong".

# Component script order

Status: proposal for review (issue
[#145](https://github.com/citry-dev/citry/issues/145)). Nothing here is
built yet. The recommendation targets 0.9.0, the last release before 1.0
that may change behavior without a deprecation period.

## What this decides

A Citry component can ship JavaScript: its own `js`, the files listed in
its nested `Dependencies` class, and the `onServerRender` callback it
registers through `$component({...})`. When a page holds several such
components, the browser has to run their code in some order. This document
decides which parts of that order Citry promises for 1.0, which parts it
leaves open, and what happens when one script fails.

The question matters now because it is lopsided. Citry can add an opt-in
way to run scripts out of order after 1.0 without breaking anyone. It
cannot drop an ordering promise after 1.0 without breaking pages that
rely on it, whether the docs stated that promise or not.

Downloading scripts in parallel while still running them in order is a
separate question, and it is already solved (see "What Citry does today").

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
      onServerRender() {
        this.$el.style.color = accent;
      },
    });
    """
```

```citry-html
<c-theme />
<c-badge />
```

Today this works: `Theme`'s script runs before `Badge`'s because `Theme`
renders first, and Citry waits for each script to finish before it starts
the next. If Citry let ready scripts run as soon as they arrive, `Badge`
could run first and fail with `TypeError: window.appTheme is undefined`
on some page loads and not others, depending on network timing.

The example is fragile on purpose. A `Dependencies` file, or an import in
a future ES-module model, is the better way to share `appTheme`. But users
write code like this, and whatever Citry promises decides whether it keeps
working.

## Four layers of "order"

"Script order" mixes four things that happen at different times. The rest
of the document keeps them apart.

1. **Script evaluation.** The browser runs each script file once per
   page. For a component's `js`, this is also when `$component({...})`
   registers the component type's options with Citry.
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

Labels in the "Status" column:

- **Promised and tested**: the public docs state it and a test checks it.
- **Tested, not promised**: a test checks it but no public doc states it.
- **Built, untested**: the code does it, nothing checks it.
- **Open**: no rule exists. The result depends on timing or on code that
  was not written to decide it.

### Script evaluation

| Behavior | Evidence | Status |
|---|---|---|
| Scripts run one at a time. Citry inserts the next script only after the previous one fired `onload`. | `loadTypeScript` (`client.js:3049-3084`) and the loop in `primeInitialAssets` (`client.js:3171-3174`); test `e2e/test_vue_dynamic_element_e2e.py::test_initial_script_preloads_overlap_fetch_but_keep_serial_execution` | Tested, not promised |
| Downloads overlap. Citry adds `<link rel="preload">` for every script before the serial loop, so later files are usually already fetched when their turn comes. This is the #137 work. | `createAssetPreloadBatch` (`client.js:2658-2728`); server-side hints in `_vue/serialization.py:173-215`; the same test as above (responses arrive in reverse, execution stays `["first", "second"]`) | Tested, not promised |
| The order is: Citry's own scripts and extension early scripts, then every `Dependencies` file, then every component `js`. Within each group, components appear in the order they first render. | `_resolve_records` docstring (`ext/dependencies/emission.py:509-513`); records collected parent first in `ext/dependencies/extension.py:204-257`; tests `test_deps_emission.py::test_nested_url_dependencies_emit_once_in_first_seen_order` and `e2e/test_document_e2e.py::test_component_and_dependency_assets_execute_in_bucket_order` | `Dependencies` before component `js` is promised (`docs_site/content/advanced/dependency-files.md:9-13`). The rest is tested, not promised |
| Each script file runs at most once per page. A type that a later server render or fragment needs again reuses the earlier load. | `scriptRecordKey` (`client.js:2891-2893`); test `e2e/test_fragment_e2e.py::test_fragment_reuses_a_component_script_the_page_already_loaded` | Tested, not promised |
| All type scripts of the first render run before Vue creates the app. | `client.js:3256-3265` runs `primeInitialAssets` and the definitions before app creation | Promised (`docs_site/content/reference/browser-apis.md:631-635`) |
| Scripts on the Vue path must be ordered classic scripts. `async`, `defer`, `nomodule` and `type="module"` are rejected. | `_serialization_security.py:567-580` and `normalizeAssetSource` (`client.js:2828-2844`); test `test_browser_render.py::test_prepared_browser_scripts_require_synchronous_classic_execution` | Tested, not promised |
| On a page without the Vue runtime (`deps_strategy="simple"`), Citry writes plain `<script>` tags in the same order and the browser's own rules apply, including any `async` or `defer` the user adds. | `ext/dependencies/emission.py:294-317` | Tested for the written order |

The order is "first render order", not "HTML order". The two usually
agree, but not always:

- A `Dependencies` file of a component lower on the page runs before the
  `js` of a component higher on the page, because all `Dependencies` files
  run first.
- A component inside a slot fill registers when the receiving component
  renders that slot, after the receiver itself. This follows from the
  code; no test checks it.

### `onServerRender` and Vue hooks

| Behavior | Evidence | Status |
|---|---|---|
| Vue hooks follow Vue: `setup` and `created` run parent first, `mounted` runs child first. Citry wraps these hooks but does not reorder them. | `typeOptions` (`client.js:2287-2591`) | Open (Vue's behavior, no Citry test) |
| The first `onServerRender` runs after the instance's `mounted`, children before their parent. | `options.mounted` queues one task per instance (`client.js:2534-2556`); docs `docs_site/content/guides/upgrading-to-0-6-0.md:241-243` and `docs_site/content/vue/component-options.md:238-239` | Promised. One test checks it, only for a hydrated page with one parent and one child (`e2e/test_vue_events_default_e2e.py::test_static_physical_document_shell_hydrates_with_csr_parity` asserts `["leaf", "page"]`) |
| Siblings, slot fills and repeated types on the first mount; the same on a page Vue mounts without hydrating. | Each instance's task waits on its own Promise (`client.js:2545-2546`), so the order holds only while those Promises resolve in the order they were created | Built, untested |
| After a server render, callbacks run in this order: components the server render updated (in the order the response lists them), then remounted components, then newly mounted ones. Citry awaits each callback's synchronous part before the next. | `applyEnvelope` (`client.js:5441-5465`) | Open (not documented, not tested). This is a different rule from the first mount |
| A callback that returns a Promise is not awaited. A rejection is logged and the page keeps going. | `runCallback` (`client.js:4826-4840`); test `e2e/test_vue_component_context_e2e.py::test_async_initializer_runs_beside_the_page_and_its_cleanup_still_runs` | Promised and tested (`docs_site/content/reference/browser-apis.md:128-133`) |

### Fragments and server renders

- On a server render, Citry loads new compiled templates first, then new
  type scripts one at a time, then new styles in parallel
  (`client.js:3943-3959`). The first page load runs styles, then scripts,
  then compiled templates (`client.js:3165-3174`, `3262-3265`). Compiled
  templates are not user code, so the difference is not visible to user
  scripts. It is not documented.
- Separate fragments start on their own
  (`packages/js/citry-client/src/citry-fragments.ts:47-110`), so two
  fragments inserted together have no order between them. They share the
  per-URL cache, so a script still runs once. Open.

### Failures

| Behavior | Evidence | Status |
|---|---|---|
| A script that fails to load stops startup (or the server render) before later scripts are inserted. | `loadTypeScript` `onerror` (`client.js:3076-3079`); test `e2e/test_vue_dynamic_element_e2e.py::test_extension_script_loader_retries_and_restarts_same_app_id` | Tested, not promised |
| A component script that loads but never calls `$component({...})` stops startup, and later scripts do not run. | `client.js:3071-3074`, `3153-3155`; test `e2e/test_vue_dynamic_element_e2e.py::test_initial_preloaded_later_script_does_not_execute_after_first_registration_failure` | Tested, not promised |
| A script that throws while it runs still fires `onload`. If it threw after registering its options, or it is a `Dependencies` file that registers nothing, the next script runs as if nothing happened. On a page whose scripts are inline, each tag runs on its own, so the same holds. | `client.js:3071-3075`: the `onload` handler checks only the registration | Built, untested |
| A synchronous `onServerRender` that throws stops the app on the first mount and on a server render. | `client.js:2547-2550`, `5466-5474` | Built, untested |

### What users can use today to depend on another script

- `Dependencies` files, which run before every component's `js`.
- An extension's `ctx.early_scripts`, which run before those.
- `provide` / `inject` between Vue components.
- The `citry:ready` event and `whenReady`, which wait for the first-mount
  callbacks (`client.js:4857-4867`).
- A global set by a script that renders earlier, relying on the order
  above.

There is no way to declare "this script needs that one" and no ES-module
output. The ES-module design ([`esm.md`](esm.md), issue #35) is parked
research.

## How other frameworks handle it

- **The browser itself.** Classic scripts the parser finds run in document
  order. A script added by code is async by default, unless the code sets
  `script.async = false`, which runs such scripts in insertion order.
  `type="module"` scripts run after parsing, in document order. `async`
  scripts and `import()` give no order. (WHATWG HTML, "scripting".)
- **htmx and Turbo** recreate each `<script>` in swapped content with
  `async = false`, so swapped scripts run in the order they appear (htmx
  2.0.4 `duplicateScript`; Turbo 8.0.12 `activateScriptElement`). Both
  chose ordered execution for content inserted after load, which is
  Citry's case for server renders and fragments.
- **Livewire** runs a component's `@script` once per instance, before
  Alpine initializes that component, and loads `@assets` once per page
  before any of those scripts.
- **Astro islands** hydrate independently, so sibling islands have no
  order. A nested island waits for its nearest server-rendered parent
  island to send `astro:hydrate`, so a parent always hydrates first.
  Astro added that wait after nested islands broke (Astro #3455 and
  later). Lit components that started before hydration finished broke
  too (Astro #10633).
- **Vue and Nuxt** hydrate depth-first: `setup` parent first, `mounted`
  child first. Lazy hydration (Vue 3.5 `hydrateOnVisible`, Nuxt delayed
  hydration) gives up sibling order, as an opt-in per component.
- **Stimulus and Phoenix LiveView** promise order only inside one
  controller or hook, nothing across them.
- **Web components** upgrade in tree order once defined; code that needs
  another element waits on `customElements.whenDefined()`.

The pattern: frameworks that run scripts arriving with server HTML keep
them in order (htmx, Turbo, Livewire). Frameworks that run components out
of order make it an opt-in per component (Vue, Nuxt) or build a readiness
signal for the parent-child case (Astro, web components).

## Options

### Option 1: keep ordered execution and write the rules down

Keep today's behavior. Publish the order rules from "What Citry does
today" as the 1.0 contract, decide the rows marked open, and add the
missing tests.

- Breaking impact: none for pages that work today. Pages relying on
  undocumented timing keep working.
- Cost: scripts keep running one at a time. Downloads already overlap, so
  what is left is a short wait between one script's `onload` and the next
  insertion. That wait is not measured yet (see "What would show this
  wrong").
- Leaves room for Option 2 later, as an addition.

### Option 2: keep the ordered default, add an opt-in for unordered scripts

Option 1, plus a way to mark a script as independent so it runs as soon
as it arrives. One shape: `Dependencies.js` entries and component `js`
accept an `order="any"` flag; an unordered script may not rely on any
other component's script, and Citry starts the Vue app only once every
script, ordered or not, has run.

- Breaking impact: none. Existing scripts stay ordered.
- Cost: a new public flag, its docs, and the error cases it opens (an
  unordered script that does read a global set by another). The gain is
  unknown until measured.
- Does not need to ship in 0.9.0. It can arrive in any 1.x release.

### Option 3: make unordered the default, with declared dependencies

Run each script as soon as it is ready. A script that needs another one
says so, either through a `depends_on` list on the component or through
`import` in an ES-module model (#35). Citry orders only along declared
edges and rejects cycles at startup.

- Breaking impact: high. Every page that shares a global between
  component scripts, like the example above, can break at random. The
  failure depends on network timing, so tests on a fast local machine may
  pass while users see it.
- Cost: a dependency-declaration API, cycle and missing-dependency checks,
  and a migration for every existing page. It also needs the ES-module
  design, which is parked.
- Must ship before 1.0 or not at all for 1.x, because it removes a
  behavior pages already rely on.

### Option 4: guarantee less than today

Keep running scripts in order in practice, but publish only "`Dependencies`
before component `js`" and state that other order is unspecified. This
keeps the freedom to choose Option 3 in a later major release.

- Breaking impact: none now, but it only shifts the break to whenever the
  freedom is used. Users rely on observed order regardless of docs, so the
  freedom is mostly on paper.

## Recommendation for 0.9.0

Choose **Option 1** now and keep Option 2 open for 1.x. Concretely:

1. **Promise the evaluation order.** Publish: "On one page, Citry runs
   component scripts one at a time and each file once. Citry's own
   scripts and extension early scripts run first, then every
   `Dependencies` file, then every component's `js`. Inside each group,
   components run in the order they first render: a parent before the
   components in its template, and a component before the ones after
   it." State the two cases where this differs from the HTML order (a
   later component's `Dependencies` file, a component in a slot fill).
   Do not promise HTML order.
2. **Promise that a render's scripts finish before its components
   start.** All type scripts of the first render run before Vue creates
   the app. All new type scripts of a server render run before any
   callback of that render. Both hold today.
3. **Give `onServerRender` one rule.** The first-mount rule is documented
   already: children before their parent, siblings in page order. In
   0.9.0, make callbacks after a server render follow the same rule
   instead of "updated, then remounted, then new". This is a behavior
   change for a rule nobody documented, and 0.9.0 is the last window for
   it. Add browser tests for siblings, slot fills and repeated types, on
   hydrated pages and on pages Vue mounts without hydrating.
4. **Make a script that throws stop the page, the same as a script that
   fails to load.** Today a throw is caught only when it happens before
   `$component({...})`. In 0.9.0, a script that throws while it runs
   stops startup or the server render, on every path (loaded and inline),
   with an error that names the file. This is the one breaking change in
   the recommendation (see "Migration notes").
5. **Leave fragments unordered relative to each other**, and say so. Inside
   one fragment, the rules above apply.
6. **Measure before Option 2.** Compare ordered execution with preloads
   against unordered execution on the benchmark pages that #145 cites
   (140 and 1,400 outputs). Build Option 2 only if the difference is worth
   a public flag (see "What would show this wrong").

Why not Option 3: it breaks pages at random and at a distance, needs an
API and the ES-module design that do not exist yet, and its gain is not
measured. #145 itself says the 14 ms chain it observed was the loading
chain, not an estimate of what unordered execution saves. Once downloads
overlap, the scripts still run on one main thread, so unordered
execution can only save the gaps between them. That is reasoning from how
the browser works, not a measurement.

## Error modes

- **A script fails to load** (network error, blocked by CSP, integrity
  mismatch). Unchanged: startup or the server render stops before later
  scripts run, with `Citry Vue type script failed to load: <url>`.
- **A component script never calls `$component({...})`.** Unchanged: it
  stops with "did not register its declared Options".
- **A script throws while it runs.** Proposed: Citry stops startup or the
  server render and reports the file and the original error. Later scripts
  do not run. Detecting this needs a `window` `error` listener scoped to
  the script's run, or a wrapper around the code, on both the loaded and
  the inline path. On a page without the Vue runtime, the browser runs the
  tags and Citry cannot stop later ones; the docs say so.
- **A synchronous `onServerRender` throws.** Unchanged: the app stops.
- **An async `onServerRender` rejects.** Unchanged: logged, the page keeps
  going.
- **Two fragments both bring the same new script.** Unchanged: it runs
  once, and both wait for it.
- **A user adds `async`, `defer` or `type="module"` to a script on the Vue
  path.** Unchanged: rejected when the page is serialized, because those
  attributes would break the order this document promises.

## Migration notes

For most users nothing changes. The notes below go in the 0.9.0 upgrade
guide.

- **A component script that throws now stops the page.** If a page worked
  while one script logged an uncaught error, it now fails to start and
  the error names the file. Fix the script, or catch the error inside it
  when the failure is expected (for example, a missing optional browser
  API).
- **Callbacks after a server render run in a new order.** They now run
  children before parents, siblings in page order, the same as on the
  first mount. Code that relied on "updated components first" should pass
  the value through `provide` / `inject` or wait for `citry:ready`
  instead.
- **Sharing a global between component scripts keeps working** when the
  component that sets it renders first. A `Dependencies` file is the
  clearer place for shared setup.

## What would show this wrong

- **The measurement.** If unordered execution saves more than about 10 ms
  on the 1,400-output page, or more than 10% of "browser plus subsequent
  requests" time on the 140-output page, compared with ordered execution
  with preloads, Option 2 is worth building soon. If it saves more than
  half of that time, reconsider Option 3 before 1.0. These thresholds are
  a starting proposal for the maintainer to set.
- **The callback rule.** If ordering callbacks after a server render by
  tree position needs data the client does not have, or measurably slows
  large server renders, keep today's order and document it instead.
- **The throw rule.** If real pages commonly ship a script that throws on
  some browsers but still works (for example, feature detection that
  throws), stopping the page is too harsh. A survey of the example apps
  and the docs site before the change would show this.
- **The slot-fill case.** If a browser test shows a slot-fill component's
  script running before its receiver's, the published rule in item 1 is
  wrong and must change before it ships.

## Decisions for the maintainer

1. Option 1 now, Option 2 possibly later: yes or no.
2. One `onServerRender` rule for first mount and server render (item 3):
   yes, or keep today's order and document it.
3. A script that throws stops the page (item 4): yes or no.
4. The measurement thresholds in "What would show this wrong".

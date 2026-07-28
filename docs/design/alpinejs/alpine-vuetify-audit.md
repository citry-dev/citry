# Audit: the maintainer's Alpine packages (old Vuetify-to-Alpine port)

Audience: the citry Events design (docs/design/events.md section 16, "umbrella
option": delegate client runtime reactivity to AlpineJS, one Alpine component
per interactive citry instance, reactive data = public State fields plus
`loading`/`error`, magics like `$onEvent`/`$sendEvent`).

Path shorthand used below:

- `VUE` = `/private/tmp/claude-501/-Users-mac-repos-citry/73f703cb-6307-4ae1-9c01-a5061174cbc5/scratchpad/old-vuetify/vuetify`
- `DJC` = `/private/tmp/claude-501/-Users-mac-repos-citry/73f703cb-6307-4ae1-9c01-a5061174cbc5/scratchpad/old-djc/django-components`

The four packages live under `VUE/packages/`. All four are published on npm
today at exactly the snapshot versions (verified with `npm view` during this
audit): `alpine-composition` 0.1.29, `alpine-reactivity` 0.1.11,
`alpine-provide-inject` 0.3.0, `alpine-alpine` 0.1.0 (and `alpinui` 0.0.1).
None of the four has a single test file or a changelog. All are MIT, authored
solely by Juro Oravec.

## Executive summary

- The stack is small and layered: `alpine-reactivity` (~450 LOC) rebuilds
  Vue's `ref`/`computed`/`watch` on top of the four primitives Alpine
  re-exports from `@vue/reactivity`; `alpine-composition` (~1050 LOC) builds
  Vue-style components (props, emits, `setup()`, lifecycle, plugins) on top of
  `Alpine.data()`; `alpine-provide-inject` (60 LOC) and `alpine-alpine`
  (14 LOC) are one-magic plugins.
- **Scope isolation is implemented in `alpine-composition`**, not in a
  separate plugin: components registered through it are isolated by default
  by truncating the element's Alpine data stack to its own layer
  (`VUE/packages/alpine-composition/src/component.ts:165-170`). Details in
  section 2.
- **The perf work the maintainer remembers is NOT in this repo.** The
  Vuetify-monorepo git history has zero perf commits and its TypeScript
  sources still contain the slow designs. The optimized code exists only as
  hand-patched dist bundles in the old django-components snapshot:
  `DJC/other/alpine-comp-modified.js` (composition rework, with
  `window.timeSpentInUseProps` / `window.timeSpentIn_init` counters) and
  `DJC/other/alpine-modified.js` + `alpine-partial.js` (patched Alpine core
  3.14.9). That work was never backported to TS source and never published
  (npm latest is still the pre-rework 0.1.29). Details in section 5.

## 1. alpine-reactivity (v0.1.11)

**What it does.** Reimplements the Vue reactivity API for Alpine users:
`ref`, `computed`, `writableComputed`, `shallowRef`, `reactive`, `readonly`,
`toRef`, `toRefs`, `toRaw`, `unref`, `isRef`, `isComputed`, `watch`,
`watchEffect`, `stop`, plus `setAlpine`/`getAlpine`. Single source file
`VUE/packages/alpine-reactivity/src/reactivity.ts` (447 LOC).

**Why it exists (upstream limitation).** Alpine is built on `@vue/reactivity`
but exposes only `reactive`, `effect`, `release` (stop), and `raw` (toRaw),
and lets embedders swap in a custom reactivity engine. Importing Vue's own
`ref`/`computed` directly would create a second, disconnected reactivity
graph, so the README explicitly advises against it and rebuilds everything
from Alpine's four primitives (`VUE/packages/alpine-reactivity/README.md`,
"How it works").

**Mechanism highlights.**
- A ref is `Alpine.reactive({ [_refBrand]: true, value })`, sealed
  (`reactivity.ts:72-82`). `computed` is a frozen getter over an inner ref,
  updated by `Alpine.effect` (`reactivity.ts:49-68`).
- Alpine instance discovery: module-level global
  `globalThis._alpineReactivity`, set by `setAlpine()` or automatically on the
  `alpine:init` event from `window.Alpine` (`reactivity.ts:16-30`). One Alpine
  per page is assumed.
- `watch` is a simplified port of `@vue-reactivity/watch` using only
  `Alpine.effect` (`reactivity.ts:255-397`): single/multi source, `immediate`,
  `deep` (recursive `traverse`), `flush: 'post'` via `nextTick`.

**Known gaps in code.**
- `flush: 'sync'` is not implemented; a TODO says it is assumed to behave like
  `pre` (`reactivity.ts:391-393`).
- `shallowRef` is not actually shallow; it wraps a normal (deep) ref in a
  writable computed (`reactivity.ts:117-127`), so it emulates the API shape,
  not the performance benefit.
- `toRefs` has a workaround note: "For some reason having an object of
  computed's doesn't work, so internally we actually expose refs"
  (`reactivity.ts:141-143`); it pairs each ref with a one-way syncing
  computed, i.e. writes to the ref do not write back to the source object.
- `readonly` returns a fresh Proxy on every property access and only warns on
  writes (`reactivity.ts:198-218`); object identity is unstable across reads.

**Shape.** TypeScript; builds cjs + esm via `tsc` and a CDN bundle via rollup
(`scripts/rollup.config.mjs`); typedoc markdown docs under `docs/typedoc/`.
`alpinejs ^3.14.1` and `vue ^3.4.34` are devDependencies only (types and the
Alpine global at runtime); there are no runtime dependencies and no
peerDependencies declared.

## 2. alpine-composition (v0.1.29): the main act, and the isolation answer

**What it does.** A Vue-flavored component model over `Alpine.data()`:
`defineComponent({ name, props, emits, setup, isolated, initKey })`,
`registerComponent(Alpine, options)`, and a plugin system
(`createAlpineComposition({ plugins })`) that returns a `registerComponent`
which runs each plugin against every created instance. Files:
`component.ts` (302), `composition.ts` (71), `emit.ts` (144),
`reactivity.ts` (229), `errorHandling.ts` (51), `types.ts` (99),
`utils.ts` (152), under `VUE/packages/alpine-composition/src/`.

**Public API surface.**
- `defineComponent`, `registerComponent`, `registerComponentFactory`,
  `createAlpineComposition`, `createReactivityAPI`, `hasEvent`, plus a re-export
  of all of `alpine-reactivity` (`src/index.ts`).
- Instance magics added on top of Alpine's own: `$name`, `$props`, `$attrs`,
  `$options`, `$emitsOptions`, `$emit`, `$initState`, `$onBeforeUnmount`
  (`component.ts:218-293`, README "Setup context and Magics").
- `setup(props, vm, reactivity, ...args)` receives a per-instance reactivity
  API whose refs/watches are auto-disposed on destroy
  (`src/reactivity.ts:72-228`), including Vue lifecycle shims: `onBeforeMount`
  and `onMounted` run immediately, `onBeforeUnmount`/`onUnmounted` map to
  Alpine `destroy`, `onBeforeUpdate`/`onUpdated` are driven by a watcher over
  all registered reactives, `onActivated`/`onDeactivated` are noops
  (`src/reactivity.ts:220-227`).
- Props: declared Vue-style (type constructors, `required`, `default`),
  passed in HTML via an `x-props` attribute holding a JS object expression.
  Not a registered Alpine directive; the attribute is read with
  `el.getAttribute('x-props')` and evaluated with
  `Alpine.evaluateLater(el.parentNode, expr)`, deliberately against the
  PARENT element's scope (`component.ts:80-84`). One `watchEffect` per prop
  key keeps each prop live (`component.ts:95-141`), with type validation and
  defaults.
- Emits: Vue-fidelity `$emit` that calls handler props `onX` / `onXOnce`
  looked up on `$props`, warns on undeclared events, supports per-event
  validator functions, does not bubble and sends nothing without a handler
  prop (`emit.ts:69-114`).
- Init state channel: a `data-x-<initKey>` attribute (default `data-x-init`)
  holding JSON is parsed into the `$initState` magic (`component.ts:64-71`),
  the "initialize internal state from server HTML without making it a prop"
  channel.

**The isolation mechanism (the thing the maintainer asked to find).**
It is in this package, on by default (`isolated = true`,
`component.ts:207`), documented in the README section "Component isolation".
How it works:

1. Alpine's normal scoping: every `x-data` element pushes a scope object onto
   `el._x_dataStack`, and an expression anywhere below evaluates against
   `Alpine.mergeProxies(Alpine.closestDataStack(el))`, the merged chain of
   the element's own scope plus all ancestor scopes. That is exactly the
   "outer component data leaks into inner components" behavior.
2. `isolateInstance` truncates the chain at the component root:
   `el._x_dataStack = el._x_dataStack.slice(0, 1)`
   (`component.ts:165-170`), keeping only the component's own (innermost)
   scope layer.
3. Truncation only affects future lookups, so the already-created instance
   proxy is rebuilt from the truncated stack:
   `Alpine.mergeProxies(Alpine.closestDataStack(el))` again
   (`makeInstance`, `component.ts:158-163`), called from `init()` right after
   isolation (`component.ts:250-263`). The code comments there call out that
   ordering is load-bearing, and that `loadInitState` must run only after the
   rebuild because new keys are written to the last context layer and
   isolation drops all layers but the first (`component.ts:265-272`).
4. Data still crosses the boundary in exactly one sanctioned way: `x-props`
   is evaluated against `el.parentNode` (step above), so the parent's scope
   feeds the child's declared props reactively while nothing else leaks.
   Opt-out is `isolated: false` per component.

Note the isolation is per registered component and happens inside `init()`
during Alpine's tree walk; it is a semantic patch on Alpine internals
(`_x_dataStack` is a private field), which is version-coupled to Alpine 3.

**Shape/deps.** TypeScript; same build as alpine-reactivity (tsc cjs+esm plus
rollup CDN bundle, typedoc docs). One runtime dependency:
`alpine-reactivity ^0.1.11`. `alpinejs ^3.14.1` and `vue ^3.4.34` as
devDependencies; **type-only** imports from `vue` (`Prop`, `EmitsOptions`,
`InjectionKey`, `ComponentObjectPropsOptions`) mean the published `.d.ts`
files still require Vue types downstream. Its `types.ts` also declares the
`$provide`/`$inject` magics, assuming alpine-provide-inject is installed
(`types.ts:15-23`); `createReactivityAPI.inject/provide` delegate to those
magics (`src/reactivity.ts:145-164`), so the packages are runtime-coupled
without a declared dependency.

**Known gaps in code (published version).**
- The update watcher for `onUpdated` hooks is torn down and recreated every
  time any ref is registered, and touches every reactive and every prop on
  each run (`src/reactivity.ts:83-120`). This is the exact hot spot the
  patched bundle later reworked (section 5).
- `applySetupContextToVm` copies setup results onto the plain factory object
  (`component.ts:172-179`), not through the reactive data layer; the patched
  bundle fixed this to write through `Alpine.closestDataStack(el)[0]` so
  updates stay reactive.
- Async `setup` is supported by `.then(...)` (`component.ts:278-282`), so a
  component can render before its data lands; no loading affordance.
- `$attrs` builds a fresh plain object per access, non-reactively
  (`component.ts:146-156`).
- Prop keys without a definition are silently treated as event handler props
  (`component.ts:104-108`); the patched bundle tightened this to throw on
  unexpected props unless the key starts with `on` (with a TODO to require
  the third letter capitalized).

## 3. alpine-provide-inject (v0.3.0)

**What it does.** Adds `$provide(key, value)` and `$inject(key, default?)`
magics with Vue provide/inject semantics. Whole implementation is
`VUE/packages/alpine-provide-inject/src/index.ts` (60 LOC).

**Mechanism.** `$provide` writes into an ad-hoc `el._provides` record on the
DOM element itself; `$inject` walks `parentElement` upwards until it finds a
`_provides` containing the key, else returns the default or throws
(`index.ts:22-59`). Because it rides the DOM tree rather than Alpine's scope
chain, it works across alpine-composition's isolation boundary by
construction. That combination is the Vue model: props down, provide/inject
for deep passing, everything else isolated. Nearest-provider-wins shadowing
comes free from the upward walk. Git history shows a `$injectSelf` variant
was removed (`c8f0c57`).

**Shape.** TypeScript, esbuild build (`scripts/build.js`, cdn + esm + cjs
outputs like official Alpine plugins), no runtime deps, no tests. Cleanup
gap: `_provides` stays on the element until the element dies; no unmount
hook, fine for DOM-lifetime data, wrong for anything holding big references
on long-lived elements.

## 4. alpine-alpine (v0.1.0)

**What it does.** One magic, `$Alpine`, returning the Alpine object the
plugin was registered with (`VUE/packages/alpine-alpine/src/index.ts`,
14 LOC). Motivation: inside expressions and setup code you otherwise reach
for the `window.Alpine` global, which breaks with bundled/multiple Alpine
instances; this pins "the Alpine that owns this component tree". The `dev/`
folder is an untouched Vite scaffold (still shows the Vite counter demo),
so the package was published without a real playground.

## 5. The performance work: where it actually lives

**Not in the Vuetify monorepo.** `git log --all` there has no perf commits;
`VUE/packages/alpine-composition/src/reactivity.ts` still has the
recreate-the-world update watcher and `component.ts` still creates one
`watchEffect` per prop key. The only dev-branch extra is a "temp: dump"
commit (`286341d`) with cosmetic TODO markers.

**The source of the ~0.3s to ~0.15s init win is the patched bundles in the
django-components snapshot**, annotated with `// TODO CHANGED` markers and
timing counters:

`DJC/other/alpine-comp-modified.js` (base: published alpine-composition
0.1.29; orig copy alongside as `alpine-comp-orig.js`):
- **One watcher for all props instead of one per prop key**: the whole
  parse/validate loop moved inside a single `watchEffect` per component
  (`alpine-comp-modified.js:623-711`). For Vuetify-scale components (dozens
  of props) times 300-500 instances this is the big init multiplier.
- **Per-ref persistent watchers instead of the global recreated one**: one
  persistent props watcher plus one small persistent watcher per registered
  ref, all funneling into a shared `onReactiveChange()` that fires
  `onBeforeUpdate`/`onUpdated` (`alpine-comp-modified.js:350-398`). Kills the
  O(n^2) "touch everything again on each new ref" behavior.
- **Proxy bypasses**: `createReactivityAPI(instance, _self)` gained a raw
  second argument to skip magic-proxy lookups (`:346-348`); `makeInstance`
  returns `Alpine.closestDataStack(el)[0]` directly instead of
  `mergeProxies(...)` since after isolation there is exactly one layer
  (`:733-738`); `$el` is read once into a captured variable (`:826-829`).
- **Reactive-correct setup application**: `applySetupContextToVm` writes
  through the element's current data layer so setup results stay reactive
  (`:746-759`).
- **Timing counters**: `window.timeSpentInUseProps` (`:602`, `:714`) and
  `window.timeSpentIn_init` (`:764`, `:885`).
- Props hardened to throw on unexpected keys; `loadInitState`/`data-x-init`
  channel commented out (server side likewise commented out in
  `DJC/src/django_vue/component.py:66-73`).

`DJC/other/alpine-modified.js` (base: Alpine core 3.14.9,
`alpine-orig.js`; ~438 diff lines) patches Alpine itself:
- `injectMagics` rebuilt as a single Proxy with `get`/`has` traps instead of
  `Object.defineProperty` per magic per object, plus a per-element
  `cachedUtils` map; comment: faster creation "speeds up start up time"
  (`alpine-modified.js:404-469`).
- `walk` rebuilt on an XPath query that visits only elements carrying
  Alpine attributes instead of walking every DOM node
  (`alpine-modified.js:877-918`).
- Regexes hoisted out of hot paths (evaluator, directive parsing, string
  helpers) (`:533-547`, `:800-816`, `:2903-2921`); `findClosest` made
  iterative (`:972-982`); bound magics defined with `value:` instead of a
  getter allocating a closure per read (`:1818-1828`).
- `DJC/other/alpine-partial.js` is an intermediate cut with instrumentation
  counters `window.injectMagicsCalls` / `window.injectMagicsEls`
  (`alpine-partial.js:410-411`).

**Status**: all of this is dist-bundle-only, marker-annotated, uncommitted to
any TS source, unpublished. The XPath walk has at least one visible bug
(`skippedEls.push(el)` pushes the walk ROOT rather than the skipped element,
`alpine-modified.js:912-914`), consistent with "experiment, not release".

## 6. Upstream Alpine limitations these packages were compensating for

Recorded in READMEs, comments, and the patch bundles:

1. No props contract; data flows by implicit scope inheritance
   (composition README "Component isolation" shows the leak example).
2. Only four reactivity primitives re-exported; no `ref`/`computed`/`watch`,
   and a custom-reactivity hook that makes importing Vue directly unsafe
   (reactivity README "How it works").
3. No provide/inject (solved on the DOM, not the scope chain).
4. Lifecycle is only `init`/`destroy`, and `destroy` takes a single function
   (hence `$onBeforeUnmount` accumulating callbacks and the immediate-run
   `onMounted` shims).
5. No emits/events contract (`$emit` built on `on*` handler props; no bus).
6. Init cost on component-heavy pages: per-magic `defineProperty` on every
   scope object, full-DOM walk, per-prop watchers (all three attacked in the
   patched bundles).
7. No way to reach "the Alpine that registered me" without a global
   (`alpine-alpine`).
8. From the wider snapshots: prop-vs-attribute ambiguity on component tags
   needs a runtime middleman
   (`DJC/src/django_vue/utils/vue_alpine2django.py:155-166`), and fragment JS
   must register before reactive markup activates (`<template x-if="false">`
   trick, covered in the earlier old-djc recon).

## 7. Reusability verdict for the citry Events runtime

Context: Events needs, per interactive instance, a reactive scope holding
public State fields plus `loading`/`error` meta, magics `$onEvent`/
`$sendEvent`, and isolation so one instance's scope does not bleed into
nested instances. It does NOT need Vue component fidelity: no props system,
no emits-as-props, no `setup()`, since kwargs/slots never travel and events
go to the server, not to parent components.

**Lift as-is (concepts and small code, not necessarily the packages):**
- The isolation mechanism: `isolateInstance` + `makeInstance` rebuild
  (component.ts:158-170, 250-263) is ~15 lines and exactly the needed
  semantics. Citry would apply it in the `Alpine.data` factory it generates
  per interactive instance. Keep the ordering comments; they encode real
  footguns.
- The plugin/magic pattern from `createAlpineComposition`
  (composition.ts:39-71) as the shape for installing `$onEvent`/`$sendEvent`/
  `$forwardEvent` magics per component rather than globally.
- `alpine-provide-inject` was initially considered reusable verbatim if
  parent-to-descendant sharing became necessary across isolation.
  **Superseded 2026-07-24:** the callable names and ancestor-only behavior
  remain useful, but the DOM storage and `parentElement` walk do not satisfy
  Citry's landed slot, rootless, mirror, teleport, and morph contracts. The
  current decision is
  [`component_provide.md` section 10](../component_provide.md#10-client-provide-inject-and-unprovide-design).
- The `data-x-init` JSON attribute channel (component.ts:64-71) is prior art
  for "server delivers initial reactive data in an attribute"; citry's
  equivalent is the State snapshot next to the signed token.
- The perf lessons as design rules for `citry-events.js`: one watcher per
  concern, never per field against a shared expression; never recreate
  watchers on registration; avoid per-instance `defineProperty` storms;
  batch or index DOM discovery instead of walking everything. If citry ships
  its own thin reactive layer, these decide its shape.

**Needs rework before reuse:**
- `alpine-reactivity` is sound as a pattern (build on `Alpine.reactive` +
  `Alpine.effect` only) but citry likely needs just `reactive` + `effect` +
  a small `watch`; the file is copy-and-prune material (the `watch` port,
  reactivity.ts:255-397, is the valuable part). `shallowRef`, `readonly`,
  `toRefs` carry known caveats (section 1) and should not be lifted blind.
- The patched-bundle optimizations exist only as annotated dist JS; anything
  adopted must be re-derived in source form (the single-props-watcher and
  per-ref-watcher patterns port cleanly; the Alpine-core patches do not,
  they are a fork of Alpine internals).

**Obsolete for this use case:**
- The whole Vue-fidelity component layer of `alpine-composition`: props
  declarations/validation, `$emit`/`onX` handler props, `setup()`, lifecycle
  shims, `$attrs`, `mergeProps`/`normalizeClass` utils. Events' State comes
  validated from the server; client-side prop typechecking is dead weight.
- `alpine-alpine` (trivial; citry's runtime holds its own Alpine reference).
- The Alpine-core fork: citry cannot ship a patched Alpine; if init cost on
  300-500 components resurfaces, the levers on unforked Alpine are fewer
  components' worth of `x-data` scopes, `x-ignore` + lazy activation, or
  batching, not core patches. Worth recording in the Events design as a known
  scaling risk with measured history (~0.3s to ~0.15s was achieved only by
  forking).

**Version coupling warning.** Both the isolation trick (`_x_dataStack`) and
`makeInstance` (`closestDataStack`/`mergeProxies`) touch Alpine private
internals, tested against Alpine 3.14.x. Any citry adoption should pin the
Alpine major and add a canary test around the isolation behavior.

## 8. Housekeeping flags for the maintainer

- **Leaked credential**: a live-looking PyPI upload token is committed in
  `VUE/packages/alpinui-django/TODO.md:8` (twine upload line). It should be
  revoked regardless of whether this repo ever goes public again.
- The four packages have zero tests and no changelogs; `alpinui` TODO.md
  says 89/89 components ported but 0/89 tested.
- npm `latest` for alpine-composition (0.1.29) still contains the
  slow-watcher design; anyone depending on it today gets the pre-rework code.

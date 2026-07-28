# Recon: citry's client-side JS runtime and fragment delivery

Audit of the surface a `Component.Events` extension ($sendEvent / $onEvent) would extend.
Sources read in full: `docs/design/dependencies.md`, the client runtime
`packages/py/citry/citry/extensions/dependencies/client/citry.js` (238 lines, plain JS package data),
the dependencies extension (`__init__.py`, `scripts.py`, `emission.py`, `routes.py`, `types.py`),
`serialize.py`, `extension.py`, `citry.py`, `util/routing.py`, `util/id.py`, the contrib adapters,
and the four named test files plus `tests/e2e/conftest.py`. All paths below are repo-relative under
`packages/py/citry/` unless prefixed otherwise.

---

## 1. $onComponent: signature, payload, timing, pipeline

**It is a server-side source rewrite, not a client API.** `$onComponent(` in a component's
`Component.js` is expanded once, when the class's JS is first cached, by the regex
`\$onComponent\s*\(` -> `Citry.manager.registerComponent("<class_id>", `
(`citry/extensions/dependencies/scripts.py:46`, `scripts.py:56-66`, applied in
`cache_component_js` at `scripts.py:91`). Both the inlined tag and the URL-served file carry the
expanded form (`tests/test_contrib_fastapi.py:66-68`, `tests/test_deps_vars.py:146-152`).
Detection is a plain substring check `"$onComponent" in content` (`scripts.py:69-72`).
Being regex/substring based, it also matches occurrences inside JS strings or comments; nothing
guards against that today.

**User-facing signature:** `$onComponent(fn)` where `fn` receives one object. The client invokes it
as `fn({ id: call.componentId, els: els, data: data })` (`client/citry.js:151`):

- `id`: the instance's render id (e.g. `c1A2b3c`), same string as in the DOM marker.
- `els`: `Array` of elements matching `[data-cid-<componentId>]`, queried at call time
  (`client/citry.js:145-147`). A component with several root elements gets several entries.
- `data`: the instance's `js_data()` result (JSON round-tripped), or `null` when the record carries
  no vars hash (`client/citry.js:131, 144`).

There is no fourth property; the payload object is the natural extension point for new per-instance
magics (see section 4).

**Registration and invocation machinery** (`client/citry.js:110-157`):

- `registerComponent(classId, fn)` appends to a `Map<classId, fn[]>`; multiple `$onComponent` calls
  in one component's JS all register, and every registered callback runs per instance call
  (`client/citry.js:112-117, 148-154`).
- `registerComponentData(classId, varsHash, data)` fills a `Map<"classId:varsHash", data>`
  (`client/citry.js:119-122`). The data arrives via a generated "variables script" that calls it
  with the base64-armored `js_data()` JSON (`scripts.py:164-188`).
- `callComponent(classId, componentId, varsHash)` pushes onto `pendingCalls`
  (`client/citry.js:124-127`). Calls come from the page manifest
  (`client/citry.js:182-188`).
- `flushCalls()` runs after every registration/call: a call executes only when its callback exists
  and (if `varsHash != null`) its data exists (`isCallReady`, `client/citry.js:129-132`). Calls
  stay queued in order, so manifest, component JS, and data script may arrive in any order
  (`client/citry.js:137-139`). Callback errors are caught and logged per callback
  (`client/citry.js:149-153`).

**When it fires:** in a `document` page, emission places runtime, then manifest, then component
scripts before the last `</body>` (`emission.py:144-151`; order asserted in
`tests/test_deps_vars.py:246-249`). Manifests already in the document are processed at startup
(`DOMContentLoaded` when still loading, else immediately, `client/citry.js:229-237`); manifests
inserted later (fragments) are picked up by a MutationObserver watching for
`script[type="application/json"][data-citry]` (`client/citry.js:201-213`). Each manifest tag is
processed once, marked with `data-citry-processed` (`client/citry.js:191-199`). There is exactly
one invocation per manifest call entry; no re-run on DOM changes, no teardown on element removal.

**Server-side collection that produces the call:** the dependencies extension's
`on_component_data` hook records a `DependencyRecord(class_id, component_id, js_vars_hash,
css_vars_hash)` per rendered instance that has any assets
(`citry/extensions/dependencies/__init__.py:203-236`; the record type at
`citry/extensions/dependencies/types.py:45-63`). Records bubble to the root context through
`on_render_context_merge` as an insertion-ordered dict (dedup on insert,
`__init__.py:238-247`). At serialize, a call `(class_id, component_id, js_vars_hash)` is emitted
only when the class's JS uses `$onComponent` and the strategy includes the client runtime
(`emission.py:286, 334-335`).

## 2. Identity in the DOM and the runtime

- **Render id (instance id).** `component.id`, e.g. `c` + 6 base62 chars (`citry/util/id.py:56-71`,
  `citry/constants.py:1-2`). Precedence: explicit `id` argument, then
  `CitrySettings.id_generator`, then the built-in counter (`citry/component.py:447-456`). Unique
  per process (counter with random start), not a secret, meant to be unique per rendered page
  (`util/id.py:1-8`).
- **DOM marker.** Serialization stamps each component's root element(s) with a boolean attribute
  named `data-cid-<id>` (value `""`), not `data-cid="<id>"` (`citry/serialize.py:104`, module doc
  `serialize.py:1-10`). When a child component is its parent's root element, the element carries
  both markers. Extensions add extra root markers per instance through
  `CitryContext._add_root_markers` (the dependencies extension adds `data-ccss-<hash>` for CSS
  variables, `__init__.py:220-223`, `scripts.py:191-217`).
- **Class id.** `Component.class_id`, class name + short hash of import path, stable across
  processes; reverse lookup via `Citry.get_component_by_class_id` (`citry/component.py:98-113`,
  `citry/citry.py:333-345`). Used in cache keys, script URLs, and the manifest.
- **Runtime state maps** (`client/citry.js:41-47`): `loaded` (js/css URL sets), `callbacks`
  (classId -> fn[]), `componentData` ("classId:varsHash" -> data), `pendingCalls`. Element
  association is one-way and lazy: the runtime finds an instance's elements by attribute selector
  at call time; it keeps no element -> instance registry, no live-instance list, and exposes no
  reverse lookup.
- `<template c-render-id="...">` placeholders exist only during serialization
  (`serialize.py:163-217`) and do not survive into delivered HTML.

## 3. Fragments end to end

**Server API.** A fragment is `render().serialize(deps_strategy="fragment")`
(`emission.py:115-116, 435-470`). Output = the HTML (with `data-cid` / `data-ccss` markers intact),
followed by two script tags appended at the end:

1. A **pre-loader**: if `globalThis.Citry` is missing, inject `<script src="<prefix>/citry.js">`,
   then remove its own tag (`emission.py:376-394`; asserted in
   `tests/test_deps_fragments.py:71-78`).
2. A **JSON manifest** `<script type="application/json" data-citry>` with base64-armored fields
   (`emission.py:401-432`): `markLoaded` (empty for fragments), `fetch` (js/css lists of
   `{tag, attrs, content}` descriptors, `types.py:147-155`), and `calls`
   (`[[classId, componentId, varsHash|null], ...]`). Component and variables scripts ride as cache
   URLs (`cache/<class_id>.<js|css>`, `cache/<class_id>.<vars_hash>.<js|css>`); local-file
   `Dependencies` entries ride as inline content descriptors; pre-rendered `__html__` entries are
   rejected loudly (`emission.py:460, 482-492`; `tests/test_deps_fragments.py:39-112`).

**Mount contract.** Fragments hard-require a mounted web integration: `_emit_fragment` raises
`RuntimeError` with guidance when `citry.mounted_prefix is None` and there are records
(`emission.py:449-458`); a fragment with no asset-bearing components needs no mount
(`emission.py:449-450`). Adapters' `mount()` both register routes and record the prefix
(`citry/contrib/fastapi.py:30-36`; `Citry.set_mounted_prefix` / `build_url` at
`citry/citry.py:302-331`; `set_mounted_prefix` is the escape hatch for render-only workers).
Routes served (GET only): `cache/{class_id}.{script_type}`,
`cache/{class_id}.{vars_hash}.{script_type}` (more specific first, first-wins matching),
`asset/{file_name}`, and `citry.js` (`citry/extensions/dependencies/routes.py:105-121`;
`citry/util/routing.py:128-141`). Class scripts lazily repopulate the cache on miss; variables
scripts cannot and 404 when absent (`routes.py:79-87`, `scripts.py:120-137`), hence the
shared-cache requirement for multi-worker fragments (`docs/design/dependencies.md:521-533`).

**Client insertion.** Citry does NOT insert fragments. The host page does (HTMX swap, `fetch` +
`innerHTML`, etc.; `docs/design/dependencies.md:478-480`, `citry/citry_render.py:152-153`). The
runtime reacts after insertion: the MutationObserver sees the manifest tag (JSON is inert under
`innerHTML`, which is the whole point, `client/citry.js:22-27`), then `loadComponentScripts` marks
`markLoaded` URLs, appends `<link>`s to `<head>` and `<script>`s to `<body>` for the `fetch`
descriptors, deduping by URL against what the page already loaded (`client/citry.js:165-189,
83-108`), and queues the `calls`. The e2e tests prove the full path against a live WSGI server
(`tests/e2e/test_fragment_e2e.py:41-62`; dedup against a document page's `markLoaded`:
`test_fragment_e2e.py:65-151`; harness at `tests/e2e/conftest.py:84-113`).

**Document-side half of the contract.** A mounted `document` page ships the runtime by URL plus a
`markLoaded` manifest naming its inlined scripts' cache URLs whenever it has calls OR mounted
component assets (`emission.py:140-149`), so later fragments fetch nothing already present
(`tests/test_deps_fragments.py:195-229`). Pages with neither stay lean: no runtime, no manifest
(`emission.py:144-145`, `tests/test_deps_fragments.py:231-245`,
`tests/test_deps_vars.py:251-261`). `simple` strategy is the no-runtime mode (component JS still
emitted, but nothing registers or calls it; CSS variables still work,
`tests/test_deps_vars.py:264-290`).

## 4. What the runtime and engine expose for extension

**Client side: nothing beyond the manager.** The public surface is exactly
`globalThis.Citry.manager = { registerComponent, registerComponentData, callComponent, loadJs,
loadCss, markScriptLoaded, isScriptLoaded, _loadComponentScripts }` (`client/citry.js:217-227`).
There is no client-side event bus, no `CustomEvent`/`dispatchEvent` anywhere, no lifecycle hooks
(mount/unmount), no plugin registration, no configuration object. The only listeners are
`DOMContentLoaded` and the manifest MutationObserver. The double-load guard returns early if
`Citry.manager` exists (`client/citry.js:34-36`).

**Server side, three real seams:**

1. **Source rewrite at cache time**, the `$onComponent` precedent (`scripts.py:56-66` inside
   `cache_component_js`, `scripts.py:75-93`). A `$sendEvent` magic implemented as a source rewrite
   would live in the same place, but note this transform is owned by the dependencies extension's
   caching, not exposed as a hook.
2. **`on_js_loaded` / `on_css_loaded` extension hooks**: every extension can transform a
   component's JS/CSS content when it is first loaded (`citry/extension.py:515-521`, fired from
   `citry/assets.py:272-274`, result-threaded via `emit(..., result="map")`,
   `extension.py:719-773`). This runs BEFORE the dependencies extension caches and rewrites, so an
   Events extension could expand its own `$`-sugar here without touching the dependencies code.
3. **`on_dependencies` custom hook**: mutate the final script/style tag lists at serialize time,
   for both documents and fragments (`emission.py:61-78, 131-135, 463-466`). An Events extension
   could append its own client-runtime `Script` here; URLs added here are also marked as loaded in
   the document manifest (`emission.py:146-147`).

Plus the general machinery an Events extension stands on: `Extension.urls` route contribution
(user extensions namespaced under `ext/<name>/`, built-ins at the prefix root,
`citry/extension.py:390-401, 660-685`), `URLRoute.methods` supporting non-GET
(`citry/util/routing.py:78`; adapters return 405 otherwise, `contrib/asgi.py:88-89`,
`contrib/wsgi.py:49-50`, tested at `tests/test_contrib_fastapi.py:74-80`), and the design doc's
fixed slot for Events: per-component routes through `Extension.urls`, handler shaped as
`MyComp(**inputs).render().serialize(deps_strategy="fragment")`
(`docs/design/dependencies.md:641-663`).

**How to inject a `$sendEvent` into component JS scope.** Two grounded options, matching what
exists:

- **Callback-payload property** (per instance): extend the object passed at `client/citry.js:151`
  to `{ id, els, data, sendEvent }`. This scopes the magic to `$onComponent` callbacks, gets
  instance identity for free, and needs no source rewrite. It is the only per-instance scope the
  runtime has.
- **Global + rewrite** (anywhere in component JS): a `Citry.events.send(...)` global plus a
  `$sendEvent(` -> `Citry.events.send("<class_id>", ` rewrite via `on_js_loaded` or the cache-time
  transform. Caveat: component JS executes in two different scopes today, IIFE-wrapped when
  inlined (`Script.wrap` defaults true, `types.py:212-223, 248-258`) but raw and unwrapped when
  served from the cache endpoint (`routes.py:88` returns `script.content` directly), so any scope
  trick must not rely on the wrapper being present.

## 5. Gaps for Events (what is missing)

1. **No client transport.** The runtime performs zero HTTP itself; it only creates `<script>` /
   `<link>` elements (`client/citry.js:71-108`). No `fetch`/XHR/WebSocket, no CSRF token handling,
   no header or body serialization, no retry/error surface. The e2e pages hand-write their own
   `fetch` (`tests/e2e/test_fragment_e2e.py:31-35`). $sendEvent needs a transport client built
   from scratch (or a documented HTMX-style delegation).
2. **No response dispatch or swap/morph.** Nothing client-side inserts server HTML into the DOM;
   insertion is explicitly the host page's job (`docs/design/dependencies.md:478-480`). There is
   no morphdom/idiomorph equivalent anywhere in the package (grep for morph/innerHTML confirms
   only prose mentions). An Events round trip (send event -> receive fragment -> update DOM) has
   no client half; only the "after insertion, load deps and run JS" tail exists via the manifest
   observer.
3. **No client lifecycle or teardown.** One callback invocation per manifest call; no unmount when
   elements leave the DOM, no de-registration of callbacks or data (both Maps grow
   monotonically), and no way to re-run a callback for re-inserted content except a new manifest.
   $onEvent listener cleanup semantics would be entirely new machinery. Also, the design doc lists
   a stuck-call console warning as part of the runtime (`docs/design/dependencies.md:507`), but
   `citry.js` does not implement one; a call whose script never arrives waits silently in
   `pendingCalls` forever.
4. **No server-side instance addressability.** After serialize, an instance exists only as four
   strings in a `DependencyRecord` (`types.py:45-63`); no state store maps a `component_id` back
   to inputs. An Events handler can be class-addressed (`class_id` -> class,
   `citry.py:333-345`) and must reconstruct or re-receive inputs; instance-addressed events need
   new state (or client-supplied payloads).
5. **Request/response shapes are minimal.** `RouteResponse` is content/content_type/status only,
   no headers, no redirects, no streaming (`util/routing.py:42-53`); handlers receive an opaque
   `request` that citry never reads (`util/routing.py:12-14`), so body/query/file parsing for
   event payloads is unsolved in the framework-neutral layer. All current routes are GET; the
   `methods` field exists but nothing exercises POST handlers yet.
6. **Fragment script execution order is not guaranteed.** `loadComponentScripts` fires `loadJs`
   per descriptor without chaining promises, and injected `<script src>` elements never set
   `async = false` (`client/citry.js:174-180, 83-98`), so several fetched scripts may execute in
   completion order. The manager's own register/call machinery is deliberately order-independent
   (`client/citry.js:137-139`), which contains the risk for component JS/data, but a vendored lib
   that component code needs at execution time has no ordering guarantee. Any Events client
   runtime delivered through this path must be self-contained and order-independent too.
7. **Inline vs served scope asymmetry** (detail of gap area, repeated for visibility): document
   inlining IIFE-wraps component JS, the cache endpoint serves it unwrapped
   (`types.py:256-257` vs `routes.py:88`); top-level names leak to `window` only in the fragment
   path.

## 6. Small factual notes for the design doc

- Runtime file is plain readable JS shipped as package data; the TypeScript + minified
  `packages/js/citry-client` build is still an open loose end
  (`docs/design/dependencies.md:3-6, 898-901`).
- The manifest and all string fields inside it are base64-armored so no value can break out of the
  script tag; verified round trip in `tests/test_deps_vars.py:102-117`.
- `js_data()` without component JS produces no vars hash and delivers nothing
  (`scripts.py:175-176`, `tests/test_deps_vars.py:119-134`); same rule for CSS
  (`scripts.py:207-208`).
- Identical `js_data()` across instances shares one cached script and one browser fetch
  (`scripts.py:152-161`, `tests/test_deps_vars.py:66-79`).

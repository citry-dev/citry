# Recon: citry history and prior decisions constraining the Events extension

Scope: decisions already made in citry's design docs, status notes, and archived
cursor chats that constrain or feed the `Component.Events` / server-interactive
extension design. Every load-bearing claim cites file:line. Paths are relative
to `/Users/mac/repos/citry/` unless absolute.

---

## 1. The mandate (extensions_roadmap.md section 3)

The row "Server-interactive / reactive components"
(`docs/design/extensions_roadmap.md:62`) is the charter. Its binding decisions:

- **One extension, one design exploration.** "This is a **single design
  exploration**, not several features." It must weigh **HTTP vs WebSocket
  transport** and the **Tetra / Alpine / live-components / `Component.View` /
  `Component.Events` approaches together**, aiming for "one extension shape
  that supports all of them."
- **`Component.Events` is a named part of it**: "handlers named by the event
  they handle, multiple endpoints per component."
- **The Alpine scoped-slot mechanic is also in scope**: "client-side slot data
  via `x-teleport`, scopes mirroring component isolation." This is the only
  place in the design docs where `x-teleport` appears (verified by grep across
  `docs/design/`).
- **Seams already built** and expected to be stood on: `Extension.urls`, the
  fragment delivery strategy, the mount contract (`dependencies.md` section
  9.5).
- **"Needs its own design doc."** Also stated at
  `docs/design/migration_djc.md:150` and `docs/design/dependencies.md:661`.
- **Feeder work must not be built separately**: "The old `Component.View` /
  `url` extension and the Vue-plugin prototype feed this; do not build them
  separately."

Supporting roadmap decisions:

- **Section 4, open hooks** (`extensions_roadmap.md:73-91`): parse-time tag
  hooks (`on_tag_*`) and resolved-input hooks exist only if the **Alpine
  slot-context piece** concretely requires them; "decide while building ...
  do not add speculatively" (`:81-85`). Asset post-process hooks
  (`on_js_postprocess` / `on_css_postprocess` / post-render
  `on_template_postprocess`) are built when the first consumer lands; "the
  reactive extension's whole-HTML wrap" is one of the three named candidate
  consumers (`:86-91`, echoed at `docs/design/asset_compiler.md:308`).
- **Section 6, decided-against list**: the DJC `url` extension is "subsumed by
  the reactive / `Component.Events` work in section 3"
  (`extensions_roadmap.md:135`). Vue "feel" transpilers and a Vue SFC loader
  are rejected ("citry's V3 syntax is already Vue-like"), but "the Alpine slot
  mechanic survives, inside the reactive extension" (`:137`). An **htmx
  component pack is explicitly out of scope** (`:138`), so Events is not an
  HTMX wrapper, even though fragments target HTMX-style insertion.
- **Section 7, sequencing** (`extensions_roadmap.md:143-153`): Cache and Scoped
  CSS come first; the reactive/interactive extension is "its own design-doc
  track because it is the largest and the most cross-cutting"; the open hooks
  of section 4 are decided *while* building it, not before.

---

## 2. Per-file migration verdicts (migration_djc.md)

The migration doc records the fate of every django-components file. Verdicts
relevant to Events:

### `extensions/view.py` (415 lines upstream)

- `ComponentView` (`Component.View` with `get`/`post`/..., `as_view()`):
  **dropped for API shape**. "The HTTP-method-named handler API is not ported;
  the concept returns redesigned as `Component.Events`"
  (`docs/design/migration_djc.md:1099`).
- `get_component_url()` / public view auto-registration: **to migrate
  (later)**. "Returns with the `Component.Events` design, on `Extension.urls`
  + the fragment strategy" (`migration_djc.md:1100`).

### The planned-features row (the redesign rationale)

`migration_djcd:150` states the motivating failure: "DJC's `View` forced
every action onto an HTTP-method name, which broke down when one component
backed several mutations (one had to go under `post()`, another under
`patch()`)." The redesign: handlers named by the event they handle
(`Events.submit()`, `Events.delete()`, ...), and "each handler declares what it
accepts (query args, request body, file upload, eventually websocket events)."
`dependencies.md:658-661` adds "with a route derived per event."

### URL handling

- `urls.py` (Django URL mounting): **superseded**. Citry owns the combined
  route table (`Citry.urls`); Django mounting became the
  `citry.contrib.django` adapter (`migration_djc.md:740`).
- `URLRoute` / `URLRouteHandler`: **ported** to `citry/util/routing.py`, plus
  `RouteResponse`, an explicit `methods` field, `{param}` paths, and a small
  first-wins router shared by the generic adapters (`migration_djc.md:942`,
  detail at `:2846-2851`).
- `format_url` (query params + fragment suffix on a URL): **ported** to
  `citry/util/misc.py`, and explicitly earmarked: "a future component-URL
  builder is its first caller" (`migration_djc.md:859`). The Events URL
  builder is that caller.
- `add_extension_urls` / `remove_extension_urls`: **reshaped** into
  `Extension.urls` combined into `Citry.urls`, user extensions namespaced
  under `ext/<name>/` (`migration_djc.md:430`).

### Dependencies / fragments

- Six DJC strategies reduced to four + positions:
  `serialize(deps_strategy="document"|"simple"|"fragment"|"ignore",
  deps_position=...)` (`migration_djc.md:348`, `:487`;
  `dependencies.md:360-383`). Strategy lives at serialize time, not context
  state.
- The client runtime was **rewritten, not ported**: `globalThis.Citry.manager`,
  `$onComponent` callbacks called with `{id, els, data}` per instance via
  `data-cid` markers, `data-citry` JSON manifests base64-armored
  (`migration_djc.md:493`).
- Fragments are **built end to end** (phase 4, `migration_djc.md:2831-2906`):
  manifest `fetch` lists are `{tag, attrs, content}` descriptors; a fragment
  whose components carry no assets needs no mounted integration; one with
  assets raises a pointed `RuntimeError` when unmounted; pre-rendered
  (`__html__`) entries are rejected loudly in fragments (`:2871-2880`). The
  documented interim pattern for serving a component over HTTP is a user
  route: `Table(rows=rows).render().serialize(deps_strategy="fragment")`
  (`:2890-2901`).
- **Caching lesson that carries into Events**: caches must store
  `CitryElement`/`CitryRender` **objects**, never HTML strings, because string
  caching freezes render ids and js/css hashes (`migration_djc.md:729`,
  `:1085`, djc #1650). Any Events-side response caching inherits this rule.

### Interactivity, Alpine, Vue plugin, websockets in the migration doc

The migration doc itself contains **no Alpine or Vue-plugin verdict rows and no
websocket design** (grep verified); its only websocket mention is the
"eventually websocket events" clause in the Events row
(`migration_djc.md:150`). The Alpine/Vue material lives in the roadmap row
(section 1 above) and the archived chats (section 7 below).

---

## 3. The surfaces Events stands on (dependencies.md)

### Section 9.5: the fixed design slot (`dependencies.md:641-663`)

- Serving components over HTTP is "the natural companion of fragments ('a URL
  that serves a fragment')". It was deliberately **not** in the dependencies
  package's first build, "but the design slot is fixed: a future extension
  declares per-component routes through the same `Extension.urls` surface
  (`ext/<name>/<class_id>/...`), and its handler is two lines on top of this
  package" (`:646-649`).
- The dependencies package "only guarantees the surfaces it will stand on
  (`Extension.urls`, the fragment strategy, the mount contract)" (`:661-663`).
- The FastAPI test app doubles as the worked example of the interim pattern
  (`:650-651`).

### The mount contract (`dependencies.md:594-616`)

- Each adapter's `mount()` registers routes **and** records the mounted prefix
  on the `Citry` instance; URL building formats `prefix + route path`;
  building with no mounted prefix raises with guidance (`:605-608`).
- A `CitrySettings.url_prefix` setting was **considered and rejected**
  (settings are frozen at construction; mounting happens later and elsewhere)
  (`:610-616`). `set_mounted_prefix(...)` is the escape hatch for render-only
  processes. Events URL generation must go through this same contract.

### Fragments and the client manager (`dependencies.md:473-532`)

- A fragment targets HTMX swap, Unpoly, Turbo, `fetch` + `innerHTML`, jQuery
  `.load()` (`:477-479`). Its payload is a pre-loader script plus an **inert
  JSON exec manifest** (`<script type="application/json" data-citry>`,
  base64-armored) that a MutationObserver ingests, so it works however the
  HTML is inserted, including `innerHTML` where scripts do not execute
  (`:482-491`).
- Client runtime API (`:498-507`): `registerComponent(classId, fn)`,
  `registerComponentData(classId, hash, data)`, `callComponent(classId,
  componentId, varsHash)`; calls queue until script and data arrive, then run
  against elements matching `[data-cid-<componentId>]`; `loadJs`/`loadCss`
  from descriptors; `markScriptLoaded`/`isScriptLoaded` keyed by URL.
- **Operational constraints that propagate to Events endpoints**
  (`:521-532`): fragments hard-require a mounted web integration, and
  multi-process deployments need a **shared cache** (variables scripts are
  written by one worker, served by another; class scripts self-heal, variables
  scripts cannot). Both failure modes get explicit errors, a house pattern
  Events should follow.
- Routing surface layout (`:546-554`): `<prefix>/cache/...`,
  `<prefix>/citry.min.js`, `<prefix>/ext/<extension_name>/...`. Handlers stay
  framework-neutral; logic lives in plain extension methods, adapters wrap in
  a dozen host-specific lines (`:556-561`). Generic ASGI + WSGI apps cover
  almost every host; fastapi/flask/django sugar on top (`:563-588`).

---

## 4. Extension-system decisions that shape Events (extensions.md)

Section 7 (deliberately deferred pieces) and neighbors:

- **`on_component_input` is mutate-only; the short-circuit mechanism is
  deferred** (`docs/design/extensions.md:290-311`). When short-circuiting
  lands, the likely shape is "**not** a core hook but a pair of
  cache-extension-owned custom hooks via `emit()`" (`:313-319`). The governing
  principle: extension-owned lifecycle points are `emit()`-owned custom hooks,
  not new core hooks. Events should own its hooks the same way.
- Short-circuit / post-render return type is `CitryRender | str | None`; the
  struct form keeps deps recoverable, `str` is convenience (`:321-327`).
  Relevant to any Events handler that returns replacement output.
- `Extension.urls` is **built** (`extensions.md:475-485`): framework-neutral
  `URLRoute`s combined into `Citry.urls`; route handlers reach engine state
  through `self.citry` (the manager-set back-reference).
- Per-component nested config is the established pattern: `Extension.Config`
  with weakref back-reference, three-level defaults on a real settings schema
  (`extensions.md:179-243`); `Component.Events` as a nested class follows
  `Component.Cache` / `Debug` precedent (`extensions_roadmap.md:48-50`).
- `Extension.Config` already reserves the `component=None` out-of-lifecycle
  case (for Storybook's render endpoint, `extensions_roadmap.md:66`), a
  precedent for extension code running outside a normal render.

---

## 5. Current state: what is live vs planned (TODO docs)

From `TODO/project_status_june_2026.md` (refreshed 2026-06-22):

- **Live**: the full Python runtime; slots/fills, provide/inject, the
  dependencies system including the browser client and render strategies,
  dynamic components, Const optimization, `on_render` + error bubbling, and
  web integrations for Django, FastAPI, Flask, Starlette, WSGI, ASGI
  (`project_status_june_2026.md:8-19`, `:194-204`). 1,126 Python tests pass
  (`:206`). `citry` runtime is v0.1.0 on PyPI, `citry_core` v1.3.0
  (`:174-193`).
- **Multi-language reality**: only the Python `LangImpl` is real; JS, PHP, Go,
  Rust are structural stubs (`:297-306`); other language bindings are
  longer-term (#27, `:536-537`).
- **Performance decision settled**: the render walk stays in Python (~1.29x a
  bare Django template); the Rust render-walk prototype was measured and
  archived (`:543-567`). No pending plan to move runtime logic to Rust.
- The extension substrate listed in section 1 of the roadmap
  (`ExtensionManager`, name-keyed dispatch, `emit()`, `Extension.urls` with
  contrib mount adapters, `ExtensionCommand` + CLI, `on_attrs_resolved` /
  `on_serialize` / `on_render_context_merge`) is built; **`dependencies` is
  the only shipped built-in extension** (`extensions_roadmap.md:21-31`).

From `TODO/resume_notes_djc_citry.md` (historical context): DJC shipped HTML
fragments for HTMX / AlpineJS / vanilla JS, the extension system with custom
CLI commands and URL routes, and pluggable deps strategies
(`resume_notes_djc_citry.md:85-91`), so the Events design draws on shipped
upstream experience, not speculation. The README north star already showcases
fragments as a user-facing feature (`README.md:432-442`).

---

## 6. Multi-language architecture rules and where Events logic lives

The rule, stated as design intent: "**Extensions are host-language-specific by
design.** An extension hooks runtime lifecycle data, so it lives in the host
language (Python today; JS/PHP/Go later), not in the shared Rust core. The
Rust core shares only the parser, AST, and compiler output. So each live
binding grows its own extension layer; this is the intended shape, not a cost
to remove" (`extensions_roadmap.md:33-37`). CLAUDE.md's high-risk list matches:
the Rust contract is grammar, AST, compiler output, `LangImpl`, PyO3 glue.

Implications for Events:

- **Host language (Python, `packages/py/citry/`)**: the extension class,
  `Component.Events` nested config, handler dispatch, request parsing, route
  declaration via `Extension.urls`, hook definitions via `emit()`.
- **Language-neutral, by precedent**:
  - The **wire protocol**: the `data-citry` JSON manifest format, base64
    armoring, descriptor shapes, and URL layout are already contracts the
    client consumes independent of host language
    (`dependencies.md:482-491`, `:546-554`).
  - The **client JS**: ships today as package data
    (`citry/extensions/dependencies/client/citry.js`); its planned home is
    the monorepo's first JS package, `packages/js/citry-client/`
    (TypeScript, built, minified, vendored into the wheel)
    (`dependencies.md:509-515`). Events client code belongs on the same
    track.
  - **Rust only for shared primitives**: the established precedent is the
    scoped-CSS selector rewrite being "a candidate for the Rust
    `html_transform` layer so JS/PHP/Go can reuse it"
    (`extensions_roadmap.md:49`). If Events ever needs template-level
    knowledge (for example event attributes parsed from templates), that is
    a grammar/AST/compiler contract change and triggers CLAUDE.md Mechanism
    2 (plan mode) and Mechanism 4 (the five `lang/*.rs` impls, PyO3 glue,
    `_rust.pyi`, Python wrapper, both test suites).
- **WebSocket/SSE precedent**: browser live-reload (#9) already sketches the
  push-channel seam: "an extension mounts a dev-only SSE or WebSocket endpoint
  via `Extension.urls` ... and a small injected script reloads on message"
  (`docs/design/hot_reload.md:431-438`; also `:166-169`, "needs net-new
  design"). So `Extension.urls` is the expected surface even for non-HTTP
  transports, but nothing WebSocket-shaped exists yet in the route table or
  adapters (`URLRoute` handlers take `(request, **path_params)` and return a
  `RouteResponse`, `migration_djc.md:2846-2851`); transport beyond
  request/response is genuinely open design work.

---

## 7. Cursor chat archive findings

642 chats searched by filename and content for ninja, events, livewire,
unicorn, tetra, websocket, interactive, alpine, vue, view, get_component_url.
Decision-bearing material:

- **`cursor-chats/chats/2025-03-15_Integrating_Vue_with_Django_and_Rust_72662b58.md`**:
  an interview-transcript article documenting the **Vue-plugin prototype**
  that `extensions_roadmap.md:62` says feeds this design. Key recorded
  choices: reactivity is delegated to **AlpineJS instead of shipping Vue's
  runtime** ("Vue-like interactivity while maintaining control over the HTML
  rendering in Django"); custom utility functions reconstructed Vue's
  `watch` / `computed` / `ref` on top of Alpine's `watchEffect` and a reactive
  object; the long-term goal was writing Vue-style files server-side with an
  escape path to a separate frontend (lines 36-46 of the chat). This is the
  concrete content behind "the Vue-plugin prototype feeds this."
- **`cursor-chats/chats/2025-04-04_Autocomplete_Component_Development_for_Events_d2f6b73a.md`**:
  despite the name (calendar events app), this is a real-world exercise of
  DJC's `Component.View` pattern: a subclassable autocomplete component whose
  subclass "can define `get` and `post` methods", exposed "as views and added
  to urlpatterns with `Component.as_view()`", with AlpineJS client state, a
  3-character threshold, and 150 ms debounce (chat lines 12-27). It is
  first-hand evidence of the usage shape (one component, multiple server
  actions, Alpine on the client) that the Events redesign responds to.
- **`cursor-chats/chats/2026-01-16_Optional_keyword_arguments_for_get_component_url_5b817158.md`**:
  upstream DJC work adding **route parameters to component URLs** via
  `get_route_path` plus `get_component_url(args, kwargs)`, with docs and
  changelog updates. Feed for Events: the URL builder must cover route
  params; citry's ported `format_url` (`migration_djc.md:859`) and
  `{param}` `URLRoute` paths already anticipate this.
- **`cursor-chats/chats/2025-07-31_Define_templates_and_assets_as_separate_files_af17060b.md`**:
  a short Tetra-vs-DJC comparison; records only that Tetra defaults to
  inlining template/JS/CSS in Python while DJC's idiom is separate files. No
  design decision.
- **`cursor-chats/chats/2025-02-20_Creating_a_Pulsating_Overlay_for_HTMX_Requests_3bdf219b.md`**:
  usage-level CSS for an `htmx-request` loading overlay; evidence the
  maintainer's own interactive pattern is HTMX fragment swaps, nothing more.
- **Negative results**: no decision-bearing chat found for django-ninja,
  Livewire, django-unicorn, or websockets. All content grep hits for those
  terms land in unrelated 2026-03/04 side-project chats (orchestrator, socials,
  jurora-write app). The Tetra framework itself appears in the design docs only
  at `extensions_roadmap.md:62` and `docs/design/asset_compiler.md:41,105`
  (its esbuild bundling informed the asset-compiler design). "live-components"
  appears only in the roadmap row.

---

## 8. Constraint checklist for the Events design doc

1. One extension covering serving-over-HTTP and client interactivity; weigh
   HTTP vs WebSocket and Tetra / Alpine / live-components / View / Events
   together (`extensions_roadmap.md:62`).
2. Handlers named by event, multiple endpoints per component, each declaring
   accepted inputs (query args, body, file upload, eventually websocket
   messages), route derived per event (`migration_djc.md:150`,
   `dependencies.md:653-661`).
3. Stand on `Extension.urls` (routes under `ext/<name>/<class_id>/...`), the
   fragment strategy, and the mount contract; do not invent parallel routing,
   serving, or URL building (`dependencies.md:641-663`, `:594-616`).
4. Implementation is Python-only for now; wire protocol and client JS are the
   language-neutral surfaces; Rust involvement only for a shared primitive
   with a proven cross-language consumer (`extensions_roadmap.md:33-37`,
   `:49`; `dependencies.md:509-515`).
5. The Alpine scoped-slot mechanic (`x-teleport`, scopes mirroring component
   isolation) is in scope and is the piece that may justify parse-time hooks;
   decide those while building, not before (`extensions_roadmap.md:62`,
   `:81-85`).
6. The whole-HTML wrap may need the post-render `on_template_postprocess`
   hook; same build-when-needed rule (`extensions_roadmap.md:86-91`).
7. Own custom lifecycle points as `emit()` hooks, not new core hooks
   (`extensions.md:313-319`); per-component config as a nested
   `Component.Events` class on `Extension.Config` with three-level defaults
   (`extensions.md:179-243`).
8. Fragment operational constraints apply to Events responses: mounted
   integration required when assets are referenced; multi-worker needs a
   shared cache; fail with explicit, pointed errors (`dependencies.md:521-532`).
9. Never cache or replay serialized HTML across requests; cache
   `CitryRender` objects (`migration_djc.md:729`, `:1085`).
10. Do not rebuild the `url` extension, `Component.View`, or the Vue plugin
    as separate deliverables (`extensions_roadmap.md:62`, `:135`, `:137`);
    an htmx component pack stays out of scope (`:138`).
11. Sequencing: this extension comes after Cache and Scoped CSS, as its own
    design-doc track (`extensions_roadmap.md:143-153`).
12. Process: CLAUDE.md Mechanism 1 (prior-art header) applies to the design
    doc; Mechanism 2 (plan mode) and Mechanism 4 (cross-binding audit) apply
    if the design touches grammar, AST, compiler output, `LangImpl`, or PyO3
    surfaces.

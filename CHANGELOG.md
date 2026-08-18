# Release notes

## v0.4.0

_Beta release · 18 Aug 2026_

Citry v0.4.0 is the first beta release! 🎉

The Citry API is now mostly stable. There might be occasional bugs and minor API breakages.

### Added

- Configure CSP compatibility, JavaScript delivery, script integrity, and per-response nonces; strict mode ships an Alpine CSP runtime and rejects incompatible output.
- Build server and browser localization with Fluent catalogs, locale fallback, typed `tr()`/`fmt`, `<c-i18n>`, `<c-trans>`, `$i18n`, `$c-tr`, strict localized input, time-zone/DST handling, and coverage/extract/check/compile/inspect commands.
- Analyze Citry, Python, Alpine, JavaScript, CSS, and Fluent in editors through portable catalogs, source maps, diagnostics, completion, hover, and definition lookup.
- Run `citry check --static` or `citry --app module:attribute check` with stable finding codes and deterministic JSON output.
- Run `citry format` on Citry templates and conservatively discovered Python, JavaScript, and CSS assets, with check/diff modes and explicit Biome providers.
- Format definite inline component assets programmatically with `format_python_templates()`, `prepare_python_component_assets()`, `finish_python_component_assets()`, and `format_python_component_assets()`.
- Seed every component Alpine scope directly from `js_data()`; equal wire payloads still produce independent nested state per instance and refresh safely on rerender.
- Supply explicit root context with `render(provides=...)` and pass existing values unchanged with `provide(key, value)`.
- Configure shared and component-specific lint severity/types with `LintSettings` and `Component.Lint`.
- Use `citry.ext.i18n.make_context()`, `citry.Markup`, `citry.SecurityError`, and the typed public `Component.Events` contract.
- Inspect registry-complete component metadata with `Citry.template_analysis()`, portable catalog serialization, declaring-module provenance, and conservative asset ownership fingerprints.

### Changed

- Declared `TemplateData`, `JsData`, and `CssData` schemas now return their normalized defaults and coercions to templates and extensions.
- Inline `template`, `js`, and `css` declarations now remove shared Python indentation; file-backed assets remain byte-exact.
- Tag identity is now explicit: lowercase `c-`, case-insensitive component suffixes and HTML tag/attribute identity, but case-sensitive component inputs, slots, State fields, handlers, and custom events.
- Event modifiers follow dispatched-event capabilities: `.prevent` works for cancelable custom names and `.enter`/`.escape` filter any keyed event.
- `<select multiple>` State values are now `list[str]`, while custom-element State uses the element's typed `value` property in both directions.
- `:c-*` now accepts editable native controls or custom elements only; unsupported/unknown input types fail explicitly and recover safely after live type changes.
- Literal Events bindings are compiled from parser-proven attributes, so binding-shaped text in raw/comment/verbatim bodies stays literal.
- `<c-element>` validates State against its resolved HTML tag and attributes dynamic bindings to the lexical authoring component.
- `#c-key=None` now omits the key for that render; `False`, `0`, and `""` remain keys.
- Browser handler state is callable: `$error.message` becomes `$error()?.message`, with matching `error(name?)` and `loading(name?)` callback accessors.
- `actions.Data` always waits for its caller; `wait=False` now raises `ValueError` and the wire format omits `wait`.

### Fixed

- Component `#c-key` and `#c-ignore` now protect complete comment-delimited component ranges, including multi-root, rootless, transparent, keyed, and moved output.
- HTML `@c-*` bindings now receive non-bubbling native/custom events on their owning element with correct `.stop` and synchronous `$event.currentTarget`.
- Python 3.14 retains typed `TemplateData`/`Kwargs` source and C3-composed schema behavior.
- JavaScript/CSS formatting now handles final newlines, quote/escape variants, CRLF/lone-CR output, bounded streams, timeouts, and Windows cleanup without partial edits.
- Python comments inside `{{ ... }}` no longer consume apostrophes/braces or the host `}}` delimiter.
- `LibraryComponent` now exposes the complete public `Component` type surface in editors and static checkers.

## v0.3.1

_29 Jul 2026_

### Fix

- Event handlers now work when Citry is installed from PyPI. In 0.3.0 the
  browser runtime that Citry serves for `Events` was left out of the published
  package, so a page with an event handler loaded a script the server could not
  produce, and the call never reached Python. Upgrade to use `Events`; no code
  change is needed.
- `format_attrs()` now omits empty `class` and `style` values produced by
  `merge_attrs()`, matching hand-built structured values.
- `<c-error-fallback>` now escapes ordinary fallback strings. Use a fallback
  fill when the fallback needs markup.
- `$component()` is now recognized only as a live call expression. Matching
  text inside strings, comments, template-literal text, regular expressions,
  and function or method declarations no longer activates Citry's browser
  runtime or gets rewritten as a component callback.
- A configured extension instance can no longer be silently moved from one
  `Citry` engine to another. Pass the extension class or create a fresh
  instance for each engine. A failed engine construction restores the
  instance's previous owner.
- `citry create` now scaffolds both `Kwargs` and `Slots`, and relies on Citry's
  default template data instead of generating a redundant data method.

## v0.3.0

_28 Jul 2026_

### Breaking changes

- The built-in extensions package is now `citry.ext`: anything
  you imported from `citry.extensions.*` now lives at `citry.ext.*` (for
  example `from citry.ext.dependencies import Script`). The
  `Citry(extensions=[...])` setting is unchanged.
- The six JS/CSS dependency types (`Script`, `Style`,
  `CitryDependencies`, `Dependency`, `DependencyRecord`, and
  `OnDependenciesContext`) are now importable only from
  `citry.ext.dependencies`, so `from citry import Script` stops working. The
  one-line fix: `from citry.ext.dependencies import Script` (and likewise for
  the other five).

### New features and fixes

- Added a `Citry(mode="production" | "development")` setting (production by
  default) that selects the build environment. It is the single source of truth
  for developer-only output; today, in development the client ownership graph
  carries source provenance that production omits. An unrecognized `mode` value
  is rejected at construction.
- Fixed: a `@c-<event>` handler for a custom event whose name begins with
  `poll` (for example `@c-pollchange`) rendered fine on the server but made
  the browser reject the page's whole ownership manifest, so client behavior
  never activated. The browser now treats only the exact `@c-poll.<interval>`
  form as polling, matching the server.
- The `citry-client-graph/1` protocol package now ships a full golden-fixture
  corpus (valid and invalid manifests with a machine-readable index), and its
  reference validator rejects four manifest defects it previously accepted:
  component-tag client-binding payloads under the wrong binding key, nested
  component parent regions naming
  no region, one render id reused across graphs, and instance-ancestry
  cycles. Manifests the Citry server emits already satisfied these rules;
  they matter for hand-built or third-party manifests.

- Slot outlet data now arrives at fills as an immutable, slotted `SlotData`
  record. Identifier keys support attribute access while the mapping interface
  remains available for unusual keys and names that collide with mapping
  methods. `<c-fill data="...">` also supports one-level destructuring,
  `source as target` aliases, and a final `**rest` binding, with parse-time
  identifier, duplicate, ordering, and variable-shadowing validation.
  Parameterized `SlotInput[T]` declarations also validate explicit
  destructuring sources against `T`'s fields when the effective slot name and
  data binding are static, while dynamic or unresolved shapes retain the
  runtime missing-field check.
- Added first-class component-library publishing. Package authors can define
  inert `LibraryComponent` classes in an explicit `ComponentLibrary` manifest,
  and applications can install the package into each engine with
  `Citry.register_library()`. Imported definitions support direct template tags
  after registration and contextual Python composition through the exact
  per-Citry installation. Catalog classes and installation records publish and
  roll back atomically, repeated registration is idempotent, `clear()` retires
  old handles, required extension names are validated before class creation,
  and module-relative assets and component declaration inheritance are
  preserved during per-engine materialization. Ordered manifest inputs are
  enforced, failed installation removes loaded-file index entries, public
  publishing annotations resolve for introspection tools, and static checkers
  see the normal `Component` instance-authoring methods on inert definitions
  without treating those definitions as concrete `Component` classes.
- Nested component declarations now inherit automatically through the
  component class's C3 MRO. Child `Kwargs`, `Slots`, data-output schemas,
  extension config classes, Events, and State declarations add to their
  parents without explicitly naming the parent nested class; nearer fields,
  methods, and handlers win. Assigning the nested name to `None` resets that
  component-level inheritance, while a nearer declaration can reopen the
  chain. Dependencies keeps its branch-based merge while accepting reusable
  definition bases and preserving their module-relative asset provenance.
  Cross-branch schemas preserve a consistent frozen dataclass mode and reject
  incompatible adapter families, mixed frozen modes, NamedTuple branches, and
  multiple slotted dataclass layouts instead of silently losing fields.
  Concrete nested declarations are immutable after class creation,
  and extension `class_name` values must be valid, unique, and non-reserved.
  Extension class-created hooks can inspect the
  exact authored chain through `ctx.nested_declarations(name)`, whose
  `NestedClassDeclaration` records retain source classes even after Citry
  builds the effective runtime config.
- Added the runtime-checkable `ComponentLike` protocol for context-dependent
  Python composition. A third-party value can implement
  `__citry_element__(citry)` and render through `{{ ... }}`, slot content, or
  `Component.on_render` while preserving the active Citry instance,
  provide/inject scope, dependency collection, and component ownership.
  Resolution is single-step and rejects non-elements and elements associated
  with another Citry instance; there is no global fallback outside a render.
- Added `Component.unprovide(key)` for compound-component boundaries. The
  current component can still inject the inherited payload, descendants see
  the key as missing, and a nearer provider can establish a fresh value.
- Added rendered client context through `$component`'s `provide`, `inject`,
  and `unprovide` helpers plus Alpine's `$provide`, `$inject`, and
  `$unprovide` magics.
- Fixed dependency declarations and delivery at their edge cases:
  whitespace-only `Component.js`/`css` no longer creates fragment URLs that
  return 404, mixed-case inline closing tags are rejected safely, unhashable
  pre-rendered `__html__` entries de-duplicate and emit normally, and invalid
  `Dependencies.css` media values now identify the media key and component.
- Added opt-in output caching through per-component `Component.Cache` and the
  reserved, transparent `<c-cache>` fragment component, with
  typed effective-kwargs variation, custom `Cache.vary()`, strict Slot-source
  handling, TTL and version controls, detached subtree replay, and exact-key
  deletion. Hits keep current-call ownership and fresh descendant identities,
  notify observers only after ownership settles, and expose safe DEBUG
  diagnostics without retaining live render state. Fragment bodies preserve
  current Slot-writer ownership and replay dependency and Events payloads with
  fresh descendant identities. Active Debug highlighting conservatively
  bypasses render caching.
- Hardened render-cache replay and untrusted entries. A literal `<c-slot>`
  nested inside `<c-cache>` now preserves a caller fill through transitive Slot
  writers, including nested components. Stale CSS-variable payloads are
  rejected when the current component has only whitespace CSS, then rerendered
  and overwritten without leaking markers or repair writes. Artifact strings
  and object keys must be valid UTF-8, multibyte limits use encoded byte size,
  and deeply nested or malformed entries fail as controlled cache misses rather
  than serialization or recursion errors.
- Component class garbage collection now invokes no Citry lifecycle operation,
  registry mutation, cached-body eviction, or extension callback, preventing a
  finalizer from blocking on a lock held by the code it interrupted. Extensions
  perform deterministic cleanup for explicit component removal in
  `on_component_unregistered`, while weak indexes continue to discard collected
  classes automatically. `Citry.clear()` remains a bulk teardown and emits no
  per-component unregistration hooks. The unsafe GC-time
  `on_component_class_deleted` hook and its
  `OnComponentClassDeletedContext` have been removed; extensions must move
  cleanup to `on_component_unregistered`.
- Added exact render-cache key helpers at `citry.ext.cache`, with typed,
  bounded canonical variation encoding and explicit local or deployment-shared
  key scopes. Cache engine defaults now validate at `Citry` construction.
  First-party cache backends apply one strict TTL contract, the in-memory LRU
  is thread-safe, and Redis fractional TTLs round upward. Mutations from
  `on_component_input` now pass through final typed kwargs and Slots validation
  before component data methods run, with defaults and factories evaluated
  once.
- Citry instances and component class generations now expose stable
  process-lifetime identity tokens for exact same-process metadata joins. The
  new frozen component-introspection records provide validated schema, asset,
  extension, and canonical JSON value shapes for tooling integrations. Shared
  dataclass field discovery now follows constructor inputs by accepting
  `InitVar` fields and excluding `init=False` fields. You can query registered
  component definitions with `Citry.inspect_component()` and
  `Citry.inspect_components()`, including optional path resolution and portable
  schema defaults, without loading or compiling component assets. Runtime
  component identities are immutable even during class-created hooks, and
  dynamically generated class names now produce route-safe `class_id` values.
  Effective schema fields also expose conservative per-field authoring module,
  qualified class, and already-loaded source-file provenance, including the
  distinct declaration owners of C3-composed schemas.
- Component introspection now supports explicitly requested, versioned
  extension metadata. Extension authors can publish allowlisted JSON through
  `Extension.inspect_component()` using `ComponentIntrospectionContext`, with
  failures reported as `ComponentIntrospectionError`. The built-in Events
  projection exposes stable public handler, request-schema, return-type,
  docstring, and client-timing metadata without publishing executable or
  private configuration. The built-in Cache projection exposes effective
  component policy, normalized TTL, lossless tagged versions, variation mode,
  and declaration-level Slot-source possibility without running user code or
  exposing backend scope secrets.
- Added the built-in Events extension: typed server handlers, signed State,
  generated per-event and batch routes, protocol schemas, Alpine magics,
  declarative `@c-*` bindings and forms, queueing, transports, render actions,
  and keyed state-preserving morphs now form one end-to-end client/server
  contract. `State._public` controls client visibility and `State._model`
  controls client writability; a narrowed or empty `_model` now travels in the
  class descriptor so the browser rejects disallowed `$state` writes before
  mutating reactive State or queueing an update. Live descriptor refreshes
  update every instance of the class and discard newly forbidden pending or
  failed-call updates with a warning, while the server remains the authority
  on every call. A mirrored instance self-renders all of its placements while
  preserving each placement's local Alpine state. Concurrent non-blocking
  calls retain accurate busy state, polling and custom transports remain
  stable across runtime startup, and delayed binding flushes protect unsent
  drafts. Browser calls to GET handlers use pasteable per-event URLs, while
  pending two-way writes wait for the next mutating call.
- Events handlers can now return `actions.PushUrl(...)` or
  `actions.ReplaceUrl(...)` to update browser history without navigation, or
  return `actions.Download(...)` from a dedicated `@event(bundle=False)`
  handler to send a file with safe ASCII and UTF-8 filename headers. Download
  saves begin only after the call survives timeout and latest-wins checks.
  Unicode-only basenames now receive a usable `download` ASCII fallback while
  retaining their extension and exact UTF-8 filename.
  Raw `RouteResponse` handlers use the same per-event, unbundled contract and
  must leave State unchanged because their responses bypass the normal result
  envelope.
- Events transports now validate a complete response envelope before applying
  any batch result, including protocol, correlation, result count, shape, and
  epoch echoes. Malformed or mismatched custom-transport responses therefore
  cannot apply an earlier result before a later invalid slot is discovered.
  Server result hooks cannot emit actions outside the client's advertised
  capabilities, and a failing error observer retains the original controlled
  500 response. Compatibility responses also handle non-JSON values without
  leaking a host exception.
- Events data validation now accepts parameterized `Mapping` fields as object
  shapes. Component introspection also excludes the exact deferred
  `typing.ClassVar` spelling from published request fields, and a subclass can
  use any `ClassVar` form to remove an inherited input field.
- `citry inspect --json` now emits the selected engine's compact, versioned
  runtime component catalog for local scripts and CI. It completes normal
  discovery, uses the introspection API defaults, and deliberately has no
  static-analysis fallback. `citry list` now projects the same catalog while
  retaining its merged names, class, path, and built-in rows; catalog ordering
  makes rows and extra manual aliases deterministic.
- Component-catalog `FieldInfo` records now carry optional per-field source
  module, qualified class name, and already-loaded absolute module path. The
  provenance identifies the authored declaration across inherited and
  C3-composed schemas, while generated or otherwise unprovable fields leave it
  absent for conservative editor navigation.
- Client-active pages now share one Citry-owned Alpine instance, including
  pages whose components use Alpine or Component.js without declaring Events.
  `Citry.alpine.beforeStart(callback)` is the supported pre-start extension
  point for Alpine plugins, magics, directives, and data providers. Component
  callbacks also receive a validated `graph` route with distinct render,
  logical-instance, and stable-browser-anchor identities. Duplicate Citry or
  foreign Alpine bundles are diagnosed while the original Citry runtime keeps
  its single startup and permanent hooks.
- Fragment component callbacks now wait for their stylesheets to load, share
  concurrent CSS requests, retry failed loads, and reload a class stylesheet
  after its last-instance cleanup collected the previous link.
- `$c-props` now raises during rendering when its final resolved target has no
  `$component(...)` registration, instead of shipping an ownership manifest
  for a browser no-op. The check follows runtime `<c-component>` selectors to
  the actual target and also rejects stale detached cache replays before
  extension staging; a final `None` or `False` still removes the binding.
- Client component boundaries now support declared reactive `$c-props`,
  parent-scoped Alpine and `@c-*` handlers, exact call-site scope for supplied
  slot content, receiver scope for fallback content, multi-root listener
  groups, and rootless lifecycle ownership. Client-active deployment must
  preserve Citry's ownership manifest, `citry:g1` ownership comments, and `data-cid-*` /
  `data-citry-*` markers through minification and DOM updates.
- Built-in render IDs now use a `c` prefix followed by eight lowercase
  base-36 characters. Custom
  `id_generator` values must contain only lowercase ASCII letters, digits,
  hyphens, and underscores. This prevents distinct mixed-case IDs from
  collapsing onto one `data-cid-*` marker because HTML attribute names are
  case-insensitive; graph and Events consumers reject unsafe wire values too.
- Component autodiscovery no longer crashes when editor or OS junk files sit
  inside a scanned directory. Files and directories with a dot in their name
  (an `.#card.py` editor lock file, a macOS `._card.py` copy, a `.cache/`
  tree, a `card.old.py` backup) are now skipped during the scan, the same way
  underscore-prefixed paths already were, and a dotted directory name hides
  its whole subtree.
- Added the opt-in `citry.ext.debug.Debug` extension for development-time
  component and slot highlighting. It draws labeled blue component boundaries
  and red slot boundaries, configured globally through
  `extensions_defaults["debug"]` or per component with a nested `Debug` class.
  Authored roots keep their Citry markers, transparent components and full
  documents are not wrapped, and embedded renders remain safe when their root
  engine does not install Debug. The wrappers are real DOM elements and are
  intended for inspection, not production or layout-sensitive tests.
- Unregistering a component's final name now releases its cached render body,
  and render-cache keys hold component classes weakly. Fully rendered classes
  can therefore be garbage-collected after plugin unload or hot replacement,
  and their weak file-index entries disappear with them. Replacing a class
  with the same module and name also refreshes its class-level JavaScript and
  CSS instead of serving the retired class's cached assets. Generated class
  asset URLs are content-addressed, so retained old classes and overlapping
  workers cannot overwrite the cached version named by a page. Mixing
  fragments from different deployed versions in one live page remains
  unsupported; use worker draining, version-sticky routing, or a full reload.
- Servers can now call `app.initialize()` before starting request workers to
  complete configured component discovery, built-in registration, and
  parse-time tag-rule construction at a known startup point. Concurrent first
  use or component mutation now raises `CitryLifecycleInProgress` promptly
  instead of exposing partial state; failed initialization remains retryable.
- Failed built-in initialization and component autodiscovery no longer leave an
  engine marked ready with empty or partial component state. Citry rolls back the
  failing registration work and retries on a later lookup. Recursive discovery
  now raises clearly, built-in names remain protected during extension hooks,
  and engine-level mutations keep hooks, class-ID lookup, caches, and discovery
  state synchronized.
- Component classes now have one immutable `Citry` owner. `app.register()`
  supports aliases and re-registration only for classes owned by `app`, and a
  concrete component subclass uses the same owner as its concrete component
  bases. Reusable modules can expose `register_components(app)` to define a
  fresh component tree bound to that Citry instance during startup. Component registration,
  lookup, initialization, and clearing are public through `Citry`; the
  standalone `ComponentRegistry` API and `app.registry` attribute have been
  removed.
- Added `Citry.atomic_registration()` for publishing an additive group of
  component classes as one Citry-owned registry change. An exception restores
  names, class-ID lookup, tag rules, and discovery state without compensating
  unregistration hooks; unrelated extension and Python side effects remain
  outside that rollback.
- Inherited `template_file`, `js_file`, and `css_file` declarations now stay
  anchored beside the class that declared them, so subclasses in another
  module load the correct files. Absolute `PathLike` entries in
  `Dependencies.css` and `Dependencies.js` are treated as local files and
  inlined instead of becoming root-relative URLs. A component whose template
  declares a slot outside its closed `Slots` schema now raises on every render,
  rather than only on the first compilation attempt.
- A tag now accepts one explicit spelling per logical attribute: `x` together
  with `c-x` is a parse error, including typed kwargs, dynamic tag names,
  slot/fill fields, and component-tag client bindings such as `$c-props`,
  `@click`, and `@c-poll.5s` on a nested `<c-*>` tag. Plain-element
  `class`/`c-class` and
  `style`/`c-style` remain accumulating exceptions. `c-bind` can interlace with
  one explicit spelling and repeats in source order because a spread key is
  known only at render time. A slot/fill `c-bind` value of `None` contributes
  nothing, and dynamic duplicate fill names are checked after resolution.
  Bare, empty, and whitespace-only static `is` values on
  `<c-component>` and `<c-element>` are now parse errors, while dynamically
  resolved empty targets retain their runtime errors.
- Mixed static `is="..."` and `c-bind="..."` now stays on the dynamic path for
  `<c-component>` and `<c-element>`, so the rightmost source-order contribution
  selects the real target and void-element validation applies to that winner.
  Dynamic elements also merge every `class` and `style` contribution like a
  statically written element. Runtime-produced HTML attribute names are now
  checked before formatting, so non-string or malformed spread keys raise a
  targeted error instead of emitting broken markup. Component and dynamic tag
  names ending in a newline are rejected too.
- Structural tags now reject attributes they cannot consume: `c-bind` directly
  on `<c-if>`, `<c-elif>`, `<c-else>`, `<c-for>`, `<c-empty>`, or `<c-raw>` is a
  parse error (the same spread remains valid on an element/component carrying a
  control-flow shortcut), and special `c-bind`, `c-is`, `c-name`, and
  `c-required` inputs reject nested-template values when their tag contract
  requires an expression.
- Slot metadata now follows authored source order around one explicit name or
  requiredness provider and any `c-bind` contributions; fill `data`/`fallback`
  variable metadata stays
  conservative after a spread. Bare, empty, and whitespace-only static
  slot/fill names fail at parse time, and template comments surrounded by any
  amount of formatting whitespace no longer create or satisfy an implicit
  default fill. Static slots inside template-valued attributes now propagate to
  the writer component's metadata and closed `Slots` validation.
- Template-valued `c-*` attributes can now render `<>...</>` fragments. The
  grouping delimiters are removed before the nested template is compiled, so
  text, expressions, multiple roots, and nested components render instead of
  raising a parse error. The delimiters must wrap the entire non-whitespace
  value and cannot be mixed with sibling roots. Adjacent real-tag roots need no
  fragment; their boundary detection now follows the grammar's tag-name rules
  and recognizes a final HTML void element instead of relying on a narrower
  hard-coded closing-tag alphabet or a raw `/>` suffix.
- Control-flow shortcut attributes are now validated with the same semantics
  as their explicit tag forms: `c-if`/`c-elif` require expression values,
  `c-for` requires a loop clause, `c-else`/`c-empty` reject values, and orphaned
  or out-of-order shortcut branches are parse errors instead of being lowered
  into invalid runtime nodes.
- Loop and fill no-shadow validation is now lexical and scope-aware. Using a
  newly bound name in its own body is valid, while self-reading loop targets,
  duplicate targets, nested reuse, and collisions with the actual render
  context fail before the binding is applied. Const body caches partition on
  the visible-name set, and const-unrolled loops retain a live binding guard.
- Errors inside nested template-valued attributes now report positions and
  source lines from the complete outer template. Recursive nesting no longer
  double-counts offsets, Unicode prefixes use character columns, and malformed
  nested tags raise `SyntaxError` instead of escaping as a Rust panic.
- Component JavaScript registration is now `$component(...)`; update existing
  `$onComponent(...)` calls when upgrading. The config-object form now uses
  `init` for its callback instead of `handler`. Each component class accepts
  one registration, and a second definition throws an error naming the class.
- Constructing `CitrySettings(...)` directly now applies the same normalization
  and validation as `Citry(...)`: directory entries become absolute `Path`s (a
  relative one raises `ValueError`), and the extension/resolver/codec sequences
  and the `extensions_defaults`/`template_globals` mappings are copied into the
  frozen settings, so editing the values you passed in afterwards can no longer
  change them. Before, only `Citry(...)` applied these.
- Route handlers now receive a framework-neutral request and can set response
  headers. Under every web adapter (ASGI/FastAPI, WSGI/Flask, Django) a
  handler's first argument is a `citry.RouteRequest` with `method`, `path`,
  `query` (repeated keys preserved), case-insensitive `headers`, the raw
  `body` bytes, `content_type`, and `native` (the untouched host request
  object), so the same handler can read a POST body under any framework; a
  handler that ignored its `request` argument keeps working unchanged.
  `citry.RouteResponse` gains a `headers` field of `(name, value)` pairs that
  every adapter forwards to the client (under Django a repeated header name
  raises a pointed error instead, since Django's response object holds one
  value per name). Under the ASGI adapter a handler can
  now be `async def` (it is awaited), and plain handlers run in a worker
  thread so a slow one no longer blocks the event loop; the synchronous WSGI
  and Django adapters reject an `async def` handler with a `TypeError` that
  points at the ASGI adapter as the fix.
- You can now hot-reload component files during development: edit a component's
  `template_file`, `js_file`, or `css_file` and the next render shows the new
  content without restarting the process. Run `citry watch` to watch your
  component directories (or `citry watch --path some/dir`), and install a fast
  native watcher with `pip install citry[watcher-watchfiles]` (or
  `citry[watcher-watchdog]`); a dependency-free polling fallback is built in, so
  `citry watch` works without either. On Django, call
  `citry.contrib.django.enable_hot_reload(citry_instance)` from your
  `AppConfig.ready()` to drive the reloads off Django's own autoreloader; on
  FastAPI or Starlette, pass `citry.contrib.asgi.reload_lifespan(citry_instance)`
  as the app's `lifespan` so the watcher starts and stops with the app. Under the
  hood `citry_instance.invalidate_file(path)` drops the cached template/JS/CSS
  for every component that loaded that file and returns those components (and
  `invalidate_all()` resets every loaded component when a change cannot be pinned
  to one file), so you can call them directly to wire up any other watcher.
  Watcher callbacks receive resolved, de-duplicated paths even when a backend
  reports multiple aliases for the same file.
- You can now define template variables once and have them available in every
  component, instead of returning the same value from every `template_data()`.
  Set them when you build the engine with `Citry(template_globals={...})`, or
  change them on a live instance through `citry.template_globals`, which is a
  plain dict (`citry.template_globals["site_name"] = "Acme"`, `.update(...)`,
  `del citry.template_globals["site_name"]`). The default `citry` instance can
  be configured this way too, after import. You can also set globals for a single
  render with `element.render(template_globals={...})`, layered on top of the
  instance's globals for that render only and reaching every component in it,
  which suits per-request values like the current user without touching the
  shared engine. A component's own `template_data` wins when it returns a key of
  the same name, so globals act as defaults, and a global never has to appear in
  a component's declared `TemplateData`.
- You can now read a component's inputs directly in its template without
  writing `template_data`: by default `template_data` returns the component's
  `kwargs`, so a `Kwargs` field named `title` is available as `{{ title }}`
  with no boilerplate. Returning your own dict from `template_data` still
  overrides the default, and a declared `TemplateData` still validates the
  result. One consequence: a template now resolves an input name ahead of a
  same-named `template_globals` entry, so an input shadows a global of the same
  name (your component's own data wins over globals, the documented
  precedence).
- You can now use the `citry` command line, installed with the package. Scaffold
  a component with `citry create MyButton`, list the components an engine has
  registered with `citry list` (one row per component, with all its registered
  names and the file that defines it, when it has one), and list
  or run the commands your extensions
  provide with `citry ext list` and `citry ext run <extension> <command>`. Point
  any command at a specific engine you built with `citry --app module:attribute
  ...`; the target resolves against your working directory the way ASGI/WSGI
  servers resolve theirs, so `citry --app app:engine list` works from a plain
  project root. Check the version with `citry --version`. An extension declares its
  own commands by listing `ExtensionCommand` subclasses (with argparse-style
  `CommandArg` arguments) in `Extension.commands`; the commands your extensions
  provide then show up under `citry ext list` and `citry ext run`.
- You can now control the per-render component id with `Citry(id_generator=...)`.
  Pass a function (or a `"path.to.func"` import string, or a class that builds
  one) returning the id stamped on each component as it renders, which is handy
  for stable ids in snapshot tests. It must return ids that are unique among the
  components on one page. This does not affect a component's `class_id`.
- You can now have citry import your component modules for you. Point it at your
  component directories with `Citry(dirs=["/path/to/components"])` and the
  modules under them are imported the first time you render a page, so their
  components register themselves without you importing each file by hand. It is
  on by default and does nothing until you set `dirs` (so existing setups are
  unaffected); turn it off with `Citry(autodiscover=False)`, or run it yourself
  with `citry_instance.autodiscover()`. The directories must be importable (on
  your `PYTHONPATH`); a directory that holds components but is not importable
  raises an error that says exactly that.
- `<c-raw>` now works. A `<c-raw>...</c-raw>` block renders its contents
  verbatim, with no template processing inside, so `{{ ... }}`, `{# ... #}`,
  and nested `<c-*>` tags are emitted literally (handy for showing template
  syntax or embedding code samples). It previously failed at render time with
  `No component registered as 'raw'`.
- You can now turn off the expression sandbox with
  `Citry(sandbox_expressions=False)`. Template expressions (`{{ ... }}` and
  dynamic `c-*` attributes) then run as plain Python, which is faster, but the
  checks that block dangerous operations are gone - so only do this when you
  trust every template you render. The sandbox stays on by default, and turning
  it off does not change the output of a successful render.
- Pages built from many components that share a constant value (a theme, a
  layout config) render faster. When a component input is computed entirely from
  constant values - like `<c-Tab c-class="base + '-active'" />` where `base` is
  constant - Citry now treats the result as constant too, so the child component
  can reuse the work it already did for that input, the same as it does for a
  plain literal like `c-class="'tab-active'"`. Inputs that depend on per-render
  data are unaffected.
- Rendering is faster, most noticeably on deeply nested pages: gathering a
  page's JS/CSS dependencies grew with the component tree's depth (work
  repeated at every level) and is now flat, so a large nested page's repeat
  render is several times quicker. Repeat renders are leaner across the board
  too: attribute formatting, HTML escaping, per-component id generation, and
  component construction each do less work per render.
- Flask and Django join FastAPI as supported hosts for citry's endpoints:
  `citry.contrib.flask.mount(app, citry_instance)` and
  `citry.contrib.django.urlpatterns(citry_instance, prefix=...)` (for
  `include()`-ing in your `urls.py`).
- More cache backends: `citry.contrib.caches.RedisCache` and `DiskCache`
  wrap a `redis.Redis` / `diskcache.Cache` you construct, and
  `citry.contrib.django.DjangoCache` reuses any cache your Django project
  already configured. All plug into `Citry(cache=...)`.
- Local-file `Dependencies` entries can now be served instead of inlined:
  set `local_files = "serve"` on a component's `Dependencies` class (or
  globally via `extensions_defaults={"dependencies": {"local_files":
  "serve"}}`) and the file is emitted as a fingerprinted URL
  (`asset/<content hash>.<ext>`), so browsers cache it and fragments
  de-duplicate it. Falls back to inlining when no web integration is
  mounted.
- `URLRoute` and `RouteResponse` are exported from the `citry` package, for
  extensions that declare their own HTTP endpoints (`Extension.urls`).
- HTML fragments now work end to end:
  `serialize(deps_strategy="fragment")` renders a partial for HTMX-style
  swaps (or any `fetch` + `innerHTML` insertion). Nothing is inlined; the
  fragment ends with a JSON manifest of URLs the client-side manager
  fetches, so a component used by many fragments is downloaded once per
  page, and a fragment landing on a page that lacks the manager loads it
  itself.
- You can now mount citry's endpoints (cached component JS/CSS, the client
  runtime) into your web app: `citry.contrib.fastapi.mount(app,
  citry_instance)` for FastAPI/Starlette, or the dependency-free
  `citry.contrib.asgi` / `citry.contrib.wsgi` sub-apps for everything else.
  On a mounted app, `"document"` pages serve the runtime by URL
  (browser-cacheable) and tell the manager which scripts the page already
  has, so later fragments refetch nothing.
- Extensions can now serve HTTP endpoints: declare framework-neutral routes
  on `Extension.urls` (they mount under `ext/<extension name>/`), reachable
  through the same adapters. Every extension instance also carries
  `self.citry` now, the back-reference to its engine instance.
- Multi-worker note: fragments reference per-render variables scripts by
  URL, and the worker serving the URL may not be the one that rendered the
  page, so production setups using fragments with `js_data()`/`css_data()`
  should configure a shared cache backend (`Citry(cache=...)`).
- Per-render data now reaches the browser. In your component's JS, register a
  callback with `$component(({ id, els, data }) => { ... })`: it runs once
  per rendered instance, with the instance's root elements and its
  `js_data()` result. Identical data is sent to the browser once, however
  many instances share it, and values are transported so they can never
  break out of the script tag.
- `css_data()` results become CSS custom properties scoped to the instance:
  the component's CSS reads them with `var(--name)`, backed by a generated
  stylesheet and a `data-ccss-<hash>` marker on the instance's root
  elements. Pure CSS: this works even with the `"simple"` strategy.
- Pages rendered with the `"document"` strategy include citry's client-side
  dependency manager (`globalThis.Citry.manager`) and a JSON page manifest,
  but only when some component actually registered a callback; other pages
  carry no extra JavaScript. The `"simple"` strategy never includes the
  runtime, so per-instance JS does not run there.
- Components' JS and CSS now reach the rendered page: every rendered
  component's `Component.js`/`css` and `Dependencies` entries are collected
  and placed into the final HTML at serialize time. CSS goes before the first
  `</head>`, JS before the last `</body>`; on a page with neither, CSS is
  prepended and JS appended. Inline component JS is wrapped in a
  self-executing function; duplicate dependencies (same URL or same content)
  are emitted once, however many components share them.
- New `<c-js />` and `<c-css />` built-in tags mark exactly where the
  collected scripts and stylesheets go. When the same tag appears more than
  once, the first one (in document order) receives the tags.
- `serialize()` (and `str()` on a render) takes `deps_strategy`
  (`"document"`, `"simple"`, `"ignore"`; `"fragment"` is reserved for the
  upcoming client-side manager) and `deps_position` (`"smart"`, `"prepend"`,
  `"append"`).
- `Dependencies` entries are emitted by type: URLs become
  `<script src>`/`<link href>` tags, local files are inlined, `Script`/`Style`
  objects control the exact tag, pre-rendered tags pass through verbatim. The
  CSS media type (`css = {"print": ...}`) becomes the tag's `media`
  attribute. `get_dependencies()` now returns local files as absolute `Path`
  objects (URLs stay strings).
- Two new hooks adjust the emitted tags: `Component.on_dependencies(scripts,
  styles)` (classmethod, this component's own entries) and an extension-level
  `on_dependencies` (the page-wide lists, after de-duplication).
- New extension hooks `on_render_context_merge` (a nested render's collected state
  merges into its parent; extensions own their slice) and `on_serialize`
  (rewrite the final HTML at the end of `serialize()`).
- You can now plug in a cache backend: `Citry(cache=...)` takes any object
  with `get`/`set`/`delete`/`has` (see `citry.CitryCache`), or a
  `"path.to.Cache"` import string. The default is a per-instance in-memory
  cache (`citry.InMemoryCache`). Citry stores derived content there, starting
  with the processed JS/CSS scripts of the dependency-rendering work.
- New `Component.js_data()` and `css_data()` methods (mirroring
  `template_data()`), with optional typed `JsData` / `CssData` schema classes:
  return per-render variables for the component's JS and CSS. The
  `on_component_data` extension hook now carries `js_data` and `css_data`
  alongside `template_data`. Delivery into the rendered page lands with the
  dependency-rendering emission phase.
- New `Script` and `Style` objects (importable from
  `citry.ext.dependencies`): declare a `<script>` / `<style>` /
  `<link rel="stylesheet">` dependency with exact control over the emitted
  tag, and use them directly as entries in a component's `Dependencies` class.
- Every component class now has a stable `class_id` (e.g. `Table_a1b2c3`),
  deterministic across processes; look classes up with
  `Citry.get_component_by_class_id()`.
- The `<c-component>` built-in tag now works: it renders the component named
  by `is` in its place (`<c-component c-is="comp" />`, where the value is a
  registered name or a `Component` class). All other attributes and the body
  (fills included) pass through to the target. A static `is="MyComp"` is
  resolved at compile time and costs nothing at render.
- New `<c-element>` built-in tag: renders a plain HTML element whose tag name
  is decided at render time (`<c-element c-is="heading_tag">...</c-element>`).
  Any tag name works, custom web components included; void elements (`br`,
  `img`, ...) reject children. A static `is="div"` compiles to the literal
  element. Misspelled *component* names still fail loudly: `<c-component>`
  never falls back to rendering an element.
- The names `component` and `element` are now reserved in the component
  registry for the built-in tags; registering a component under them (e.g. a
  class named `Element`) raises `AlreadyRegistered`.
- `citry_core.template_parser` now exports `HTML_VOID_ELEMENTS`, the HTML
  void-element names, single-sourced from the Rust parser.
- Dynamic attributes on plain HTML elements now work as documented:
  - `c-bind` spreads a dict onto the element (it previously rendered the dict
    as text).
  - A `True` value renders the bare attribute, `False` and `None` omit it
    (previously `disabled="True"` / `disabled="False"`).
  - `class` and `style` accept structured values (string, dict, nested
    lists, like Vue), and when one element gets them from several sources
    the values merge instead of overwriting.
- A tag rejects the static and dynamic form of the same logical attribute
  (`id="form"` together with `c-id="..."`). Plain-element `class`/`c-class`
  and `style`/`c-style` are the accumulating exceptions; conditional
  overrides belong in `c-bind`.
- A dynamic attribute with no value (`<div c-foo>`, `<div c-foo="">`) is now
  a parse error: there is nothing to evaluate, and it almost always means
  you wanted the static `foo` or forgot the value. The control-flow
  shorthands `c-else` and `c-empty` still take no value.
- New helpers for building attribute dicts in Python: `merge_attrs`,
  `format_attrs`, `normalize_class`, `normalize_style`, `parse_string_style`
  (importable from `citry`).
- New extension hook `on_attrs_resolved`: rewrite an element's resolved
  attribute dict before it is rendered (e.g. class deduplication).
- Render errors now tell you where they happened. The error message starts
  with the component path from the root down to the failure ("An error
  occurred while rendering components MyPage > Card > Card(slot:body)"), and
  when the failure sits in a template, it also shows the failing template
  lines with line numbers and a `^^^` underline.
- An extension can now recover from a component's render error: when a
  component fails, each enclosing component's `on_component_rendered` hook
  is called with the error on the way up, and returning replacement output
  swallows the error in that component's place. Untouched parts of the page
  still render; an error no extension handles raises as before.
- New `Component.on_render()` hook: return content to use it as the
  component's whole output instead of its template (a string, a composed
  element like `OtherComp(...)`, an already-rendered `CitryRender`, or a
  `Slot`), or return `None` (the default) to render the template as usual.
  The accepted values are published as the `RenderReplacement` type alias
  (importable from `citry`).
- `on_render()` also has a generator form: include a `yield` to receive the
  component's finished output (children included) as `(result, error)` and
  react to it. Return new content to replace the output, raise to replace
  the error, or return nothing to keep the result; if a child component
  failed, `error` is set and returning content swallows it (this is how
  error boundaries are built). You can yield replacement content any number
  of times; each yield receives the settled result of the previous one. The
  generator shape is published as `OnRenderGenerator` (importable from
  `citry`).
- New `<c-error-fallback>` built-in tag: an error boundary. Wrap content
  that might fail to render, and on error the fallback shows in its place
  while the rest of the page renders normally. Give the fallback as the
  `fallback` attribute, or as a `fallback` fill that receives the error as
  slot data (`<c-fill name="fallback" data="d">{{ d["error"] }}</c-fill>`).
  Boundaries nest (the innermost one wins), and a failing fallback defers
  to the next boundary up. The name `error-fallback` is now reserved in the
  component registry.
- New `Component.ancestors` property: iterate a component's ancestors during
  render, nearest first up to and including the root (e.g.
  `any(isinstance(c, Theme) for c in self.ancestors)`). Like `parent`, the
  chain follows who wrote the component: content passed into another
  component's slot keeps its author's chain (unlike Vue's `$parent`, which
  points at the slot host). For "am I rendered inside X, slots included",
  use `provide`/`inject`.
- `citry_core.safe_eval` now exports `format_error_with_context`, the
  formatter that adds an underlined source snippet to an error message
  (previously internal to `safe_eval`).
- Your component's `$component` callback can now return a cleanup function.
  The client runtime calls it right before the callback fires again for the
  same component instance (for example when the same fragment HTML is
  inserted into the page again), and now also when the instance's last element
  leaves the page, so event listeners, timers, and widgets set up in the
  callback are torn down both before they are re-created and when the component
  is removed rather than re-rendered. A callback that synchronously registers
  or calls another component while it runs no longer makes its own callback and
  cleanup run twice.

## v0.2.0

### Feat

- Citry now logs through the standard `logging` module, under the `"citry"`
  logger, with a `TRACE` level (5, below `DEBUG`). The logger traces each component,
  slot, and node as it renders. Turn it on to debug a render:

  ```python
  import logging
  logging.getLogger("citry").setLevel(5)
  ```

### Fix

- A default value for a slot set at `Component.Slot.<attr>` is now correctly used.

- Include JS runtime script when a Component has any JS/CSS scripts

### Refactor

- Citry now raises error when template contains `<c-slot name="X">`, but `Component.Slots` omits `X`.

  A component without a `Slots` class accepts any fills
  and is unaffected.

## v0.1.0

_30 Jun 2026_

Initial release.

## 2025-12-21

Initial commit.

This project was forked from [django-components/djc-core](https://github.com/django-components/djc-core) at commit [49e20dc](https://github.com/django-components/djc-core/commit/49e20dc).

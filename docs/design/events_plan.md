# Implementation plan: the Events extension (work packages)

> **Historical implementation ledger.** The work packages below preserve the
> names and shapes used while Events was built. They are not the current wire
> specification. On 2026-07-26 the working `citry-events/1` contract moved to
> strict named call, result, descriptor, and manifest records, and the golden
> `fixtures/` directory became `tests/` with index key `dynamic_fields`.
> [`packages/protocol/events/v1/spec.md`](../../packages/protocol/events/v1/spec.md)
> is authoritative for current field names and validation rules.

**Status (2026-07-23 snapshot; client wave ended 2026-07-17): the v1 events
stack is implemented end to end.** WP1 through WP17.2, plus WP21 (the `#c-*`
parser channel) and WP22 (the `@event` queue knobs), are implemented,
adversarially reviewed and approved, and the full combined gate is
green: server pipeline, protocol package, and the complete client
runtime (applier with keyed linking, fetch transport under the vendor
media type, the dependency-DAG queue, bindings, forms, and
preservation). WP23's explorations and mechanism spikes are complete. The
maintainer selected graph-first Alpine and `$c-props` on 2026-07-20; the A0-A10
client-boundary, registry, root-shape, slot-scope, atomicity, structural, and
closeout packages have since landed as recorded in
[`alpinejs_plan.md`](alpinejs_plan.md). WP23 remains below as a historical
ledger and must not be dispatched.
The maintainer's client-model calls (2026-07-15) and review round
(2026-07-17) are folded into the design; the decision records live in
events.md 14.3 and the research register in
[`events_research/`](events_research/README.md). WP18's protocol conformance,
cross-host, middleware, example-port, and browser gates landed and passed on
2026-07-22. WP19's public guide, security guidance, API-reference pass, and
sibling-doc closeout also landed and passed independent review that day.
WP20's four migration guides, shared parity matrix, and executable examples
landed and passed independent review on 2026-07-23. The Events closeout and the
pooled low-severity polish batch (WP26) are complete.
The v1.x history and download response actions landed as WP27, including the
server, client settlement, protocol fixture, guide, and browser coverage.
Alpine research
and reproductions are indexed in [`alpinejs/`](alpinejs/README.md); the golden
design is [`alpinejs.md`](alpinejs.md).

This doc is the delegation companion to [`events.md`](events.md). It
takes the v0 substrate (the core changes the design needs first; design
section 12), the protocol package, the spike, and the v1.0 build of the
design, and breaks them into self-contained work packages, each sized
for one coding agent: the original twenty-two numbered packages plus WP23
and WP25 (WP24 is reserved for the separate `template_data` default), of which the two
client packages WP16 and WP17 ship as five sub-packages (WP16.1 to
WP17.2), each dispatched like any other WP.
The design doc stays the source of truth
for *what* and *why*; this doc says *who reads what, builds what, and
proves it how*. When a decision here seems to conflict with the design
doc, the design doc wins; flag the conflict instead of improvising.
This plan deliberately leaves out v1.x and v2 scope (multipart,
postMessage, WebSocket, push, the dogfood port); section 5 lists it so
nobody builds it by accident.

For operating rules see [`/CLAUDE.md`](../../CLAUDE.md).

---

## 1. How to delegate a work package

Every agent brief must carry the rules with it (a delegated agent sees only
the brief). Copy this template and fill in the WP number (a
sub-package number like WP16.2 fills in the same way):

```
You are implementing work package WP<N> of the citry Events extension.
Repo: /Users/mac/repos/citry. Work in the fable-mode skill; effort: max.

Read first, in this order:
1. /CLAUDE.md (operating rules, code conventions, house style).
2. docs/design/events.md, the sections listed under WP<N> in
   docs/design/events_plan.md. Read them in full; the design carries
   decisions (naming, defaults, error wording) that are normative.
3. docs/design/events_plan.md, your WP<N> entry: scope, deliverables,
   tests, boundaries.
4. The code files listed in the WP entry, before writing anything.
5. Any other files your WP entry names beyond events.md and code:
   research reports under docs/design/events_research/, the alpine
   audits under docs/design/alpinejs/, sibling design docs, the WP6
   spike report. They are named deliberately and are normative where
   the entry says so; read them before writing.

Rules that bind this work:
- Scope is exactly WP<N>. Respect its "Boundaries" list; if you believe
  the scope is wrong, stop and report instead of expanding it.
- New or changed behavior ships with tests. Tests that assert exact
  generated output are authored observe-then-lock: run the real thing,
  read the output, then lock it into the assertion. (Exception: the
  protocol fixtures of WP5 are authored first, as the contract, and
  implementations must match THEM; see the WP5 entry.)
- Generated output must be deterministic (no set iteration into output,
  no timestamps, no environment-dependent ordering).
- Errors this design specifies are part of the contract: match the
  design's wording intent (what failed, why, the concrete fix), and
  test the message content, not just the exception type.
- Finish with the full repo gate: .venv/bin/python scripts/check.py
  --reporter agent, and fix everything it reports, including failures
  in files you changed indirectly.
- Report back: what you built, the test evidence, and any deviation
  from the plan with your reasoning.
```

Additional dispatch rules for the coordinator:

- **One WP per agent, one reviewable change set per WP.** Do not batch WPs.
- **Parallel WPs need worktree isolation** when they touch overlapping
  files. The wave table marks safe parallelism; WPs that share files
  (noted per wave) run in sequence, not in parallel.
- **Worktrees need the venv.** The gate command assumes
  `.venv/bin/python`, which a fresh worktree lacks; set it up (or
  symlink the shared one) before dispatching. Do not let a worker fall
  back to bare `uv run`: it re-resolves and can fail on the editable
  citry-core install.
- **Land order follows the waves.** A WP whose dependency has not merged
  builds on a stale contract.
- **WP6 (the spike) gates the client wave.** Do not dispatch WP15 to WP17
  before the WP6 report lands and its assertions pass. If the spike
  disproves the client model, the design doc's section 13.2 consequence
  applies (redesign before hardening) and this plan's client WPs get
  rewritten.
- When a WP lands, update its status line in section 4, and when a whole
  phase completes, update the status header of [`events.md`](events.md).
- **Record design changes made after a WP started (or landed) in that
  WP's status block**: what changed in the design, and whether the WP
  needs a re-run or an amendment pass. The status blocks are the re-run
  queue; a design edit that touches an in-flight or landed WP is not
  done until its status block says so.

---

## 2. What already exists (do not rebuild)

The substrate the design stands on is live in the repo; WPs extend it and
must not fork it:

- Extension system: `Extension`, `Extension.Config` weaving, three-level
  defaults, `emit()`, `Extension.urls` with `ext/<name>/` namespacing
  (`citry/extension.py`), built-ins prepended
  (`extension.py`, `_builtin_extensions`).
- Routing: `URLRoute` / `RouteResponse` / `match_route`
  (`citry/util/routing.py`), adapters (`citry/contrib/*.py`), the mount
  contract (`citry.py`, `build_url` / `set_mounted_prefix`), `format_url`
  (`citry/util/misc.py`).
- The fragment pipeline: `serialize(deps_strategy="fragment")`, the
  `data-citry` manifest, the client dependency manager
  (`citry/extensions/dependencies/`, `client/citry.js`), `$component`
  rewrite (`dependencies/scripts.py`).
- Typed inputs: nested-class dataclass conversion (`citry/component.py`),
  `CitryCache` (`citry/cache.py`), `CitrySettings` (`citry/settings.py`),
  the `citry` CLI and `ExtensionCommand`.

---

## 3. Sequencing

Status legend, used here and on the section 4 headings: ✅ is done and
review-approved, ⏳ is in progress, 🟠 is paused mid-work, 🔵 is not
started, and 🚧 marks user review pending: something in that WP's
status block awaits a maintainer answer. The wave table below carries
only the completion glyph; 🚧 rides the section 4 headings alone,
where the status block says what is waiting. Collapsing a WP body in
a `<details>` block is the maintainer's own review ledger: he wraps a
section once he has read and approved it, so a visible body means the
maintainer has not signed it off yet. Agents never add or remove
these wrappers.

| Wave | Packages | Notes |
|---|---|---|
| 1 | ✅ WP1, <br/>✅ WP5 | The `ext/` rename must land before anything imports `citry.ext.events`; the protocol package is pure authoring with no code overlap |
| 2 | ✅ WP2, <br/>✅ WP3, <br/>✅ WP4 | Substrate. WP2 and WP3 both touch `contrib/django.py`: run WP2 first or isolate in worktrees; WP4 is disjoint (client JS) |
| 3 | ✅ WP6, <br/>✅ WP7 | The spike (after WP4's hooks) and the extension skeleton (after WP1) are disjoint |
| 4 | ✅ WP8, <br/>✅ WP9 | Tokens (needs WP3) and data schemas, <br/>both on WP7. Both edit the events package; they share `citry/ext/events/__init__.py` exports, so isolate in worktrees or land WP8 first |
| 5 | ✅ WP10, <br/>✅ WP12 | Serializer integration (needs WP8's mint) and the binding rewrite (needs WP7). Both register hooks on the events extension class; worktree isolation or land WP10 first |
| 6 | ✅ WP11 | Actions and encoding; needs WP9's schemas and WP10's render-to-fragment path |
| 7 | ✅ WP13 | Dispatcher, routes, codecs, CSRF, URL builder, compat mode; integrates WP2, WP3, WP8 to WP12 |
| 8 | ✅ WP14 | ViewEvents shim + OpenAPI command (needs WP13's routes and WP9's schemas) |
| 9 | ✅ WP15 | Client: Alpine embedding, scopes, magics (gated on WP6; needs WP4, WP10, and it replaces WP13's runtime.js stub) |
| 10 | ✅ WP21, <br/>✅ WP22 | The `#c-*` parser channel, grammar to rendered HTML (the one Rust-contract WP; CLAUDE.md Mechanisms 1/2/4 apply) and the `@event` queue-knob amendment (decorator, descriptor emission, protocol descriptor fields; it amends the landed WP5/WP7/WP10 surfaces). Disjoint code from each other and from every client WP; the client wave consumes what both emit (WP16.1 reads WP21's emitted attributes, WP16.3 reads WP22's descriptor fields) |
| 11 | ✅ WP16.1 | Client applier: `applyActions`, the uncorrelated-id lifecycle, keyed linking, the five machinery requirements (needs WP15, WP21, WP5's fixtures) |
| 12 | ✅ WP16.2 | Client transport: envelope, fetch, CSRF autowiring, timeout, the public surface (needs WP16.1, WP13, WP5) |
| 13 | ✅ WP16.3 | Client queue: the dependency DAG, batching, the `@event` knobs, timeout release, busy-from-the-gesture (needs WP16.1, WP16.2, WP22) |
| 14 | ✅ WP17.1 | Component-tag client bindings: `$c-props`, delegated Alpine handlers such as `@click`, and Citry handlers such as `@c-poll.5s` resolved from a nested `<c-*>` tag. The parent owns each expression or server handler; the child supplies the browser boundary. (Needs WP16.3, WP12.) |
| 15 | ✅ WP17.2 | Client forms: two-way and one-way bindings, form collection, preservation wiring (needs WP17.1, WP16.1, WP12) |
| 16 | ✅ WP23 research | Superseded for implementation by [`alpinejs_plan.md`](alpinejs_plan.md); its graph-first A0-A10 implementation has landed |
| 17 | ✅ WP25 | Breaking client registration rename and one-registration-per-class rule (needs WP17.1's config form) |
| 18 | ✅ WP18 | Conformance runner + e2e suite (needs everything above) |
| 19 | ✅ WP19, <br/>✅ WP20 | Docs: the guide and sibling updates (WP19) and the migration pages (WP20); disjoint content, they link to each other |
| 20 | ✅ WP24, <br/>✅ WP26, <br/>✅ WP27 | Core input default, pooled closeout, then history and download response actions |

The five client sub-packages all edit the same runtime workspace
(`packages/js/citry-client/` and the committed bundle), so they run in
sequence; their dependency edges force that order anyway.

Dependency edges, regenerated from the per-WP needs; read `A <- B` as
"B needs A" (the wave notes and this list must never disagree):
WP1 <- WP7; WP4 <- {WP6, WP15};
WP6 <- WP15; WP3 <- {WP8, WP13}; WP7 <- {WP8, WP9, WP10, WP12, WP22};
WP8 <- {WP10, WP13}; WP9 <- {WP11, WP13, WP14}; WP10 <- {WP11, WP13,
WP15, WP22}; WP11 <- WP13; WP12 <- {WP13, WP17.1, WP17.2}; WP2 <-
WP13; WP13 <-
{WP14, WP15, WP16.2}; WP5 <- {WP16.1, WP16.2, WP18, WP22};
WP21 <- WP16.1; WP22 <- WP16.3; WP15 <- WP16.1;
WP16.1 <- {WP16.2, WP16.3, WP17.2}; WP16.2 <- WP16.3;
WP16.3 <- WP17.1; WP17.1 <- {WP17.2, WP25};
all landed Events work <- WP18 <-
{WP19, WP20}.

Shared-surface warning for the events package: WP7, WP9, WP11, and WP14
all append to `citry/ext/events/__init__.py` (the pure re-export
surface), and WP10, WP12, and WP13 add hooks to the extension class
file. Any two of those dispatched concurrently need worktree isolation;
the waves above sequence them, so this only bites if waves are
compressed.

---

## 4. Work packages

### ✅ WP1: the `ext/` rename and public-entrypoint hygiene

**Status: landed 2026-07-07, review-approved (fix round applied the two
minor findings; re-review: approve, zero findings; full gate green).**

**Decisions recorded by the implementation (maintainer-approved 2026-07-22):**

1. The griffe bullet landed as an explicit `public_entrypoints()`
   enumeration in `docs_site/_internal/reference.py`, plus reference pages for
   the 12 entrypoint exports that previously had none; the coverage
   test now covers all three entrypoint shapes.
2. `citry/contrib/__init__.py` declares `__all__` (submodule names)
   without eager submodule imports, so `import citry.contrib` behaves
   exactly as before.
3. Resolved by the maintainer 2026-07-07: the six dependencies types
   (`Script`, `Style`, `CitryDependencies`, `Dependency`,
   `DependencyRecord`, `OnDependenciesContext`) are exported from
   `citry.ext.dependencies` ONLY. Removing the root export is a
   breaking change; the CHANGELOG's v0.3.0 section records it together
   with the `citry.extensions.*` to `citry.ext.*` path change.

**Goal:** `citry/extensions/` becomes `citry/ext/`, and the design's
public-API rule holds for the existing package before Events lands on
it. The rule: there are three entrypoint shapes (`citry`,
`citry.contrib.<name>`, `citry.ext.<name>`), and public `__init__.py`
files are pure re-export surfaces with `__all__` and no logic.

**Read first:** `events.md` 3.4 (the paragraph "The import paths are
governed by one public-API rule") and 14.1.12 (last part); code:
`citry/extensions/` (the whole tree), `citry/contrib/*.py`,
`citry/__init__.py`, the docs-site griffe configuration (find it under
`docs_site/`; it selects the entrypoints the API reference renders).

**Build:**

- `git mv citry/extensions citry/ext`; update every import repo-wide
  (source, tests, docs_site config). Design docs are NOT rewritten:
  they already say `citry/ext/` forward-looking, and historical
  `file:line` citations in them stay as they are.
- For `citry/ext/dependencies/` and `citry/contrib/__init__.py`: move
  any logic out of `__init__.py` files into sibling modules so the public
  `__init__.py` is imports plus `__all__` only, and add `__all__` where
  missing. The flat contrib modules (`contrib/asgi.py`,
  `contrib/django.py`, ...) stay flat: a flat module IS its own public
  surface, so the pure-`__init__` rule applies only to packages; add
  `__all__` to each flat module instead. Do not rename module internals
  beyond what the moves require.
- Point the docs-site griffe collection at the three entrypoint shapes and
  confirm the rendered reference still contains the same public symbols
  (the reference is the enforcement of the rule).
- CHANGELOG entry: import-path change is user-observable
  (`citry.extensions.*` imports stop working); one line, with the new
  path.

**Tests:** the existing suite is the test (imports break loudly if the
rename is incomplete); add one test asserting `citry.ext.dependencies`
exposes its documented surface via `__all__` and that
`citry/ext/dependencies/__init__.py` contains no `def` or `class`
statements (the pure-re-export rule, cheap AST check).

**Boundaries:** no Events code, no new symbols, no behavior change. If a
module resists the pure-`__init__` rule (circular imports), report the
cycle instead of restructuring the module.

---

### ✅ WP2: neutral request, response headers, ASGI async (substrate 12.1 to 12.3)

**Status: landed 2026-07-07, review-approved (one fix round; re-review:
approve).** Decisions and follow-ups recorded:

1. Contract addition made during review: the Django adapter raises a
   pointed error on repeated response-header names (Django's response
   object holds one value per name, so silently keeping only the last
   value would drop a `Set-Cookie`). Promoted into design 12 item 3 and
   the CHANGELOG wording.
2. After this WP landed, design 6.2 gained an explanation of how each
   adapter owns its sync/async split; it documents exactly the
   mechanism as built (`call_maybe_sync`, per-adapter knowledge), so no
   re-run is needed.
3. The orchestrator resolved the reviewer's low-severity findings
   ("lows") post-approval: the CHANGELOG qualifier for the Django
   header caveat, the docs-site web-category description, and a
   regression-lock test for the guard that GET requests never drain
   `receive`
   (test_contrib_request.py::TestAsgiBodyStream::test_get_request_never_drains_receive).
4. A maintainer-requested clarity pass was applied post-landing
   (behavior-neutral): each adapter module's docstring states the
   shared translate-dispatch-translate shape; the ASGI and Django
   adapters gained the same `_build_request` extraction the WSGI
   adapter already had; and `asgi_app` / `wsgi_app` / `_make_view` and
   the response translators carry docstrings narrating each step.
5. Maintainer rename, pre-release: the case-insensitive headers mapping
   is `RouteHeaders` (aligning it with the other Route* constructs);
   applied repo-wide with no leftover occurrences.

**Goal:** route handlers receive a framework-neutral `RouteRequest` with a
readable body under every adapter, can set response headers, and the ASGI
adapter awaits `async def` handlers and offloads sync handlers to a worker
thread.

**Read first:** `events.md` 12 (items 1 to 3), 3.3 (the `request`
injectable row, for the field set the extension will need); code:
`citry/util/routing.py` (all of it; note the docstring stating handlers
never read `request` today), `citry/contrib/asgi.py`, `wsgi.py`,
`django.py`, `fastapi.py`, `flask.py`, `tests/test_contrib_fastapi.py`
and sibling contrib tests, `tests/test_deps_urls.py`.

**Build:**

- `RouteRequest` frozen dataclass in `citry/util/routing.py`: `method`,
  `path`, `query` (mapping, repeated keys preserved), case-insensitive
  `headers`, `body: bytes`, `content_type`, `native` (the untouched host
  object). Adapters construct it: ASGI drains `receive` for bodied
  methods; WSGI reads `wsgi.input` per `CONTENT_LENGTH`; Django wraps
  `HttpRequest` (`request.body`); the FastAPI/Flask sugar paths inherit
  from the ASGI/WSGI cores they wrap.
- `RouteResponse.headers: tuple[tuple[str, str], ...] = ()`; every adapter
  forwards them.
- ASGI adapter: `async def` handlers are awaited; sync handlers run in a
  worker thread (`asyncio.get_running_loop().run_in_executor` unless the
  repo already depends on anyio; add no new dependency). Expose the
  offload as a reusable helper in `citry/util/routing.py` (`async def
  call_maybe_sync(fn, /, *args, **kwargs)`: awaits coroutine functions,
  runs sync callables in the executor), used by the ASGI adapter here
  and by WP13's async dispatcher later. WSGI and sync
  Django reject `async def` handlers with a pointed error naming the
  deployment fix.
- Existing handlers (the dependencies extension's) keep working unchanged;
  they ignore `request` today, which is why this is a contract tightening,
  not a break.
- CHANGELOG entry (routing util public API change).

**Tests:** per adapter (FastAPI TestClient, WSGI environ, Django test
client): a POST handler reads a JSON body and echoes it; a handler sets a
response header and the client sees it; repeated query keys survive;
`native` is the host object. ASGI only: an `async def` handler works; a
sync handler does not block the loop (smoke: run two concurrent requests
where one sleeps briefly in the handler). WSGI: `async def` handler
raises the pointed error.

**Boundaries:** no Events code, no CSRF, no codecs, no size caps. Do not
change route matching or the mount contract.

---

### ✅ WP3: the settings trio and the Django secret helper (substrate 12.4)

**Status: landed 2026-07-08, review-approved (three review rounds; the
final review had zero blocking findings). Two items for the maintainer,
both flagged by the review as judgment calls and accepted 2026-07-22:**

1. **The CHANGELOG entry was dropped, not added.** The three fields are
   inert storage today (no consumer until WP8/WP13), so by CLAUDE.md's
   changelog test a user cannot yet do anything with them, and the only
   honest wording would leak roadmap. WP8/WP13 introduce
   `secret=`/resolvers/codecs to users when their consumers make the
   fields do something. If you want an API-record entry now, say so and
   it goes back verbatim.
2. **Pre-existing normalization bug the review surfaced: FIXED in a
   standalone follow-up (2026-07-08, review-approved).** Input
   normalization had lived only in `Citry.__init__`, so direct
   `CitrySettings(...)` construction stored un-normalized, caller-aliased
   values for `extensions`, `dirs`, `extensions_defaults`, and
   `template_globals` (the same shape as the `secret`/resolver/codec bug
   WP3 fixed in `__post_init__`), and `dirs` skipped its Path coercion
   and absolute-path validation on that path. The follow-up moved all
   `CitrySettings` input normalization into `__post_init__` (with one
   documented boundary `type: ignore` for the `dirs` Path typing) and
   removed the duplicate coercion from `Citry.__init__`, so both
   construction paths now normalize identically (proven by a cross-path
   equality test). It shipped its own user-facing CHANGELOG entry (a
   relative `dirs` entry now raises `ValueError` on direct construction
   where it previously stored a raw string).

**Goal:** `CitrySettings.secret`, `event_result_resolvers`,
`event_payload_codecs` exist as frozen constructor-passable fields, plus
`citry.contrib.django.secret()`.

**Read first:** `events.md` 12 (item 4), 3.5 (the engine-wide paragraph),
6.2 (what payload codecs and result resolvers are, for the docstrings;
the naming is a recorded decision, 14.2), 7.1 (secret
resolution and rotation); code: `citry/settings.py`, `citry/citry.py`
(how `cache=` and `extensions=` constructor kwargs flow into settings),
`citry/contrib/django.py`.

**Build:**

- `CitrySettings.secret: str | list[str] | None = None` (a list means
  rotation: the first secret signs, all of them verify; internally,
  normalize a bare string to a one-element list),
  `event_result_resolvers: tuple = ()`,
  `event_payload_codecs: tuple = ()`.
  All three ride the `Citry(...)` constructor like `cache=` does.
  Docstrings per the public-docstring conventions; the resolver/codec
  docstrings point at the design's 6.2 concepts without duplicating them.
- `citry.contrib.django.secret()`: returns Django's `SECRET_KEY` for
  passing as `Citry(secret=...)`; lazy Django import, pointed error when
  Django is not configured.
- No consumer yet: the fields are storage; Events (WP8, WP11, WP13) reads
  them.

**Tests:** construction with each field; immutability (assignment raises);
string-vs-list secret normalization; `secret()` under a configured Django
settings module and the error without one.

**Boundaries:** no signing code, no resolver/codec base classes (WP9/WP11
own those shapes); this WP is settings plumbing only.

---

### ✅ WP4: client-runtime extension points: `decorateContext` and teardown (substrate 12.5)

**Status: landed 2026-07-07, review-approved (two fix rounds; final
review: approve, zero findings).**

**Amendment landed 2026-07-08, review-approved (one low finding, below).**
The component-identity spike (`spike-component-identity.md`) added a
component-instance lifecycle layer to this file's scope. Three items (the
removal reconciler with teardown-on-removal, the deferred/coalesced
`Component.css` garbage collection, and the `flushCalls` re-entrancy fix)
were built in `citry.js`, each mutation-proven in the e2e suite (5 new
tests; the F-CI-4 same-class-re-render test proves the GC must be
deferred, an inline GC makes it fail). The manager gained no new public
method (the API-surface contract test stays green); the CSS-only presence
record it consumes is pinned in the WP10 entry above and `dependencies.md`
8.4. The original two extension points (`decorateContext` and callback
teardown) are unchanged. Low finding, not blocking, recorded for a future
optimization: the reconciler's sweep iterates the whole `liveInstances`
map per debounced mutation batch and `classLiveCount` does another full
pass, so on very dense pages the per-batch cost is O(live instances); fine
for now, worth a bucketed index if profiling shows it.

**Design note 2026-07-17:** design 5.5 gave `$component` a second
accepted form, a config object with `init` and `props`. The build
is WP17.1 scope and is additive: the bare-callback form, the payload
decoration, and this WP's teardown contract are unchanged, so no
re-run.

**Goal:** other extensions can extend the dependencies manager's
`$component` callback payload, and callbacks may return a cleanup
function that runs before the callback re-fires for the same instance.

**Read first:** `events.md` 12 (item 5), 5.2 (the teardown contract and
the payload members Events will add later); for the amendment,
`docs/design/dependencies.md` 8.4 (the lifecycle layer, in full) and
`spike-component-identity.md` (the removal reconciler F-CI-5, the deferred
`Component.css` GC F-CI-4, and the two-layer composition F-CI-3, all
normative here), plus the morph-and-Alpine spike's finding F9
(`spike-morph-alpine.md`, the teardown-on-removal gap this closes); code:
`citry/ext/dependencies/client/citry.js` (the whole file; note
`flushCalls`, `pendingCalls`, and the payload object),
`docs/design/dependencies.md` 8.2,
`tests/e2e/test_fragment_e2e.py` and the JS-exercising tests under
`tests/` (grep `$component`).

**Build:**

- `Citry.manager.decorateContext(fn) -> unregister`: registered
  decorators run over the callback payload object at flush time, just
  before the callbacks, in registration order, mutating it in place
  (return values ignored; design 12 item 5 pins this contract). A
  throwing decorator is caught and logged like a callback error and the
  flush continues. Document the contract in the file header comment.
- Teardown: when a callback returns a function, the manager stores it
  keyed by (classId, componentId, callback); before re-invoking callbacks
  for a componentId (a later manifest `calls` entry for the same id), the
  stored cleanups for that id run first, then are discarded. Errors in a
  cleanup are caught and logged like callback errors.

Amendment build items (2026-07-08; `dependencies.md` 8.4 is the spec):

- Removal reconciler (spike finding F9 / F-CI-5): an instance's stored
  cleanups also run when its last `[data-cid-<id>]` element leaves the DOM.
  Keep the set of instance ids whose callbacks have fired; on DOM mutation
  and after each render, sweep that set against the live DOM and retire any
  id with no live element left (run and discard its cleanups). The sweep
  must catch both a real node removal and an in-place attribute swap (the
  same node losing its old `data-cid-<id>`), so a re-render that changes an
  instance's id retires the old id exactly once.
- `Component.css` garbage collection (spike finding F-CI-4): remove a
  class's `Component.css` sheet (found by `data-citry-css-class="<class>"`,
  WP10) when its last live instance leaves. **The GC must be deferred to a
  later task and re-check the live count then, never run inline on
  retirement**: a solo-instance same-class re-render retires the old id
  before the fresh same-class id registers, so an inline check would drop
  the sheet on every re-render (and a URL-served sheet would not be
  re-fetched, a permanent style loss). A same-tick same-class arrival
  cancels the pending GC. Leave the `data-ccss-<hash>` vars sheets alone.
- Flush re-entrancy fix (spike; same file): snapshot and clear
  `pendingCalls` before iterating in `flushCalls`, so a callback or
  decorator that synchronously triggers a nested flush cannot re-run the
  in-flight call (fixes double cleanup and unbounded recursion).
- Update the runtime's header comment and `dependencies.md` 8.2 and 8.4
  (the design-doc note lives there, not in events.md, since the
  dependencies extension owns this file).
- CHANGELOG entry: `$component` callbacks may return a cleanup function,
  and cleanups now also run when a component leaves the page (both
  user-observable runtime behavior).

**Tests:** extend the existing JS e2e harness: a decorator adds a member
and callbacks see it, and stops after its unregister function runs; a
throwing decorator does not break the flush; a callback returning a cleanup sees the cleanup run
exactly once before its re-fire when the same instance id is called
again; a throwing cleanup does not break the flush. For the amendment:
a cleanup runs once when the instance's last `data-cid-<id>` element is
removed, and once when the same node's id attribute is swapped in place; a
solo-instance same-class re-render does NOT drop the class's
`Component.css` sheet (the deferred GC is cancelled by the fresh
same-class arrival), while removing the genuine last instance of a class
does drop it; a callback that synchronously triggers a nested flush does
not re-run the in-flight call or double-fire its cleanup.

**Boundaries:** the two original extension points plus the amendment's
lifecycle layer (removal reconciler, `Component.css` GC, flush re-entrancy
fix), inside the existing file, in its existing style (plain ES5-ish JS,
matching the file). No Events runtime, no Alpine, no morph, and no anchor
concept: the anchor is an events-runtime idea (`events.md` 5.5) and never
appears in this file, which stays keyed by component id and class id.

---

### ✅ WP5: the protocol package (design 4.1)

**Status: landed 2026-07-07, review-approved (one fix round; re-review:
approve). The fix round aligned the contract with the design where they
had drifted (`event` is optional on the per-event route, matching 4.2)
and added one rule decided during review: a handler-returned `event`
action with no explicit target is self-addressed by the server at
encode time (decision 12 below). The orchestrator resolved the
reviewer's lows: the spec section 3 `instance` bullet now names all
three self-addressed action kinds, and an epoch-on-error golden pair
was added (error_forbidden fixtures) so WP18 can replay decision 8.**

**Update 2026-07-07 (maintainer order): the package self-checks run in
CI now.** `packages/py/citry/tests/test_events_protocol_package.py`
loads the checker functions from `validate.py` by path and runs every
check as pytest, one case per fixture. Because it lives under the
`packages/py/citry/tests` testpath, the full gate (`repo--check.yml`,
which has no path filters and runs on every change) collects and runs
it. The standalone `.venv/bin/python
packages/protocol/events/v1/validate.py` run keeps working for binding
authors without pytest. Correction 2026-07-08: the first wiring left a
gap the maintainer caught, `packages/protocol/**` was in no workflow
path filter, so a protocol-only change (a fixture, schema, or spec
edit) did not trigger the `py--tests.yml` cross-version matrix; that
path is now added to `py--tests.yml`, so the files whose change should
re-run these tests now do. This wires only the package's
self-consistency checks; WP18's conformance runner (fixtures replayed
through the dispatcher) is unchanged.

**Contract decisions recorded by the implementation.** events.md
section 4 left these unpinned; `spec.md` states them normatively (the
authoring inversion: spec and fixtures are written first and are the
contract). **The adversarial review ruled on these 2026-07-07: every
one fills a gap the design left open, none contradicts the design.**
The design-worthy ones are promoted into events.md (4.1
fixture-authored error texts, 4.2 capabilities keys and baseline
constant and the calls range, 4.3 the self-address rule, 3.7 the
403-to-forbidden mapping, plus the 6.1 dispatcher table, which carries
decisions 2, 3, 4, and 8). Decision 12, recorded during review: a
handler-returned `event` action with no explicit target is
self-addressed at encode time to the calling instance; instance-less
calls dispatch on `document` (events.md 4.3). The original eleven:

1. The `capabilities` action-kinds key is named `actions` (parallel to
   the designed `swaps` key).
2. The v1 baseline is pinned as `CAPABILITIES_BASELINE_V1`: all v1
   swaps except `morph`, all six v1 action kinds.
3. The implicit token-refresh `state` action is placed BEFORE
   handler-returned actions, and the client applies any received token
   refresh to its registry before running the actions array (revised
   during the maintainer's WP5 review: when the refresh applied last, a
   dispatch listener that sent immediately still carried the
   pre-mutation token).
4. Unknown-major and cap rejections mirror per call, so `results[i]`
   answers `calls[i]` unconditionally; the server answers under its own
   protocol string.
5. `payload_too_large` (413) covers both envelope caps (byte size and
   the 16-call cap); the byte cap's value is deployment configuration,
   not protocol.
6. An `event` action with absent `target` dispatches on `document`;
   the fixtures self-target the caller (following the 4.3 example).
7. A user-raised `EventError(status=403)` carries code `forbidden`;
   user-raised 404/409 mappings are left to WP13.
8. `epoch` echoes on error results whenever the call carried it.
9. Error message texts (including the `invalid_args` per-field
   message) are authored in the fixtures and are contract from here on.
10. The canonical fixture component carries a `_guard` (denies
    rename-to-"admin" via `self.event.args`) to produce `forbidden`
    deterministically from the envelope.
11. `calls` has `minItems: 1` (a zero-call envelope is meaningless).

Also noted: the schemas omit `$id` (no project domain is pinned
anywhere in the repo).

**Amendment due (2026-07-16, the client-model round; owned by WP22):**
the class descriptor gained the queue knobs `latest_wins` and `bundle`
(events.md 3.5 and 4.4), which this package predates:
`descriptor.schema.json`'s `eventHint` and spec section 7's descriptor
prose and example carry only `method`/`debounce`/`throttle` today.
WP22 adds the two optional boolean fields to the schema, the spec, and
`validate.py`'s descriptor smoke example, in one change set per this
package's authoring-inversion rule. No fixture envelope embeds a
decoded descriptor, so the golden call/result pairs are untouched.

**Goal:** `packages/protocol/events/v1/` exists: the normative prose
spec, three JSON Schemas, and golden fixtures with a convention for
declaring volatile paths, all matching `events.md` section 4 exactly.

**Read first:** `events.md` sections 4.1 to 4.5 in full (the envelope
fields, the action vocabulary with `delay`/`wait`, the error codes with
fixed statuses, target addressing, `capabilities` and the per-major
baseline, the manifest payload of 4.4), 3.8 (routes and batch
semantics); `docs/codebase.md` (monorepo layout conventions for a new
`packages/` entry).

**Build:**

- `spec.md`: normative prose translated from events.md section 4 (the
  design doc explains and argues; the spec states). Includes: the
  envelope schemas in prose, the action vocabulary table, the error
  code-to-status table, the capabilities baseline constant for v1
  (named, exact), target addressing (plain selector = all matches,
  `cid:` override), ordering rules (faithful order, redirect semantics,
  `delay`/`wait`), the batch endpoint semantics, and the canonical
  fixture component defined in citry template syntax (a counter with
  `increment`, `rename`, `crash` handlers and one stateless data
  handler), which every binding implements for conformance.
- `call.schema.json`, `result.schema.json`, `descriptor.schema.json`:
  JSON Schema 2020-12, `additionalProperties` control per the design
  (strict on calls), the `calls` length cap (16), the field patterns
  from 4.2/4.3.
- `fixtures/`: golden request/response pairs against the fixture
  component covering at least: single call happy path (render action),
  data-only handler, dict-to-data coercion, batch of two, each error
  code once, a `state` action response, `delay`/`wait` fields present,
  unknown-major rejection. Plus `fixtures/README.md` defining the
  volatile-path convention (JSON paths whose values are
  environment-dependent: instance ids, tokens, asset hashes) and the
  conformance rule ("a binding passes when replaying every fixture
  call produces that fixture's result, identical except at the
  declared-volatile paths"), and a
  machine-readable `fixtures/index.json` listing each fixture as
  `{call, result, volatile_paths}` so WP16.1, WP16.2, and WP18 iterate
  structured
  data instead of parsing README prose.
- **Authoring inversion, stated in the spec**: unlike compiler tests,
  these fixtures are written first and are the contract; the Python
  implementation (WP13, WP18) must match them, never the reverse.
  Protocol changes land as fixture+schema changes in the same PR.

**Tests:** none executable yet (WP18 wires the runner); include a tiny
`validate.py` dev script that checks every fixture against its schema so
the package is self-consistent from day one, and run it.

**Boundaries:** no Python package code beyond the dev script, no server
implementation, no client. Do not invent envelope fields the design does
not have; if section 4 is ambiguous somewhere, flag it in the report.

---

### ✅ WP6: the morph and Alpine spike (design 13.2)

**Status: landed 2026-07-07, review-approved (all nine assertions pass,
twice, deterministically; the reviewer re-ran the harness independently
with identical evidence). The client wave (WP15 to WP17) is UNGATED.**
The verdict: keep `@alpinejs/morph` 3.15.12 (the Alpine-state bridge is
load-bearing; idiomorph stays on the shelf), and the pnpm+esbuild
acquisition is confirmed with one adjustment (classic iife delivery).
The report
([`spike-morph-alpine.md`](../design/alpinejs/spike-morph-alpine.md))
records eleven findings, F1 to F11, normative for WP15/WP16; the
design-affecting ones are folded into events.md (5.3 plugin import and
hook signature, 5.2 boot-order rules, 5.5 root selector and the
scope-stack testing note) and into the WP10/WP15 entries. One residual
low: the assertion-9 range-replacement probe is not fully discriminated
(noted in the report; harmless).

**Follow-on spike (2026-07-08):** the component-identity spike
([`spike-component-identity.md`](../design/alpinejs/spike-component-identity.md))
extends this one to prove the two-identity model (a faithful component id
plus a stable client anchor) through the real morph and the byte-identical
`citry.js`. Its findings F-CI-1 to F-CI-6 are normative for WP15/WP16 and
for WP4's lifecycle amendment, and it reframed events.md 4.2/5.3/5.5;
read it alongside this report before the client wave.

**Goal:** a throwaway harness proving the client model end to end before
any client code hardens, producing a pass/fail report per assertion and
the exact Alpine/morph version pins for WP15.

**Read first:** `events.md` 13 (item 2, the assertion list), 5.3, 5.4,
5.5 (scopes, reconcile rule, magics), 4.4 (the manifest payload);
`docs/design/alpinejs/alpine-ecosystem-2026.md` (pins, the Livewire boot
playbook), `docs/design/alpinejs/alpine-vuetify-audit.md` (the isolation
mechanism, `component.ts:165-170` of the audited snapshot); code:
`citry/ext/dependencies/client/citry.js`, `tests/e2e/` (the Playwright
harness pattern).

**Build (throwaway, in a scratch directory, deleted after):** a static
page served locally with the real `citry.js` (WP4 version), a pinned
Alpine 3.15.x ESM build plus `@alpinejs/morph`, hand-built
`data-citry` / `data-citry-events` manifest tags for two component
instances, a hand-rolled scope attach with the isolation truncation
(the audit's isolation mechanism), and a scripted "render action"
applying a pre-serialized replacement fragment. Assert, each as an
explicit scripted check:

1. `$component` re-fires exactly once per re-render, after its
   teardown ran.
2. The re-fire receives the NEW `js_data` payload (fresh vars script).
3. New CSS variables take effect on the morphed roots; old ones inert.
4. Assets dedupe (no double fetch of an already-loaded script URL).
5. A focused two-way-bound input keeps value and caret through a
   debounced update cycle.
6. A `state` action updates the registry with no DOM change.
7. The Alpine scope survives the morph: `$state` object identity intact,
   reconcile rule honored (server wins per field except pending unsent
   local writes).
8. Nested-instance isolation: the inner component's expressions do not
   see the outer component's scope. Include the shared-root case
   (parent and child marking the same element): magics resolve to the
   innermost instance.
9. A multi-root (fragment) instance updates through the pairwise
   per-root morph; a changed root count falls back to range
   replacement (design 5.3 "The morph call, concretely").

**Deliverable:** `docs/design/alpinejs/spike-morph-alpine.md`:
per-assertion pass/fail with evidence, the exact version pins, surprises,
and an explicit verdict on `@alpinejs/morph` vs the idiomorph fallback
(design 5.3). Acquire Alpine + morph the way WP15 will (pnpm install into
a scratch `package.json`, esbuild bundle; the plan pins that approach in
WP15) and confirm or contest it in the report, so WP15 inherits a
validated decision. The harness itself is deleted; the report persists.

**Boundaries:** no production code changes (WP4's hooks are consumed, not
modified). If assertions fail, the report is the deliverable; do not
"fix" the design inline.

---

### ✅ WP7: extension skeleton: registration, capture, meta, vocabulary (v1 server)

**Status: landed 2026-07-07, review-approved (one fix round; re-review:
approve, three lows).** Follow-ups recorded:

1. Resolved by the orchestrator: it deleted the redundant file-level
   noqa directive in test_events.py and wired the typed-base
   contract test (test_events_typing.py) into the gate's mypy phase
   in scripts/check.py.
2. Resolved 2026-07-08: the pyright half of the typing contract is now
   enforced in the gate. A root `package.json` (private, pnpm) pins
   `pyright@1.1.411`, and `scripts/check.py` has a `pyright` phase over
   the typed-base test (the local `node_modules/.bin/pyright`); CI runs
   `pnpm install --frozen-lockfile` before the gate. The `package.json`,
   `pnpm-lock.yaml`, `check.py`, and `repo--check.yml` changes must be
   committed together so a fresh CI checkout has the pinned pyright.
3. Resolved 2026-07-13, generalized beyond the original scope. The
   original amendment (validate `extensions_defaults["events"]` keys
   against the config vocabulary in the events extension) was superseded
   by a maintainer-directed framework mechanism: a static allowed-keys
   set cannot express the events two-tier rule (underscore names come
   from a fixed vocabulary; unprefixed names are handlers and may be
   anything callable), so the `Extension` base gained an overridable
   `validate_config_fields(fields, *, component=None)` method. The
   framework calls it at both declaration points: engine init for each
   extension's `extensions_defaults` entry (`component=None`) and
   component class creation for the fields declared on the nested
   config class, so by instantiation time all field names are
   known-valid. The base implementation accepts everything (existing
   extensions unaffected). The events override implements the two-tier
   rule, with a did-you-mean hint on unknown underscore names, and
   rejects unprefixed names in `extensions_defaults` (handlers are
   declared on a component's own `Events` class, not globally). Landed
   with the framework and events tests, review-approved (two lows);
   documented in `docs/design/extensions.md`.
4. The fix round made one contract nuance symmetric: on an explicit
   dataclass State, annotating a meta name turns it into a field, and
   it then fails as an underscore field, matching the plain-class
   behavior.

**Amendment due (2026-07-16, the client-model round; owned by WP22):**
`@event` gained the queue knobs `latest_wins` (default `False`) and
`bundle` (default `True`) (events.md 3.5); the landed decorator in
`handlers.py` stores and validates neither. WP22 adds the two kwargs
with boolean validation and their storage on the handler metadata.

**Goal:** the Events extension exists as a built-in: it captures the raw
`Events` and `State` classes, converts and validates State and its meta,
derives `state_data`, enumerates handlers, validates the signature
vocabulary, and resolves the underscore config with three-level defaults.
No routes, no tokens, no dispatch yet.

**Read first:** `events.md` 3.1, 3.2, 3.3 (the vocabulary and its
class-creation errors), 3.5 (both config tables and the derived-knobs
paragraph), 3.6, 7.2 (`_public`/`_model` defaults and subset rule);
code: `citry/extension.py` (`_builtin_extensions`, the config-weaving
in `_init_component_class` at `extension.py:777-819`), the dependencies
extension's `on_component_class_created` (the raw-class capture
precedent; WP1 moves it out of `__init__.py`, so grep for it under
`citry/ext/dependencies/`), `citry/component.py:154-162`
(dataclass conversion to mirror), `tests/test_extension.py`.

**Build (under `citry/ext/events/`, public surface per WP1's rule):**

- `EventsExtension` (name `"events"`) joining `_builtin_extensions()`.
- Raw-class capture in `on_component_class_created` for `Events` and
  `State` (nested class or `State = RootClass` assignment; both forms).
- State: dataclass conversion (extension-applied, `slots=True`,
  non-frozen); underscore-annotated fields are a class-definition error;
  unknown underscore attributes are a class-definition error naming the
  five meta names; `_model` defaults to `_public`, which defaults to
  all fields; `_model` must be a subset of `_public` (load error);
  `_storage`/`_max_bytes`/`_max_age` stored with defaults.
- `state_data`: read from the Component when defined; default derivation
  builds State from same-named kwargs; State-field defaults fill gaps; a
  field with neither is a render-time error naming the field.
- Handler enumeration from the raw class: public `def`s are handlers;
  underscore `def`s are helpers (`_context` recognized as the hook);
  underscore non-`def` attributes must be recognized config names
  (error otherwise, naming the valid set).
- Signature validation at class creation: parameters must come from
  {`data`, `state`, `context`, `request`, `event`}; `*args`/`**kwargs`
  rejected; `state` declared on a State-less component rejected;
  `data`'s annotation resolved (with `get_type_hints` + localns rescue)
  and required to be a schema-convertible class; injectable annotations
  are NOT resolved (advisory). Design 3.3 only requires resolving
  `data` at runtime; resolving it eagerly at class creation is a
  deliberate strengthening, so signatures stay fully classifiable at
  class creation. If a legitimate forward-reference pattern breaks
  under it, report rather than weaken silently.
- `@event` decorator storing name/methods/guard/csrf/debounce/throttle;
  config attributes `_guard`/`_context`/`_csrf`/`_methods`/`_debounce`/
  `_throttle`/`_topics` resolved through component >
  `extensions_defaults["events"]` > factory defaults (`_topics` is
  stored and validated but inert until v2's push consumes it).
- The Events config instance's ambient attribute slots (`state`,
  `context`, `request`, `event`) exist but are populated by WP13.
- The optional generic typing base (design 3.3): exported as
  `citry.Events` from the root entrypoint, generic over the State type
  with PEP 696 defaults (`class Events(citry.Events[TodoState]):` types
  `self.state`; bare `citry.Events` yields `self.state: None`), the
  fixed ambient members typed on it. It is the same class the weaving
  uses, so subclassing it changes nothing at runtime. Include a
  typing test proven green under both mypy and pyright
  (`docs/design/events_research/typing-lab-report.md` has the verified
  patterns; npx pyright, pinned, as in that report).

**Tests:** a matrix of class-creation errors (each with message-content
assertions: the wrong name, the valid alternatives); both State forms;
meta defaults and the subset rule; `state_data` default derivation and
override; handler enumeration versus helpers versus config; decorator
and three-level default resolution; the `@event(name=...)` wire-name
override.

**Boundaries:** no URLs, no tokens, no dispatch, no client, no binding
rewrite (WP12). Do not touch `citry/component.py` (the State conversion
is extension-owned by design).

---

### ✅ WP8: state tokens and updates (v1 server)

**Status: landed 2026-07-13, review-approved.** Landed in two passes.
The first pass (2026-07-08) built `tokens.py` (mint, verify, updates,
server-store mode) and its tests, but its review escalated a genuine
design gap: the code answered 403 for every signature miss, while the
WP5 fixtures distinguish rotated-out (409) from tampered (403). The
maintainer resolved it 2026-07-13 (design 4.3, the payload
well-formedness rule): on a signature that matches no current secret,
a payload that still parses as a well-formed token answers
`stale_state` 409, anything less answers `invalid_state` 403; a
signature-only tamper is indistinguishable from rotation and takes the
409 path. The second pass implemented the split, added fixture
conformance tests locking both protocol golden vectors, and hardened
the unauthenticated payload parse (non-UTF-8 and deeply-nested-JSON
forgeries map to the malformed 403 instead of escaping the documented
contract). Along the way: non-string dict keys in State are rejected
recursively at mint with a field-naming error (JSON would silently
rewrite them to strings), and self-referential values raise the
circular-reference ValueError consistently. Noted, out of scope here:
there is no verify-time byte cap; request-size capping is the
transport's `payload_too_large` (WP13).

**Goal:** mint and verify the signed State token, apply `updates`
under the `_model` gate, and the opt-in server-side store mode
(`_storage = "server"`, in v1 for the livecomponents two-step
migration; design 7.1 and 10).

**Read first:** `events.md` 7.1 (the token format, every rule bullet,
the dispatch-order paragraph), 7.2, 3.5 (the derived token-requirement
paragraph), 4.2 (`state`, `updates` fields); code: WP7's module,
`citry/settings.py` (WP3's `secret`), `citry/cache.py` (`CitryCache` is
the server-mode store; read its expiry semantics).

**Build:**

- Mint: State instance -> canonical JSON (sorted keys, compact
  separators) -> `cev1.b64url(payload).b64url(hmac_sha256)` with payload
  `{"v": 1, "c": class_id, "s": {...}, "t": mint_epoch, "x": expiry}`;
  JSON-safe enforcement at mint with the error naming component, field,
  and fixes; `_max_bytes` cap with the id-plus-reload guidance (keep an
  id in State, reload the rest); `_max_age` -> `x`.
- Verify: constant-time tag comparison across all rotation secrets;
  class-id binding; tampered/malformed -> `invalid_state` (403); expired
  or rotated-out -> `stale_state` (409); rebuilt via `cls.State(**s)`.
- Updates: apply only to `_model` fields, each value type-checked against
  the field; violations -> 422 with per-field messages; the
  re-sign-after-handler rule (changed State -> new token for the
  response; WP13 consumes this).
- Secret resolution: settings `secret`; when it is absent, the first
  mint raises the pointed error naming the one-line fix for each host.
- `_storage = "server"` mode: mint stores the state payload in
  `Citry.cache` under a random opaque key and the token carries only
  that key (distinct token prefix, implementer's choice, documented);
  verify loads it back, honoring `_max_age` through the cache's expiry;
  a cache miss maps to `stale_state` (409) with the id-plus-reload
  guidance. The wire, the client, and the WP10/WP13 call surfaces are unchanged
  (the token stays opaque; that is the point). Document the multi-worker
  requirement: a shared cache backend, the same constraint the
  fragments feature already documents (design 7.1).
- The exposed surface, in `citry/ext/events/tokens.py` (these names are
  the contract WP10 and WP13 call; renaming them means updating both
  consumers): `mint_state_token(state, *, class_id: str,
  secret: str | list[str], max_age, max_bytes) -> str`;
  `verify_state_token(token: str, *, cls, secrets: list[str]) ->
  VerifiedState` where `VerifiedState` carries `.state_kwargs` and
  `.class_id` and raises the mapped `invalid_state` /
  `stale_state` failures; `apply_state_updates(state, updates, *,
  model_fields)` raising the per-field 422 mapping.

**Tests:** golden-vector round trips (fixed secret, fixed payload ->
exact token string, locked observe-then-lock); rotation (old secret
verifies, signs with new); each failure mode with status and
message-content assertions; canonicalization determinism (dict order
does not change the token); `_max_bytes` and `_max_age` behavior;
updates gating and type-checking; server-mode round trip (mint, verify,
mutate, re-mint), `_max_age` expiry through the cache, and the
cache-miss `stale_state` message.

**Boundaries:** no HTTP, no dispatcher; pure functions plus WP7's
classes and `Citry.cache`.

---

### ✅ WP9: data schemas, coercion, and `UploadedFile` (v1 server)

**Status: landed 2026-07-13, review-approved (one fix round).** Built
as new modules `schemas.py` and `files.py` under `citry/ext/events/`,
tests in `test_events_schemas.py` (100 tests, all proven to bite
via a 25-mutation pass with byte-identical restore). The review's high
finding was real: a wire-legal payload could raise out of
`validate_args` (an unhashable item for a bare `set` field), breaking
the structured-results contract; the fix round guarded it and swept
the class per Mechanism 3, finding one sibling (a JSON int too large
for `float` raised `OverflowError`), now both per-field 422s. Pydantic
delegation is proven both present (wholesale, with location mapping)
and absent (subprocess import-blocker test). `UploadedFile` is
re-exported from `citry.ext.events` (wired by the orchestrator).
Review: approve, one low (two pydantic message assertions lock a
stable prefix, by design, since the full wording is third-party
surface).

**Goal:** the `data` schema machinery: schema-class conversion,
validation and coercion of the wire args payload, and the neutral
`UploadedFile` type.

**Read first:** `events.md` 3.3 (the `data` row, the coercion list, the
strictness paragraph and its audit rationale), 6.2 ("Files, precisely"
for the `UploadedFile` shape; the codec itself is v1.x); code: WP7's
module, `citry/component.py:154-162` (conversion parity),
`citry/util/` (existing validation helpers, if any; align rather than
duplicate).

**Build:**

- Schema conversion: any annotated class gets the dataclass treatment
  (same rules as State); dataclasses pass through; Pydantic models
  delegate wholesale to Pydantic when installed (soft import).
- Validation of an args payload against a schema: missing-required and
  extra-keys are per-field 422 entries; coercions exactly per the design
  list (`int`/`float` cross-coercion, `str` to `UUID | datetime | date |
  time | Decimal | Enum`, `list` to `tuple`/`set`, nested annotated
  classes from objects); everything else fails per-field. No
  ORM-by-primary-key coercion.
- `UploadedFile`: `filename`, `size`, `content_type`, synchronous
  `read()`, `save(path)`, `native`. Schema fields annotated with it (or
  `list[UploadedFile]`) validate only when the payload carries file
  objects (which only the v1.x multipart codec produces; until then a
  file-typed field receiving wire JSON is a per-field 422).
- The 422 error object shape: `{fields: {name: message}}` feeding
  `EventError`'s shape (WP11 owns `EventError` itself; this WP returns
  structured validation results, not exceptions, so WP11 can map them).

**Tests:** the full coercion matrix (each listed coercion, one failure
each); extra/missing keys; nested schema; Pydantic delegation when
installed and absence when not; `UploadedFile` construction and `save`;
determinism of error ordering (sorted by field name).

**Boundaries:** no multipart parsing (v1.x codec), no dispatcher, no
OpenAPI (WP14 reuses these models).

---

### ✅ WP10: serializer integration: the events manifest and runtime injection (v1 server)

**Status: landed 2026-07-13, review-approved.** The first implementer
run was lost to a transient tool-permission denial (it stopped honestly
at the reading stage, wrote nothing, and the review round caught it);
the fix round implemented the package in full. Built: `emission.py`
under `citry/ext/events/` (per-instance capture with WP8 mint and the
`_public`-gated values map; the `data-citry-events` tag per design 4.4,
emitted before the sibling `data-citry` tag; the runtime script tag on
the fixed `ext/events/runtime.js` URL asserted before the WP13 route
exists; the `_EVENTS_BOOTSTRAP_STUB` constant WP15 will fill; the
fixed-name `data-cid` root marker), hook registration in the events
`extension.py` alongside the WP12 hooks, and the two lifecycle
additions in the dependencies emission path
(`data-citry-css-class` sheet tagging and the additive `cssInstances`
presence record in the shape the landed `citry.js` consumer pins).
Review: approve, one low (a comment overclaim on the Const-proxy
unwrap in `capture_instance`).

**Amendment due (2026-07-16, the client-model round; owned by WP22):**
the per-class descriptor gained the `latest_wins`/`bundle` carriage
(events.md 4.4), which the runtime reads at queue time (events.md
5.6); the landed `emission.py` descriptor build emits only method and
timing hints. WP22 adds the two fields, omitted at their defaults
like the timing hints.

**Goal:** rendering an Events-declaring component emits the
`data-citry-events` manifest (instances 4-tuples with the public values
map, class descriptors) and injects the events runtime script, riding
the existing dependencies pipeline.

**Read first:** `events.md` 4.4 (the payload, exactly), 5 intro (runtime
injection via `on_dependencies`), 7.2 (`_public` gates the values map),
3.5 (descriptor hints); `spike-component-identity.md` (the two emission
additions the lifecycle layer needs, finding F-CI-4, and the
boot-order dependency F2) and `dependencies.md` 8.4 (the manager side that
consumes them); code: WP7's events extension module (the captured State metadata,
`state_data`, the `_public` field set, the per-class descriptor
config), WP8's `citry/ext/events/tokens.py` (`mint_state_token`),
`citry/ext/dependencies/emission.py` (the manifest emission pattern,
base64 armoring), `citry/serialize.py` (root markers, where instance
ids stamp), `citry/ext/dependencies/routes.py` (how `citry.js` is
served, for the runtime.js precedent WP13 will mirror),
`tests/test_deps_fragments.py`.

**Build:**

- At render/serialize of an Events-declaring instance: capture State via
  `state_data`, mint the token (WP8), build the public values object
  (`_public` fields only), and register the instance entry; once per
  class, build the descriptor (`events` map with method and resolved
  debounce/throttle hints).
- Emit the `data-citry-events` tag per 4.4, for documents and fragments,
  and BEFORE the sibling `data-citry` tag in the output (the spike's
  boot-order rule: whenever a call can fire, the events manifest must
  already be parsed; design 5.2)
  alike; fragments stay self-contained. Entries are 4-tuples, every
  string field base64, matching the sibling manifest's `_b64` helper in
  `emission.py`. (The token's base64url spelling is its own internal
  format, not part of the manifest's base64 armoring.)
- Inject the events runtime script tag via the `on_dependencies` emit
  hook whenever the page or fragment contains an Events-declaring
  component. The `src` is `citry.build_url("ext/events/runtime.js")`:
  the route path is fixed by design 3.8, so nothing is imported from
  WP13, and the test asserts the emitted URL before the route exists.
- Emit the inline bootstrap stub through the manifest (design 5.2 "Load
  ordering"): this WP wires the emission with the stub body held in
  `_EVENTS_BOOTSTRAP_STUB` in the events manifest-emission module;
  WP15 replaces that constant's content with the real queueing
  implementation. Ownership stated in both WPs.
- Stamp the fixed-name `data-cid` marker (space-separated instance ids,
  innermost last) on Events-declaring instance roots, alongside the
  existing per-instance markers (design 5.5's resolution root: a CSS
  selector cannot wildcard attribute names, so `closest()` needs the
  fixed name).
- Two emission additions the dependency manager's lifecycle layer needs
  (`dependencies.md` 8.4; `spike-component-identity.md` F-CI-4): tag each
  class-level `Component.css` sheet with `data-citry-css-class="<class>"`
  on the dependencies emission path (`dependencies.md` 7) so the manager's
  CSS cleanup can find the sheet, and emit a small instance-to-class
  presence record for instances that carry CSS but no `$component` JS, so
  the removal reconciler can count a class's live instances when nothing
  else registers them. The presence record's shape is pinned by the landed
  WP4 amendment that consumes it (`citry.js` `loadComponentScripts`): a
  top-level `cssInstances` key holding a list of `[classId, componentId]`
  pairs, each element base64-armored like the `calls` entries. The presence
  record is additive: it must not change
  the existing `data-citry` sibling manifest's format. The
  events-manifest-before-`data-citry` ordering specified above is what both
  spikes rely on (boot order, spike F2); keep it.
- Determinism: instance order follows render order; descriptor key order
  sorted.

**Tests:** observe-then-lock the emitted tag for a two-instance page
(volatile fields masked the way the fragment tests already do); values
map respects `_public`; no tag on pages without Events components;
fragment emission; descriptor content including an `@event(name=...)`
override and resolved timing hints; the events manifest is emitted before
its sibling `data-citry` tag; a `Component.css` sheet carries
`data-citry-css-class="<class>"`; a CSS-only instance (styles, no
`$component`) still emits its instance-to-class presence record.

**Boundaries:** no client code, no token verification, no routes. Do not
modify the `data-citry` sibling manifest's format.

---

### ✅ WP11: actions, return coercion, and result resolvers (v1 server)

**Status: landed 2026-07-13, review-approved on the first pass (two
lows).** Built as `actions.py`, `errors.py`, and `results.py` under
`citry/ext/events/`, tests in `test_events_actions.py` (56 tests,
17-mutation bite pass). The full 3.4 coercion table, resolvers strictly
after built-ins, the two-`Data` encode-time error, redirect warnings
that never reorder or drop, and the debug tracking of
constructed-but-unreturned actions shipped in full (a ContextVar
registry stored on the per-call events instance; no extension.py edit
was needed). Decisions pinned at implementation time and test-locked:
"debug mode" means the `citry` logger at DEBUG; user-raised 404/409
map to `not_found`/`conflict` with generic `"error"` for other
statuses (see the WP13 status block: this pinning became a tracked
protocol decision); `delay`/`wait`/`detail` omitted at defaults;
`EventError` restricts status to 400-599. `actions` and `EventError`
are re-exported from `citry.ext.events` (wired by the orchestrator).

**WP27 amendment (2026-07-23):** the history constructor names now produce
the existing `url` wire action, and `Download` now produces a dedicated raw
HTTP attachment response. The original reserved-name instruction below is
the historical WP11 boundary; WP27 records the active contract and its
server/client coverage.

**Goal:** the `actions` module (constructors), the return-value coercion
pipeline with result resolvers, `EventError`, and encoding to wire
actions.

**Read first:** `events.md` 3.4 in full (constructor table, return
table, the element-coercion rule, faithful ordering and the
redirect/data validation), 4.3 (wire action shapes, `delay`/`wait`,
targets), 3.7 (`EventError`), 6.2 (result resolvers and the codec
table), 7.5 (re-renders replace the subtree and never replay call-site
fills; no events-specific validation exists there); code: WP9, WP10
(the render action invokes render + fragment serialize + manifest),
`citry/citry_render.py` (`serialize` signature).

**Build:**

- `actions` namespace: `Render(element, target=None, swap="morph")`,
  `Data(value)`, `Dispatch(name, detail=None)`, `Redirect(url)`; all
  accept `delay: float = 0` and `wait: bool = True`. (`PushUrl`,
  `ReplaceUrl`, `Download` are v1.x: reserve the names, raise
  `NotImplementedError` with the version note.)
- Return coercion: `None` -> ack; action -> itself; `CitryElement` /
  `CitryRender` -> `Render` targeting the caller; `dict` -> `Data`;
  list/tuple -> ordered coercion of each; anything else -> the pointed
  error naming `actions.Data(...)`; result resolvers from
  `CitrySettings.event_result_resolvers` claim values before the
  fallback error (first non-`None` wins), never before the built-ins.
- Wire encoding: `Render` executes the element's render +
  `serialize(deps_strategy="fragment")` (fresh events manifest included
  via WP10); targets serialize as plain selector or `cid:` form; two
  `Data` actions in one result -> encode-time error; actions after a
  `Redirect` -> debug warning and documented unreliability, a `Render`
  alongside a `Redirect` -> debug warning (never reorder, never drop).
- `EventError(message, fields=None, status=422)` and the mapping of
  WP9's validation results into the 422 error object.
- Debug-mode tracking of constructed-but-unreturned actions (a cost
  design 14.1.3 records): constructors register on the per-call events
  instance in debug mode; after encoding, any constructed action
  missing from the return value logs a warning naming the handler. If
  this proves impractical, report with reasoning instead of shipping a
  half-measure.

**Tests:** each coercion row; resolver claiming and precedence; the
double-`Data` error; redirect warnings (and that order is preserved in
the encoded list); `delay`/`wait` serialization;
observe-then-lock one full encoded actions list for a two-action return.

**Boundaries:** no HTTP, no dispatcher loop, no client. `Download` and
the escape-hatch plumbing are WP13's (route-level) concern.

---

### ✅ WP12: the binding rewrite and template-load validation (v1 server)

**Status: landed 2026-07-13, review-approved.** Landed in two passes:
the binding rewrite (2026-07-08, `bindings.py` plus the extension
hooks) and a follow-up fix pass (2026-07-13) closing its review
findings. Two of those were maintainer decisions: bare `.throttle` is
valid at a 250 ms default, mirroring bare `.debounce` (design 5.1
modifier table updated first), and the design's file-input row now
carries the "where the type is statically known" qualifier the code
already honored. The rest: the unbalanced-parentheses load error now
names the binding and carries the standard template-location suffix
like every other load error; every load-error test asserts that
suffix; and two inline comments were corrected against the actual
call sites (`on_attrs_resolved` has two). Review: approve, one low
(the state-channel bare-throttle test does not also assert debounce
stays None).

**WP23 amendment, accepted 2026-07-19:** the landed component-tag rejection
remains correct for `:c-*` on semantic component targets, but is superseded for
`@c-*`. WP23 stage two owns the source-parent validation and client binding path for
component-target Citry handlers. It also treats `<c-element>` as its selected
HTML element, so both `@c-*` and `:c-*` use the ordinary element path there.
WP12 is not rerun independently.

**Goal:** `@c-*` and `:c-*` attributes rewrite to `data-cev-*` specs at
template load (stage one) and via `on_attrs_resolved` (stage two), with
the design's hard validation.

**Read first:** `events.md` 5.1 in full (vocabulary, modifier table,
update-event table, arguments-are-Alpine-expressions, the two-stage
rewrite paragraph, the validation paragraph), 7.2 (binding-driven checks
against `_public`/`_model`); code: WP7 (handler and State metadata),
`citry/ext/dependencies/scripts.py` (the `$component` textual-rewrite
precedent and its documented sharp edges), the `on_template_loaded` /
`on_attrs_resolved` hook signatures in `citry/extension.py`,
`citry/nodes/__init__.py:430-441` (the `c-*` channel the rewrite must
not touch).

**Build:**

- Stage one, `on_template_loaded` (string level): find `@c-*` / `:c-*`
  attributes, parse name/modifiers/value, build the per-element spec
  (owner class id, handler wire name, raw arg expression when present,
  modifiers, merged timing config), replace with `data-cev-*`
  attribute(s). Accept the known `<c-raw>` textual caveat and document
  it in code (design 5.1); do not attempt the node-level transform
  (v1.x).
- Stage two, `on_attrs_resolved`: the same recognition and rewrite for
  attributes contributed at render time (spreads); validation errors here
  are render-time, same wording.
- Validation exactly per 5.1: event values name declared handlers (name
  part only); `:c-*` keys name public State fields, `_model` members
  when two-way; modifier legality (the full load-error list: unknown
  modifiers, second poll time segment, `.lazy`+`.on:`, any update-timing
  modifier on a one-way binding, `.lazy` on statically-known committed
  controls, key filters on non-keyboard events, file inputs two-way);
  any `@c-*` or `:c-*` attribute on a `<c-*>` component tag was a
  template-load error in this landed batch; WP23's amendment above replaces
  the `@c-*` half with a parent-owned client binding on semantic component targets and
  exempts `<c-element>` for both channels. Unknown binding shapes fail with the
  template location.
- The compiled contract, published: the `data-cev-*` attribute
  vocabulary is a WP12 invention (events.md 5.1 defines the author
  syntax and says it compiles to `data-cev-*`, but not the compiled
  names or payload shapes), and WP17.1/WP17.2 must match it exactly.
  Document it
  in the bindings module as a module docstring plus a frozen constant
  enumerating each emitted attribute name, its payload keys, and the
  encoding. WP17.1 and WP17.2 read this contract, never just the test
  fixtures.
- The template-scan data WP7 needs: two-way binding targets, collected
  per component (this feeds nothing in v1, since `_model` defaults to
  `_public`, but expose the scan results for diagnostics).

**Tests:** observe-then-lock rewritten template output for a
representative template (every vocabulary form); each validation error
with location and message content; stage-two rewrite through a spread
(`attrs` kwarg + `c-bind` spread); `<c-raw>` caveat documented by a test
that pins the current (imperfect) behavior explicitly as such; plain
`@click`/`:class` pass through untouched.

**Boundaries:** no client runtime, no expression evaluation (that is
Alpine's, client-side), no grammar or compiler changes (the textual
approach is the v1 decision).

---

### ✅ WP13: dispatcher, routes, codecs, CSRF, URL builder (v1 server)

**Status: landed 2026-07-14, review-approved (one fix round; review 1
raised 8 findings, all resolved; re-review: approve).** Built
as `dispatcher.py`, `routes.py`, `codecs.py`, and `csrf.py` under
`citry/ext/events/`, with the runtime.js stub at
`client/citry-events.js` (WP15 replaces its content). The review
escalated five decisions rather than improvising; all five were
maintainer-decided 2026-07-14 and are DONE (the record below replaces
the retired decision file this block used to cite). Public surface wired by the
orchestrator: `get_event_url`, `EventsDispatcher`, `TransportContext`,
`EventRequest`, `CallEvent`, `X_CITRY_EVENTS_HEADER`.

**WP13 follow-up decisions, all resolved (2026-07-14/15):**

1. **Wire codes for user-raised 404/409/unlisted statuses**: the
   protocol was extended (Option A) with `not_found` (404), `conflict`
   (409), and the catch-all `error` row carrying any other user-raised
   400-599 status, across spec 4.5, `result.schema.json`, and golden
   fixtures in one set; the former strict-xfail tripwires are real
   conformance tests, plus a full named-code/status pairing negative
   sweep.
2. **`csrf=False` and callables under Django**: design 3.5's wording
   was rescoped to the citry-side layer (the host framework's own
   token check, like Django's `CsrfViewMiddleware`, is governed by the
   host and stays on; a callable runs on top of the baseline and any
   host check).
3. **Async handlers under ASGI**: `URLRoute.handler_async` carries an
   async twin the ASGI adapter prefers; `async def` event handlers are
   awaited natively under ASGI; sync adapters byte-identical.
4. **Form/GET typed-field binding**: source-aware binding per
   events.md 3.3 (string transports bind `int`/`float`/`bool` with the
   HTML bool vocabulary; JSON stays strict; non-finite floats rejected
   at every layer, ingress and egress).
5. **Envelope byte cap**: `_max_envelope_bytes` is engine-wide only
   (events.md 3.5 and decision 8 amended).
   Related, same date: the envelope moved to the
   `application/citry-events+json` vendor media type; plain
   `application/json` on the per-event route is the flat-JSON codec
   for external API clients; the `X-Citry-Events` header floor covers
   every JSON-bodied call (events.md 6.2 codec table and 7.4).

**WP26 closeout (2026-07-22):** the per-event multi-call rejection now
mirrors one error per parsed call, preserving the envelope id and each valid
epoch. The local `_counter` template is mechanically pinned to protocol spec
section 10; spec 4.5 records strict-JSON result repair and batch isolation;
`Decimal` egress is repaired per result while validation rejects non-finite
prebuilt `Decimal` values; state-token and fingerprint JSON reject non-finite
numbers with a field-pointed mint error; and selector-render followed by a
self-addressed action emits the designed debug warning without reordering.
All six findings have regression coverage.

**Goal:** the wire comes alive: the dispatch pipeline, the three routes,
the JSON/urlencoded/GET codecs, the CSRF layers, the compat mode, and
URL building.

**Read first:** `events.md` 3.3 (the injectable shapes: the handler
`request` carries `form`/`files` on top of WP2's leaner `RouteRequest`;
`event` carries name, instance id, transport, raw args), 3.6
(`_context` and the pipeline order), 3.7
(hook timing, error mapping), 3.8 (routes, batch semantics, the curl
example), 4.2/4.3 (envelopes; epoch echo), 6.1 (TransportContext, the
dispatcher boundary, and the responsibilities table with per-item
implementation notes; that table is the pipeline checklist), 6.2
(codecs, the compat/no-JS mode, direction
split), 7.4 (CSRF layers and guards resolution); code: WP2's
`RouteRequest` and `call_maybe_sync`, WP7 to WP11 (including WP8's
`citry/ext/events/tokens.py` surface),
`packages/protocol/events/v1/spec.md` (WP5; the named capabilities
baseline constant), `citry/ext/dependencies/routes.py` (route
style), `citry/citry.py` (`build_url`, and `get_component_by_class_id`
for resolving the URL's class id), `citry/util/misc.py`
(`format_url`).

**Build:**

- `EventsDispatcher.dispatch(envelope, ctx)` (sync; async variant awaits
  async handlers, offloads sync via WP2's `call_maybe_sync`): envelope schema
  validation -> per call: component/event resolution (URL-authoritative
  on the per-event route; body fields must match when present) -> token
  verify (WP8) -> updates -> args validation (WP9) -> `on_event` emit
  (`result="first"` veto) -> `_context` -> guards (most-specific-wins) ->
  handler with by-name injection -> return coercion and encoding (WP11)
  -> `on_event_result` emit (map) -> re-sign state (render action's
  manifest, else a `state` action placed before the handler's actions,
  4.3) -> echo the request's `epoch` per
  result. `on_event_error` on uncaught exceptions; tracebacks only in
  debug. Capabilities resolution lives here: an absent `capabilities`
  field resolves to the protocol baseline constant (WP5), and the
  dispatcher passes the resolved set into WP11's action-encoding step,
  which downgrades at encode time (`morph` to `replace`) and never
  emits an action kind outside the set. Debug-mode hint: when the
  handler mutated state and the encoded actions contain nothing visible
  (no render, no data, no dispatch), log the hint that a re-render is
  probably missing (design 3.4).
- Routes via `Extension.urls`: `call` (POST, batch; per-call statuses
  inside a 200), `runtime.js` (GET; serves the file at
  `EVENTS_RUNTIME_SRC = Path(__file__).parent / "client" /
  "citry-events.js"`, mirroring the dependencies `RUNTIME_PATH` /
  `serve_runtime` precedent; ship a stub file there until WP15 lands
  its bundle), `e/{class_id}/{event}` (GET|POST; HTTP status
  mirrors the call). Method configs govern the per-event route only.
- Codecs: JSON identity; urlencoded (fields -> args payload,
  `_citry_state`/`_citry_instance` reserved); GET query codec (args from
  query; token from `_citry_state` only when the handler declares
  `state`). `CitrySettings.event_payload_codecs` prepend.
- CSRF: the always-on floor (`X-Citry-Events` header requirement +
  `Origin`/`Sec-Fetch-Site` same-origin) applied to runtime-originated
  requests; `"auto"` host-token integration under Django (the route runs
  under Django's middleware untouched; test explicitly that no
  `csrf_exempt` is needed); `False` and callable per the 3.5 table; GET
  handlers exempt from the token layer.
- Compat/no-JS mode: `Accept: text/html` or a form post without the
  header -> primary render action's HTML as the body, redirect -> 303,
  errors -> their status.
- `RouteResponse` escape: a handler returning one bypasses the envelope
  (per-event route only; batch rejects loudly).
- URL builder: `component.events.url(name, query=..., fragment=...)` and
  `get_event_url(...)` on `build_url` + `format_url`; the standard
  unmounted error.
- Envelope caps (size, calls length 16) with 413/400 mapping.
- GET handler responses carry `Cache-Control: no-store` (design 3.5 and
  section 16's default until GET caching lands), via WP2's response
  headers.
- Runtime envelope validation is structural Python (field presence,
  types, the `calls` cap), not JSON-Schema loading; WP5's schemas bind
  at test time through WP18's checker, so the protocol package never
  becomes a runtime dependency.

**Tests:** the full pipeline against a fixture component under FastAPI
and Django test clients (parity per adapter); pipeline-order assertions
(a guard sees `_context`'s result; `on_event` can veto; epoch echoes);
URL-vs-body mismatch rejection; capabilities downgrade (an envelope
without `capabilities` gets `replace`, never `morph`); the `no-store`
header on a GET handler; batch with mixed outcomes; each CSRF
layer (incl. the Django no-`csrf_exempt` proof and a cross-origin
rejection); compat mode (form post round trip, 303 on redirect); GET
tokenless vs state-declaring; the escape hatch on the per-event route
and its batch rejection; error statuses per code.

**Boundaries:** no client bundle content (the runtime.js route serves a
placeholder until WP15), no multipart, no WebSocket, no OpenAPI.

---

### ✅ WP14: the ViewEvents shim and the OpenAPI command (v1 server)

**Status: landed 2026-07-14, review-approved (one fix round; re-review:
approve, zero findings).** Built as `view_events.py` and `openapi.py`
under `citry/ext/events/`, command registered on the extension
(`commands = [OpenApiCommand]`); `ViewEvents` re-exported from
`citry.ext.events` (wired by the orchestrator). The fix round's
substantive change: the OpenAPI request body documents only
`application/x-www-form-urlencoded`, which was correct against the
routes as they then stood. WP13's follow-up decision 5 (2026-07-15) made
plain `application/json` on the per-event route the flat-JSON codec for
external API clients (events.md 6.2). The 2026-07-22 amendment documents
both content types with the same schema reference and locks them in the
OpenAPI document fixture. Determinism is proven byte-identical across hash
seeds. The gate run after this stream
updated three stale `test_extension.py::TestCommands` baselines that
encoded the old no-built-in-commands contract. Optional export not
wired: the maintainer chose the CLI as the public surface on 2026-07-22;
the document builder remains an internal command helper.

**Goal:** the verb-dispatch compatibility shim and
`citry ext run events openapi`.

**Read first:** `events.md` 10 (the Component.View migration and the
shim's contract, including its extra route `e/{class_id}` and "verb
handlers omit `state`"), 9 (the OpenAPI derivation, `--only-data`), 3.8
(route namespace context); code: WP13's routes, WP9's schemas, WP7's
events module (the per-component handler list and `data` schemas),
`Citry.components` / the component registry in `citry/citry.py` (the
enumeration the walk uses), the
`ExtensionCommand` machinery (`citry/command.py`, an existing command
for the registration pattern), `docs/design/extensions_commands.md`
(skim).

**Build:**

- `ViewEvents` (importable from `citry.ext.events`): reserves
  `get`/`post`/`put`/`patch`/`delete`/`head`/`options` handler names;
  one extra route `e/{class_id}` dispatching by HTTP method; about 40
  lines on top of Events; docstring per the design (name events after
  actions once a component has more than one mutation).
- `openapi` ExtensionCommand: walks registered Events-declaring
  components; one operation per (component, event) over
  `ext/events/e/{class_id}/{event}`; `operationId`
  `<ComponentName>_<event>`; request body (query params for GET) from
  the `data` schema (named schemas in `components/schemas`); the 422
  field-error shape; `data`-typed responses from JSON-returning
  handlers' return annotations; `--only-data` filter; `--out` file or
  stdout. Handler docstrings become operation descriptions.
- Determinism: operations and schemas sorted.

**Tests:** shim round trip (a `post` handler served at `e/{class_id}`
by method); observe-then-lock a full OpenAPI document for a two-component
fixture app; `--only-data`; docstring propagation; a GET handler's query
parameters.

**Boundaries:** no served `openapi.json` route (v1.x), no client
manifest command, no AsyncAPI.

---

### ✅ WP15: client: Alpine embedding, scopes, and magics (v1 client)

**Status: landed 2026-07-14, review-approved (one fix round; re-review:
approve, one low).** The JS workspace exists at
`packages/js/citry-client/` (pnpm workspace member; pinned Alpine
3.15.12 + `@alpinejs/morph` 3.15.12, esbuild; deps recorded in the
root `pnpm-lock.yaml`), and the committed bundle landed at
`citry/ext/events/client/citry-events.js`, replacing WP13's stub;
`_EVENTS_BOOTSTRAP_STUB` in the emission module carries the real
queueing body. The anchor registry, epoch-per-anchor bookkeeping,
three-way state split (anchor side), link-before-morph with the
`$state` inert fallback, and the six magics are in, tested through the
Playwright e2e harness (run locally with the additive-install venv
discipline; the gate runs them importorskipped). The fix round closed
two real findings: a head-placed `<c-js />` could leave a root without
its boundary scope (the interceptInit hook now self-heals right before
Alpine initializes the root), and pending unsent `$state` writes were
lost when a send failed (the rejection handler now restores updates
not overwritten in flight; failure semantics beyond the design's
happy-path rules are recorded as a WP16 hand-off note). The low:
one unbalanced backtick pair in the module docstring.

**WP23 amendment, accepted 2026-07-19:** WP23 stage two extends the landed
Events-anchor registry with general client-instance records, replaces the empty
boundary entry with each client-active instance's stable `scope`, and adds
managed `effect`/`reactive`. Components with no Events, `$component`, or client binding
activity remain free. This is WP23 scope, not a retroactive WP15 rerun.

**Goal:** `citry-events.js` exists with the Alpine layer: the pinned
bundle, boot, scope attach with isolation, and the six magics.

**Read first:** the WP6 spike report and the component-identity spike
(`spike-component-identity.md`; both are normative here, the first for
pins and Alpine/morph surprises, the second for the two-identity model,
the epoch-per-anchor guard, the three-way state split, and the
link-before-morph ordering), `events.md` 4.2 (the per-anchor epoch), 5
intro (bundle and boot), 5.3 (link before morph, the `$state`
inert-fallback), 5.5 in full (scopes, the two identities and the index,
isolation, magics table, `$state` write rules, the three-way split,
local-first example), 4.4 (manifest consumption), 7.2 (`_model` gate
client-side);
code: WP13's events routes module (the `EVENTS_RUNTIME_SRC` path this
WP's bundle lands in), WP4's hooks,
`citry/ext/dependencies/client/citry.js` (style and
the manifest observer pattern), the vuetify audit's isolation mechanism
(`docs/design/alpinejs/alpine-vuetify-audit.md`).

**Build (in `packages/js/citry-client/`, a new JS workspace this WP
creates):** the workspace holds `package.json` with the pinned deps and
a committed lockfile, uses esbuild as the only build tool, and commits
the build output at `citry/ext/events/client/citry-events.js`, so
Python packaging and serving never run node. The repo has no JS
toolchain today; this WP introduces it, per the decided plan, and WP6's
report has already validated the acquisition.

- The bundle: pinned Alpine 3.15.12 + `@alpinejs/morph` 3.15.12 (the
  spike's exact pins), compiled in and served as a classic iife script
  evaluated right after citry.js (a page module loses the manifest
  race, spike F2): observer and decorator registration happen at
  evaluation time, only `Alpine.start()` waits for DOMContentLoaded;
  the console warning when a second
  Alpine instance is detected. Register the plugin and call Alpine.morph
  (the named export is the installer, spike F1); register
  `Alpine.addRootSelector` for the instance marker (spike F5); add a
  pinned-version canary test over the private APIs the runtime touches
  (`addScopeToNode`, `_x_dataStack`, `cloneNode`); the scope purity
  test asserts against the scope stack, not `Object.keys` on the merged
  proxy (spike F6). Teardown when an instance leaves the DOM is the
  dependency manager's job, not this runtime's: WP4's amended removal
  reconciler (`dependencies.md` 8.4) sweeps the live `[data-cid-<id>]`
  elements and runs the retired id's cleanup, so the events runtime rides
  that lifecycle and needs no morph `removed` hook (component-identity
  spike F-CI-3/F-CI-5). Land the build output at
  `citry/ext/events/client/citry-events.js`, the fixed path WP13's
  `EVENTS_RUNTIME_SRC` reads, replacing its stub file.
- Replace the content of `_EVENTS_BOOTSTRAP_STUB` (WP10's placeholder
  in the events manifest-emission module) with the real queueing stub
  body: defines a queueing `Citry.events`, registers the WP4 context
  decorator.
- Manifest processing: `data-citry-events` observer (sibling pattern to
  the dependencies observer); registry of instance id -> class, token,
  values; class descriptors.
- Scope attach at manifest time (eager), per design 5.5's pinned
  mechanics: the reactive State object held in the registry, keyed by the
  anchor (the stable client-internal identity of a DOM position, design
  5.5), with a component-id-to-anchor index mapping the faithful, changing
  id onto the stable anchor (the State object is never an element expando:
  morph swaps clone nodes and drop expandos), magics resolving via
  `closest("[data-cid]")` to the innermost component id, then through the
  index to the anchor's registry entry, an empty boundary scope entry
  per root via `addScopeToNode` carrying the audit's isolation
  truncation (private-API use on a pinned version, documented in a
  header comment), and nothing ever written into user `x-data`.
- The anchor registry and its tie to the DOM (design 5.5, the
  component-identity spike): an anchor is a runtime object holding the
  current component id, the current class id, the epoch counter and
  highest-applied epoch, the reactive State, the pending unsent writes, and
  the current token. The component-id-to-anchor index is the only tie; no
  anchor attribute rides the DOM and no node-keyed WeakMap is used (a
  wholesale morph swap orphans it, spike F-CI-1/F-CI-6).
- Epoch bookkeeping lives on the anchor, not per component id (design 4.2,
  5.5): the counter and the highest-applied epoch are per anchor, because
  the id changes every render. WP16.2 does the send-side increment and
  WP16.1 the apply-side comparison; this WP owns
  the structure.
- The three-way state split on an incoming render, chosen by comparing the
  anchor's current class id against the render token's class field (`c`),
  design 5.5: same class reconciles (server wins per field except pending
  unsent writes; the scope and `$state` identity persist); a different
  class discards the old state and adopts the server token and values
  wholesale, rebuilding the boundary scope; a plain-HTML render makes the
  anchor non-interactive and discards its state and scope. WP16.1 applies
  these inside `applyActions`; this WP owns the anchor-side state handling.
- Link before morph (spike F-CI-2): the fresh component id is bound to the
  anchor and the anchor's State updated before the morph runs, so the
  incoming fragment's bound expressions resolve during the patch. `$state`
  stays inert (an empty read, never a throw) for a marker-bearing node
  whose id is momentarily unregistered mid-morph; confirm this against the
  real magics as this WP lands (design 16.1's deferred item).
- Magics: `$state` (reactive over public values; writes to `_model`
  fields queue updates, non-model writes throw the pointed error),
  `$loading` (callable, per-handler variant), `$error` (last envelope or
  null, cleared on success), `$sendEvent`, `$onEvent`. `$loading` and
  `$sendEvent` validate handler/event names against the class
  descriptor and throw the pointed error naming the declared handlers.
  `$component` payload gains `state`, `sendEvent`, `onEvent` via the
  decorator.
- The reconcile rule on incoming values (the same-class branch of the
  three-way split above): server wins per field except pending unsent
  local writes.

**Tests:** extend the e2e harness (Playwright): scope isolation between
nested instances; `$state` read reactivity and write gating; the
reconcile rule; the anchor-side of the three-way split (same-class
reconcile keeps `$state` identity, a different class rebuilds it, a
plain-HTML render discards it, driven by stubbed incoming render
metadata, no real morph); the faithful component id updates on the
registry entry through a re-render while the anchor's `$state` identity
persists; `$loading`/`$error` transitions driven by a stubbed
transport; magic availability inside user `x-data` within a component;
user `x-data` on the instance root itself coexists with the scope (its
checked on the scope stack, since Alpine's merged proxy hides keys
from `Object.keys`, spike F6); an element carrying two
instance ids resolves magics to the innermost; unknown names in
`$loading`/`$sendEvent` throw the pointed errors.

**Boundaries:** no transport (WP16.2 owns it, stubbed here), no
bindings (WP17.1/WP17.2), no morph application logic beyond what
scope-survival needs (WP16.1 owns applyActions).

---

### ✅ WP16: client: transport, queue, envelope, and the actions applier (v1 client)

Split 2026-07-17 into three sub-packages, because the single package
was overloaded; each is sized for one coding agent, same as every
other WP. **WP16.1** is the actions applier and the anchor lifecycle,
**WP16.2** is transport, envelope, and CSRF autowiring, and
**WP16.3** is the event queue, a dependency DAG the maintainer
flagged as nuanced enough to be its own package. They land in that
order, and each sub-entry carries its own status, goal, reading list,
build, tests, and boundaries. Two carried-over notes live here so the
sub-entries stay lean: WP15's hand-off note on send-failure semantics
resolves across WP16.2 and WP16.3 (the failure paths have designed
semantics: every settle path releases the queue, design 5.6), and the
2026-07-16 rewrite for the ratified client-model round (events.md
14.3) rides in the sub-entries (the uncorrelated-id lifecycle, keyed
linking, the five machinery requirements, and the preservation rules
in WP16.1; the R3 surfacing contract spread across all three).

#### ✅ WP16.1: client applier: `applyActions`, the anchor lifecycle, and keyed linking

**Status: landed 2026-07-17, review-approved on the first pass; its four
low findings closed by WP26 on 2026-07-22.** The interrupted first run's near-complete applier was
surveyed as untrusted, verified line by line, and completed with
seven verified fixes (self-addressed actions route by the send-time
correlation instance through a new ApplyContext.instance field;
cid-targeted liveness is element existence; the parent-stamped
composite key is carried across a reconcile self-render, see the
caller-key preservation below; keyed matching under `inner` scopes to the
container; markEpochApplied covers every self-addressed swap kind;
pointed retired-instance messages; every top-level fragment script is
post-patch machinery, never a morph root). All five machinery
requirements, the three-way split through real morph, keyed linking
with the horizon cut, the preservation opt-ins, and the R3 surfacing
are e2e-proven: 16 new tests including all 19 protocol fixtures
replayed through the applier, five mutation rounds proving every test
bites. `preserveCallerKey` is ratified as designed behavior
(2026-07-17): the same-class reconcile branch re-stamps the
parent-authored key the fragment cannot re-emit, forced by morph
comparing root keys before any hook, and it is captured in design 5.3
and 5.5.

**WP26 disposition:** graph physical-placement caps now distinguish adjacent
mirror copies from a multi-root placement, with a legacy adjacency fallback
only outside the graph. A `cid:` event action deliberately dispatches once on
the first live root (rather than duplicating document/global and `onEvent`
delivery across every root); events.md 4.3 and a mirrored-root test pin that
decision. Exact retired/epoch debug breadcrumbs are asserted. The plain-HTML
teardown concern was already superseded by A8 coverage proving each component
callback cleanup runs exactly once, so no duplicate test or code change was
needed.

**WP23 amendment, accepted 2026-07-19:** client binding adoption before incoming-root
initialization, first-live-root ownership transfer, dynamic `<c-component>`
target replacement, and exact client binding cleanup extend this landed lifecycle in
WP23 stage two. The original WP16.1 package remains historical scope.

**Goal:** every result envelope applies: `applyActions` with faithful
ordering and per-action liveness, the uncorrelated-id lifecycle with
keyed linking, the five machinery requirements, morph with the
`updating` hook and the composite-key callback, the preservation
hooks, and the epoch comparison at apply time; every drop observable,
every promise settled.

**Read first:** `events.md` 4.3 in full (the action table, ordering
and redirect rules, `delay`/`wait`, targets, the multiple-`data`
rule), 4.2 (epoch mechanics; this WP owns the
apply-iff-strictly-greater comparison), 5.2 (the drop event's
`reason` contract, the lifecycle DOM events and their `detail`
contract, the `applyActions` public-surface row), 5.3 (morph rules
incl. the composite key attribute and its callback, the manifest-tag
carriage, busy attributes, the ignore marker and its instance-root
warning), 5.5 in
full (the preservation block and its pending-writes re-apply rule, the
three-way split, the uncorrelated-id lifecycle, keyed linking with the
horizon cut, the five machinery requirements, multi-target mirroring);
the component-identity spike
(`spike-component-identity.md`; normative for routing by correlation
id, the per-anchor epoch, the faithful `data-cid`, and
link-before-morph) and the keyed-morph spike (`spike-keyed-morph.md`;
normative for the class-id-scoped key form, the hot-callback rule
F-KM-8, and the preservation matrix the e2e assertions encode); the
two analyses (`analysis-nested-anchor-continuity.md`,
`analysis-target-other-renders.md`) for the scenario walkthroughs the
tests replay; WP5's fixtures (result fixtures replay through
`applyActions` in tests, via `fixtures/index.json`); code: WP15 (incl.
its status block's hand-off note), WP21's emitted attributes (the
composite key and the ignore marker this WP consumes).

**Build:**

- The uncorrelated-id lifecycle in `applyActions` (design 5.5, the two
  spikes): route each response to the caller's anchor by
  the correlation id (the envelope `id`), never by a component id; the
  morph lands the server's fresh `data-cid-<id>`, so the DOM always shows
  the server's current id. Link-before-morph generalized to every id
  in the fragment (machinery item 1); the three-way split for the
  correlated caller (same class reconciles, a different class adopts
  the new token wholesale, a plain-HTML render retires the anchor);
  reset for every uncorrelated id; keyed linking for `#c-key` matches
  (same class plus same composite key within the applied region,
  recursive per region, duplicates matched in document order with a
  debug warning) with the horizon cut at link time; targeted renders
  as remove-and-replace; multi-target mirroring of one shared instance
  with duplicate-manifest-tag stripping. Wire the
  `updating` hook (ignore-marker `skip()` with the instance-root debug
  warning; the pending-draft focused-value guard, whose
  `hasUnsentDraft` check reads a draft record this WP defines and
  WP17.2 populates for the mid-debounce stage) and the composite
  `key` callback (a bare attribute read, spike F-KM-8); do not
  wire a morph `removed` hook for teardown, because instance teardown on
  removal is the dependency manager's removal reconciler (WP4's amendment,
  `dependencies.md` 8.4), which the events runtime rides.
- The five machinery requirements verbatim (design 5.5): pre-swap
  registration of every fragment id; applier-owned manifest-tag
  insertion after morph patches (both tags, unmarked, first insertion
  only on multi-target); the anchor retirement sweep with the
  pending-writes debug warning; per-action liveness re-checks in
  faithful list order, within one result and across results in one
  batch envelope (retired-caller responses: `data` resolves,
  instance-mutating actions drop with reason `retired`; a
  self-addressed `event` action on a dead id drops with a debug log);
  the recurring-timer retirement structure with the no-double-poll
  dedupe (this WP owns the structure; WP17.1 wires the binding timers
  onto it).
- `applyActions`: faithful order; `render` (morph via `@alpinejs/morph`
  per the pinned call block in design 5.3, pairwise multi-root
  fallback;
  `replace`/`inner`/`append`/`prepend`/`remove`/`none` variants; plain
  selector targets via `querySelectorAll` with the zero-match warning;
  `cid:` targets),
  `data`, `state` (registry update, no DOM; any received token refresh
  applies to the registry before the actions array runs, 4.3), `event`
  (bubbling
  CustomEvent under the raw name), `redirect` (applied in place when
  reached; later actions still apply and merely race the navigation,
  design 4.3; the client never drops or reorders), `url` reserved
  (v1.x producer). `delay` (seconds) blocking by default,
  `wait: false` scheduling; scheduled actions re-resolve their targets
  and re-check liveness when they fire, not when their response
  arrived (design 4.3's timing-fields rule).
- Epoch comparison at apply (design 4.2, 5.5): instance-mutating
  actions apply iff the response's epoch is strictly greater than the
  anchor's highest-applied, per anchor, not per component id since
  the id changes every render (the counters are WP15's structure;
  WP16.2 does the send-side increment); the guard is the net beneath
  the queue.
- Surfacing (design 5.2, the R3 contract): the one drop event
  (`citry:events:stale`) and the lifecycle CustomEvents with the
  `{instance, class, event}` detail contract plus the event-specific
  fields design 5.2's examples pin (`ok` on `:after`, `els` on
  `:swapped`, `reason` on `:stale`); every promise settles; this WP
  fires the apply-side pieces (`:swapped`, and `:stale` with reasons
  `epoch` and `retired`) and builds the shared dispatch helper the
  other two sub-packages extend (WP16.2 adds `:before`/`:after`/
  `:error` and reasons `timeout` and `version`; WP16.3 adds reasons
  `cancelled` and `superseded`); never a console throw for a
  routine race.
- Preservation hooks (design 5.3/5.5): the post-patch re-apply of
  `:c-*` bindings incl. pending-writes fields, the guard-kept-control
  exemption, and the busy re-stamp for linked anchors whose
  loading count is nonzero after a swap (new roots plus the
  triggering element where it survived the patch, design 5.5).
- Capabilities: apply-side downgrade tolerance (the advertising half
  is WP16.2's envelope).
- `Citry.events.applyActions` as the public action-interpreter entry
  point (design 5.2's table pins its contract).

**Tests:** replay every WP5 result fixture through `applyActions` in a
DOM harness (no transport; results are fed directly). The lifecycle:
a self-render lands the server's fresh
`data-cid-<id>` in the
DOM while the anchor's `$state` identity and epoch persist (routing by
correlation id, not by component id); the three-way split through a real
morph (a plain-HTML render retires the anchor and runs the deps
reconciler's teardown exactly once); an unkeyed child under a parent
render resets (fresh anchor, pending writes gone, the retirement
warning logged when they were
non-empty); a `#c-key`-matched child links (draft, `$loading`,
subscription, and epoch pair survive; the form-field flip: two keyed
inputs swap positions and their typed values follow); the horizon cut
drops a linked child's in-flight render while its `data` resolves; a
targeted render retires and re-mints, and a keyed match inside its
fragment links; the caller-inside-target result drops the following
self-render per per-action liveness (same drop across results in one
batch envelope); a multi-target render mirrors one shared instance and
strips duplicate manifest tags; a stale-epoch response's
instance-mutating actions drop while its `data` resolves (drop event
reason `epoch`); the two
preservation poles (design 5.5): fast typing over a patch loses
nothing, and submit-then-clear clears a still-focused flushed field;
ordering incl. a delayed non-blocking action re-resolving its target
at fire time;
zero-match warning; the lifecycle event sequence.

**Boundaries:** no wire code (WP16.2 owns envelope, fetch, and CSRF),
no queue (WP16.3), no declarative bindings (WP17.1/WP17.2 wire
listeners, timers, and form collection onto this WP's structures), no
multipart switch (v1.x), no WebSocket, no server-side changes (WP21
owns the `#c-*` emission; report gaps instead of patching around
them).

#### ✅ WP16.2: client transport: envelope, fetch, CSRF, and the public surface

**Status: landed 2026-07-17, review-approved on the first pass; its three
low findings closed by WP26 on 2026-07-22.** Envelope construction per 4.2, the real fetch transport
under `application/citry-events+json` with the header floor and CSRF
autowiring, the bounded timeout with drop-on-late-arrival, version
skew surfacing, and the public surface per 5.2, proven against a live
test server in e2e. The chain's mid-gate failure was environmental
(leftover additive e2e packages made the gate's pytest phase run
browser tests; the venv-cleanliness pre-check is now part of every
gate brief) and cleared before the final gate.

**WP26 disposition:** Playwright is now an intentional declared development
dependency, so the former shared-venv contamination report is superseded.
Client-minted errors omit `fields` while explicit server fields still pass
through unchanged. The early bootstrap stub now queues both
`registerTransport` and `applyActions`; registrations drain in a declaration
pass before queued configure/send/apply calls, so a pre-runtime configured
custom transport is usable deterministically.

**Goal:** calls go over the wire: envelope construction, fetch POST
with CSRF autowiring, promise settlement, the epoch send path, the
bounded timeout, version-skew surfacing,
`configure`/`registerTransport`/`on`, capabilities advertising, and
the download escape hatch.

**Read first:** `events.md` 4.2 in full (envelope fields, epoch
mechanics, capabilities, the `calls[]` array), 4.3 (results answer
calls; the error envelope shape), 4.5 (the version-skew flow this WP
surfaces), 5.2 in full (send/on semantics,
`configure` incl. the 30 s timeout
default, the escape-hatch table, the code examples, load ordering),
6.1 (the client transport interface), 6.2 (the vendor media type),
7.4 (client CSRF attachment), 3.8 (the per-event URL template and the
batch endpoint); code: WP15 (the registry and bootstrap stub), WP16.1
(`applyActions`, which this WP hands results to), WP13's events
routes and dispatcher (the live server the round-trip test boots).

**Build:**

- `Citry.events.send(...)` / instance `sendEvent`: envelope construction
  (protocol string, correlation id, capabilities, calls with
  token, pending updates, epoch), fetch POST to the per-event URL for a
  single call or the batch endpoint for an envelope carrying several
  (which calls share an envelope is WP16.3's dequeue logic; this WP's
  send path carries one or more calls either way),
  carrying `Content-Type: application/citry-events+json` (the envelope's
  vendor media type, design 6.2), with
  `X-Citry-Events` and the configured CSRF source (default: read the
  `csrftoken` cookie, send it as `X-CSRFToken`; the `csrf` config
  object of design 5.2 overrides cookie, header, or token source),
  promise resolution
  from the `data` action, structured rejection from errors; `opts`
  carries `timeout` and `wait`.
- Epoch send path (design 4.2): increment the anchor's counter on
  every send and echo it in the call (the counters are WP15's
  structure; WP16.1 owns the apply-side comparison).
- The bounded timeout (design 5.6): the `configure({timeout})` 30000
  ms default with per-call override; a timeout rejects the caller's
  promise with the timeout error, fires `citry:events:error`, and
  drops a late-arriving response with the drop event (reason
  `timeout`) and a debug log (releasing queue dependents is WP16.3's
  settle wiring).
- Surfacing on the send path (design 5.2): `citry:events:before`
  (cancellable: `preventDefault()` stops the send and rejects the
  caller's promise), `:after` (`ok`), `:error` (the error envelope),
  through WP16.1's dispatch helper; client-minted rejections carry
  the `{status: 0, code, message}` shape.
- Version-skew surfacing (design 4.5, 5.2): the two skew signals of
  4.5, a `capabilities` mismatch and the `stale_state` flow, fire
  `citry:events:stale` with reason `version` through WP16.1's
  dispatch helper (no call promise rides it; a stale-state call
  settles through its own error result, 5.2's reason table); the
  default handling, a soft reload prompt, is configurable.
- Content-Disposition detection on responses -> blob download path (the
  escape-hatch consumer).
- Capabilities: advertise `morph` + baseline in the envelope (the
  apply-side downgrade tolerance is WP16.1's).
- The public client surface of design 5.2 and 6.1: `Citry.events.on`,
  `Citry.events.configure({transport, url, csrf, timeout})`, and
  `Citry.events.registerTransport(name, {send, subscribe?})` with the
  fetch transport registered through it (the function ships in v1 even
  though the
  first alternative transport is v1.x). Design 5.2's tables pin
  each method's contract and `configure`'s field set; match them
  exactly.

**Tests:** envelope construction locked against WP5's call fixtures
(protocol string, correlation id, token, pending updates, epoch);
CSRF header attachment under a cookie and under the token-source
override; per-event URL versus batch endpoint selection; promise
resolution from `data` and structured rejection from an error result;
the timeout: a hung request rejects at the configured timeout with
`citry:events:error`, and a response arriving after it drops with the
drop event (reason `timeout`) and a debug log; a
`citry:events:before` listener's `preventDefault` stops the send and
rejects the caller's promise; a version-skew signal (a `stale_state`
error result, and a capabilities-mismatch downgrade) fires
`citry:events:stale` with reason `version` through the dispatch
helper, with no call promise riding it, and the default soft-reload
prompt is configurable; `configure` field by field per 5.2's
table;
`registerTransport` routes `send` through a registered fake; a
Content-Disposition response takes the blob download path; the
capabilities field advertises `morph` plus baseline; one full
Playwright round trip against a live WP13 server (the counter).

**Boundaries:** no queue logic (WP16.3 owns edges, batching, knobs,
and busy state), no applier changes beyond handing results to WP16.1,
no bindings (WP17.1/WP17.2), no multipart switch (v1.x), no
WebSocket, no server-side changes (report gaps instead of patching
around them).

#### ✅ WP16.3: client queue: the dependency DAG

**Status: landed 2026-07-17, review-approved on the first pass; its four
low findings closed by WP26 on 2026-07-22.** The queue as the ratified explicit dependency DAG:
enqueue-time containment edges, all-edges-settled dispatch,
independent branches parallel, co-eligible batching into one
envelope, early-cancel with the R3 reasons, the `@event` knobs read
from the descriptor (`latest_wins` drop/abandon with `superseded`
rejections, `bundle=False` send-alone), `wait: false` bypass, timeout
release, and busy-from-the-gesture, all e2e-proven.

**WP26 disposition:** dependent-release tests now hold the predecessor and
assert exact `dispatched`/`waitsOn` edges before deterministic rejection or
timeout. Removed and still-connected-but-ownerless Element targets cover both
dequeue deadness branches, including stale reason, no wire call, and busy
cleanup. Gesture busy uses per-trigger/per-anchor outstanding counts, so two
concurrent `wait:false` sends cannot clear each other. Recurring keys moved to
an internal bindings-only parameter; arbitrary public `opts.recurring` no
longer changes the always-Promise `send()` contract.

**Graph-first amendment, accepted 2026-07-19 and consolidated 2026-07-20:** a
component-tag `@c-*` binding keeps the source parent anchor as its
queue owner while separately checking the physical child target's liveness
and busy marker. The general logical-ownership and physical-liveness update to
the landed queue belongs to `alpinejs_plan.md` A8.

The normative design is events.md 5.6 (the DAG), with the decision record in
14.3.4.

**Goal:** sends ride an explicit dependency DAG: containment edges
computed at enqueue and re-verified at dequeue, settled-means-applied
release, eligible-together batching with the `@event` knobs,
dequeue-time early cancel, `wait: false` bypass, busy from the
gesture, and the tick-skip rule; every settle path releases
dependents.

**Read first:** `events.md` 5.6 in full (the DAG: nodes, edges,
containment resolution and re-verification, settled means applied,
failure settles, batching and the sixteen-call cap, the knobs,
`wait: false`, busy, tick-skip, the recorded fallback), 3.5 (the
`latest_wins`/`bundle` rows and the per-handler-on-purpose paragraph
below the table), 4.2 (the `calls[]` array; epoch as the net beneath
the queue), 4.3 (the timing fields the settle definition leans on),
5.2 (the drop-reason rows `cancelled` and `superseded`; `sendEvent`
opts), 5.5 (the graph-selected owner and physical-marker liveness lookup;
machinery item 5's fire-time re-resolution), 14.3.4
(the decision record incl. the 2026-07-17 DAG amendment); code: WP15
(the anchor registry), WP16.1 (`applyActions` and the
applied-means-settled signal), WP16.2 (the send path), WP22's
descriptor fields (the queue knobs this WP reads at queue time).

**Build:**

- The DAG (design 5.6): queued events are nodes; at enqueue the new
  event gains a dependency edge to every not-yet-settled event whose
  graph-selected dispatching owner is the same logical owner as, an ancestor
  of, or a descendant of its own. Physical markers locate live regions but do
  not define that ancestry. An event dispatches
  when every edge it holds is settled; independent branches run in
  parallel; edges only point at earlier events.
- Settled means applied: an event holds its dependents until its
  result's actions have applied (a data-only result settles at
  promise resolution; a blocking delay holds, a `wait: false` action
  does not); every failure path releases the dependents (transport
  error, error result, timeout: the timeout mechanism is WP16.2's,
  this WP wires dependent release into every settle path).
- Dequeue: re-verify logical containment against the active graph revision,
  physical liveness against the live DOM, and the not-yet-settled events (new
  edges go only to events enqueued
  earlier that are still unsettled, preserving the earlier-events-only
  invariant that keeps the graph acyclic; a later-enqueued overlap
  already holds its own enqueue-time edge to this event). Map the stored
  logical dispatch owner into the active graph revision without deriving it
  from the physical carrier. A missing logical owner or dead carrier cancels
  early (never sent, promise rejects `cancelled`, drop event with reason
  `cancelled`, debug line).
- Eligible-together batching into one `calls[]` envelope posted to
  the batch endpoint (each call
  its own promise and result; the sixteen-call cap splits in order),
  honoring `@event(bundle=False)` and `@event(latest_wins=True)` from
  the class descriptor (design 3.5 and 4.4 pin that carriage; WP22
  lands it across the three server surfaces, the `@event` kwargs in
  `handlers.py`, the descriptor emission in `emission.py`, and the
  protocol descriptor schema and spec, so this WP consumes the
  fields and reports any residual gap rather than patching
  server-side); supersession rejects with code `superseded`, sent or
  not.
- `wait: false` joins no graph: it fires immediately, gains no edges,
  and no event gains an edge to it; late responses are left to the
  epoch net (WP16.1's comparison).
- Busy from the gesture (design 5.6): `data-citry-busy` stamps and
  `$loading` counts from enqueue, one continuous state through queue,
  flight, and apply; busy clears on every settle path (WP16.1's
  linked-anchor re-stamp keeps it visible across parent renders).
- The tick-skip rule: a `@c-poll` tick that fires while the binding's
  previous call is still queued or in flight is skipped with a debug
  breadcrumb (WP17.1 wires the timers themselves).

**Tests:** a child send waits behind a slow parent poll and observes
the applied render (fresh token, fresh DOM) before it fires; two
sibling widgets never wait on each other; an event enqueued under two
overlapping in-flight scopes dispatches only after both settle (one
edge each); a network-failed send and a timed-out send release their
dependents; a dequeue-time dead element cancels early (reason
`cancelled`, promise rejected, nothing sent); eligible-together sends
bundle into one envelope with per-call promises, `bundle=False` sends
alone, and `latest_wins=True` drops the queued predecessor and abandons
the in-flight one (rejections with code `superseded`); a
`wait: false` send fires immediately and holds nothing, and its late
response is epoch-dropped (late render dropped, promise resolved,
drop event reason `epoch`, with WP16.1's comparison); busy spans the
queue from the gesture.

**Boundaries:** no envelope or fetch changes (WP16.2), no applier
changes (WP16.1), no bindings (WP17.1/WP17.2), no server-side changes
(WP22 owns the knob carriage; report gaps instead of patching around
them).

---

### ✅ WP17: client: bindings runtime, expressions, and forms (v1 client)

Split 2026-07-17 into two sub-packages, because the single package was
overloaded; each is sized for one coding agent, same as every other
WP. **WP17.1** is the
bindings runtime (delegated listeners, expressions, `@c-poll`, and the
`$component` props form) and **WP17.2** is forms, two-way and
one-way bindings, and the preservation wiring. They land in that
order. Both carry the 2026-07-16 rewrite for the ratified client-model
round (events.md 14.3): bindings ride the queue and the
uncorrelated-id lifecycle, and binding state respects anchor
lifecycles instead of capturing anchors.

#### ✅ WP17.1: client bindings: delegated listeners, expressions, `@c-poll`, and client props

**Status: landed 2026-07-17, review-approved (one fix round;
re-review: approve, zero findings).** The delegated listener layer
over the data-cev-* specs with the full modifier matrix (bare
debounce and throttle at 250 ms, keyboard filters, explicit timings),
Alpine-expression args, `@c-poll` riding the timer-retirement
machinery (hidden-tab pause proven), and the `$component` props
form live end to end: the fix round wired the config-object
normalization into `citry.js` (the reviewer-prescribed territory
extension, called out), with resolved values, defaults including
function defaults, constructor-array types, and pointed
validation-failure skips proven in e2e. Discovery recorded for a
maintainer ticket decision: `citry.js` consumes a pending manifest
call at the FIRST registerComponent for the class, so a second
same-class registration misses the page-load flush (pre-existing,
unchanged).

**WP23 amendment, accepted 2026-07-19:** WP23 stage two adds component-target
client bindings for Alpine and parent-owned Citry handlers, source-facade evaluation
for whole Alpine expressions and optional Citry argument expressions,
source-parent Citry handler dispatch, grouped-listener behavior according to
the spike verdict, and the accepted managed context helpers. HTML-element
bindings and the landed props declaration/resolution remain WP17.1's
historical scope.

**Goal:** the compiled `data-cev-*` event specs come alive: delegated
listeners with the full modifier table, Alpine-expression args, poll
timers that respect anchor lifecycles, and multi-binding elements;
plus `$component`'s config-object form with declared props.

**Read first:** `events.md` 5.1 in full (the tables, the
arguments-are-Alpine-expressions block, the `#c-*` block), 5.5
(bindings riding the scope; machinery item 5, the timer rules; the
client-composition block: the two `$component` forms, the prop
definition fields, validation timing, and the open passing side), 5.6
(bindings enqueue like any send; the tick-skip rule; busy from the
gesture), 3.8 (the per-event URL template); code: the `data-cev-*`
contract WP12 documents in the bindings module (the attribute names
and payload shapes; its locked tests are examples, the documented
contract is the source), WP15/WP16.1/WP16.3 (the scope, lifecycle,
and queue structures this WP rides),
`citry/ext/dependencies/client/citry.js` (the `$component`
registration this WP extends, in its style), WP13's events routes
(the server the e2e tests boot).

**Build:**

- Delegated listeners per DOM event type at the document root, reading
  `data-cev-*` specs; modifier semantics per the 5.1 table (prevent,
  stop, self, once, key filters, debounce with the 250 ms bare default,
  throttle) with the `_debounce`/`_throttle` descriptor defaults from
  the manifest. Every send resolves its anchor at fire time from the
  element, never from an anchor captured in a listener, timer, or
  debounce closure; a fire-time miss, or a hit on a class that does
  not declare the event, drops the send with a debug log (design 5.5
  machinery item 5), never a throw or an unhandled rejection.
- Arg expressions: evaluate via Alpine bound to the owning element
  (`$state`, `$el`, `$event`, user scopes visible); non-object results
  raise the pointed runtime error naming the binding.
- `@c-poll`: interval sends, hidden-tab pause; timers keyed to the
  element, one timer per element, so a morph survivor dedupes against
  the fresh instance's own manifest-initialized interval instead of
  double polling, and a replaced region's timer dies with it (the
  retirement structure is WP16.1's; this WP wires the binding timers
  onto it). A tick that fires while the binding's previous call is
  still queued or in flight is skipped with a debug breadcrumb (the
  queue's tick-skip rule, design 5.6).
- Multiple event bindings on one element (the explicit e2e case).
- The `$component` config-object form (design 5.5, decided
  2026-07-17): accept `{init, props}` alongside the bare callback
  (the registration lives in the dependencies runtime, `citry.js`;
  extend it there in its style, with prop resolution and validation
  in the events runtime). Prop definitions carry `type`, `required`,
  and `default` (a function default is called per instance);
  validation runs at instance initialization, before init,
  failing loudly naming the component and the prop; resolved values
  arrive on the callback context under `props` (an empty object for
  the bare form), reactive via plain Alpine reactivity. The passing
  side is design-open (events.md 16.1), so in this WP values resolve
  from declared defaults; prop reactivity through a live supplier is
  exercised when the passing side lands.

**Tests (Playwright against a WP13 server):** the modifier matrix
(prevent, stop, self, once, key filters, debounce against the
descriptor defaults, throttle); arg expression evaluation incl. the
non-object pointed error; fire-time anchor resolution (a queued
listener firing on a region a render just replaced drops with a debug
log, never a throw); a `@c-poll` region replaced mid-interval stops
polling (no dead interval, no double poll after a morph) and a tick
overlapping its previous call skips with the breadcrumb; the
multi-binding element; the props form: a bare callback sees an empty
`props`; a config object validates (a missing required prop and a
type mismatch fail loudly naming component and prop; defaults resolve
per instance, and an object default produced by a function is not
shared between instances); init receives resolved values under
`props`.

**Boundaries:** no two-way or one-way binding application and no form
collection (WP17.2); no queue or lifecycle changes (extend WP16.1 and
WP16.3, do not fork them); no passing mechanism for props (the
design-open piece, events.md 16.1; report the gap if a test seems to
need one); no new server code (report gaps instead); no multipart.

#### ✅ WP17.2: client forms: two-way and one-way bindings, form collection, and preservation wiring

**Status: landed 2026-07-17, review-approved (one fix round); its two low
findings closed by WP26 on 2026-07-22.** Two-way and one-way state bindings end to end (the control
update-event table with `.lazy` and `.on:`, one call carrying the
field update plus the named event), form collection with the
source-aware typed binding, and the preservation poles both proven in
e2e with real held-response races: the mid-typing draft survives
patches at every unsent-draft stage while a legitimate server clear
still lands on unfocused controls.

**WP26 disposition:** known controls now mark an unsent draft on their
natural `input`/`change` event even when `.on:` or `.lazy` selects a later
flush trigger; a pre-Enter server render preserves value and focus, then Enter
flushes and clears the mark. The LiveSearch pitch fixture was simplified back
under its published 32-line bound and the assertion no longer carries a
two-line allowance. The pitch suite also extracts the published Counter,
LiveSearch, and ContactForm blocks and compares their executable class source
verbatim (apart from the harness-only `citry = c` registration), so the docs
and fixtures cannot drift independently.

**Goal:** two-way bindings send one call carrying the `$state` write
plus the named handler; one-way bindings re-apply through reactivity
and rebind across renders without stacking; form submits collect
named controls; and the draft bookkeeping feeds WP16.1's patch-time
guard, closing the preservation contract's two poles.

**Read first:** `events.md` 5.1 (the update-event table, `.lazy` and
`.on:`, the forms example), 5.3 (the preservation pointer and keying
guidance, incl. the sibling-window depth rule), 5.5 (the preservation
block incl. the pending-writes re-apply and the guard's two draft
stages), 5.6 (two-way flushes enqueue like any send; piggybacked
updates), 4.2 (the `updates` field and the piggyback rule), 7.2 (the
`_model` gate); code: the `data-cev-*` contract WP12 documents,
WP17.1's listeners (the update events ride them), WP16.1 (the guard
and re-apply structures this WP feeds), WP13's events routes (the
server the e2e tests boot).

**Build:**

- Two-way bindings: the update-event table (input/change per control,
  `.lazy`, `.on:` override), one call carrying the `$state` write plus
  the named handler, enqueued per the dependency DAG (design 5.6);
  pending updates piggyback on any earlier call.
- The draft bookkeeping the patch-time guard consumes: populate
  WP16.1's draft record for the unflushed mid-debounce stage, so
  `hasUnsentDraft` covers both draft stages (a pending unsent `$state`
  write, and the unflushed DOM draft before it; design 5.5).
- One-way bindings: Alpine `effect()` over `$state.<key>` applying to
  the control. After a self-render the reconcile keeps the State
  object's identity, so re-application comes from reactivity alone;
  verify it. After a parent render or a targeted render the innermost
  id under a bound control may have changed (reset or link, design
  5.5), and the old effect subscribed to a retired anchor's State
  object no future write will touch, so re-walk bound controls under
  the applied region and rebind. The rebind must not stack: it tears
  down (or reuses) the element's previous effect and any timer before
  installing new ones, so a control that lived through three parent
  renders holds one binding and one timer, not three. Value
  application on rebind follows the preservation rules (design 5.5): a
  pending-writes field re-applies its preserved draft, and a focused
  control's unflushed draft is never clobbered.
- Form collection on submit-triggered events: named controls into the
  args payload, expression args win on collision, mirrored against the
  urlencoded codec in one parity test.

**Tests (Playwright against a WP13 server):** the three pitch examples
of `events.md` section 2 pass end to end at (or under) their line
counts; live-search focus/caret survival; the draft-under-parent-render
pair from the nested analysis: a draft typed into an unkeyed child
resets when the parent's poll response lands (observable through the
retirement warning, never silently), and the same page with `#c-key`
keeps the draft, whose debounce flush then delivers it with the fresh
token; the two preservation poles as live typing (fast typing over a
patch loses nothing, whether the draft sits in `$state` or is still
mid-debounce; submit-then-clear clears a still-focused flushed
field); form 422 -> `$error.fieldErrors`
inline display; one-way re-application
after a self-render (reactivity alone) and after a parent render (the
rebind walk, exactly one live effect and one timer per control);
`.lazy` and `.on:` behaviors; parity of form-post (no-JS)
and runtime submission payloads.

**Boundaries:** no new server code (report gaps instead); no multipart;
the queue, applier, and listener structures are WP16.1's, WP16.3's,
and WP17.1's (extend them, do not fork them).

---

### ✅ WP18: conformance runner and the e2e gate (v1 verification)

**Status: landed 2026-07-22, review-approved after one fix round.** The
Python conformance runner replays all 19 golden fixtures through the real
dispatcher, masks only declared volatile paths, compares strict JSON, and
schema-validates every result. One consolidated suite locks exact Django and
FastAPI parity plus exact-event-path Django middleware behavior; the existing
Django CSRF suite remains the security authority. Browser acceptance ports the
django-components form submission and fragments examples plus the
unicorn-style live search, with the relevant cases green on Chromium, Firefox,
and WebKit. The fragments port exposed and forced the browser GET transport:
stateful and stateless token rules, flattened protocol/id/capabilities,
correlation echo, morph negotiation, epochs, and pending-write preservation are
now locked. The protocol README records Python 0.2.0 conformance. The full
repository gate passed after the fix round; independent re-review reported no
remaining implementation findings.

**Goal:** the protocol fixtures run green against the Python dispatcher,
and the cross-adapter e2e suite is the merged definition of v1-done.

**Read first:** `events.md` 11 (the conformance rules, volatile paths),
13 (v1.0 exit criteria), 15 (falsifiers are the design's numbered
outcomes that would prove it wrong; the spike report plus this WP
retire or trip falsifiers 1, 2, 4, and 5); WP5's package; code: WP13
and the WP16.x/WP17.x test suites (extend, do not duplicate).

**Build:**

- A pytest module in the citry package that registers the fixture
  component from the protocol spec, feeds every fixture call envelope
  through `EventsDispatcher`, and asserts the result matches the
  fixture everywhere except the paths it declares volatile; it also
  schema-validates everything the dispatcher emits (vendored JSON
  Schema checker in the citry package's test deps only; respect the uv
  workspace dependency ownership rule in CLAUDE.md when adding it).
- The consolidated e2e matrix: the WSGI/ASGI parity run (same suite,
  Django and FastAPI hosts), and the falsifier-driven checks not already
  covered: the Django CSRF review case (no `csrf_exempt` anywhere),
  the per-event URL middleware case (a host middleware attached to one
  event path fires for it and not others).
- The three example ports of design 13 v1.0 item 5, as e2e tests: the
  old django-components form-submission example, the fragments example,
  and a unicorn-style live search (the migration guides of WP19 lift
  their code from these).
- A short conformance section in the protocol package's README recording
  "Python: passing as of <version>".

**Tests:** this WP is tests; its own acceptance is the full
`.venv/bin/python scripts/check.py --reporter agent` green including the
new suites.

**Boundaries:** no production-code changes beyond what red conformance
legitimately forces (each such fix must cite the fixture it satisfies);
no new fixtures without a matching spec change (WP5's inversion rule).

---

### ✅ WP19: docs and sibling updates (v1 close-out)

**Status: landed 2026-07-22, review-approved after two fix rounds.** The
server-events guide, security expansion, API-reference and public-docstring
pass, discoverability links, and sibling design and changelog updates are in
place. Documentation fencing now protects Events bindings inside code blocks;
the static site exports the Events runtime used by standalone examples; and
minification preserves Citry ownership-cap comments. Focused tests, all 12
Chromium docs journeys, the strict docs build, and the full repository gate
passed. Independent re-review reported no remaining findings. Links from the
guide to the four migration pages remain WP20-owned and land with their real
targets so the strict internal-link guard stays truthful.

**Goal:** user-facing docs exist, sibling design docs reflect reality,
and the roadmap row is updated.

**Read first:** `events.md` 13 (item 5), 10 (the migration content to
turn into guides), CLAUDE.md's house style for user-facing docs (lead
with the symptom; no internals; section-title rules) and the docstring
conventions; `docs_site/` structure (where guides live);
`docs/design/extensions_roadmap.md` section 3.

**Build:**

- User guide (docs site): the section 2 pitch flow (counter, live
  search, form) and the showcase demos (the unnumbered showcase section
  before section 1: six pain-focused copy-paste examples; verify each
  against the tested e2e suites and
  fix the doc, not the tests, on drift), the trace, State and the security doctrine (public
  State is client input), bindings and magics reference tables, the
  events-naming convention (`MyCard:submit`), the list-identity and
  child-continuity guidance (`#c-key` on reorderable `<c-for>` items
  and on interactive children under re-rendering parents, design 5.3),
  including the keying-depth line: a key rescues reordering within
  one sibling window only, so keep a keyed element at the same tree
  position across conditional branches (design 5.3),
  the faithful-order authoring note (dispatch before the render that
  destroys its audience, design 4.3), the
  `js_data`-versus-State split (design 5.4), the fresh-tree golden
  rule highlighted (design 7.5: a handler's render shares no inputs and
  no fills with the original render; everything is passed explicitly),
  and the multi-target rendering distinction (maintainer-requested
  2026-07-15): a render action whose selector matches several elements
  inserts ONE shared instance mirrored in each place (one State, one
  token; a later self-render updates every copy together, the cart
  badge in the desktop header and mobile drawer being the canonical
  case), while independent per-region widgets need distinct renders
  (one `Render` action per target, each its own instance); frame it
  around what the reader sees (both badges always agree) and the
  natural first mistake (expecting one copy to update alone).
- The security page: visibility ("anything in State is visible in page
  source"), CSRF per host, guards, the client-input doctrine.
- Migration content is WP20's (one page per source framework); this
  WP's guide links to those pages.
- Public docstrings pass over the WP7 to WP14 surface (they render into
  the API reference; audit against the docstring conventions).
- Sibling updates: `events.md` status header (v1 shipped state);
  `extensions_roadmap.md` section 3 row updated to point at events.md
  and mark status; `dependencies.md` 9.5 note that the slot is filled
  (one line, positive framing per the writing rule); CHANGELOG entries
  consolidated for the release.

**Tests:** the docs build passes; example code blocks in guides are
lifted from the tested e2e fixtures (state where each came from in the
PR description, not in the docs).

**Boundaries:** no new features, no design changes; discrepancies found
while documenting are reported, not silently fixed.

---

### ✅ WP20: migration guide pages (v1 close-out)

**Status: landed 2026-07-23, review-approved after the adversarial fix
rounds.** Four source-framework guides and their shared capability matrix are
now maintained docs-site content. Every page includes the mental-model shift,
before/after examples, syntax mapping, the dynamic-attribute trap, deliberate
exclusions, and a link to the common v1/v1.x/v2/dropped ledger. The
livecomponents guide keeps the two storage steps independently shippable and
distinguishes server storage from `_public` browser projection.

The Citry examples live in `docs_site/snippets/` and execute in an isolated
verifier, with docs tests covering source expansion and the shared authoring
contract. Focused docs tests, Ruff, the strict docs build, and Chromium docs
tests passed. Review fixes also removed stale normative claims about Alpine,
Unicorn request payloads, livecomponents parity, multipart delivery, State
visibility, CSRF overrides, direct file responses, and client runtime
packaging. The independently reviewed result has no remaining WP20 findings.

During verification, the aggregate non-browser docs suite exposed a separate
component-class finalizer lock wait. The reviewer confirmed that WP20's
subprocess-isolated snippets did not introduce it. The core lifecycle follow-up
removed Citry lifecycle work from component class garbage collection; see
[`component_initialization.md`](component_initialization.md).

**Goal:** one documentation page per source framework, each with
before/after code, plus the parity matrix as a maintained artifact.

**Read first:** `events.md` 10 in full (the per-audience arguments and
the dropped-features list), 13 (item 5); WP18's example-port tests (the
tested code the pages lift from); CLAUDE.md's user-facing docs style
(symptom-first, wrong-then-right example pairs, no internal jargon);
the docs_site content layout and WP19's page structure.

**Build:**

- Four pages: from Component.View (the `ViewEvents` shim path), from
  django-unicorn, from Tetra, from livecomponents. Each page: the
  audience's mental-model shift in one opening paragraph; a
  before/after code pair per major concept (lifted from WP18's tested
  ports where they exist, authored and run otherwise); the syntax
  mapping table, which on every page calls out the attribute
  interpolation trap (attribute values are raw strings in citry, so
  href="{{ url }}" renders literal braces; the citry spelling is
  c-href="url"); what is gone by design, with the acceptance argument
  (from section 10's dropped list, reworded per house style).
- The livecomponents page leads with the two-step path: step one, a
  mechanical per-component port keeping server-held behavior via
  `_storage = "server"`; step two, per component and optional, the
  switch to signed tokens. Each step independently shippable.
- The parity matrix: every capability each prior tool has, this
  design's answer, and a delivery tag (v1, v1.x, v2, or dropped with
  its argument); one artifact all four pages link, and the acceptance
  checklist for v1 (design 13).
- Example code in pages is lifted from tested fixtures and e2e suites;
  provenance stated in the PR description, not in the docs.

**Tests:** the docs build passes with the new pages; build-check guards
green; every code block traces to a tested source.

**Boundaries:** no new features, no design changes; discrepancies found
while writing are reported, not silently fixed.

---

### ✅ WP21: the `#c-*` attribute channel (parser to rendered HTML)

**Status: landed 2026-07-17, review-approved (one fix round; re-review:
approve); its two doc-comment lows closed by WP26 on 2026-07-22.** The channel works parser to
rendered HTML: a new atomic grammar rule accepts `#c-*` attribute
names (grammar untouched elsewhere; zero atomicity impact on the
compound-atomic cascade, whole crate suite green twice), the AST
carries the meta-attribute kind, the compiler emits server-side
evaluation, and rendered HTML carries the class-id-scoped composite
key attribute and the morph-ignore marker per the keyed-morph spike
verdict. The Mechanism 4 enumeration is in the workflow record: no
LangImpl method, PyO3 surface, or `.pyi` change was needed beyond the
enumerated updates; placement errors carry the offset-adjusted
template location, and the transparent-component `#c-key` error names
the tag the way registration derives it. WP26 corrected
`_apply_valued_markers` to describe the shared innermost-last convention
without claiming client root resolution uses `data-citry-key`, and extended
the mirrored `HtmlAttr` stub docstring to include `#c-*` metadata. Original
section follows.
Added 2026-07-16 by the client-model round
(events.md 14.3.1). This is the one package in this plan that touches
the Rust contract, so CLAUDE.md Mechanisms 1, 2, and 4 apply in full
(prior-art header, an `ExitPlanMode` plan before editing, and the
cross-binding audit), and the section 6 rule below carves it out by
name. Sequenced before the client wave: WP16.1 consumes its emitted
attributes.

**Goal:** `#c-key` and `#c-ignore` parse, validate, compile, and
render. A template authoring `#c-key="item.id"` on a plain element or
a `<c-*>` tag produces the composite `data-citry-key` attribute on the
rendered element (on every root marker element for a component child),
`#c-ignore` produces the runtime ignore marker, and the load-error
rules of design 5.1 are enforced with template locations.

**Read first:** /CLAUDE.md in full (the high-risk list names every
file this WP touches), `crates/citry_template_parser/AGENTS.md` and
that crate's deep agent INDEX (the Pest atomicity gotcha before any
grammar edit); `events.md` 5.1 (the `#c-*` block: the two members, the
validation rules, the template-authored-only v1 rule for spreads), 5.3
(the composite attribute: its name, the class-id-scoped value form and
the empty scope segment for plain elements, all-roots stamping for
multi-root children, and the rule that the plain `key` attribute is
never touched), 14.3.1 (the decision record), and the keyed-morph
spike's verdict (`spike-keyed-morph.md`: the class-id-scoped pin, and
F-KM-7, never a per-render id inside a key); code:
`crates/citry_template_parser/src/grammar.pest`, `src/ast.rs`,
`src/parser.rs`, `src/compiler.rs`, `src/lang/lang.rs` and the five
per-language impls, `crates/citry_core_py/src/lib.rs`,
`packages/py/citry_core/citry_core/_rust.pyi`, and the Python
consumers the emission lands in (the nodes layer under
`packages/py/citry/citry/` and `serialize.py`'s marker emission).

**Build:**

- Grammar: `#c-*` attribute names parse as their own channel (a new
  rule; check the atomicity cascade against every rule the change
  touches before editing). Unknown `#c-*` names, a valued `#c-ignore`,
  a valueless `#c-key`, and `#c-ignore` on a component tag are
  parse-time errors carrying the template location, per design 5.1.
- AST and compiler: `#c-key`'s value rides the same server-evaluated
  expression machinery as `c-*`. On a plain element the compiler emits
  the composite `data-citry-key` attribute inline (empty scope segment
  plus the evaluated key). On a component tag the key is carried as
  framework metadata on the component node, never as a kwarg (plain
  `key` and `c-key` component inputs stay completely ordinary). The
  compiler output format change is a contract change: enumerate the
  whole cross-binding surface per Mechanism 4 in the WP's plan (the
  five `LangImpl` surfaces, noting which need real work versus a stub
  update; the PyO3 registration; the `.pyi` stub; the Python wrapper;
  the Rust and Python tests).
- Python side: the nodes layer hands the evaluated component-tag key
  to the serializer; serialize stamps the class-id-scoped composite
  value onto every root marker element of the child (multi-root
  children key all roots); `#c-ignore` emits
  `data-citry-morph="ignore"`. A `#c-*` key arriving through an
  attribute spread or dynamic attributes is a render-time error naming
  the fix (the template-authored-only v1 rule, design 5.1).
- Determinism: emitted attributes are byte-deterministic given fixed
  inputs (never iterate a set into output; the standing rule).

**Tests:** Rust parser and compiler tests authored observe-then-lock
(run the real parser and compiler on representative templates, observe
the output, lock it; the established throwaway-harness discipline; run
the suite twice to catch non-determinism, per the crate's AGENTS.md).
The load-error cases assert message content, not just the error type.
Python render tests lock the emitted HTML for: `#c-key` on a plain
element, on a single-root child, on a multi-root child (all roots
stamped), and inside `<c-for>` (per-item evaluation); `#c-ignore` on
an element; the spread and dynamic-attrs render errors; and a guard
test that plain `key` and `c-key` behave exactly as before (the
ordinary-attribute contract, including `key=""` normalizing to the
boolean attribute).

**Boundaries:** no client runtime changes (WP16.1 consumes the emitted
attributes), no events-extension changes, no `@c-*`/`:c-*` rewrite
changes, and no grammar changes beyond the `#c-*` channel. If the
channel appears to require changing an existing rule's atomicity or
the shape of an existing AST node, stop and report (Mechanism 2
territory) instead of improvising.

---

### ✅ WP22: the `@event` queue knobs and their descriptor carriage (v1 server amendment)

**Status: landed 2026-07-17, review-approved on the first pass (zero
findings).** `@event(latest_wins=..., bundle=...)` exists end to end
on the server: validated decorator parameters, descriptor carriage (a
bare handler carries neither field), and the protocol amendment
(descriptor schema, spec, fixtures, index) as one coherent set; the
protocol self-checks type-lock both knobs as booleans. Combined gate
after WP21+WP22: all 10 phases passed with no fixes needed. Original
section follows.
Added 2026-07-16 by the client-model round
(events.md 14.3.4 and 14.3.6): the ratified queue design gave
`@event` two knobs that the landed server predates. This WP amends
three landed surfaces in one pass; the matching amendment records
live in the WP5, WP7, and WP10 status blocks, and WP16.3 consumes the
result.

**Goal:** `@event(latest_wins=..., bundle=...)` exists end to end on
the server: the decorator accepts and validates the two knobs, the
per-class descriptor carries them to the client, and the protocol
package's descriptor contract admits them.

**Read first:** `events.md` 3.5 (the `latest_wins` and `bundle` rows
and the per-handler-on-purpose paragraph below the table), 4.4 (the
descriptor carriage and its example), 5.6 (the queue semantics the
knobs govern, for the docstrings); code:
`citry/ext/events/handlers.py` (the `@event` decorator and its
options record), `citry/ext/events/emission.py` (the descriptor
build), `packages/protocol/events/v1/` (`descriptor.schema.json`,
`spec.md` section 7, `validate.py`; per WP5's authoring-inversion
rule the schema, spec, and validation change land as one set).

**Build:**

- `@event` gains `latest_wins: bool = False` and `bundle: bool = True`:
  boolean-validated (a non-bool is a pointed class-definition error,
  matching the timing-value errors), stored on the handler metadata.
  The knobs are per-handler only, the design's own rule (3.5: two
  call sites that need different semantics are two handlers), so the
  decorator is their single declaration point.
- Descriptor emission: each event's descriptor entry carries
  `latest_wins` and `bundle`, omitted at their defaults the way the 4.4
  example shows (only non-default values ride, keeping the emitted
  descriptor small and byte-deterministic).
- Protocol package: `descriptor.schema.json`'s `eventHint` gains the
  two optional boolean fields; spec section 7's descriptor prose and
  example document them as client hints the runtime reads at queue
  time; `validate.py`'s descriptor smoke example exercises them. No
  fixture envelope embeds a decoded descriptor, so the golden
  call/result pairs are untouched.

**Tests:** extend the WP7 decorator matrix: non-bool rejection with
message-content assertions, `@event(latest_wins=True)` and
`@event(bundle=False)` round-tripping into the handler metadata, and
the defaults when omitted. Observe-then-lock the emitted descriptor
for a class with one knobbed handler and one bare handler (the bare
entry carries neither field). The protocol package self-checks stay
green (`test_events_protocol_package.py` picks up the schema and
example changes).

**Boundaries:** no client code (WP16.3 reads the fields), no queue
logic, no dispatcher changes, no envelope or schema changes beyond
the descriptor. If carrying the knobs appears to require anything
outside the three named surfaces, stop and report.

---

### ✅ WP23: client props and Alpine-boundary research (historical)

**Status: research and focused spikes complete. Do not dispatch this work
package.** The maintainer selected the graph-first Alpine target and
`$c-props` on 2026-07-20. The normative design is
[`alpinejs.md`](alpinejs.md), and the implementation was split into work
packages in [`alpinejs_plan.md`](alpinejs_plan.md), whose A0-A10 sequence
has now landed. The body below is the
historical research ledger; its old architecture and spelling rationale do not
override those documents.

The stage-one exploration landed 2026-07-17 at
[`alpinejs/exploration-client-props-passing.md`](alpinejs/exploration-client-props-passing.md)
(adversarially critiqued and revised): it evaluated and selected the now
superseded registered-Alpine-directive candidate. It also recommended
plain-Alpine reactivity via one supplier effect
per carrying element, and pins validation timing and the identity
rules. The maintainer ratified and amended those calls in the
2026-07-17 decision record: supply and Alpine handlers are authored on
the child component tag and relocated, invalid updates never retain a
stale value, init preserves parent-before-descendant ordering, direct
`x-for` should need no wrapper once a valid named client identity exists, and
the context gains managed Alpine helpers.
The round-two exploration landed 2026-07-18 at
[`alpinejs/exploration-x-props-round-2.md`](alpinejs/exploration-x-props-round-2.md).
It designs the manifest-backed client binding and general instance registry, the init
ancestry DAG, managed helpers and reactive `scope`, update validation, unknown
keys, and defaults; it also includes a checked-in real-Alpine browser harness
for loop-scope refresh/cleanup and clear-to-`undefined`. The maintainer has
accepted all sections plus the later boundary amendments: client bindings are
exactly `$c-props`, Alpine handlers, and parent-owned Citry `@c-*` handlers;
direct, dynamic, and `c-bind` contributions resolve in source order; ordinary
HTML/Alpine attributes remain kwargs; and dynamic `<c-component>` forwards to
its actual selected target. The init DAG, managed `effect`/`reactive`, and one
stable multi-root `scope` are accepted. The grouped multi-root listener and
stable live `ctx.els` representation passed their cross-browser spike and now
back the landed client binding/morph integration. The rootless comment-range lifecycle
also passed its cross-browser
spike: context-sensitive HTML requires `Range.createContextualFragment()` plus
a parent-shaped morph container, nested fresh IDs require stable-anchor
normalization and the tested keyed inert-template guard, mirrored physical
ranges support one grouped logical lifetime, and preserved Citry comments are
the required `citry:g1` deployment contract settled by A2/A6. The
named client target needed for a truthful wrapper-free
`x-for` product case is still undesigned; client-side instantiation of a
server-rendered blueprint remains a separate later feature.
The original work-package shape follows for history. The graph-first work
packages and open-decision register in `alpinejs_plan.md` supersede it.

**Goal:** a parent supplies the prop values a child client component
declares (`$component`'s config-object `props` form, design 5.5),
closing the "props down" half of client composition.

**Read first:** `events.md` 5.5 (the settled client binding, context, and
composition contract), 16.1 (the remaining edge spikes), the round-two report,
`docs/design/alpinejs/alpine-vuetify-audit.md` (the isolation
mechanism the binding must not pierce); code: the WP17.1-landed
`$component` props resolution.

**Historical stage one (completed design exploration):**

- Reactivity: whether passed values are reactive to parent-scope
  changes (starting point: plain Alpine reactivity per the recorded
  requirements; alpine-composition's Vue-reactivity layer stays
  excluded).
- Validation timing against the declaration (5.5 validates at
  instance initialization; when does a reactive update re-validate).
- The identity rules: per-sibling inputs, no inheritance across
  depth, and what a missing required prop does (pointed error naming
  the child and the prop).

**Build, round two (design exploration after the stage-one amendments):**
complete. The report named above covers supply relocation, root shapes,
non-Citry errors, direct `x-for`, init ordering, managed helpers, Alpine
scope exposure, update validation, unknown keys, and default factories.

**Preimplementation spike status:** both root-shape mechanisms and the focused
boundary-handler isolation mechanism are DONE and positive. The Citry-owned
`RootGroup` passed pinned-Alpine single-root,
multi-root union, timing, dynamic-membership, poll, shadow, pointer, and cleanup
cases. The Citry-owned rootless lifecycle passed text/empty initialization,
stable live `els`, contextual `tr`/`td`/`option`/SVG parsing, nested and
adjacent ranges, stable-anchor normalization, grouped mirrors, keys, movement,
polling, Alpine directive lifetime, and exact cleanup. Both ran in Chromium,
Firefox, and WebKit. See
[`alpinejs/spike-root-group.md`](alpinejs/spike-root-group.md) and
[`alpinejs/spike-rootless-lifecycle.md`](alpinejs/spike-rootless-lifecycle.md).
The [boundary-handler scope spike](alpinejs/spike-citry-handler-refs.md)
passed parent and child data/ref collisions, Alpine and Citry client binding profiles, a
child-local control, grouped source and target roots, a shared physical root,
morph, delayed delivery, teleport, and liveness across the same engines. Whole
Alpine handler expressions and optional Citry argument expressions evaluate
at the exact source location at delivery; only `$el`, `$dispatch`, and
`$event` come from the physical child, while native `currentTarget` remains
untouched. The spike did not prove Citry handler parsing, validation, dispatch,
or queue ownership. Alpine plan A1 through A8 subsequently integrated all three
mechanisms with real serialization, manifests, client bindings, morphing,
source-location election, and the shared instance registry. Keep the named
client-target helper and
browser-side blueprint instantiation separate from the core client binding build.

**Historical stage-two outline:** superseded by `alpinejs_plan.md`.

- Refactor `ComponentNode.render` attribute resolution to yield `(kwargs,
  client bindings)` after source-ordered direct, dynamic, and `c-bind` contributions.
  Classify only `$c-props`, Alpine `@...` / `x-on:...`, and Citry `@c-*` as
  client bindings. Keep `x-show`, `x-model`, `:class`, `x-transition`, `class`, and all
  other non-reserved attrs as ordinary kwargs. `:c-*` remains a component-tag
  error and `#c-*` keeps its parser-level contract. Exclude `<c-element>` from
  this split: it rejects `$c-props`, and its Alpine/`@c-*`/`:c-*` keys follow
  the selected HTML element's normal attribute path.
- Carry manifest client binding records through `CitryElement`, the general instance
  registry, first-live-root supply election, parent-source facades, and the
  ancestry init DAG. Add managed `effect`/`reactive` and the stable shared
  `scope` without mutating `ctx.data` or user `x-data`.
- Evaluate component-tag Alpine handler expressions and optional Citry argument
  expressions against a live carrier for the exact authored source location.
  Supply only `$el`, the child-bound `$dispatch`, and the exact `$event` from
  the physical child. Leave native `currentTarget` untouched, including its
  `window`, `document`, and delayed `null` cases. Bridge every explicit
  source-facade key through an own getter/setter so reactive reads and
  assignments both reach the original facade. Never use the child evaluator,
  the source instance's first root, or a source-root union. Parse and validate
  each Citry binding as a declared server-handler name plus optional arguments,
  then route it through the exact source parent Events anchor while preserving
  the child loading marker and cleanup lifetime.
- Forward client bindings through dynamic `<c-component>` to the actual selected target
  separately from kwargs. Adopt client bindings before root initialization and clean
  replacement/removal exactly once.

**Tests:** cover direct, `c-*`, and `c-bind` client binding ordering/removal/type errors,
including replacement taking the winning contribution's position and remove-
then-readd taking the re-add position;
plain-element placement errors; ordinary-kwarg preservation plus child-owned
`attrs` placement; whole Alpine boundary expressions and optional Citry
argument expressions without child data/ref leakage; reactive source-facade
read and write-through for both expression profiles; physical event values
and native `currentTarget` cases for both profiles; unchanged parsed Citry
handler names reaching the source-parent `@c-*` dispatch queue; a child-local
handler retaining child scope; the explicit callback-prop-to-child-scope
recipe;
single/multi/shared/rootless shapes according to spike verdicts; dynamic
`<c-component>` selection and replacement; the init DAG; stable shared
`scope`; managed helper teardown; and the private-Alpine `x-for` canary. Every
observe-then-lock test must first be shown to fail when its relevant behavior
is reverted.

**Boundaries:** the decision-record amendment supersedes stage one's
"no server changes" boundary: component-tag client binding metadata must travel
through the parser/render/dependency-manifest path, but ordinary attributes
remain kwargs. No ambient context (provide/inject stays the separate channel,
5.5); no Vue reactivity layer; no automatic general attribute fallthrough;
and no runtime implementation before the remaining decisions and spike gates
above are resolved.

---

### ✅ WP24: `template_data` defaults to returning kwargs (core citry)

**Status: landed 2026-07-18 and maintainer-approved 2026-07-22.**
Registered from the maintainer's ratified Alpine-integration decision of
2026-07-17.
Core citry, not events: it changes a `Component` default and is
independent of the events sequencing above, so it carries no wave row.

**Goal:** a component's inputs are readable in its template without
writing `template_data`. The base `Component.template_data` returns
`kwargs` instead of `None`, so a `Kwargs` field named `title` resolves
as `{{ title }}` out of the box. A declared `TemplateData` still
validates the result, and the js/css/State data methods stay opt-in
(they cross the server-to-browser boundary; template variables only make
names resolvable to the template author's own expressions).

**Read first:** the current `template_data` contract in `component.py`; code:
`packages/py/citry/citry/component.py` (the base `template_data`),
`packages/py/citry/citry/component_render.py` (`_normalize_data` and the
template-globals overlay), `packages/py/citry/citry/util/misc.py`
(`to_dict`).

**Build:**

- Change the base `Component.template_data` body from `return None` to
  `return kwargs`. `_normalize_data` already converts a dict, a
  `NamedTuple`, or the typed `Kwargs` dataclass instance through
  `to_dict`, and validates against a declared `TemplateData`, so no new
  conversion is needed.
- Rewrite the `template_data` docstring for the new default (it
  documented the `None` default before). Record the globals precedence:
  a returned variable wins over a same-named `template_globals` entry.
- Leave `js_data`/`css_data` returning `None` (opt-in); their docstrings
  reference only their own default, so they stay as they are.

**Tests** (`packages/py/citry/tests/`): an untyped component whose kwargs
mapping passes through to the template; a typed `Kwargs` instance whose
fields resolve; an explicit `template_data` override still winning; the
global-shadowing precedence (a kwarg shadows a same-named template
global; locked); and a `TemplateData`-declaring component whose `Kwargs`
do not match its schema (the validation error names the mismatch, now
reachable without writing `template_data`).

**Boundaries:** no events code. `js_data`/`css_data`/`State` defaults are
unchanged, and `_normalize_data` gains no new conversion.

---

### ✅ WP25: client component registration rename and single-definition contract

**Status: landed, adversarially reviewed, and maintainer-approved
2026-07-18.** The full repository gate and the complete relevant browser
suites are green. The adversarial review's code findings were fixed and the
re-review approved the implementation.

Registered from the ratified Alpine-integration decision record of
2026-07-17. The required ecosystem pre-check found that the historical
third-party
[`alpine-magic-helpers`](https://www.npmjs.com/package/alpine-magic-helpers)
package also claims `$component` for cross-component lookup. Current Alpine
does not list it among its built-in magics, but the third-party collision is
real: Citry's cache-time rewrite means that helper cannot be called from a
component's `Component.js`. The maintainer re-ratified `$component` on
2026-07-18 with that collision known.

**Goal:** ship the breaking client registration rename in one pass and make
one registration define one component class. Component JS uses `$component`,
the config-object callback field is `init`, and a second registration for the
same class throws a pointed error.

**Read first:** `events.md` 5.5 and `dependencies.md` 5.2 and 8.2; code:
`citry/ext/dependencies/scripts.py`,
`citry/ext/dependencies/client/citry.js`, the events bootstrap emission,
`packages/js/citry-client/src/citry-events.ts`, and the dependency-manager
and config-form e2e suites.

**Build:**

- Rewrite `$component(` in component JS to
  `Citry.manager.registerComponent("<class_id>", ` and keep no compatibility
  alias. `$onEvent` is unchanged.
- Accept either one bare callback or one `{init, props}` config object for a
  class. The `init` function receives the existing context and keeps the
  existing cleanup return contract. Any other definition shape raises a
  pointed `TypeError` before registration state changes or pending calls flush.
- A second `registerComponent` call for a class throws an `Error` naming the
  class, stating that the component is already defined, and explaining that
  one `$component` registration is allowed per class. Reject it before
  changing registration state or flushing calls, so the original definition
  remains usable.
- Rebuild the generated Events browser bundle and update all active examples,
  tests, design references, and user documentation in the same pass.
- Add a breaking-change release note following the repository changelog rule.

**Tests:** author the transform test observe-then-lock so the new sugar fails
before the rewrite changes; lock the duplicate-registration error type and
exact message; prove the original definition still runs after the rejected
second registration; prove a malformed definition leaves the class available
for a valid definition; retain the single-registration queued-call path; and
prove a `{props, init}` registration consumes the initial page-load manifest
call. Run the focused dependency and browser suites, the client package check,
the full Chromium e2e suite, and the full repository gate.

**Boundaries:** `$component` is the only component-registration spelling and
`$onEvent` keeps its name. No props-passing implementation, WP24
`template_data` change, or pooled low-severity client cleanup.
Historical research reports and vendored django-components snapshots retain
their original vocabulary as historical evidence.

---

### ✅ WP26: the pooled low-severity polish batch (v1 close-out)

**Status: landed 2026-07-22.** All 21 recovered findings are closed and
recorded below and in their source WP status blocks. The old ledger retained
only WP16 review counts, not their finding text; the exact WP16.1/16.2/16.3
findings were recovered from the original local reviewer workflow journals
and are now durable here. WP13's separate per-event multi-call low, omitted
from the original WP26 scope summary, is included.

**Goal:** clear the parked low-severity findings in one focused pass: fix
what is worth fixing, record-as-accepted what is not, and remove the
"carried"/"Lows carried" note from each source WP's status block as its
items land, so the plan stops carrying open lows.

**Disposition ledger (21 findings):**

- **WP13 (6):** per-event multi-call rejection now mirrors every call and
  valid epoch; `_counter` is spec-pinned; spec 4.5 documents per-result
  strict-JSON repair; `Decimal` egress and non-finite validation are covered;
  state token/fingerprint JSON is strict; and the selector-render continuity
  warning is implemented and tested.
- **WP16.1 (4):** graph placements fix adjacent mirror collapse; `cid:` event
  delivery is intentionally once on the first live root and the design is
  amended; retired/epoch breadcrumbs are exact-test locked; plain-HTML
  cleanup-exactly-once was already superseded by A8 coverage.
- **WP16.2 (3):** Playwright packages are accepted as declared dependencies;
  client-minted `fields: {}` is removed; bootstrap registration/apply calls
  queue and transport declarations drain before configuration and sends.
- **WP16.3 (4):** failure/timeout dependency tests are deterministic and exact;
  both Element dequeue-deadness branches are covered; bypass busy has a
  per-trigger refcount; recurring identity is private and public sends always
  return a Promise.
- **WP17.2 (2):** natural control activity protects drafts before `.on:` or
  `.lazy` flushes; the LiveSearch pitch is back under its hard line bound.
- **WP21 (2):** both stale doc comments are corrected, with no Rust grammar or
  AST behavior change.

WP17.1 cleared on its original re-review with zero findings and contributes
nothing to this batch (its separate flush-order discovery remains owned by
WP25).

**Read first:** the status block of each WP named above (the findings
live there in full), and CLAUDE.md Mechanism 3 (sweep the class) for any
finding that turns out to have siblings.

**Boundary outcome:** the maintainer approved the two required decisions:
canonical one-root `cid:` event dispatch and early natural-event draft
protection. WP21 touched only Python/Rust-mirror documentation comments; no
grammar or AST contract reopened. This batch remains independent of the v1
release gate.

---

### ✅ WP27: history and download response actions (v1.x)

**Status: landed 2026-07-23, review-approved after one fix round.** The
independent reviewer found no blockers or major issues, and confirmed all five
minor hardening fixes. The full repository gate passed after the final fix
round.

**Goal:** complete the two response features already reserved by the design.
`PushUrl` and `ReplaceUrl` produce the existing `url` wire action. `Download`
produces one dedicated HTTP attachment response without tunneling file bytes
through JSON.

**Build:**

- Add frozen `PushUrl` and `ReplaceUrl` action values, exact wire encoding,
  and client application through `history.pushState` or
  `history.replaceState`. Preserve the page's current `history.state`, accept
  only exact modes, and let malformed or browser-rejected URL actions warn and
  skip without interrupting later actions.
- Add frozen `Download(content, filename, content_type)` as a response result,
  valid bare or as one top-level list or tuple item. Validate file and media
  type inputs and emit an attachment header with both an ASCII fallback and a
  UTF-8 `filename*` value.
- Require raw-response handlers to use `@event(bundle=False)`, run through a
  per-event HTTP route, and leave State unchanged. Reject download mixtures,
  batch calls, non-HTTP transports, and result-resolver indirection.
- On the client, recognize only successful single-call attachment responses.
  Buffer the blob beside a synthetic result and start the browser save only
  after that result survives timeout and latest-wins supersession checks.
- Add protocol history fixtures, reference entries, server and route tests,
  real-browser history and download round trips, and timeout/supersession
  negative browser cases.

**Boundaries:** no base64 file action, streaming body API, upload codec,
`popstate` synthesis, client router, or DOM/State restoration on Back and
Forward.

---

## 5. Explicitly not in this plan (do not build by accident)

Deferred by the design to v1.x: multipart codec and the client file
auto-switch, the postMessage transport and bridge, served `openapi.json`, Django
`form_class` sugar, token encryption, node-level binding rewrite.
Deferred to v2:
WebSocket transport (`WSRoute`, `asgi_ws_app`), server push (the
consumers of the stored-but-inert `_topics`), client-side same-tick
batching, and SSE. Alpine scoped-slot ownership is no longer in this
deferred list: A7 landed it through graph-first source projection.
Design-open, meaning
still undecided in the design (tracked in events.md section 16 with
reserve designs; not scheduled anywhere, do not build): lazy scope activation, the
constrained CSP mode, the `$forwardEvent` listen-and-forward magic (a
community-demand issue after v1 ships), and the packaged GraphQL
transport story (events.md section 16). Recorded v2 candidates from
the client-model round, decided out of v1 (events.md 16.1; do not
build): send-versus-apply pipelining,
the per-attribute preservation tier, and target-ordering
helpers for unrelated anchors. Post-v1: the production-app
dogfood port (events.md section 13), which is what settles falsifiers
15.2/15.3/15.8 and the post-v1 half of 15.11 (the queue's
head-of-line-blocking check) and is planned as its own effort once v1
lands.

---

## 6. Cross-cutting acceptance

Every WP, before it reports done:

- The full gate is green: `.venv/bin/python scripts/check.py --reporter
  agent` (never a scoped run as the final pass).
- Error messages introduced by the WP assert their content in tests
  (what failed, why, the fix), not just their type.
- Nothing generated iterates a set into output; manifests, tokens,
  descriptors, OpenAPI documents, and rewritten templates are
  byte-deterministic given fixed inputs (the token's timestamp field is
  the sole, explicit exception, and tests pin it to a fixed value).
- New public symbols live behind the WP's public `__init__.py` with
  `__all__`, carry reference-quality docstrings, and appear in no other
  entrypoint.
- The design doc wins conflicts; deviations are reported in the WP
  report, never silently embedded.
- No WP other than WP21 touches the Rust contract (grammar, AST,
  compiler output, `LangImpl`, PyO3); WP21 is exactly that work and
  runs CLAUDE.md Mechanisms 1, 2, and 4 in full. Any other WP that
  seems to need a Rust-contract change must stop and report
  (Mechanism 2 territory).

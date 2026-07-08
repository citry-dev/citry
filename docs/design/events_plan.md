# Implementation plan: the Events extension (work packages)

**Status (2026-07-08): seven packages landed.** WP1, WP2, WP3, WP4,
WP5, WP6, and WP7 are implemented, adversarially reviewed and approved,
and the full combined gate is green. The WP6 spike passed all nine
assertions, so the client wave (WP15 to WP17) is ungated. WP8 and WP9
are the next eligible server packages (WP8 now needs WP3, which
landed). The per-WP status blocks below carry the detail.

This doc is the delegation companion to [`events.md`](events.md). It
takes the v0 substrate (the core changes the design needs first; design
section 12), the protocol package, the spike, and the v1.0 build of the
design, and breaks them into twenty self-contained work packages, each
sized for one coding agent. The design doc stays the source of truth
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
the brief). Copy this template and fill in the WP number:

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
  (`citry/extensions/dependencies/`, `client/citry.js`), `$onComponent`
  rewrite (`dependencies/scripts.py`).
- Typed inputs: nested-class dataclass conversion (`citry/component.py`),
  `CitryCache` (`citry/cache.py`), `CitrySettings` (`citry/settings.py`),
  the `citry` CLI and `ExtensionCommand`.

---

## 3. Sequencing

Status legend, used here and on the section 4 headings: ✅ is done and
review-approved, ⏳ is in progress, 🟠 is paused mid-work, 🔵 is not
started, and 🚧 marks a package whose status block records PENDING
decisions, deviations, or follow-ups.

| Wave | Packages | Notes |
|---|---|---|
| 1 | ✅ WP1, <br/>✅ WP5 | The `ext/` rename must land before anything imports `citry.ext.events`; the protocol package is pure authoring with no code overlap |
| 2 | ✅ WP2, <br/>✅ WP3, <br/>✅ WP4 | Substrate. WP2 and WP3 both touch `contrib/django.py`: run WP2 first or isolate in worktrees; WP4 is disjoint (client JS) |
| 3 | ✅ WP6, <br/>✅ WP7 | The spike (after WP4's hooks) and the extension skeleton (after WP1) are disjoint |
| 4 | 🔵 WP8, <br/>🔵 WP9 | Tokens (needs WP3) and data schemas, <br/>both on WP7. Both edit the events package; they share `citry/ext/events/__init__.py` exports, so isolate in worktrees or land WP8 first |
| 5 | 🔵 WP10, <br/>🔵 WP12 | Serializer integration (needs WP8's mint) and the binding rewrite (needs WP7). Both register hooks on the events extension class; worktree isolation or land WP10 first |
| 6 | 🔵 WP11 | Actions and encoding; needs WP9's schemas and WP10's render-to-fragment path |
| 7 | 🔵 WP13 | Dispatcher, routes, codecs, CSRF, URL builder, compat mode; integrates WP2, WP3, WP8 to WP12 |
| 8 | 🔵 WP14 | ViewEvents shim + OpenAPI command (needs WP13's routes and WP9's schemas) |
| 9 | 🔵 WP15 | Client: Alpine embedding, scopes, magics (gated on WP6; needs WP4, WP10, and it replaces WP13's runtime.js stub) |
| 10 | 🔵 WP16 | Client: transport, envelope, actions applier (needs WP15, WP13, WP5) |
| 11 | 🔵 WP17 | Client: bindings runtime, expressions, forms (needs WP16, WP12) |
| 12 | 🔵 WP18 | Conformance runner + e2e suite (needs everything above) |
| 13 | 🔵 WP19, <br/>🔵 WP20 | Docs: the guide and sibling updates (WP19) and the migration pages (WP20); disjoint content, they link to each other |

Dependency edges, regenerated from the per-WP needs; read `A <- B` as
"B needs A" (the wave notes and this list must never disagree):
WP1 <- WP7; WP4 <- {WP6, WP15};
WP6 <- WP15; WP3 <- {WP8, WP13}; WP7 <- {WP8, WP9, WP10, WP12};
WP8 <- {WP10, WP13}; WP9 <- {WP11, WP13, WP14}; WP10 <- {WP11, WP13,
WP15}; WP11 <- WP13; WP12 <- {WP13, WP17}; WP2 <- WP13; WP13 <- {WP14,
WP15, WP16}; WP5 <- {WP16, WP18}; WP15 <- WP16 <- WP17; all <- WP18 <-
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

**Decisions recorded by the implementation (for maintainer review):**

1. The griffe bullet landed as an explicit `public_entrypoints()`
   enumeration in `docs_site/reference.py`, plus reference pages for
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

### ✅📝 WP3: the settings trio and the Django secret helper (substrate 12.4)

**Status: landed 2026-07-08, review-approved (three review rounds; the
final review had zero blocking findings). Two items for the maintainer,
both flagged by the review as judgment calls:**

1. **The CHANGELOG entry was dropped, not added.** The three fields are
   inert storage today (no consumer until WP8/WP13), so by CLAUDE.md's
   changelog test a user cannot yet do anything with them, and the only
   honest wording would leak roadmap. WP8/WP13 introduce
   `secret=`/resolvers/codecs to users when their consumers make the
   fields do something. If you want an API-record entry now, say so and
   it goes back verbatim.
2. **Pre-existing bug the review surfaced (out of WP3 scope, not
   fixed):** input normalization lives only in `Citry.__init__`, not in
   `CitrySettings.__post_init__`, so direct `CitrySettings(...)`
   construction stores un-normalized, caller-aliased values for
   `extensions`, `dirs`, `extensions_defaults`, and `template_globals`
   (the same shape as the `secret`/resolver/codec bug WP3 did fix in
   `__post_init__`). `dirs` also skips its Path coercion and
   absolute-path validation on that path. Worth its own small follow-up
   to move all `CitrySettings` input normalization into
   `__post_init__` uniformly.

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

### ✅🚧 WP4: client-runtime extension points: `decorateContext` and teardown (substrate 12.5)

**Status: landed 2026-07-07, review-approved (two fix rounds; final
review: approve, zero findings).**

**Amendment (2026-07-08, maintainer-approved, needs a re-run).** The
component-identity spike (`spike-component-identity.md`) added a
component-instance lifecycle layer to this file's scope, and the
maintainer approved it. Three items in the Build list below (the removal
reconciler, the `Component.css` garbage collection, and the flush
re-entrancy fix) are new since the original review and are not yet in
`citry.js` (the spike modeled them as an additive layer), so this WP
re-opens for an amendment pass and a fresh review, per the design-drift
rule in section 1. The original two extension points (`decorateContext`
and callback teardown) are unchanged and stay approved.

**Goal:** other extensions can extend the dependencies manager's
`$onComponent` callback payload, and callbacks may return a cleanup
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
`tests/` (grep `onComponent`).

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
- CHANGELOG entry: `$onComponent` callbacks may return a cleanup function,
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

### ✅🚧 WP5: the protocol package (design 4.1)

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
  `{call, result, volatile_paths}` so WP16 and WP18 iterate structured
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
load-bearing; idiomorph stays on the shelf), and the npm+esbuild
acquisition is confirmed with one adjustment (classic iife delivery).
The report
([`spike-morph-alpine.md`](../design/events_research/spike-morph-alpine.md))
records eleven findings, F1 to F11, normative for WP15/WP16; the
design-affecting ones are folded into events.md (5.3 plugin import and
hook signature, 5.2 boot-order rules, 5.5 root selector and the
scope-stack testing note) and into the WP10/WP15 entries. One residual
low: the assertion-9 range-replacement probe is not fully discriminated
(noted in the report; harmless).

**Follow-on spike (2026-07-08):** the component-identity spike
([`spike-component-identity.md`](../design/events_research/spike-component-identity.md))
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

1. `$onComponent` re-fires exactly once per re-render, after its
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

**Deliverable:** `docs/design/events_research/spike-morph-alpine.md`:
per-assertion pass/fail with evidence, the exact version pins, surprises,
and an explicit verdict on `@alpinejs/morph` vs the idiomorph fallback
(design 5.3). Acquire Alpine + morph the way WP15 will (npm install into
a scratch `package.json`, esbuild bundle; the plan pins that approach in
WP15) and confirm or contest it in the report, so WP15 inherits a
validated decision. The harness itself is deleted; the report persists.

**Boundaries:** no production code changes (WP4's hooks are consumed, not
modified). If assertions fail, the report is the deliverable; do not
"fix" the design inline.

---

### ✅🚧 WP7: extension skeleton: registration, capture, meta, vocabulary (v1 server)

**Status: landed 2026-07-07, review-approved (one fix round; re-review:
approve, three lows).** Follow-ups recorded:

1. Resolved by the orchestrator: it deleted the redundant file-level
   noqa directive in test_ext_events.py and wired the typed-base
   contract test (test_ext_events_typing.py) into the gate's mypy phase
   in scripts/check.py.
2. Maintainer decision pending: the pyright half of the typing contract
   still has no automated enforcement (it would add a network-dependent
   `npx pyright@1.1.411` step to the gate or CI). Until wired, the test
   file's docstring carries the pinned manual command.
3. Known edge, to fix alongside the next server WP: nothing validates
   the keys of `extensions_defaults["events"]` against the config
   vocabulary, so a misspelled key (for example `guard` for `_guard`)
   surfaces as a confusing class-definition error on components that
   use the `class Events(Parent.Events)` extension spelling. Recommended
   fix, reviewer-endorsed: validate the keys against CONFIG_NAMES where
   the extension reads the defaults, so misspellings fail loudly and
   uniformly. Documented config shapes are unaffected.
4. The fix round made one contract nuance symmetric: on an explicit
   dataclass State, annotating a meta name turns it into a field, and
   it then fails as an underscore field, matching the plain-class
   behavior.

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

### 🔵 WP8: state tokens and updates (v1 server)

**Status: not started.**

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

### 🔵 WP9: data schemas, coercion, and `UploadedFile` (v1 server)

**Status: not started.**

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

### 🔵 WP10: serializer integration: the events manifest and runtime injection (v1 server)

**Status: not started.**

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
  presence record for instances that carry CSS but no `$onComponent` JS, so
  the removal reconciler can count a class's live instances when nothing
  else registers them. The presence record is additive: it must not change
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
`$onComponent`) still emits its instance-to-class presence record.

**Boundaries:** no client code, no token verification, no routes. Do not
modify the `data-citry` sibling manifest's format.

---

### 🔵 WP11: actions, return coercion, and result resolvers (v1 server)

**Status: not started.**

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

### 🔵 WP12: the binding rewrite and template-load validation (v1 server)

**Status: not started.**

**Goal:** `@c-*` and `:c-*` attributes rewrite to `data-cev-*` specs at
template load (stage one) and via `on_attrs_resolved` (stage two), with
the design's hard validation.

**Read first:** `events.md` 5.1 in full (vocabulary, modifier table,
update-event table, arguments-are-Alpine-expressions, the two-stage
rewrite paragraph, the validation paragraph), 7.2 (binding-driven checks
against `_public`/`_model`); code: WP7 (handler and State metadata),
`citry/ext/dependencies/scripts.py` (the `$onComponent` textual-rewrite
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
  any `@c-*` or `:c-*` attribute on a `<c-*>` component tag is a
  template-load error with the kwargs-plus-events guidance (design 5.1
  "HTML elements only"); unknown binding shapes fail with the template
  location.
- The compiled contract, published: the `data-cev-*` attribute
  vocabulary is a WP12 invention (events.md 5.1 defines the author
  syntax and says it compiles to `data-cev-*`, but not the compiled
  names or payload shapes), and WP17 must match it exactly. Document it
  in the bindings module as a module docstring plus a frozen constant
  enumerating each emitted attribute name, its payload keys, and the
  encoding. WP17 reads this contract, never just the test fixtures.
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

### 🔵 WP13: dispatcher, routes, codecs, CSRF, URL builder (v1 server)

**Status: not started.**

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

### 🔵 WP14: the ViewEvents shim and the OpenAPI command (v1 server)

**Status: not started.**

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
for the registration pattern), `docs/design/extension_commands.md`
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

### 🔵 WP15: client: Alpine embedding, scopes, and magics (v1 client)

**Status: not started. Blocked on WP6's report.**

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
  the id changes every render. WP16 does the send-and-compare; this WP owns
  the structure.
- The three-way state split on an incoming render, chosen by comparing the
  anchor's current class id against the render token's class field (`c`),
  design 5.5: same class reconciles (server wins per field except pending
  unsent writes; the scope and `$state` identity persist); a different
  class discards the old state and adopts the server token and values
  wholesale, rebuilding the boundary scope; a plain-HTML render makes the
  anchor non-interactive and discards its state and scope. WP16 applies
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
  `$onComponent` payload gains `state`, `sendEvent`, `onEvent` via the
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

**Boundaries:** no transport (WP16 stubs it here), no bindings (WP17),
no morph application logic beyond what scope-survival needs (WP16 owns
applyActions).

---

### 🔵 WP16: client: transport, envelope, and the actions applier (v1 client)

**Status: not started.**

**Goal:** calls go over the wire and responses apply: fetch transport
with CSRF autowiring, envelope construction, epoch, `applyActions` with
faithful ordering, timing fields, and morph.

**Read first:** `events.md` 4.2/4.3 in full (envelope fields, action
table, ordering and redirect rules, `delay`/`wait`, targets, epoch
mechanics, the multiple-`data` rule), 5.2 (send/on semantics, lifecycle
DOM events and their `detail` contract, the code examples), 5.3 (morph
rules, busy attributes, `data-citry-morph="ignore"`), 6.1 (client
transport interface), 7.4 (client CSRF attachment), 3.8 (the per-event
URL template the transport posts to); the component-identity spike
(`spike-component-identity.md`; normative for routing by correlation id,
the per-anchor epoch, the faithful `data-cid`, the three-way split, and
link-before-morph); WP5's fixtures
(result fixtures replay through `applyActions` in tests, via
`fixtures/index.json`); code: WP15, WP13's events routes and dispatcher
(the live server the round-trip test boots).

**Build:**

- `Citry.events.send(...)` / instance `sendEvent`: envelope construction
  (protocol string, correlation id, capabilities, single call with
  token, pending updates, epoch), fetch POST to the per-event URL with
  `X-Citry-Events` and the configured CSRF source (default: read the
  `csrftoken` cookie, send it as `X-CSRFToken`; the `csrf` config
  object of design 5.2 overrides cookie, header, or token source),
  promise resolution
  from the `data` action, structured rejection from errors.
- Epoch bookkeeping per anchor (design 4.2, 5.5), not per component id
  since the id changes every render; stale responses drop instance-mutating
  actions, promises still resolve.
- The faithful-id and anchor model in `applyActions` (design 4.2, 5.5, the
  component-identity spike): route each response to the caller's anchor by
  the correlation id (the envelope `id`), never by a component id; the
  morph lands the server's fresh `data-cid-<id>`, so the DOM always shows
  the server's current id. Before the morph, link the fresh id to the
  anchor and update the anchor's State (spike F-CI-2, link before morph),
  then apply the three-way split by comparing the anchor's class id against
  the render token's `c` (same class reconciles, a different class adopts
  the new token wholesale, a plain-HTML render retires the anchor). Wire the
  `updating` hook only (ignore marker, focused-value protection); do not
  wire a morph `removed` hook for teardown, because instance teardown on
  removal is the dependency manager's removal reconciler (WP4's amendment,
  `dependencies.md` 8.4), which the events runtime rides.
- `applyActions`: faithful order; `render` (morph via `@alpinejs/morph`
  per the pinned call block in design 5.3, minus the `removed` hook above:
  `updating`-hook `skip()` for
  the ignore marker, focused-value protection, plain `key` attribute
  matching, pairwise multi-root fallback;
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
  `wait: false` scheduling.
- Busy state: `data-citry-busy` on the triggering element and instance
  roots; the lifecycle CustomEvents (`citry:events:before` cancellable,
  `:after`, `:error`, `:swapped`, `:stale`) with the
  `{instance, class, event}` detail contract plus the event-specific
  fields design 5.2's examples pin (`ok` on `:after`, `els` on
  `:swapped`).
- Content-Disposition detection on responses -> blob download path (the
  escape-hatch consumer).
- Capabilities: advertise `morph` + baseline; apply-side downgrade
  tolerance.
- The public client surface of design 5.2 and 6.1: `Citry.events.on`,
  `Citry.events.configure({transport, url, csrf, timeout})`, and
  `Citry.events.registerTransport(name, {send, subscribe?})` with the
  fetch transport registered through it (the function ships in v1 even though the
  first alternative transport is v1.x), plus `Citry.events.applyActions`
  as the public action-interpreter entry point. Design 5.2's tables pin
  each method's contract and `configure`'s field set; match them
  exactly.

**Tests:** replay every WP5 result fixture through `applyActions` in a
DOM harness; a self-render lands the server's fresh `data-cid-<id>` in the
DOM while the anchor's `$state` identity and epoch persist (routing by
correlation id, not by component id); the three-way split through a real
morph (same-class reconcile keeps a focused input; a different class
adopts the new token wholesale; a plain-HTML render retires the anchor and
runs the deps reconciler's teardown once); epoch reorder scenario keyed on
the anchor (late response's render dropped, promise resolved); ordering
incl. a delayed non-blocking action;
zero-match warning; lifecycle event sequence and cancellation; CSRF
header attachment under a cookie; one full Playwright round trip against
a live WP13 server (the counter).

**Boundaries:** no declarative bindings (WP17), no multipart switch
(v1.x), no WebSocket.

---

### 🔵 WP17: client: bindings runtime, expressions, and forms (v1 client)

**Status: not started.**

**Goal:** the compiled `data-cev-*` specs come alive: delegated
listeners, Alpine-expression args, two-way and one-way bindings, and
form collection.

**Read first:** `events.md` 5.1 in full (the tables and the
arguments-are-Alpine-expressions block, the forms example), 5.3
(re-apply rule), 5.5 (bindings riding the scope), 3.8 (the per-event
URL template); code: the `data-cev-*` contract WP12 documents in the
bindings module (the attribute names and payload shapes; its locked
tests are examples, the documented contract is the source),
WP15/WP16, WP13's events routes (the server the e2e tests boot).

**Build:**

- Delegated listeners per DOM event type at the document root, reading
  `data-cev-*` specs; modifier semantics per the 5.1 table (prevent,
  stop, self, once, key filters, debounce with the 250 ms bare default,
  throttle) with the `_debounce`/`_throttle` descriptor defaults from
  the manifest.
- Arg expressions: evaluate via Alpine bound to the owning element
  (`$state`, `$el`, `$event`, user scopes visible); non-object results
  raise the pointed runtime error naming the binding.
- Two-way bindings: the update-event table (input/change per control,
  `.lazy`, `.on:` override), one call carrying the `$state` write plus
  the named handler; pending updates piggyback on any earlier call.
- One-way bindings: Alpine `effect()` over `$state.<key>` applying to
  the control; re-application after a morph comes from reactivity
  alone, verify it.
- `@c-poll`: interval sends, hidden-tab pause.
- Form collection on submit-triggered events: named controls into the
  args payload, expression args win on collision, mirrored against the
  urlencoded codec in one parity test.
- Multiple event bindings on one element (the explicit e2e case).

**Tests (Playwright against a WP13 server):** the three pitch examples
of `events.md` section 2 pass end to end at (or under) their line
counts; live-search focus/caret survival; form 422 -> `$error.fields`
inline display; poll; the multi-binding element; one-way re-application
after morph; `.lazy` and `.on:` behaviors; parity of form-post (no-JS)
and runtime submission payloads.

**Boundaries:** no new server code (report gaps instead); no multipart.

---

### 🔵 WP18: conformance runner and the e2e gate (v1 verification)

**Status: not started.** WP5's package self-checks now run in CI as
pytest (see the WP5 status block); that covers only the package's
self-consistency, so this WP's scope is unchanged: the conformance
runner still replays every fixture through the dispatcher and asserts
the results match the fixtures everywhere except the declared volatile
paths.

**Goal:** the protocol fixtures run green against the Python dispatcher,
and the cross-adapter e2e suite is the merged definition of v1-done.

**Read first:** `events.md` 11 (the conformance rules, volatile paths),
13 (v1.0 exit criteria), 15 (falsifiers are the design's numbered
outcomes that would prove it wrong; the spike report plus this WP
retire or trip falsifiers 1, 2, 4, and 5); WP5's package; code: WP13,
WP17 test suites (extend, do not duplicate).

**Build:**

- A pytest module in the citry package that registers the fixture
  component from the protocol spec, feeds every fixture call envelope
  through `EventsDispatcher`, and asserts the result matches the
  fixture everywhere except the paths it declares volatile; it also
  schema-validates everything the dispatcher emits (vendored JSON
  Schema checker in test deps only; respect the mirrored-deps gotcha in
  CLAUDE.md when adding it).
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

### 🔵 WP19: docs and sibling updates (v1 close-out)

**Status: not started.**

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
  events-naming convention (`MyCard:submit`), the list-identity
  guidance (`c-key` on reorderable `<c-for>` items, design 5.3), the
  `js_data`-versus-State split (design 5.4), and the fresh-tree golden
  rule highlighted (design 7.5: a handler's render shares no inputs and
  no fills with the original render; everything is passed explicitly).
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

### 🔵 WP20: migration guide pages (v1 close-out)

**Status: not started.**

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

## 5. Explicitly not in this plan (do not build by accident)

Deferred by the design to v1.x: multipart codec and the client file
auto-switch, `PushUrl`/`ReplaceUrl`/`Download` implementations, the
postMessage transport and bridge, served `openapi.json`, Django
`form_class` sugar, token encryption, node-level binding rewrite.
Deferred to v2:
WebSocket transport (`WSRoute`, `asgi_ws_app`), server push (the
consumers of the stored-but-inert `_topics`), client-side same-tick
batching, SSE, the Alpine scoped-slot milestone. Design-open, meaning
still undecided in the design (tracked in events.md section 16 with
reserve designs; not scheduled anywhere, do not build): the client
props API for named client components, lazy scope activation, the
constrained CSP mode, the `$forwardEvent` listen-and-forward magic (a
community-demand issue after v1 ships), and the packaged GraphQL
transport story (events.md section 16). Post-v1: the production-app
dogfood port (events.md section 13), which is what settles falsifiers
15.2/15.3/15.8 and is planned as its own effort once v1 lands.

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
- No WP touches the Rust contract (grammar, AST, compiler output,
  `LangImpl`, PyO3); if one seems to need to, stop and report
  (CLAUDE.md Mechanism 2 territory).

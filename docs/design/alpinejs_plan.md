# Implementation plan: graph-first Alpine integration

**Status (2026-07-22): A0 through A10 complete.** This plan records how Citry closed the gap
between the former Alpine-first Events runtime and the now-landed target in
[`alpinejs.md`](alpinejs.md). The target architecture and `$c-props` spelling
are maintainer-ratified. This plan calls `$c-props`, Alpine event handlers such
as `@click`, and Citry handlers such as `@c-save` or `@c-poll.5s` resolved
from a nested `<c-*>` tag **component-tag client bindings**. Their expressions
or server handlers remain parent-owned while the child supplies the component
boundary. Research mechanisms have passed focused spikes, but A1's server
graph, typed client bindings, and slot ownership capture have
landed. A2's versioned serialization, physical caps, and atomic revision
staging have also landed. The general live client registry and rootless
product lifecycle landed in A3 and A4, together with the permanent Alpine
broker, stable per-logical-instance scope and `els`, init-DAG scheduling,
cap-owned rootless lifetime, exact managed cleanup, dynamic RootGroups,
contextual range morphing, fill-region groups, and shared-root rebinding.
Exact supplied-fill and fallback source projection, detached-origin isolation,
Citry-magic routing, structural-template propagation, and native teleport
composition landed in A7. Atomic graph, Events, dependency, and DOM adoption,
O9 correspondence, runtime physical placements, logical queue containment,
and cross-revision fill-source handoff landed in A8.
Structural clone cleanup, grouped Citry enter/leave, compatible client binding
succession, transition-safe ownership markers, and pointed rejection of
copied server component identity are implemented in A9.

This plan does not rebuild the complete Events runtime. It extends and
consolidates the landed anchors, morph transaction, queue, bindings,
`$component` registration, and dependency manager. The historical
client-boundary research ledger in [`events_plan.md`](events_plan.md) is
superseded by this plan and [`alpinejs.md`](alpinejs.md).

For operating rules see [`/CLAUDE.md`](../../CLAUDE.md).

---

## 1. Delivery rules

Each work package is independently reviewable and finishes with:

- focused unit and three-browser acceptance tests for its behavior;
- observe-then-lock proof for generated output and browser behavior;
- updates to both [`alpinejs.md`](alpinejs.md) and this status ledger if the
  implementation reveals a design correction;
- an independent adversarial review after implementation fixes;
- the full repository gate: `python scripts/check.py --reporter agent`.

Production packages never import the research adapters from
[`alpinejs/`](alpinejs/README.md). A work package ports the smallest proven
mechanism into typed product code and keeps the evidence harness as an
independent differential or acceptance fixture.

No package silently expands into ESM, a new evaluator, an Alpine fork, or
client-side instantiation of server-rendered component blueprints. Those are
separate decisions.

## 2. Current baseline

Do not rebuild these landed capabilities:

- exact Alpine 3.15.12 and `@alpinejs/morph` 3.15.12 bundle pins;
- classic IIFE loading, duplicate-Alpine warning, pre-start registration, and
  one owned `Alpine.start()`;
- Events manifests, stable Events anchors, fresh render-ID mapping, epochs,
  State reconciliation, and keyed linking;
- morph action application, queueing, compiled Events bindings, forms,
  polling, busy state, and cleanup;
- `$state`, `$loading`, `$error`, `$sendEvent`, and `$onEvent`;
- `$component` rename, one registration per class, bare/config forms, prop
  declarations/defaults, payload decorators, and returned cleanup;
- `#c-key`, `#c-ignore`, `@c-*`, `:c-*`, ordinary `c-*`, and `c-bind` parser
  channels;
- `template_data()` returning kwargs by default.

The current runtime is concentrated in:

- `packages/js/citry-client/src/citry-events.ts`;
- `packages/py/citry/citry/ext/dependencies/client/citry.js`;
- `packages/py/citry/citry/serialize.py`;
- `packages/py/citry/citry/nodes/__init__.py`;
- `packages/py/citry/citry/component_render.py`;
- `packages/py/citry/citry/slots.py`;
- `packages/py/citry/citry/ext/events/`;
- `crates/citry_template_parser/` for syntax-contract changes.

## 3. Dependency order

`RootGroup` is Citry's one-listener adapter over every current element root of
one logical component instance.

```text
A0 contract and acceptance locks
  -> A1 server ownership capture
      -> A2 versioned graph manifest
          -> A3 general client registry and hook broker
              -> A4 component lifecycle and isolation
                  -> A5 $c-props and boundary handlers
                  -> A6 RootGroup and rootless regions
                      -> A7 slot source projection
                          -> A8 atomic morph and Events integration
                              -> A9 structural Alpine cases
                                  -> A10 conformance, performance, and docs
```

A5 and A6 may run in parallel only after A4 if isolated worktrees avoid their
shared runtime files. A7 needs both. A8 is the integration gate and must run
before broad `x-if`, `x-for`, and teleport claims in A9.

## 4. Work packages

### A0: contract migration and failing acceptance shells

**Status:** complete (2026-07-20).

**Goal:** make the approved vocabulary and implementation boundary explicit
before behavior is added.

**Build:**

- Reserve `$c-props` as a Citry client-runtime directive on component tags.
- Accept the orthogonal server-dynamic spelling `c-$c-props` and a
  `$c-props` key in `c-bind` mappings.
- Reject literal `$c-props` on plain HTML and `<c-element>` at the earliest
  reliable phase; define equivalent runtime diagnostics for dynamic keys.
- Recognize only `$c-props` as Citry's component-boundary props directive;
  ordinary `x-*` names remain in the Alpine/plugin namespace.
- Preserve the already-proved generic parser, compiler, and HTML round trip,
  then add special classification, Python binding, syntax-highlighting, and
  generated fixtures where the Rust contract requires them.
- Add skipped or expected-failing browser acceptance shells for the complete
  target matrix. These tests must distinguish an unimplemented path from a
  passing no-op.

**Decision gate:** confirm that `$` remains round-trippable in direct
attributes, `c-*` names, spread keys, diagnostics, source spans, and HTML
serialization. The syntax decision is already made; a failure here changes
the lowering mechanism, not the public spelling.

**Acceptance:** exact parse/compile/render snapshots for `$c-props`,
`c-$c-props`, `c-bind`, invalid plain-element use, dynamic removal, and source
ordering.

**Landed result:** the parser reserves the two exact lowercase spellings on
component boundaries, preserves the generic static/expression compiler nodes
and source spans, exempts the directive from Python kwarg declaration rules,
and gives pointed placement and empty-value errors. Python resolution applies
the source-ordered string/value/removal contract for direct, server-dynamic,
and `c-bind` contributions, including runtime rejection on plain elements and
both forms of `<c-element>`. The Citry lexer highlights the direct value as
JavaScript and the server-dynamic value as Python. Strict browser acceptance
shells for all three supply forms fail on the missing client binding in Chromium,
Firefox, and WebKit while proving the real runtimes boot first.

A1 replaces the temporary `raw_kwargs` transport: `$c-props` and both handler
families now travel as typed component-tag client binding records and stay out of
`raw_kwargs`, typed kwargs, and untyped kwargs. No client expression is
evaluated and no declared client prop is supplied yet.

### A1: server ownership capture

**Status:** complete.

**Goal:** preserve logical ownership before component and slot rendering
flattens it into HTML.

**Build:**

- Introduce typed internal records for component invocation, logical instance,
  source location, supplied fill, fallback fill, physical region request, and
  init ancestry.
- Split resolved component-tag contributions at the accepted point in
  `ComponentNode.render`: ordinary kwargs versus structured client bindings.
- Capture the exact winning post-template-hook runtime source span and source owner for direct,
  `c-$c-props`, handler, and `c-bind` contributions.
- Carry client bindings through static and dynamic `<c-component>` to the actual
  selected target, separately from kwargs.
- Record body-slot construction, fill collection, slot invocation, fallback
  ownership, nested transitions, and render-queue deferral without changing
  Python slot output.
- Keep `<c-element>` on the plain HTML path.

**Locked choices:**

- distinct typed graph-local integer IDs with immutable ordered snapshots;
- transparent caller-to-selected-target init ancestry for runtime
  `<c-component>`, with the wrapper recorded only as a server diagnostic;
- explicit detached Python origins with no invented lexical client source for
  Python `Slot`, callable, trusted HTML, and typed-default supplies;
- one fresh source-location record per executed location, even when several
  executions share one compiled source span.

**Acceptance:** server-only traces for nested components, direct and dynamic
targets, supplied and fallback fills, multiple invocations of one `Slot`,
rootless output, mirrors, and render deferral. The trace must prove exact
ownership without inspecting final DOM ancestry.

**Landed result:** `OwnershipGraph` captures typed source locations,
component invocations, winning client bindings, logical instances, init ancestry,
logical fills, physical-region requests, and queue settlement before output
flattening. Component attributes split once in `ComponentNode.render`, runtime
dynamic selectors forward the authored invocation and client bindings to the selected
target, and supplied/fallback/Python-slot paths keep distinct ownership
without changing their Python output. Graph-local invocation IDs keep their
owning graph across delayed Slot calls, and settled output discarded by
generators, extensions, or error unwinding is explicitly retired. Typed
TagRules recognize boundary
handlers as instructions rather than kwargs, while the Events load rewrite
preserves component `@c-*`, rejects component `:c-*`, and keeps `<c-element>`
on its plain-HTML path. The detailed contract is
[`alpinejs/a1_server_ownership.md`](alpinejs/a1_server_ownership.md).

### A2: versioned graph manifest and physical caps

**Status:** complete (2026-07-21).

**Goal:** serialize A1 records deterministically and reconstruct them without
guessing from flattened HTML.

**Build:**

- Define a compact versioned manifest with `componentClasses`,
  `componentInstances`, fresh render IDs, `sourceLocations`,
  `nestedComponents`, `slotRegions`, and
  `componentExecutionOrderConstraints`.
- Give client bindings discriminated wire payloads. `$c-props` and Alpine
  handlers carry Alpine expressions; a Citry `@c-*` client binding carries a compiled
  DOM-event or poll binding with a server-handler name and an optional raw
  Alpine argument expression. Never serialize the whole Citry value as an
  expression for Alpine to execute.
- Retire A1's generic boundary-handler `expression` vocabulary when producing
  those payloads. Internal fields and user-facing diagnostics must distinguish
  an Alpine client expression from Citry server-handler binding source.
- Reuse one strict Events binding parser for ordinary elements and component
  client bindings. It must consume the complete winning string, reject trailing text,
  and validate direct, `c-@c-*`, and `c-bind` winners against the exact source
  parent's declared server handlers before manifest emission.
- Treat the optional JavaScript argument as opaque while parsing the outer
  server-handler call shell. Parentheses inside strings, template literals,
  regex literals, and nested JavaScript expressions must not confuse the
  shell parser. Preserve the non-empty inner expression verbatim for Alpine;
  normalize `handler()` to the same no-arguments form as bare `handler`;
  require the final non-whitespace character to close the outer call and
  reject anything outside that complete shell.
- Decide whether and how runtime source spans map back through
  `on_template_loaded` rewrites and nested-template fragments before exposing
  author-file coordinates. Define serialized byte, code-point, or UTF-16 units
  explicitly.
- Aggregate every ownership graph reachable from the final render tree,
  including pre-rendered foreign subtrees and delayed cross-root Slot results,
  or reject that tree fail closed. Freeze the graph set only after delayed
  descendants have settled so a prior snapshot cannot omit later records.
- Define element-group markers for single, multi, rootless, adjacent, nested,
  and mirrored regions. A2 later locked the proved exact `citry:g1` cap
  mechanism as the required representation.
- Preserve contextual parsing requirements for table, select, and SVG
  fragments.
- Emit the graph beside dependency and Events manifests with explicit
  processing order.
- Validate the entire manifest before exposing any record to callbacks.
- Define fragment deduplication, repeated insertion, and malformed-manifest
  behavior.

**Locked choices:**

- client-active output requires preserved `citry:g1` caps;
- v1 writes strings inline (no shared table), carries a top-level `mode` that
  drops source provenance in production, has no fixed protocol byte ceiling,
  and does not split one manifest;
- a client-active tree caps logical instances included in the graph and
  selected physical fill occurrences only, while `simple` and `ignore` emit
  no graph artifacts;
- every selected mirror occurrence has a fresh physical region ID while
  keeping its shared logical fill ID.

**Acceptance:** deterministic golden manifests, distinct Alpine-expression and
compiled-Citry-handler client binding fixtures, malformed-record rejection,
partial-fragment failure, comment-preservation checks, initial document and
fragment insertion, and realistic payload measurements.

**Landed result:** ordinary and boundary Citry bindings now share one strict
complete-value parser, and component client bindings compile against their exact source
parent into discriminated expression, DOM-event, or poll payloads. The server
aggregates settled same-`Citry` ownership graphs in physical order, writes its
strings inline and (in development) post-hook UTF-8 byte locations, rejects
reused concrete render occurrences and foreign `Citry` trees, and emits exact
instance and selected-region comment caps. `document` and `fragment` place the
versioned graph before graph-linked Events and dependency manifests, while
`simple` and `ignore` stay free of graph artifacts. The core runtime checks
the canonical SHA-256 revision, base64/UTF-8, bidirectional
instance/invocation endpoints, fill and region ownership, init and region
DAGs, and logical-to-physical cap ancestry before one atomic commit. Events
manifests stage fully and acknowledge successful anchor adoption before
graph-linked callbacks run. Failed transactions reject waiters and blocked
manifests; non-cloneable tag identity ensures copied processed attributes
cannot bypass duplicate-revision rejection. The published schema, fixtures,
and validator live under `packages/protocol/client_graph/v1`, and the detailed
contract is [`alpinejs/a2_client_graph.md`](alpinejs/a2_client_graph.md).

### A3: general client registry and permanent Alpine hook broker

**Status:** complete (2026-07-21).

**Goal:** create the runtime-neutral authority below optional Events anchors.

**Build:**

- Add typed registries for logical instances, render IDs, stable browser
  anchors, source locations, fill records, and physical regions.
- Parse and stage A2 revisions atomically.
- Reuse or bridge the landed Events anchor rather than maintaining two
  competing continuity objects.
- Install one permanent broker for Alpine init interception, root selectors,
  mutation handling, magics, morph hooks, and future Citry directives.
- Define one public pre-start extension path for Alpine plugins and custom
  magics while preserving Citry's single owned startup and duplicate-copy
  warning.
- Route callbacks through the active graph revision. Never stack permanent
  Alpine hooks on a fragment or hot reload.
- Centralize private Alpine access and extend version canaries.

**Acceptance:** graph adoption before and after Alpine startup, fragment
insertion races, duplicate runtime loading, revision replacement, invalid
revision rollback, hook-count stability, and components with and without
Events.

**Landed result:** the core dependency manager now normalizes each validated
A2 revision into read-only graph-qualified indexes for component classes,
component instances, source locations, nested components, fills, slot regions,
component execution order constraints, logical client instances, and stable
browser anchors. Graph-linked
callbacks carry a validated route and fragment scripts load in manifest order.
An explicit replacement transaction preserves both identities for a supplied
same-class correspondence, preserves only the positional anchor for a class
replacement, and retires both for plain output; it never guesses a mapping.
Events anchors attach as optional sidecars to the general anchor after an
atomic graph/class preflight.

`Citry.alpine` owns one permanent mutation fan-out, root selector, init
interceptor, magic dispatcher per Citry magic, morph entry point, pre-start
extension queue, duplicate-copy guard, and guarded startup. The current pinned
Alpine/Events bundle installs into that broker and is emitted for every
client-active graph, including graphs without Events; the historical runtime
path remains a packaging detail for now. Client-active element roots carry
`data-citry-root`, while rootless instances remain registry-active through
their comment caps. Browser acceptance locks no-Events startup, Events
bridging, invalid route rollback, duplicate hook counts, and all three
explicit replacement outcomes. A8 later removed the temporary
graph-quarantine morph path and now calls this replacement transaction.

### A4: component lifecycle, scope, and init DAG

**Status:** complete (2026-07-21).

**Goal:** make the general registry own client component isolation and
lifetime.

**Build:**

- Create one stable reactive `scope` per client-active logical instance.
- Attach the correct isolated Alpine stack to every current element root
  without mutating user `x-data`.
- Extend `$component` payloads with stable `scope`, live `els`, and managed
  `effect` and `reactive` helpers.
- Preserve one registration per component class while invoking its callback
  once for each live instance render revision. On a correlated rerender,
  dispose managed effects, run the previous callback cleanup, and re-fire with
  the fresh render `id` and `js_data()` payload.
- Run parent init before dependent descendant init using an ancestry DAG.
  Independent branches proceed.
- Settle failed or removed branches without a global barrier.
- Release effects, subscriptions, timers, props suppliers, and callback
  cleanup exactly once.
- Keep components with no client-active reason out of the registry when no
  later feature needs them.

**Acceptance:** nested collision isolation, same-root `x-data`, multi-root
scope visibility, rootless init, document-order compatibility, async failure
settlement, rerender cleanup-before-refire with fresh `js_data()`, replacement,
removal, and cleanup idempotence.

**Landed result:** the general graph registry now creates one reactive scope
and one live `els` array per client-active logical identity. It projects only
the innermost component scope on a shared root, leaves same-root user `x-data`
above that layer, and uses physical comment caps as the authoritative lifetime
for rootless instances. Component callbacks carry `scope`, managed `effect`
and `reactive` helpers, and fresh render `id`/`data`; correlated same-class
replacement preserves scope and array identity while disposing the old
invocation before re-firing.

Graph calls stage synchronously before Alpine can observe a fragment, hold
unready roots with counted Citry-owned reasons, and release each root for an
explicit `initTree` pass after its callback branch settles. Init ancestry
orders dependent callbacks without blocking independent branches. Managed
effects, decorator-owned subscriptions, and returned cleanup functions retire
once in that order. Promise-returning callbacks remain unsupported: the DAG
settles synchronously, a pointed diagnostic is logged, and rejection is
handled. Client-active markers are now limited to callback, Events, client binding, and
required isolation-descendant instances; unrelated static graph branches stay
out of the lifecycle registry.

Changing which logical instance owns an already-initialized shared physical
root updates the projected stack, but Alpine directive evaluators capture
their original stack objects. A6 closes that gap with one stable reactive
router whose target changes without resetting same-root user `x-data`.

The broker also reserves a `citry-boundary` directive phase before child
`x-data`. Alpine queues an ancestor's directives first, so A5 can evaluate a
source-owned supplier after parent `x-data` exists and before Citry projects
the child scope or permits ordinary child directives. A held subtree is
suppressed only after that phase and is initialized normally on release.

### A5: `$c-props` and component-boundary handlers

**Status:** complete (2026-07-21).

**Goal:** implement the explicit down and up channels at component
boundaries.

**Build:**

- Evaluate `$c-props` at the exact A1 source location and write one reactive
  declared-props bag per logical child.
- Preserve source order and exact-key winning behavior across direct,
  `c-$c-props`, and `c-bind` sources.
- Validate declaration, required/default/type, unknown keys, supplier shape,
  and recovery before init and on updates.
- Relocate Alpine handlers and compiled `@c-*` bindings to the child's
  RootGroup. Evaluate the whole Alpine handler expression, but only a Citry
  binding's optional argument expression, at the exact source.
- Report the pointed rootless-handler diagnostic while a component-tag Alpine
  handler or DOM-event `@c-*` binding has no element root, and keep that client binding
  dormant so the same lifecycle can activate it if a root later appears;
  props, init, and logical `@c-poll` remain valid throughout.
- Supply `$el`, child-bound `$dispatch`, and `$event` from the physical child.
  Leave native target/currentTarget untouched.
- Route the compiled `@c-*` server-handler name, dispatch, and queue ownership
  through the exact source parent Events anchor.
- Preserve child-local handler behavior and the explicit callback-through-
  props capability pattern.

**Decision gate:** lock the per-field and whole-bag invalid-update transaction,
clear-to-`undefined` behavior, diagnostic episode rules, and recovery.

**Acceptance:** the full props matrix plus a corrected refs client binding differential
across Chromium, Firefox, and WebKit. Its Citry profile must use a real parsed
handler call, evaluate only the argument object, assert the unchanged handler
name reaches the source parent queue, and cover invalid/trailing binding text.
Parser cases must include parentheses inside quoted strings, escaped strings,
template literals, regex literals, and nested expressions without truncation
or false unbalanced-parenthesis errors.
Include grouped source and target roots, shared roots, morph, delayed handlers,
teleport, shadow DOM, native structural directives, and liveness.

**Landed result:** each logical child now owns one stable reactive props
controller with a read-only public view, once-per-lifetime default factories,
source-reactive supply, per-field update commits, whole-bag supplier failure,
episode-deduplicated diagnostics, and first-supply init settlement. Direct,
server-dynamic, and spread providers share the A1 source-order winner rule.

The client registry captures an exact parent-side Alpine evaluation carrier
before child isolation and relocates Alpine and compiled Citry handlers onto
one lifecycle-owned RootGroup. Parent data, refs, IDs, root, and Citry magics
remain lexical; `$el`, `$dispatch`, `$event`, target, and currentTarget remain
physical. Citry queue nodes can lock the source Events owner while tracking a
separate child liveness and busy carrier, including after a delayed dequeue.
Rootless children accept props, init, and logical poll while reporting each DOM
handler directly. The product suite covers source collisions, refs, physical
magics, real parsed server calls, source-locked queue delay, multi-root shared
once state, shared roots, rootless behavior, recovery, every supply spelling,
and relocated submit form collection with explicit-argument precedence across
Chromium, Firefox, and WebKit. A6 covers dynamic regions, fill mirrors,
shared-root rebinding, and the grouped shadow-path matrix. A9 completed the
broad transition, teleport, and native structural lifecycle matrix.

### A6: RootGroup and rootless product lifecycle

**Status:** complete (2026-07-21).

**Goal:** port the proven root-shape adapters into the general registry.

**Build:**

- Implement one RootGroup listener layer with union containment, shared
  modifier/timer state, stable live `els`, dynamic membership, polling, and
  exact cleanup.
- Port the proved required `citry:g1` logical ranges for text-only and empty
  output and preserve A2's exact marker and deployment contract.
- Use contextual fragment parsing and parent-shaped morph containers.
- Accept explicit stable correspondence before nested Alpine init without
  guessing the still-open O9 policy.
- Guard nested logical islands during range operations.
- Support the locked hybrid mirror lifetime: shared logical component state
  and RootGroup behavior with copy-local ordinary Alpine directive state.
- Define shared physical-root precedence through graph records.
- Rebind already-initialized Alpine directive evaluators when dynamic
  membership changes the owning component of a shared root. Use either a
  stable per-root reactive router or proved safe directive teardown and
  re-initialization, without resetting same-root user `x-data`.

**Decision gate:** lock mirror State and prop sharing, copy-local listeners,
refs, IDs, transitions, focus, event-carrier, and cleanup policy before
claiming those features broadly. Keep A2's required preserved-comment
representation and pointed deployment failure.

**Acceptance:** port the RootGroup and rootless cases that define A6's product
contract into product-facing tests, then rerun the complete saved research
harness as a differential. Native pointer capture, transition behavior, and
structural creation/removal remain explicit A9 acceptance work.

**Landed result:** one lifecycle-owned RootGroup now keeps `els` stable while
deriving its dynamic members from the outermost authored marked roots inside
exact instance caps. Unmarked serialization-extension wrappers stay outside
the public `els`. Alpine and Citry boundary bindings share once, debounce, throttle,
outside/away union, global, key, enter/leave, shadow-path, and timing state.
Direct events keep their actual carrier; global and logical poll work reelects
the first connected live root. Removed direct carriers drop pending delivery,
and final range retirement cancels the group exactly once.

Required `citry:g1` caps now own continuous liveness. Exact text, order,
the topology mode recorded at adoption, and recorded nesting are checked after
DOM mutations. Valid same-task complete-range moves survive; changed, split,
reversed, partial, or later-detached caps retire without resurrection and
produce a deduplicated deployment diagnostic when corruption remains
observable. The narrow Document-to-body topology remains bounded by its exact
caps for root enumeration and range morphing.

The range morph adapter parses table, select, SVG, and top-level body fragments
in their real parent context and protects nested live ownership ranges as
inert keyed islands. It scans every live graph revision, holds lifecycle
reconciliation while islands are inert, and supports the validated
Document-to-body cap shape without moving the load-bearing outer cap. It
preserves an incoming island only through caller-supplied stable
correspondence, leaving O9 inference and atomic commit/rollback to A8.
Server-authored fills expose stable region groups across multiple physical
copies and final-copy retirement. Their `liveSlotRegions` and stable `els` array
follow current physical document order, including after complete range moves.

O6 is locked as a hybrid: props, Citry scope, Events State, component init and
managed cleanup, and boundary RootGroup state are shared by the logical owner;
ordinary Alpine `x-data`, child-local listeners, refs, IDs, transitions,
focus, and directive cleanup are physical-copy-local. A direct event uses its
actual copy, while global/outside/poll uses the first connected live copy.
Removing one copy performs physical cleanup; logical cleanup waits for the
last copy. Physical order never reelects the exact lexical source. A7 owns
source projection; A8 now normalizes Events multi-target mirrors with
client-owned runtime placement caps.

A stable reactive scope router retargets already-initialized evaluators when
shared-root ownership changes. Same-root user `x-data` remains above that
router and is neither torn down nor reinitialized. Product acceptance covers
the grouped modifier and carrier matrix, capture/passive options, dot/camel
names, submit flushing, Event redispatch, dynamic roots, logical polling,
rootless activation, cap corruption and movement, shared-root rebinding,
contextual morphing, cross-revision nested islands, reordered fill mirrors,
top-level Document-to-body ranges, and Debug extension wrappers in all three
browsers. Originless source carriers also activate props, init, and logical
poll for nested rootless boundaries when both source and target use that
top-level topology. The saved isolated RootGroup and rootless harnesses
remain passing differentials.

### A7: slot source projection

**Status:** complete (2026-07-22).

**Goal:** make supplied fill and fallback Alpine scope follow exact server
ownership transitions.

**Build:**

- Link supplied fill regions to the caller source and fallback regions to the
  receiver source.
- Project source data after the source `x-data` exists but before fill-local
  `x-data` initializes.
- Propagate source links through direct structural templates and later clones.
- Preserve nested component isolation inside a source-linked fill.
- Compose teleport-origin lexical ownership with teleported physical DOM.
- Route Citry magics through the graph-selected evaluation owner, not
  automatically through the nearest physical child.
- Implement the O7-selected owner for `Citry.events.send(element)` inside a
  source-linked fill.
- Support multi-root, rootless, mirrored, replacement, and cleanup lifetimes
  from A6.
- Project source links only from the complete A2 graph set. Foreign-graph and
  delayed Slot descendants must either participate in the same atomic client
  revision or make projection fail closed.

**Landed:** every supplied template fill carries the exact component-call
invocation that created its source carrier. Fallback fills use the inverse
receiver transition. Receiver-specific forwarding creates distinct logical
attachments while repeated outlets share one mirrored fill identity. A
Citry-owned directive projects a live source frame before fill-local `x-data`
and ordinary directives initialize. It also propagates through direct
`x-if`/`x-for` templates, composes with Alpine teleport backlinks, preserves
nested component isolation, and retires when its source or final physical
region dies.

Only settled fill regions containing Alpine directive attributes activate the
graph on their own. Plain server-only slot output keeps the historical minimal
HTML path. Once another client feature activates the graph, every fill edge
included in that revision is still validated and available.

A same-graph subtree stringified from a render hook may rebase omitted parent
instances and discard its inert outer fill wrapper. Direct Alpine on that
wrapper still fails closed because its caller is outside the fragment; Alpine
inside a nested component remains owned by the nested component and does not
spuriously activate caller projection.

Detached Python content has no public client-source opt-in in A7. When it is
already present in a client-active graph it receives an empty isolated base,
so local `x-data` works without borrowing the receiver. Detached content does
not activate the graph or Alpine runtime by itself.

Compiled `@c-*` bindings and `$sendEvent` use the graph-selected lexical
source owner. The public `Citry.events.send(element, ...)` API intentionally
keeps physical-element ownership. Citry does not redispatch teleported events;
native target, currentTarget, propagation, and containment follow the physical
placement. A8 owns cross-revision source replacement, while A9 completed the
broad structural hardening matrix.

Queued declarative sends lock their source owner and cancel if its liveness
predicate fails. Fill retirement actively removes route and scope state,
clears magic caches and backlinks, and isolates any surviving teleported DOM
with an empty retired scope. Public element sends keep physical-only
re-resolution while queued, and captured declarative send closures check
source liveness before immediate dispatch.

**Acceptance:** product tests cover parent supply, child fallback, nested
transitions, shared roots, refs and IDs, local `x-data`, `x-if`, `x-for`,
teleport, nested components, Citry magics, public imperative send, mirrors,
rootless fills, same-revision region morph, exact same-class call sites,
transparent dynamic targets, final-region cleanup, and detached Python
content in Chromium, Firefox, and WebKit. Independent document and fragment
revisions use revision-qualified internal source routes and cannot overwrite
one another.

### A8: atomic morph, dependency manager, and Events integration

**Status:** complete (2026-07-22).

**Goal:** make graph, DOM, dependency, and Events revisions commit as one
coherent transaction.

**Build:**

- Extend the landed actions applier to stage graph and Events manifests before
  morph.
- Remove A2's temporary Events-render quarantine of incoming graph tags and
  cap comments once that staged morph path is atomic.
- Apply the O9-selected correspondence for incoming render IDs and keyed
  children before Alpine evaluates incoming expressions.
- Keep old mappings available only for the required morph phase.
- Commit DOM, graph revision, scope/source links, bindings, State, and busy
  markers in the documented order.
- Retire old logical instances and physical regions exactly once after commit,
  at the point selected by O9.
- Roll back or fail closed on malformed graph data without half-new ownership.
- Derive queue containment from logical ownership and recheck physical
  liveness at dequeue.
- Preserve caller-authored keys on compatible child self-renders.

**Acceptance:** initial render, self-render, parent keyed render, targeted
replacement, class change, plain HTML replacement, batched actions, stale and
superseded results, removal during flight, fragment scripts, and malformed
revision rollback under the O9-selected correspondence and retirement rules.

This is the product architecture gate. If the integrated path cannot preserve
the accepted semantics with isolated private Alpine use, stop and report the
specific blocker before considering a fork or replacement runtime.

**Landed result:** the Events applier preserves incoming graph caps and stages
the graph, Events, and dependency manifests before epoch or DOM mutation. It
publishes a provisional graph only to internal correspondence code, activates
source routes and client bindings for morph evaluation, adopts the landed
physical caps, commits the public revision, and waits for graph-linked
dependencies. Malformed preflight rejects without changing DOM, epoch,
anchors, callbacks, or public revisions. Dependency preflight validates calls,
instance CSS, loaded and fetched asset lists, and decoded element descriptors.
If an unexpected failure occurs after morph begins, the transaction fails
closed: it removes the live target DOM and incoming ownership, rejects public
readiness waiters, restores prior Events class descriptors, releases the
adoption hold, and runs retirement cleanup. General restoration of arbitrary
pre-morph DOM is not part of the A8 contract.

O9 preserves both browser and logical identity for same-class self-renders
and same-class keyed children, preserves only the browser anchor across a
self-render class change, retires both for plain self output, and gives
uncorrelated IDs fresh identities. General keyed continuity does not require
an Events sidecar. A class-changing graph-backed self-render without an Events
sidecar still preserves only its general browser anchor. Fresh children are
reparented to the final preserved logical identity, and caller-authored keys
remain on compatible self-renders.

The server wire remains canonical `citry-client-graph/1`. For an Events render
targeting several selector matches, the canonical copy keeps its `citry:g1`
caps and each additional copy receives client-owned `citry:p1` placement caps.
All copies share logical scope, State, props, lifecycle, and fill source while
ordinary Alpine physical state remains copy-local. Cross-revision supplied
fills stage the new graph-owned source route and retarget a preserved Alpine
source frame reactively. Queue containment now follows graph logical ancestry
and still rechecks physical liveness at dequeue. Provisional routes remain
private, placement arrays are frozen snapshots, inactive all-dead revisions
are pruned, and used-revision tombstones continue to reject replay.

**Acceptance:** focused product coverage locks same-class, class-change,
plain-output, rootless, keyed no-Events, multi-placement, fill-source,
dependency-order, malformed graph/Events/dependency behavior, provisional
privacy, waiter rejection, post-morph fail-closed cleanup, logical-parent
rebinding, Events class-registry restoration, revision pruning, and immutable
placement snapshots. The A8 acceptance file passes Chromium, Firefox, and
WebKit; the combined Chromium
ownership, lifecycle, slot, queue, boundary, and Events regression group is
green.

### A9: structural Alpine and dynamic client identity

**Status:** complete (2026-07-22).

**Goal:** close the structural cases after the integrated transaction is real.

**Build:**

- Harden source-link propagation through native `x-if`, `x-for`, and
  `x-teleport` creation, removal, movement, and morph.
- Define accepted grouped semantics for outside, away, enter/leave, pointer
  capture, transitions, models, refs, and IDs.
- Design the named client target or browser blueprint protocol needed for a
  direct `x-for` clone to become a real Citry client instance.
- Keep server-rendered component cloning out until that protocol mints every
  graph and lifecycle identity, not only `data-cid-*`.

**Decision gate:** the client-instantiation protocol is a separate maintainer
decision. A9 may ship structural source propagation without shipping cloned
Citry components.

**Acceptance:** repeated create/remove cycles, keyed reorder, nested loops,
teleport movement, transition cleanup, ref/ID collision, and no registration,
effect, listener, or anchor leaks.

**Landed result:** native structural fills preserve the exact graph-selected
source through nested keyed reorder, model updates, local data, repeated
`x-if` removal and recreation, teleport movement, and `x-id` reuse. Per-clone
cleanup retires source lookup and releases directive effects and listeners.
Pinned Alpine duplicate-ref behavior remains native and explicit.

Citry and Alpine RootGroup enter/leave handlers now apply the same union
`relatedTarget` filter before shared modifier state. Pointer capture remains
physical-element-owned. Compatible full caller renders transfer incoming
boundary endpoints, retire the prior boundary set owned by every rerendered
source lifecycle, reactivate preserved roots, and let inactive revisions
prune. This also handles a successor with no client bindings: the old supplier stops,
declared defaults are reapplied, and removed handlers cannot fire. A
handler-only successor installs only its new handler. A child-only self-render
keeps its caller-authored client binding because the parent source lifecycle was not
rerendered.

The inverse handler-only-to-props transition also settles before the child
callback, remains reactive when a compatible morph replaces the physical root,
and releases cleanly on the next succession.

Consumed Citry `.once` bindings detach their native listeners from every
current root immediately and never attach to later roots. Detached fragment
adoption runs the unsupported structural-clone scan before provisional graph
activation, so rejection cannot leave lifecycle or anchor residue.

When Alpine morph skips attributes for an active transition or shown-state
mismatch, adoption force-updates only graph-owned root markers inside the
transferred exact caps. Alpine transition, model, refs, scope, and DOM identity
remain intact.

O10 is deferred by explicit decision. Native `x-for`, `x-if`, and
`x-teleport` reject a server-rendered client-active Citry component before
graph activation or descendant init. A future target must mint the complete
identity and lifecycle inventory in
[`alpinejs/a9_client_instantiation.md`](alpinejs/a9_client_instantiation.md).

**Acceptance:** 33 A9 cases pass across Chromium, Firefox, and WebKit. The
adjacent atomic-morph, component-boundary, root-shape, and slot-scope set adds
77 passing Chromium cases. The adversarial pass added and closed regressions
for zero-client binding, handler-only, and props-adding successors, detached adoption
rejection, and physical `.once` listener detachment.

### A10: conformance, performance, documentation, and closeout

**Status:** complete.

**Goal:** prove the target as a supported product and retire transitional
documentation.

**Build:**

- Add a conformance matrix spanning server rendering, manifests, browsers,
  morph, Events, root shapes, and structural Alpine.
- Add private-API, hook-count, manifest-version, and comment-preservation
  deployment canaries.
- Benchmark startup, fragment adoption, memory, effects, listener count,
  manifest bytes, and morph cost at realistic production component counts.
- Document plugin registration, duplicate Alpine handling, CSP, debugging,
  `$c-props` authoring, arbitrary attrs, props callbacks, slot scope, and
  rootless deployment.
- Preserve retired package labels only in the explicitly historical Events
  ledger and research records; live design and dispatch guidance use
  `alpinejs.md` and this plan.

**Acceptance:** all conformance cases green in Chromium, Firefox, and WebKit;
no unbounded hook/listener/effect growth; documented payload and startup
budgets; full repository gate green. The closeout gate passed all ten phases
with 3,013 Python/browser tests passing and two skipped; the focused compact
conformance matrix adds 12 green Chromium, Firefox, and WebKit cases.

## 5. Open decisions register

These questions require implementation evidence or an explicit maintainer
call. They do not reopen the graph-first architecture or `$c-props` spelling.

| ID | Question | Must settle by |
|---|---|---|
| O1 | Settled: `citry-client-graph/1` is the exact A2 wire package | A2 |
| O2 | Settled: client-active selected instances and fill occurrences use required `citry:g1` caps | A2 |
| O3 | Settled for A7: detached Python content has no public source opt-in; an already-active graph gives it an empty isolated base, and detached content alone does not activate the client graph | A7 |
| O4 | Settled through A5/A8: transparent caller-to-selected-target ancestry is locked; compatible selected-target replacement follows O9 continuity and cleans old client binding resources exactly once | A5/A8 |
| O5 | Settled: invalid initial supply blocks init; invalid updates clear declared values to `undefined`, do not keep stale data, and recover on the next valid evaluation | A5 |
| O6 | Settled: logical owner shares props, Citry scope, Events State, init/effects/cleanup, and boundary RootGroup state; Alpine directives/listeners/refs/IDs/transitions/focus are copy-local; direct carrier is actual and global/outside/poll carrier is first live | A6 |
| O7 | Settled: compiled `@c-*` and `$sendEvent` are source-owned; `Citry.events.send(element)` remains physical-element-owned | A7 |
| O8 | Settled through A9: Citry adds no teleport redispatch; lexical evaluation follows the source graph, native delivery and movement follow physical placement, and structural clone cleanup is exact | A7/A9 |
| O9 | Settled: same-class self and same-class keyed matches preserve browser plus logical identity; self class change preserves only the browser anchor; plain self output retires both; uncorrelated IDs are fresh; non-self targets preserve only explicit keyed matches | A3/A8 |
| O10 | Deferred by A9: server-rendered client-active clones fail pointedly; a named client target or browser blueprint requires a separate protocol and maintainer decision | separate decision |
| O11 | Settled: A2 requires the literal `citry:g1` prefix, exact protocol v1, and cap-preserving deployment without a fixed protocol byte ceiling; A6 adds continuous validation and pointed corruption retirement; A10 adds deployment canaries and payload regression budgets | A2/A6/A10 |
| O12 | Settled: mirror removal/reorder never reelects a source; last-region or source death retires projection; same-revision region morph reprojects it; A8 preserves exact graph-owned source across replacement by staging the incoming route and retargeting preserved frames | A6/A7/A8 |
| O13 | Settled: v1 exposes post-hook runtime UTF-8 byte offsets, not pre-hook author coordinates | A2 |
| O14 | Settled through A7: projection uses only complete graph edges; cross-graph and foreign-owner relations remain rejected, delayed descendants do not acquire a guessed source, and detached origins stay graph-qualified and isolated | A2/A7 |

## 6. Research evidence to preserve

The research directory is intentionally flat because its harnesses import
adjacent adapters. Keep it that way unless all reproduction paths are updated
together. The evidence index is
[`alpinejs/README.md`](alpinejs/README.md).

The root-shape, refs client binding, slot-scope, and component-first harnesses are
design evidence. During implementation they should remain runnable against
their isolated adapters while product tests are added. A product test passing
does not justify deleting an independent differential unless its claim is
fully covered elsewhere.

## 7. Explicit non-goals

This plan does not include:

- ESM or TypeScript module execution for `Component.js`;
- a virtual DOM;
- a Citry replacement evaluator or reimplementation of Alpine directives;
- an Alpine fork without an A8 blocker report and maintainer decision;
- transparent cloning of server-rendered Citry components under `x-for`;
- general component root-attribute fallthrough;
- changing ordinary `x-show`, `x-model`, `:class`, `x-transition`, or `class`
  into client bindings;
- a general ambient data inheritance channel in place of props or
  provide/inject;
- changing the Events wire protocol beyond the versioned client graph data
  required for ownership integration.

The Alpine-specific deferred items are collected in
[issue #37](https://github.com/citry-dev/citry/issues/37); it excludes the
existing compiler (#10) and ESM-delivery (#35) scopes.

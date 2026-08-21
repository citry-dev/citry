# A10 Alpine conformance matrix

**Status (2026-07-22): implemented.** This record maps the product contract in
[`../alpinejs.md`](../alpinejs.md) to executable checks. It is a closeout
record, not a second source of behavior.

## Required browser gate

Citry supports the graph-first Alpine runtime in Chromium, Firefox, and
WebKit. The compact A10 gate runs on every browser-runtime pull request in all
three engines. The entire browser suite runs in Chromium on pull requests and
in all three engines on the scheduled cross-browser workflow.

The matrix calls `$c-props`, Alpine event handlers such as `@click`, and Citry
handlers such as `@c-save` or `@c-poll.5s` resolved from a nested `<c-*>` tag
**component-tag client bindings**. Their expressions or server handlers remain
parent-owned while the child supplies the component boundary.

Run the compact gate locally with:

```bash
uv run --no-sync pytest \
  packages/py/citry/tests/e2e/test_alpine_conformance_e2e.py \
  --browser chromium --browser firefox --browser webkit
```

Run the complete repository gate with:

```bash
python scripts/check.py --reporter agent
```

## Matrix

| Contract | Primary executable evidence |
|---|---|
| Server ownership capture, exact manifest production, protocol schema, canonical revision, and case-safe render IDs | `test_ownership.py`, `test_ownership_manifest.py`, `test_component_id.py`, `test_id_generator.py`, `test_client_graph_protocol_package.py` |
| Exact `citry-client-graph/1`, UTF-8 offsets, the literal `citry:g1` prefix, and eight-character comment aliases across producer, schema, and browser | `test_wire_constants_are_locked_across_producer_schema_fixture_and_browser_consumer`, `test_ownership_comment_builder_and_parser_share_the_literal_prefix`, and the protocol JavaScript comment tests |
| Alias collisions reject before publication and aborted transactions release their reservation | `test_active_revision_alias_collision_is_rejected_and_released_after_abort` |
| Valid manifests larger than one megabyte remain accepted by the server artifact, reference reader, and browser reader | `test_manifest_artifact_does_not_impose_a_protocol_size_limit`, `test_reference_reader_accepts_a_valid_manifest_larger_than_one_megabyte`, and `test_browser_accepts_a_valid_manifest_larger_than_one_megabyte` |
| Initial-document delivery, parser-time fragment adoption, contextual HTML parsing, and one atomic graph commit | `test_ownership_manifest_e2e.py` and `test_protocol_caps_and_runtime_versions_survive_real_document_delivery` |
| Missing or stripped physical caps reject before anchors, lifecycles, or callbacks become visible | `test_stripped_comment_caps_fail_before_graph_activation` |
| Scope isolation, initialization DAG, one registration per class, managed helpers, replacement, and complete retirement | `test_alpine_lifecycle_e2e.py` |
| Reactive declared props, parent lexical handler scope, physical event values, validation, recovery, queue ownership, and rootless handling | `test_alpine_boundary_contract_e2e.py` |
| Single-, multi-, rootless-, shared-root-, mirrored-, nested-, adjacent-, and document-body ranges | `test_alpine_root_shapes_e2e.py` |
| Supplied and fallback slot source scope, nested transitions, detached content, mirrors, teleport, Citry magics, and cleanup | `test_alpine_slot_scope_e2e.py` |
| Client context values, symbols, defaults, block/restoration, rootless hooks, exact literal/object-bind/programmatic-bind cleanup, shared-root ordering, ancestor initialization, structural-route moves, mirror consensus, one supplied-fill route, teleport origin, and compatible-morph retirement | `test_alpine_ambient_context_e2e.py`; the broader remaining-case matrix stays explicit in `component_provide.md` section 10.11 |
| Atomic graph, Events, dependency, and DOM morph; stable anchors; keyed identity; class changes; plain replacement; rollback | `test_alpine_atomic_morph_e2e.py` |
| Native `x-if`/`x-for` propagation, clone retirement, unsupported active-component cloning, client binding succession, grouped enter/leave, and transition-safe markers | `test_alpine_structural_e2e.py` |
| Events State, binding, queue, stale-response, action ordering, busy, transport, forms, and recurring-resource integration | `test_events_*_e2e.py` |
| Pinned Alpine and morph versions plus every private source/API shape used by the runtime | `packages/js/citry-client/test/canary.test.mjs` |
| Runtime bundle, 325-instance graph/document, and 450-instance large-graph regression budgets | `test_client_performance_payload.py` |
| No live hook, listener, effect, graph, class-data owner, queue, timer, or lifecycle growth through 25 compatible morphs | `test_effect_listener_and_graph_counts_stay_bounded_through_morph_churn` |

## Observable resource contract

`Citry.alpine._debug().runtime` and
`Citry.events._internal.debug()` expose aggregate numbers only. They do not
return live nodes, callbacks, scopes, reactive proxies, or mutable registry
objects. The churn gate snapshots those counters before and after every morph.

The Alpine snapshot covers registrations, class data, logical lifecycles,
stable anchors, ownership revisions and states, client bindings, fill sources,
RootGroups, root bindings, Citry-owned native listener targets, props effects,
managed effects and resources, client context magic frames, class-data owners,
dependency claims, the replay ledger, graph failures, and pending calls. The Events snapshot covers
anchors, render IDs, class records, elements with native binding listeners,
element/event-type listener registrations, polled elements, intervals,
controls, form effects, pending flushes, and queued calls.

Hook counters have a different expected shape: installation, root-selector,
init-interceptor, and startup counts remain fixed; the coordinated morph count
increases exactly once per requested morph. Ownership keeps the active base
and incoming revision while the transaction runs, then remains bounded.
Live dependency claims follow those live revisions. Class-data ownership is
reference-counted by pending calls and live instances, and its live owner
count must stay fixed. The payload map itself is a page-lifetime,
content-addressed cache paired with the loaded variables-script URL cache. The
test requires one entry per distinct hash and proves that a fresh graph can
reuse an earlier hash without reloading its script or stalling its callback.

The replay ledger has a different lifetime. It retains one SHA-256 revision
string for every graph accepted by the current document, including retired
graphs, so old concrete render IDs and caps cannot be cloned and reinserted.
The churn gate requires exactly one ledger entry per accepted morph and keeps
this intentional history separate from live-resource leak assertions.

These are diagnostic and conformance interfaces. They do not promise the
identity or storage layout of the underlying runtime registries.

## Dependency bump rule

An Alpine or morph version change must update the exact package pins, pass the
Node canaries, and pass this matrix in all three browsers. Removing a private
API canary is allowed only when production no longer uses the corresponding
behavior. Replacing a source-shape assertion requires equivalent behavioral
coverage, not merely a renamed substring.

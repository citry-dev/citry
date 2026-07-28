# AlpineJS research and spike index

Evidence and locked batch contracts behind the normative graph-first Alpine design in
[`../alpinejs.md`](../alpinejs.md) and its implementation plan in
[`../alpinejs_plan.md`](../alpinejs_plan.md). These files are research
records, not production code. When an older report records a candidate that
the maintainer later changed, the golden design wins. In particular, the
historical `x-props` candidate is superseded by `$c-props`, and
`c-$c-props` is an accepted orthogonal dynamic form.

Keep this directory flat. Several harnesses load adjacent adapters and
scenarios through `Path(__file__).parent`.

Some audit paths refer to session-local extractions of `old-djc.zip`,
`old-chk.zip`, and `old-vuetify.zip` at the repository root.

## Ecosystem and application audits

- [`alpine-ecosystem-2026.md`](alpine-ecosystem-2026.md): Alpine upstream
  health, Alpine-TS, alternatives, embedding risks, CSP, and the Livewire
  ownership pattern.
- [`alpine-vuetify-audit.md`](alpine-vuetify-audit.md): the maintainer's four
  historical Alpine packages, including the scope-isolation mechanism and
  private-version coupling.
- [`alpine-workproject-audit.md`](alpine-workproject-audit.md): production
  Django application usage, plugins, component counts, props patterns, and
  startup pressure.

## Props and component boundaries

In these reports, a **component-tag client binding** is a browser-side
`$c-props`, Alpine event handler such as `@click`, or Citry handler such as
`@c-save` or `@c-poll.5s`, resolved from a nested `<c-*>` tag. The parent owns
the expression or server handler, while the child supplies the component
boundary where the browser applies it.

- [`exploration-client-props-passing.md`](exploration-client-props-passing.md):
  first props exploration. Its `x-props` spelling is historical.
- [`exploration-x-props-round-2.md`](exploration-x-props-round-2.md): source-
  ordered client-binding design, init DAG, managed helpers, scope, validation, dynamic
  targets, and root-shape requirements. Its spelling is historical, while the
  mechanics feed `$c-props`.
- [`xprops_round_two_harness.py`](xprops_round_two_harness.py): pinned-Alpine
  loop-scope, refresh, cleanup, and clearing evidence.
- [`spike-citry-handler-refs.md`](spike-citry-handler-refs.md): exact parent
  source scope for Alpine handler expressions and optional Citry argument
  expressions, with physical child event values. It does not cover Citry
  server-handler parsing or dispatch.
- [`refs_client_binding_adapter.js`](refs_client_binding_adapter.js),
  [`refs_client_binding_scenarios.js`](refs_client_binding_scenarios.js), and
  [`refs_client_binding_harness.py`](refs_client_binding_harness.py): saved
  three-browser reproduction.

## Root shapes

- [`spike-root-group.md`](spike-root-group.md): grouped multi-root listeners,
  stable live `els`, union containment, shared modifiers, dynamic membership,
  polling, shadow behavior, and cleanup.
- [`root_group_adapter.js`](root_group_adapter.js),
  [`root_group_scenarios.js`](root_group_scenarios.js), and
  [`root_group_harness.py`](root_group_harness.py): saved reproduction.
- [`spike-rootless-lifecycle.md`](spike-rootless-lifecycle.md): text-only and
  empty lifecycles, contextual parsing, nested and adjacent ranges, stable
  anchors, mirrors, polling, and exact cleanup.
- [`rootless_lifecycle_adapter.js`](rootless_lifecycle_adapter.js),
  [`rootless_lifecycle_scenarios.js`](rootless_lifecycle_scenarios.js), and
  [`rootless_lifecycle_harness.py`](rootless_lifecycle_harness.py): saved
  reproduction.

## Slots and fill scope

- [`exploration-slots-alpine-scope.md`](exploration-slots-alpine-scope.md):
  empirically redone exploration for exact call-site source ownership,
  child-owned fallback, nested transitions, structural templates, teleport,
  and product gates.
- [`slots_scope_adapter.js`](slots_scope_adapter.js),
  [`slots_scope_scenarios.js`](slots_scope_scenarios.js),
  [`slots_scope_harness.py`](slots_scope_harness.py), and
  [`slots_scope_server_harness.py`](slots_scope_server_harness.py): saved
  server and three-browser reproduction.
- [`../../../packages/py/citry/tests/e2e/test_alpine_slot_scope_e2e.py`](../../../packages/py/citry/tests/e2e/test_alpine_slot_scope_e2e.py): A7 product acceptance for supply and fallback sources, structural templates, nested isolation, refs and IDs, teleport, Citry magics, mirrors, rootless fills, dynamic targets, morph, detached content, and cleanup.

## Morph and identity

- [`spike-morph-alpine.md`](spike-morph-alpine.md): Alpine and morph pins,
  boot ordering, root selectors, private APIs, and core morph assertions.
- [`spike-component-identity.md`](spike-component-identity.md): fresh server
  component ID plus stable browser anchor, State reconciliation, and lifecycle
  composition.
- [`spike-keyed-morph.md`](spike-keyed-morph.md): key matching, keyed moves,
  preservation costs, and the contextual key fallback.
- [`a9_client_instantiation.md`](a9_client_instantiation.md): A9's decision to
  reject cloned server component identity and the full inventory required by
  any future named client target or browser blueprint.

The Events policy analyses that frame these spikes remain in
[`../events_research/`](../events_research/README.md).

## Graph-first architecture exploration

- [`exploration-alpine-component-first.md`](exploration-alpine-component-first.md):
  the complete architecture comparison and selected graph-first recommendation.
- [`component_first_server_ownership_findings.md`](component_first_server_ownership_findings.md):
  server capture findings.
- [`a1_server_ownership.md`](a1_server_ownership.md): locked production A1
  record, ID, dynamic-target, client binding, fill, and Python-origin policies.
- [`a2_client_graph.md`](a2_client_graph.md): locked production A2 wire,
  physical-cap, transaction, validation, and failure policies.
- [`component_first_syntax_report.md`](component_first_syntax_report.md):
  `$c-props` syntax and browser transport evidence. The decision update makes
  `$c-props` and `c-$c-props` normative.
- `component_first_*_harness.py`, `component_first_*_scenarios.js`, and
  [`component_first_adapter.js`](component_first_adapter.js): saved server,
  syntax, broad browser, comparison, scaling, and partial real-render vertical
  evidence.

The architecture exploration proves mechanisms and comparative feasibility.
Production A1 through A10 now provide server capture, the validated graph
manifest, typed client indexes, stable anchors, Events bridging, the permanent
Alpine broker, component scope lifecycle, reactive props supply, and
source-owned boundary handlers. A6 also lands dynamic RootGroups, continuous
citry:g1 range validation, contextual range morphing with nested-island
protection, grouped fill-region lifetime, and shared-root scope rebinding.
A7 lands exact invocation-owned supply projection, inverse-transition
fallback, detached isolation, direct structural-template propagation, native
teleport composition, and graph-selected Citry magics. A8 lands atomic incoming
graph plus DOM adoption. A9 hardens structural churn, grouped enter/leave,
client binding succession, transition-safe marker adoption, and unsupported clone
diagnostics. A10 locks the supported product with the
[`conformance matrix`](a10_conformance.md) and
[`performance budgets`](a10_performance.md). The completed batch ledger is
[`../alpinejs_plan.md`](../alpinejs_plan.md).

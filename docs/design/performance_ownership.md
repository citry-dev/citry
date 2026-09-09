# Ownership tracking cost and reusable template work

Implementation follow-up and current measurements are recorded in
[Repeat-render optimization research](performance_render_research.md).
The measurements and representation descriptions below describe the earlier
investigation baseline.

Measured September 8, 2026. Ownership tracking accounted for about a quarter
of instrumented tree-building time in the large Citry benchmark. Most of
that work describes the current execution: fresh components, slot attachments,
physical placements and output replacement. Some template metadata can be
prepared once, but retaining source-site metadata across renders did not
produce a convincing complete-render improvement in the bounded probe below.

## Prior art and measurement scope

The investigation read `ownership.py`, its callers in `component_render.py`,
`nodes/__init__.py` and `slots.py`, the consumers in `ownership_manifest.py`,
and the ownership tests. These paths are under `packages/py/citry/`.
The relevant designs are [Alpine ownership](alpinejs.md#54-server-capture-and-serialization),
[component ranges](component_ranges.md), and
[the previous optimization results](performance.md#1010-highest-value-follow-up-results-2026-08-21).

This is the existing large project-page fixture, including `pure = True` on
`HeroIcon` and `ProjectOutputBadge`. Python was 3.14.3 on macOS 26.6.2 arm64.
The installed native extension matched `target/release/libcitry_core_py.dylib`
byte for byte. It was not rebuilt, so this does not establish that every
working-tree Rust change was included. HEAD was
`b3772513079dfc52408dff756bbab0202253783b`, with extensive existing local changes.
The scenario SHA-256 was
`05703823414b5c1feb2b01067861b514f9b2d03906b46eb8d918fb55c64781be`.

The earlier 30-sample baseline measured a median 35.75 ms building the tree,
3.29 ms final serialization and 39.02 ms total. The deeper operation probe used
ten warm renders and averaged 39.45 ms for the instrumented tree. Its selected
ownership operations totaled 10.08 ms, or 25.5%. The preceding broader probe's
10.30 ms / 25.8% describes the same boundaries in another short run.

Timers subtract nested measured operations. In particular, slot-region capture
does not include separately timed body/node execution, although it retains
some callback setup and wrapper work. Ownership context-manager work outside
these selected methods remains in other categories. These are useful cost
boundaries, not an exact semantic partition of every ownership-related
instruction. Timer overhead prevents treating these times as uninstrumented
costs or guaranteed possible savings.

## What ownership records mean

Citry must remember who authored slot content, which component received it,
where it appeared, and which output survived hooks. Template-authored slot content reads template variables from its source
component's scope even when it appears inside another component's HTML. Repeated outlets can give one logical supply several
physical placements. Text-only, empty and multiple-root components also need
identity. Final HTML alone cannot recover those relationships.

The renderer creates one `OwnershipGraph` for the root execution. It records
component calls and fills, binds newly created component IDs, captures each
slot placement, and tracks deferred-child progress. Hooks can select other
output; the graph then keeps the selected relationships and retires displaced
ones. Serialization uses snapshots of these records to produce the client
graph and physical markers.

## Where the ownership time goes

The rows below exclude each other's timed work. For example, recording a
component call invokes source-location recording, but its own row excludes
that nested operation.

| Operation | Calls per render | Instrumented ms/render |
|---|---:|---:|
| Capture a slot placement and wrap its result | 274 | 2.36 |
| Record a source occurrence | 1,081 | 1.40 |
| Retire replaced component output | 1 | 1.21 |
| Bind a new component instance | 342 | 1.18 |
| Record a template fill | 468 | 1.08 |
| Record a component invocation and initial queue entry | 339 | 0.86 |
| Find selected physical regions | 1 | 0.70 |
| Bind supplied slots to their receiver | 342 | 0.40 |
| Bind fills to the originating invocation | 339 | 0.28 |
| Mark a component's queue entry settled | 342 | 0.27 |
| Release transient region-result references | 1 | 0.23 |
| Retire unselected hook-attempt records | 1 | 0.12 |
| **Total, before rounding** | | **10.08** |

The work is numerous small record creations, dictionary/weak-reference
lookups, context changes and relation traversals. During one diagnostic
render, the eight record/site classes were constructed 6,815 times. The
settled snapshot contained 3,182 records, plus 115 shared source-site objects.
The extra 3,518 constructions came from replacing immutable records as targets,
receivers, results and lifecycle states became known.

That count is allocation evidence, not a measurement that constructors alone
consume 10 ms. The same methods also perform validation, bookkeeping and
traversal.

## This benchmark retires most of its structured child output

| Family | Captured records | Still active or settled after root completion |
|---|---:|---:|
| Source occurrences | 1,081 | Source records do not carry lifecycle state |
| Component invocations | 339 | 43 |
| Component instances | 342 | 46 |
| Initialization relationships | 339 | 43 |
| Logical fills | 468 | 57 |
| Physical slot regions | 274 | 30 |
| Deferred queue entries | 339 | 43 |

The fixture's `TabItem.on_render` serializes five tab bodies with
`deps_strategy="ignore"` and stores their trusted HTML. `Tabs.on_render`
then returns an `_TabsImpl` replacement that inserts those strings. The
original bodies still execute, but most of their structured ownership is
retired when that replacement wins. This includes 296 of 342 component
instances and 244 of 274 regions.

See [the fixture](../../packages/py/citry/tests/test_benchmark_citry.py),
`TabItem.on_render` and `Tabs.on_render`. Its comment explicitly describes
this synthetic flattening. These record counts do not imply that the retired
records consumed the same proportion of runtime, or that their work can be
skipped: the hook chose its replacement after the children ran. A client page
that preserves live child ownership may have a different cost distribution.

## Work that could be prepared once

### Source metadata is already shared within a render

`_SourceSite` holds immutable source text, origin, byte and character spans,
line and column. `OwnershipGraph._source_site_cache` currently shares these
values only within one graph. The page records 1,081 occurrences at 115 distinct
sites. Each later root render reconstructs the same 115 sites, while all 1,081
calls still obtain the origin, construct a lookup key and create a fresh
owner-specific occurrence record.

A temporary probe gave each graph the same dictionary of immutable sites,
keyed exactly as today by source text, byte span and origin. It retained the
115 sites while continuing to create fresh IDs, owners, order and occurrence
records. Thirty alternating A/B pairs measured complete warm renders:

| Configuration | Median complete-render time |
|---|---:|
| Existing per-graph site cache | 38.761 ms |
| Shared immutable sites | 38.771 ms |

The median paired saving was +0.224 ms, but the mean paired saving was
-0.177 ms. Together with effectively identical separate medians, this does
not establish a repeatable complete-render win. It does not justify presenting
cross-render site caching as a substantial performance improvement.

Both configurations produced exactly equal ownership snapshots and
1,013,746-byte HTML with deterministic component IDs. Eight existing ownership
tests also passed with the shared-site probe installed: repeated loop sites,
Unicode offsets, cross-render slot isolation, retired-slot revival,
fill-owning parent preservation, selected-descendant ancestry, and selecting
one nested or rootless sibling region.

A stronger candidate would bind an immutable source-site reference to each
final cached runtime node or attribute, removing the lookup as well as the
conversion. That was not prototyped here. The entire source-occurrence
operation costs only 1.40 instrumented ms in this run, and fresh occurrence
construction would still remain, so this candidate addresses a limited part
of the ownership total.

A production cache should follow the actual compiled template/body lifetime.
Class identity alone is insufficient for standalone templates, nested source
projections, resets and extension-generated nodes. Preserve source/span/origin
identity, validate UTF-8 boundaries, and retain lazy error timing for unused
branches. Reset or body eviction must release obsolete metadata. Concurrent
first use needs a defined publication rule. The temporary dictionary was
unbounded and tested only as a probe; it is not a production cache design.

### Other template work appears in other timing categories

Two additional candidates were found in source, but were not benchmarked:

- **Literal component-boundary Events payloads.** The compiled-template Events
  hook validates direct literal bindings using `compile_citry_boundary_binding`
  but discards the returned specification. Runtime input resolution compiles
  the winning binding again. A final literal contribution could reuse an
  immutable payload, while retaining fresh occurrence records. Dynamic values,
  later spreads and parent-specific handler metadata must still be respected.
  The measured fixture has no component-tag client-binding source records, so
  this candidate does not explain its 25% ownership share. Sources:
  `ext/events/bindings.py::_validate_component_boundary_attrs` and
  `nodes/__init__.py::ComponentNode._resolve_inputs`.
- **Static fill properties and body classification.** Component slot collection
  repeatedly checks whether an implicit body is only whitespace. Fill
  collection repeatedly resolves literal names and validates data/fallback
  identifiers. Those results could follow the final specialized body or be
  computed on first execution. Dynamic names, spreads, control flow, lexical
  variable checks and current slot closures remain live. Much of this work
  sits in the child-input/slot category, rather than the ownership table.
  Sources: `ComponentNode._collect_slots` and `FillNode._resolve_props`.

## Work that cannot be copied from the first render

Fresh component IDs, execution order, selected component targets, evaluated
keys, client-binding values, slot receivers, containing regions and hook
outcomes describe the current execution. A loop can execute the same authored
call zero times or many times. Two calls can share one source-site descriptor
while requiring distinct invocation and placement records.

Existing tests make these constraints concrete:

- `test_one_compiled_location_executed_in_loop_gets_fresh_records` requires
  separate occurrence IDs while sharing one source-site object.
- `test_template_fill_reused_in_later_render_keeps_graph_local_ids_isolated`
  protects slot provenance across root renders.
- `test_replacement_reusing_retired_slot_creates_active_fill_occurrence`
  requires a fresh active attachment when a retired slot is selected again.
- The selected-descendant and sibling-region tests preserve exactly the
  selected relationships, including text-only regions and lexical ancestors.

These tests are in
[`test_ownership.py`](../../packages/py/citry/tests/test_ownership.py).
Caching the first graph or its selected-region answers would violate these
conditions when inputs, branches or replacement choices change.

## The larger opportunity needs cheaper per-render state

About 8.68 of the 10.08 instrumented ownership milliseconds lies outside
source-occurrence recording. First-render source preparation cannot remove
that work. The larger candidate is reducing repeated record construction and
replacement while preserving fresh execution identity.

An internal mutable builder or compact per-attempt journal could retain live
IDs and relations, then produce immutable snapshots when needed. This could
avoid constructing a new full record for every binding and state update.
It is an unmeasured design candidate, not a demonstrated saving.

It must preserve snapshots already handed to consumers: serialization checks
that the live graph still matches the snapshot taken when it prepared the
client graph, and cache replay also consumes snapshots. Snapshot capture may
happen before the root render ends. Any new representation must preserve
these cases: selecting descendants, rendering a slot repeatedly, reviving a
retired slot, recovering from a failed render, and selecting output from
another graph. A simple discard range cannot cover all those cases.

The current implementation already builds relation indexes lazily, uses
capture-order ranges for suitable retirement operations, and caches subtree
containment within a selection pass. Previous experiments in
[performance.md](performance.md#1010-highest-value-follow-up-results-2026-08-21)
found that eagerly indexing every render object made the complete render
slower. A new representation should demonstrate less construction work and a
complete-render improvement while retaining the existing ownership tests.

No production renderer code was changed. The temporary scripts and raw results
for this investigation are under `/tmp/citry-ownership-profile-20260908/` on
the measurement machine: `operations.py`, `phases.json`, `probe.py`,
`probe.json`, `check_shared_sites.py` and `checks.txt`. The scripts reuse the
scenario loader from `/tmp/citry-render-profile-20260908/collect.py`.

For the field-consumer audit, exact retirement allocation counts and comparison
of mutable rows with packed storage, see
[Ownership storage](performance_ownership_storage.md).

# Ownership storage: what is necessary and what can be cheaper

Implementation follow-up and current measurements are recorded in
[Repeat-render optimization research](repeat_render_research.md).
The measurements and representation descriptions below describe the earlier
investigation baseline.

Citry records which component supplied content, which component received it,
where each use appeared, and which output survived component hooks. The
information has runtime consumers. Its current allocation pattern is not a
requirement: updating one field commonly constructs another complete frozen
record. Reducing these repeated allocations is the strongest candidate identified
by this investigation.

This is a source audit and bounded storage experiment from 2026-09-08, not an
implemented optimization. Read [the ownership profile](performance_ownership.md)
for the original timing method and benchmark environment. Production code was
not changed. The executable probes and raw data are in
`/tmp/citry-storage-analysis-20260908/`; that temporary directory is not a
persistent repository artifact. The results and their limits are recorded here.

## Why source sites and source occurrences are different

`_SourceSite` stores a source text reference, origin, byte span, character span,
line and column. `SourceLocationRecord` says that an operation at that site ran
for a particular owner at a particular point in capture order. It also stores
operation kind and optional mapping key/index for binding contributions.
See [their definitions](../../packages/py/citry/citry/ownership.py).

For example, a loop executing one slot outlet ten times can share one static
site, but produces ten distinct outlet occurrences. Their source text is the
same; their selected physical regions can differ. `resolve_slot_region()` uses
an occurrence's source-location ID to find its outer region. Replacing that ID
with a shared site ID would merge distinct executions.

The benchmark captures 1,081 source occurrences, backed by 115 distinct sites:
339 component calls, 468 template fills and 274 slot outlets. There are no
component-boundary client-binding occurrences in this fixture. Each occurrence
holds a reference to its site; it does not copy the full template string.

Source records serve more than developer error messages:

- Slot-outlet IDs identify the particular placement to resolve or rebind.
- Cache export and replay match source ranges and snippets to a supplied-slot
  writer, then relocate them to the current writer.
- JavaScript and CSP validation use source records to inspect reached bindings
  and report their authored position. The CSP validator currently skips a
  binding when its location is missing; deleting locations would therefore
  change validation, not just diagnostic precision.
- Manifest preparation validates source references even when production output
  omits source provenance. Snapshots and cache artifacts preserve source order.

The two concepts should remain, but they need not be two Python object types.
A possible internal occurrence row contains owner handle, operation-site handle
and capture order. Its ID can be its stable row position; a sparse side table can
hold uncommon mapping values. The operation descriptor must retain kind as well
as source site. An adapter can expose the existing SourceLocationRecord shape.
This proposal requires normalized replay IDs and complete owner lookup.

Static sites should follow the actual compiled/specialized body, with matching
invalidation. Replayed archived descriptors must also remain available for the
lifetime of retained graphs and snapshots. A component class alone does not identify all possible body/source
variants. Earlier cross-render site sharing passed eight focused checks but did
not show a convincing whole-page improvement across 30 alternating pairs. It
removes 115 site constructions, not the 1,081 dynamic occurrences.

## Which information can move or be derived

The field audit followed runtime reads, snapshot equality, cache export/import,
manifest construction, security checks, Events/i18n consumers and browser use.
All audited record families have production consumers. A value being required
in an exported record does not mean every live row needs its own stored copy.

| Current information | Plausible internal representation | Constraint |
|---|---|---|
| Source text/origin/spans/line/column | Shared template/site metadata; compute some coordinates on demand | Preserve Unicode offsets, cache matching and validation/error timing |
| Source occurrence ID | Stable row position | Replay remapping and invalid references must be checked |
| Owner class ID repeated across records | Instance handle plus class table | Detached owners and pending targets need explicit handling |
| Instance class name and transparency | Class metadata table | Retain exact class identity and cache compatibility checks |
| Authored component tag and operation kind | Compiled operation descriptor | A dynamic component's authored tag differs from its final target class |
| Fill source policy | Derive from fill kind | Reject invalid imported kind/policy pairs before normalization |
| Queue target and invocation ID | Store queue state/order beside its invocation | Validate replay consistency; preserve absent/duplicate-row behavior explicitly |
| Initialization parent/child | Derive from invocation in the normal capture path | Imported explicit edges need validation or separate storage |
| Binding payload type tag | Class constant or property | Preserve constructor, union and wire contracts |
| Empty bindings/selectors and absent mapping values | Sparse side tables | Preserve binding order, null distinctions and selector ancestry |
| Lifecycle state | Small integer or flags in mutable storage | Invocation, instance, region, init and queue states have distinct semantics |

Fields that look similar can represent different facts. A fill's source owner
is not its receiver. A region's receiver at placement time cannot always be
recovered from the fill's later receiver. A region's result owner can differ
from both. Explicitly unknown class fields must remain unknown even when instance lookup
could supply a value. Cross-family capture order is not a family's row number. A pending
invocation has a target class before it has a target instance.

`RenderQueueRecord` records one invocation's deferred-render progress. The actual renderer task
queues contain component instances, callbacks, contexts, generators and other
Python references. Slot weak maps and temporary region-result maps also have
object-lifetime behavior. A universal scalar encoding for every internal queue
would need a separate object-reference table and preserve strong/weak ownership.

## What the retirement call physically does

[retire_component_output](../../packages/py/citry/citry/ownership.py) largely
works with IDs, enum values and records containing scalar relations. The HTML
render-object traversal used to discover selected regions happens separately.
The earlier 0.70 ms selection bucket must not be attributed again to retirement.

Retirement performs these operations:

1. Build sets of explicitly preserved component/region IDs and walk their
   ownership and containment ancestors. Construct or reuse relation indexes.
2. Process lists of pending owners, instances and regions. Look up adjacency
   lists, check capture cutoffs, and add newly affected records to sets/lists.
3. Retire affected invocations and non-failed queue entries, preserving FAILED
   queue entries.
4. Scan the instance and initialization lists, replacing affected records.
5. Scan instances again to build active-receiver membership and class lookup.
6. Scan fills, constructing temporary lists of related and newly selected
   regions. Preserve or rebind surviving attachments, and retire discarded ones.
7. Update affected regions and relation-index validity.

One newly instrumented benchmark render entered this call with 340 instances,
339 invocations, 468 fills, 274 regions and 338 initialization edges. The counts
are smaller than the final graph because rendering continues after retirement.
The call constructed exactly these replacement records:

| Record | Constructions inside retirement |
|---|---:|
| Invocation | 296 |
| Queue | 296 |
| Instance | 296 |
| Initialization edge | 296 |
| Fill | 411 |
| Region | 244 |
| **Total** | **1,839** |

This new probe counts allocations; it does not split the earlier 1.21 ms into
constructor time versus graph work. Across the complete render, the previous
probe counted 6,815 constructions in eight audited classes: 3,182 final journal
records, 3,518 replacements and 115 sites. These counts do not measure all
Python allocations, nor imply constructors account for the entire ownership
bucket.

The direct candidates are updating state cells rather than copying rows,
visiting affected instance/init rows by index, avoiding per-fill temporary
lists, and maintaining useful adjacency information. Maintaining more indexes
adds work to capture and consumes memory; compare complete renders, not only
retirement. Lazy retirement flags or generation markers still need selected
ancestor closure, surviving newer regions and later Slot reuse to work.

## Storage experiment using the actual queue update stream

`layout_probe.py` captured 1,313 queue constructor/update events for 339 final
rows, then replayed that stream into alternative six-field numeric layouts.
It checked that every layout exported the same final rows and scan checksum.
Each result is the median of seven samples, with 10 build/update repetitions
and 50 scan repetitions per sample. These are small storage kernels, not
whole-render replacements or estimates of total renderer speedup.

| Representation | Build and updates, ms | Scan two fields, ms | Container and row bytes |
|---|---:|---:|---:|
| Frozen slotted dataclass | 0.3673 | 0.00565 | 29,992 |
| Mutable slotted dataclass | 0.1353 | 0.00586 | 29,992 |
| Tuple, replaced on update | 0.0636 | 0.00578 | 35,416 |
| Mutable list row | 0.0873 | 0.00598 | 38,128 |
| Packed bytearray, six int64 fields | 0.1969 | 0.02964 | 16,329 |
| Six numeric array columns | 0.1954 | 0.01254 | 17,016 |

The packed buffer used about 46% less container/row storage than the frozen
rows, but its particular Python field scan was about 5.2 times slower. Mutable
slotted rows reduced construction/update time about 63% in this kernel. Tuples
show that avoiding frozen dataclass initialization may matter even when updates
still create replacement rows; they used more row storage here.

Important limits:

- String/enumeration-to-integer conversion and the precomputed update deltas
  are outside the timer for every representation. They are real integration
  costs if a design needs to compute them during rendering.
- Packed capacity was known and preallocated. General rendering needs growth.
- Container/row sizes exclude referenced Python scalars, lookup tables,
  allocator overhead and the shared event stream. They are not heap or RSS.
- Layouts run sequentially; this is a directional microbenchmark, not a
  process-level randomized benchmark or an integrated optimization.
- The scan tests a truthy encoded state and sums IDs; it exercises field reads,
  not the full retirement algorithm. All encoded states are nonzero.
- Snapshot exports, rollback, consumer adapters and native boundary conversion
  are not included in the build/update numbers. Their costs can erase a win.

## Established techniques and whether they fit

**Mutable construction with immutable snapshots.** Python documents that
frozen dataclass initialization uses `object.__setattr__`, with an initialization
penalty. Citry also repeatedly allocates complete frozen replacements. Keep
internal updateable rows and materialize immutable snapshots only when consumed.
This is the first representation experiment to prioritize, not a demonstrated
whole-render improvement.
[Python dataclasses](https://docs.python.org/3/library/dataclasses.html#frozen-instances).

There are two immediate correctness traps: `snapshot()` currently shares frozen
rows, and replay rollback shallow-copies lists of frozen rows. Simply removing
`frozen=True` and mutating records breaks both. A candidate needs immutable
copies or versioned snapshot caching, plus a mutation journal or copied rollback
state. A mutation version cannot reuse capture order: some state/binding changes
do not advance that order. Old snapshots must remain unchanged.

**Shared dictionaries and separate frequently read columns.** Arrow documents
integer references to repeated values, contiguous numeric columns, string data
with offsets, and validity bitmaps. Those are relevant storage ideas, not a
recommendation to add Arrow as a dependency. Citry could keep class/source facts
once and store compact owner/region handles plus state/order separately. Sparse
binding and diagnostic data need not occupy every frequently accessed row. The local column
probe also shows that Python-level column scans are not automatically faster.
[Arrow format](https://arrow.apache.org/docs/format/Columnar.html).

**Packed mutable buffers.** `struct.pack_into` updates a writable buffer;
`unpack_from` returns Python tuples. This makes packing useful for storage, but
repeated scalar decoding has a cost. Use a bytearray or native numeric arrays
for updates, not repeated immutable string/bytes concatenation. Variable strings
can live in a separate table or offset buffer. A compact format must define null
values, signedness, capacity growth, overflow and invalid-handle behavior.
[Python struct](https://docs.python.org/3/library/struct.html),
[Python array](https://docs.python.org/3/library/array.html).

**Stable handles and allocation in groups.** A graph-owned append-only table can
keep IDs valid without one allocation per row. If deleted slots are reused, a
versioned handle detects stale references; slotmap documents that technique.
Citry currently keeps retired identities and can revive old Slot supplies, so
recycling at retirement is not automatically safe. The table lifetime must
follow retained graphs/slots, not merely the end of the root rendering call.
[slotmap](https://docs.rs/slotmap/latest/slotmap/).

**Move the operations with the data.** A native compact table is more attractive
if Rust also performs binding, graph traversal and retirement in batches.
Packing rows in Rust while Python retrieves fields individually retains boundary
and conversion work. PyO3 documents conversion and repeated string-allocation
costs; the recommendation to batch this graph's operations is an inference from
those costs and our access pattern. Prior Citry optimizations already showed
isolated Rust speedups need not improve whole-page time.
[PyO3 performance guide](https://pyo3.rs/main/performance).

## Capture timing and the recommended order of experiments

Prepare immutable source/operation descriptors once per compiled body. Record
owner identity, invocation/attachment identity, actual placement, order, target
and lifecycle changes each execution. Defer expanded snapshot records and
unrequested diagnostic formatting when their consumers allow it.

Do not infer that final HTML-only serialization permits skipping all capture:
hooks and slot routing have already used ownership before serialization chooses
its policy. An optional reduced-capture mode would require a proven capability
contract covering hooks, caches, validation, events and i18n, with conservative
fallback for unknown/dynamic behavior.

Recommended experiments, in order:

1. Mutable internal records with immutable snapshots and correct replay rollback.
   Compare against a cheaper immutable representation too, to separate frozen
   constructor overhead from the benefit of in-place updates.
2. Co-locate invocation, queue and ordinary init storage; enforce replay
   invariants before deriving fields or removing index dictionaries.
3. Reduce retirement-wide scans and per-fill temporary collections using measured
   adjacency/index maintenance costs.
4. If ownership still accounts for substantial render time, compare a native
   compact graph that owns
   its operations with the Python builder. Include conversion and export time.

Required checks include unchanged old snapshots; replay failure rollback;
invalid/dangling IDs and inconsistent imported records; repeated outlets in a
loop; text-only and empty placements; selector ancestry; multi-receiver fills;
retired Slot revival; selected descendants and newer regions surviving parent
replacement; Unicode positions; CSP rejection; cache writer relocation; and
unchanged selected manifests, events and i18n, as well as HTML.

The existing instrumented retirement bucket is about 3% of the instrumented
render tree. Eliminating it entirely would therefore save about 3% on that
measurement. Representation changes across capture, binding and settlement can
address a larger fraction, but no whole-render gain from this storage study has
yet been demonstrated.

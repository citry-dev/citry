# Store ownership rows beside native retirement

This records the initial experiment design. The current queue-order
representation and numeric fallback are documented in
[`../native_ownership_qualification/queue_orders.md`](../native_ownership_qualification/queue_orders.md).

## Prior art

The existing journal stores invocation and queue rows together in `src/lib.rs`.
`src/retirement.rs::retire` reads the other four Python record tables, builds a
numeric `Graph`, computes retirement and returns changes for Python to apply.
The previous incremental comparison saved only 0.053 ms. `ownership.py` creates
immutable instance, initialization-edge, fill and physical-region records, then
replaces them during binding and retirement. Snapshots and other Python readers
need the public records, but intermediate mutations need not construct them.

This experiment extends the standalone PyO3 module, not the shipped binding.
Prior source reads include `OwnershipGraph.bind_instance`, `_append_fill`,
`capture_slot_call`, `bind_template_fill_sources`, `retire_component_output`,
`import_replayed_snapshot` and the record update helpers. The existing
`check_retirement.py` differential harness and ownership/manifest/replay suites
provide comparison boundaries. The previous mutable-Python builder experiment
was neutral; native storage must improve the complete transaction to justify
adoption.

## Design and alternatives

Add native tables for instances, initialization edges, fills and regions. Keep
field references and cache immutable public rows only after a Python reader
requests them. Capture writes field tuples directly, selected updates patch
fields, and native retirement applies its plan to the same native tables.
Return only the receiver-map updates still required by Python. Keep source
records in Python for this stage.

Reuse the existing numeric retirement algorithm and its Python set-order
handling. It still derives numeric relationships when retirement occurs, but
reads native field storage without exporting Python rows and applies changes
without returning per-row edits to Python. This measures the value of removing
those intermediate rows before adding persistent numeric indexes. A complete
persistent numeric graph remains a further design; it is not claimed here.
A native shadow graph beside unchanged Python tables was rejected because it
would retain the allocation and update work this experiment is meant to remove.

Replay materializes all native tables and continues with the original Python
methods, including rollback. Custom relationship types rejected before native
mutation use the existing Python retirement path. Existing unsigned-64-bit
limits, non-atomic failed native updates, and malformed-graph exclusions remain.
The tables support the integer indexing, iteration and append/update operations
used by the qualified runtime. Arbitrary user mutation of private containers,
record factories or helper methods is outside this experiment's contract.

## Falsification and scope

Compare retained snapshots, hook-visible ownership, all HTML and Python queue
settlement order. Exercise fill revival, later-region promotion, errors and
replay with the existing focused suites. Run randomized sequential retirement
comparisons against the reference to catch stale cached public rows. Use 60
alternating complete-render pairs, first versus production and then versus the
previous native-retirement backend. All conversion, patching and snapshot work
required by the real render stays inside timing. A useful candidate should save
at least 0.5 ms over production and at least 0.25 ms incrementally in two runs,
with at least 40/60 favorable pairs in each. Stop a clearly losing initial run.

The new surface is confined to this benchmark's Rust module, stub and Python
adapter. The shipped parser, AST, compiler format, five language implementations,
PyO3 registration and `citry_core` wrapper/stub are unchanged. A production
migration and portable ownership API remain deferred until evidence supports
them. This written plan precedes editing; the session has no ExitPlanMode tool.
The opt-in native build and focused tests add no ordinary CI or release gate.
Use the existing build artifact for comparisons, keep CPU-heavy validation out
of timing runs, and record source hashes, raw observations and limitations.

## Review corrections

The first smoke render reached `bisect_right`, which requires CPython's sequence
slots; the native class now declares sequence support. Review also found cycles
through Python field values and a callback that invokes replay before a native
patch. Both native table classes now participate in GC, and transformed patches
check the current table type at the mutation site. Custom slot-name subclasses
fall back before native retirement because their hash callbacks may observe
intermediate graph state. The checks retain successful and raising mid-callback
replay cases, cached snapshots, invalid patch validation, ordered lookup and
four raw/exported GC cycles.

Native table iteration eagerly exports a snapshot list. Arbitrary mutation
while iterating private containers, custom record factories/helpers and
reentrant destructors remain outside this experiment's qualification. No
complete list replacement or production compatibility claim is made.

## Result

Keep this backend experimental. Final production-reference medians were
31.739 ms versus 31.357 ms, with a 0.250 ms median paired saving and 47/60
favorable pairs. Against the previous native retirement algorithm with Python
tables, final medians were 31.682 ms versus 31.670 ms; paired saving was
-0.040 ms with 25/60 favorable pairs. The acceptance rule is not met.

The reader diagnostic found 2,916 immutable exports for 1,423 captured rows.
A remaining Python ancestry lookup requests 907 exports to build relationship
indexes. Moving that consumer beside the stored fields is the next hypothesis;
these measurements do not establish its benefit. Full results and limitations
are recorded in the research log's twelfth iteration.

# Bind fill fields without exporting intermediate Python records

## Prior art

`packages/py/citry/citry/ownership.py:1233` binds a template fill to its
source invocation after checking policy, kind, lexical owner and an existing
binding. `bind_supplied_slots` at line 1296 revives retired fills, then either
attaches a receiver or creates a separate attachment for a forwarded slot.
`_revive_retired_template_fill` at line 1350 returns an active fill unchanged.
The immutable fill record at line 388 has thirteen fields.

`benchmarks/ownership_journal_probe/src/storage.rs` already stores fields,
exports immutable rows on demand and invalidates its cached export on patch.
Its Python adapter transforms selected constructors and patches, while Python
field readers still export rows. `check_storage.py` exercises retained records,
GC and replay inside a slot callback. Existing ownership tests cover forwarding
and retired-slot reuse. The current native reader report observes 194 exports
at source binding and 194 at revival checks in one complete fixture render.

## Design and alternatives

Add two methods to the standalone native RecordTable. One performs the existing
source-binding checks and patches the source invocation. The other attaches a
receiver only when the fill is active and its receiver is empty or equal. It
returns false for retired fills or another receiver; those cases run the
existing Python revival/forwarding path. Preserve slot iteration order and
per-slot updates, including source-binding errors after earlier successful
slots. Reuse Python rich comparisons and retain Python field references.

The adapter adds a guarded early path within the existing supplied-slot loop.
Source binding keeps the original Python loop and invocation lookup, delegating
only each fill's checks/update. Table-type guards retain the existing fallback
after replay. No callback spans a cached assumption about native table storage.

A generic field accessor would replace each exported record with repeated
Python/native calls. Batching an entire mapping could reorder user iteration
and exceptions relative to updates. These are deferred in favor of two bounded
operations that remove both reads and writes at each crossing.

## Failure modes, scope and falsification

Validate thirteen-field width and row bounds before mutation. Preserve both
source-binding RuntimeError messages and leave the failing row unchanged.
Retained immutable records must keep their earlier values after success. The
prototype still does not qualify custom factories, mutated private containers,
helper overrides, reentrant field comparisons/destructors or concurrent graph
mutation. Native borrowing can reject reentrancy; no general compatibility is
claimed for those cases.

This changes only the experimental module, its local stub and opt-in adapters.
The five template language implementations, parser/AST/compiler contract,
shipping PyO3 registration, Python wrapper and shipping stub need no changes.
Portable ownership API and production integration remain deferred. This written
plan precedes editing; ExitPlanMode is not available in this session.

First run focused source-binding/receiver cases and relevant existing ownership
checks, and verify complete fixture snapshots and HTML. Count exports outside
timing. Then compare the candidate against the existing combined native backend
in eight balanced randomized fresh-process pairs, 80 renders after six warmups,
with normal GC and all samples retained. Require seven joint wall/CPU wins and
0.25 ms median paired mean wall saving to justify further integration work.
Record exact adapter, native source and artifact hashes. No CPU-heavy checks or
builds overlap timing. Fewer exports alone do not establish a performance gain.

# Measure direct positions for ordinary ownership capture

Ownership capture appends invocation, fill, region and queue records and
maintains four dictionaries from record IDs to list positions. The ordinary
path assigns consecutive one-based IDs and appends records without deleting
retired rows. This suggests replacing dictionary reads with `id - 1` and
removing the corresponding writes.

The prior-art search covered all four index references in `ownership.py`,
record creation, retirement, immutable snapshots, replay backup/restore and
`import_replayed_snapshot`. It also covered the replay producer in
`ext/cache/replay.py`: source, invocation, fill and region rows are constructed
with sequential local IDs, while queue IDs are resolved from references.
Import allocates fresh IDs in sorted local-ID order and appends rows in
snapshot order. The ordinary path's position invariant therefore cannot be
assumed for every replay input without further qualification.

First test the performance of direct indexing on the existing large fixture.
The candidate transforms the ownership methods mechanically: index reads
become subtraction, index writes disappear, and region-index membership
becomes a bounds check against the region list. The four empty dictionaries
remain allocated; their population and lookup costs are the target. It
rejects snapshot import and mutation backup/restore explicitly. This is not
a production implementation or a bound on all possible index designs.

The candidate also changes error behavior for invalid, non-integer or custom
IDs. Direct list indexing can accept negative positions or raise a different
exception where the dictionary rejected a key. Missing-ID behavior, queue
alignment, custom record factories, constructor failures, reentrancy,
concurrent mutation and replay all need qualification before adoption.
No production source changes in this experiment.

Compare eight balanced randomized fresh-process pairs, each retaining 80
complete render samples after six warmups, with ordinary GC enabled. Require
seven joint wall/CPU wins and 0.25 ms median process-pair mean wall saving
before investing in a production-compatible design. Keep every pair and match
HTML digests and native artifacts. Separately compare every reached ownership
snapshot and assert consecutive IDs at that boundary. Untimed activation
must show populated record lists and empty candidate index dictionaries.

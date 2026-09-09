# Recheck combined native ownership storage on the current renderer

The existing standalone journal stores invocation/queue state together, keeps
instance, edge, fill and region fields in native tables, and applies retirement
there. Python readers materialize immutable public records. Its earlier timing
preceded fresh-process comparisons. The subsequent empty-hook-retirement guard
removed an unnecessary ancestry/index-building operation and helped the native
backend in an incremental comparison. Those separate historical savings cannot
be added to establish a current combined gain.

Prior art: `ownership_journal_probe/{README,storage_plan,ancestry_plan}.md`,
`storage_probe.py`, the journal loader and Rust `storage.rs`/`lib.rs`; research
iterations twelve through fourteen; the current `OwnershipGraph` methods and
the skip for equal hook capture orders in `_settle_render`. No native source or
shipping runtime changes are made for this comparison. Rebuild the standalone
locked release artifact before timing. The optional native ancestry query stays
disabled, since the current fixture skips its earlier empty-window caller.

Measure eight balanced randomized fresh-process pairs. Each worker retains 80
complete renders after six warmups with normal GC. Both variants import the
same standalone module; the reference leaves production ownership installed.
Match hash seed and render IDs within each pair, keep all samples and compare
their HTML digests. Record both shipping and experimental native hashes and the
adapter/Rust sources. Compare every ownership snapshot reached outside timing.
Untimed activation must show the four native table types at snapshots and one
native retirement with no unsupported-input fallback.

Require seven joint wall/CPU wins and 0.25 ms median process-pair mean wall saving
before investing in a broader native design. Budget this screen to less than
five minutes; no builds or CPU-heavy tests overlap timing. It measures the
combined current renderer and existing backend, not an isolated native kernel
or a gain attributable to one historical change.

All existing prototype limits remain: replay materializes Python tables;
numeric IDs/orders have native range limits; failed mutations are not fully
atomic; custom private containers, record factories, helper callbacks and
destructor reentrancy are not fully qualified. The candidate is not a shipping
list replacement. A passing screen justifies further design and qualification,
not production adoption.

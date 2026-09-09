# Prepare one slot region beside its stored ownership fields

## Prior art

`packages/py/citry/citry/ownership.py:1462` selects a logical supply, resolves
the outlet, revives retired fills, reads a containing region and appends an
eleven-field physical region before calling slot content. It updates the
region after the callback and wraps the result. `LogicalFillRecord` at line 388
and `PhysicalRegionRequestRecord` at line 463 define the fields. The standalone
storage adapter already writes field tuples and patches regions; its Python
readers still export rows. The current native reader diagnostic attributes
274 fill exports and 68 containing-region exports to slot capture.

Iteration twenty-seven's grouped binding experiment removed 388 exports but
failed the complete-render screen. This experiment targets a different unit:
field reads, region field assembly and append together, leaving binding as in
the existing native backend. Prior checks include `check_storage.py` for
mid-callback replay and errors, and ownership/manifest/cache-replay suites for
retirement, selected supplies, forwarding and nested placements.

## Design and alternatives

Add one method to the standalone region RecordTable. Given the fill table and
index, optional containing-region index, candidate region ID/order/fill/parent
IDs, optional outlet receiver/location and state values, it validates layouts,
reads an active fill, resolves receiver/transition/source fields and appends the
region. It returns its row index. A retired fill returns None without mutation;
the adapter then runs the existing capture path, including revival. Candidate
counters are computed without changing the graph and committed after success.

Keep slot callbacks, context variables, result-owner lookup and result wrappers
in Python. After any callback or result-property lookup, select the current
storage again when patching: replay can materialize the table. Retired fallback
repeats supply selection; custom selection/hash callbacks are unqualified.

A separate field getter would retain Python field assembly and additional
crossings. Moving callback invocation and wrapping into Rust would extend the
exception, context-variable and callback contract substantially. Start with the
bounded preparation operation, then require complete-render evidence before
expanding it. The rejected grouped fill-binding operations stay disabled.

## Failure modes and verification

Reject wrong table widths, malformed argument tuples and invalid row indexes
before append. Return None for inactive fills before inspecting parent rows.
Preserve previously exported immutable rows and source field object references.
Malformed private indexes, custom record factories/helpers, reentrant rich
comparisons/destructors and concurrent graph mutation remain outside the
prototype's qualification. On valid active graphs, graph counters and the
region index are updated before the callback observes them. Allocation failure
atomicity across the native append and Python map update is not qualified.

Run the existing ownership/manifest/cache-replay suites with the adapter active.
Add focused callback failure/replay and native input-validation observations,
compare all reached snapshots/HTML, and count removed exports outside timing.
Then use eight balanced randomized fresh-process pairs, six warmups and 80
complete renders per process with normal GC and all samples retained. Compare
against the existing native backend using the same artifact; require seven
joint wall/CPU wins and 0.25 ms median paired mean wall saving. Keep builds and
CPU-heavy validation out of timing. A record-count reduction is not sufficient.

The new method, registration through the existing class and local stub are
confined to the benchmark crate. Shipping PyO3 registration, wrapper/stub,
parser/AST/compiler and five language implementations need no changes. A portable
ownership API and production integration are deferred. This written plan
precedes editing; ExitPlanMode is unavailable in this session.

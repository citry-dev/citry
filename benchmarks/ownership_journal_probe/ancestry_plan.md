# Compute ancestry beside stored ownership rows

## Prior art

At `805de833`, the stored-row experiment still exports 907 records when
`OwnershipGraph._with_ownership_ancestors()` calls `_ensure_relation_indexes()`.
The original helper at `ownership.py:1775` follows logical parents, invocation
sources and selectors, then initialization parents. Historical relationships
participate regardless of state. The existing native retirement calculation in
`../../crates/citry_ownership/src/lib.rs` also closes ancestry, but uses native set iteration; reusing it
for this Python-returning helper would need to qualify ordering and identity.

`storage_probe.py` already keeps instance and initialization rows in native
field vectors beside the invocation journal. The reader diagnostic and full
render comparisons from the twelfth iteration show why moving only storage
was insufficient. Existing ownership, manifest, replay and randomized retirement
checks provide integration boundaries.

## Design

Add an opt-in native ancestry query that reads those three native row families
without exporting public records. Build only the relations ancestry needs.
Preserve the reference's logical-parent, invocation-source/selector and init
addition order, Python seed-set iteration and LIFO traversal. Add the original
Python string objects to the returned set, preserving which equal object is
first inserted. IDs require exact UTF-8-compatible strings; reject unsupported
inputs before exposing a result and use the original Python helper. Do not
mark Python indexes current: a later Python reader must still rebuild them.
Replay keeps its existing Python fallback. Unique invocation IDs and a
consistent invocation-index map are required, as in the existing native
retirement experiment. The query also qualifies key types in the unrelated
region indexes that Python would build, so bypassing their construction cannot
skip custom hash callbacks. Selector containers must be exact tuples and seeds
an exact set; other values use Python fallback.

A persistent index would reduce subsequent query setup, but adds invalidation
and update costs. Measure this bounded read operation first. Returning a native
set in arbitrary order was rejected because downstream work can observe Python
set iteration. The new query still builds temporary relations; it does not
establish a complete persistent native ownership graph.

## Qualification and decision

Run the current ownership/manifest/replay suites with this mode, retained
snapshot and mid-callback replay checks, and randomized ancestry comparisons
that check membership, iteration order and string-object identity. Include
cycles, duplicate logical-instance IDs, selectors, historical rows and
unsupported string subclasses. Use the existing randomized sequential
retirement harness with the mode active to cover its callers.

Then compare two runs of 60 alternating complete-render pairs against the
stored-row backend without native ancestry. Require at least 0.25 ms paired
saving and 40/60 favorable pairs in each. Also compare against production;
retain all output and snapshot equality checks and source/artifact hashes.
An isolated lookup gain or fewer exports alone does not justify adoption.
Stop a losing first comparison and record why. This opt-in experiment adds
no ordinary CI or release gate; do not overlap builds/tests with timing runs.

The new PyO3 method, registration and stub live only in this standalone
benchmark. Production parser, AST, compiler, five language implementations,
shipped native registration and Python wrappers are unchanged. Production
integration remains conditional on evidence and complete compatibility work.
This written plan precedes edits; ExitPlanMode is unavailable in this session.

## Result

Keep the query as an experimental mode. It meets the incremental rule, with median paired
savings of 0.699 ms and 0.469 ms over native storage with Python ancestry, with 52 and 55
favorable pairs respectively. Production comparisons show median paired savings of only
0.401 ms and 0.282 ms, with 38 and 39 favorable pairs; they do not establish a compelling
complete-backend gain.

Randomized membership/iteration/identity and sequential retirement checks pass.
The latter found that Python retirement relies on ancestry's index-building
side effect. The adapter now rebuilds indexes before entering Python retirement
fallback. Unsupported selector containers and non-set seeds also fall back.

A follow-up trace found that the default fixture's ancestry request comes from
an empty retirement interval. Test skipping that request before extending the
native query further. An empty-window guard has not yet been measured here.

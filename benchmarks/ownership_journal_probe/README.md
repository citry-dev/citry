# Combined ownership journal experiment

This standalone experiment tests whether combining component-invocation and
render-queue storage makes complete Citry renders faster. It does not replace
the shipped native extension or activate during ordinary rendering.

The Rust journal keeps one invocation's metadata and queue lifecycle together.
Binding updates its target and queue in one call. With `--bulk-retirement`, the
existing Python closure calculation passes the selected row indexes to one
native update. Immutable NamedTuple records are constructed on demand and
cached until their fields change. Snapshots therefore keep their previous
values after later updates.

## Run the experiment

From the repository root, with the benchmark environment installed:

```bash
cargo build --release \
  --manifest-path benchmarks/ownership_journal_probe/Cargo.toml
.venv/bin/python benchmarks/ownership_journal_probe/probe.py \
  --bulk-retirement --tests
.venv/bin/python benchmarks/ownership_journal_probe/probe.py \
  --bulk-retirement --pairs 40
```

The loader supports macOS and Linux. This run used macOS, Python 3.14.3 and a
release PyO3 build with `abi3-py310`. The original `citry_core` release artifact
stays loaded. The experiment has a separate pinned Cargo workspace and does
not add a dependency to the production workspace.

The harness warms the existing large scenario, compares every ownership
snapshot reached by one reference/candidate render outside timing, then checks
HTML equality in every timed pair with render IDs reset. Pair order alternates.
Snapshot materialization required by actual rendering remains inside timing.
The `--tests` mode checks retained immutable records and failed-queue ordering,
then runs the existing ownership, manifest and cache-replay suites.

## Scope and limitations

This is a hybrid backend, not a complete numeric ownership arena. Invocation
metadata still holds Python references. Source locations, instances, fills,
and regions remain in Python. Relation indexes and closure calculations remain
in Python in the original and bulk-retirement modes. The additional native
retirement mode is described below. Replayed
snapshots materialize the invocation/queue tables and use the original Python
implementation from that point onward, including rollback. The default large
scenario does not enable artifact replay, so its timing cannot measure native
replay performance.

Only normal capture and the exercised updates share target identity between the
two record views. Arbitrary direct writes of inconsistent invocation/queue
records are outside the experiment's contract. Queue orders retain their Python
integer objects, including values beyond u64. The numeric retirement calculation
uses unsigned 64-bit IDs/orders; values outside that range request Python
fallback before mutation. Invalid row indexes or record lengths raise. Failed
mutations are not generally atomic: an unexpected retirement error may leave
earlier state updates applied.
Production use would require complete validation, replay support and a portable
core that separates Python references from the ownership relations.

## Observations and decision

The initial capture/bind/settle version was neutral: 33.410 ms reference versus
33.475 ms candidate. Adding batched retirement measured 33.088 versus 32.915 ms.
Matching the reference's explicit capture signature and adding snapshot checks
produced 33.491 versus 32.497 ms in one run, but its median paired saving was
0.393 ms. A confirmation measured 32.765 versus 32.513 ms. All four reached
snapshots match in the final two runs, as does every timed pair's HTML. The
ownership/manifest/cache-replay suite passes 128 tests.

The hybrid implementation stays experimental. These results do not establish a
large whole-render gain. They also do not disprove a complete native graph:
Python readers still require immutable rows and Python/native crossings here.
The native retirement experiment below moves those closure operations into
the backend while retaining Python storage for the other record families. All observations are preserved in
`../results/performance-render/combined-journal*.json`; the research log records the
revision context and next decision.

## Native relationship calculation

The `--native-retirement` mode additionally moves component-output retirement
selection into the portable numeric calculation in `../../crates/citry_ownership/src/lib.rs`. The PyO3
adapter in `src/retirement.rs` reads invocation fields directly from the native
journal and converts the other current tables when retirement is requested.
Conversion, native selection and Python application of the returned changes
are all included in the render timer.

```bash
.venv/bin/python benchmarks/ownership_journal_probe/check_retirement.py --seeds 10000
.venv/bin/python benchmarks/ownership_journal_probe/probe.py --native-retirement --tests
.venv/bin/python benchmarks/ownership_journal_probe/probe.py \
  --native-retirement --pairs 60 --output /tmp/native-retirement.json
.venv/bin/python benchmarks/ownership_journal_probe/probe.py \
  --native-retirement --reference-bulk --pairs 60 --output /tmp/native-vs-bulk.json
```

`--reference-bulk` isolates the new retirement calculation by comparing against
the earlier combined journal and batched update. Without it, the reference is
the production Python implementation. Final reports include source/artifact
hashes, the revision, snapshot equality, per-pair HTML equality, and counts of
successful native retirement and unsupported-input fallbacks. `fallback_calls`
counts only the latter; retirement using Python tables after replay is outside
that counter. The default large scenario has no replay.

The calculation includes historical relationships and preserves Python's
integer-set queue settlement order. It promotes older fills used by later
captured regions, choosing receivers after instance retirement. String-valued
relationship IDs require exact `str`; numeric relationship IDs and order values
require exact `int`. Subclasses and strings that cannot be converted to UTF-8
fall back before native mutation. The differential harness checks 16 such
custom-value cases, including a region ID with custom hashing.

Instances, fills and regions still live in Python. Their changes are grouped by
table, with ordinary immutable record state compared against the reference;
custom record mutation callbacks are not qualified. Duplicate invocation, fill
or region IDs are rejected. The experiment assumes consistent table/index
relationships; it does not validate every arbitrary malformed graph. Replay,
numeric fallback and non-atomic failed updates follow the scope described above.

The final production-reference run measured 32.398 ms versus 31.975 ms, with a
0.348 ms median paired saving. Against the earlier bulk journal, medians were
32.085 ms versus 32.179 ms; the median paired saving was only 0.053 ms. Both
runs used 60 alternating pairs and exercised native retirement 61 times with
zero unsupported-input fallbacks. All four untimed snapshots and every HTML
pair matched. These results do not justify adopting the additional native
retirement layer. The total candidate gain includes the earlier combined journal; the
incremental retirement result is small and noisy.

The corrected implementation passes 134 ownership/manifest/cache-replay tests
and 90,000 sequential retirement comparisons: 10,000 synthetic relationship
graphs, three retirements each, repeated under Python hash seeds 0, 1 and 42.
The synthetic graphs exercise historical states, later regions, selectors,
sparse invocation IDs and unknown explicitly preserved regions. They are
relationship fixtures, not complete validated renderer lifecycles. Cargo
formatting, Clippy and the experiment's Ruff checks pass. Production validation
remains the sixth-iteration result recorded in the research log.

## Native instance, edge, fill and region storage

`storage_probe.py` additionally stores four record families in `RecordTable`.
Capture passes field tuples directly. Selected binding updates patch fields;
public NamedTuple rows are exported and cached when Python readers request them.
Native component-output retirement applies state and receiver changes directly
to those tables, returning the receiver-map edits still needed by Python.
Numeric relationships are still derived at retirement. This is not a complete
persistent numeric graph: source records, receiver maps, capture orchestration
and other readers remain in Python.

```bash
.venv/bin/python benchmarks/ownership_journal_probe/check_storage.py
.venv/bin/python benchmarks/ownership_journal_probe/check_retirement.py --storage --seeds 1000
.venv/bin/python benchmarks/ownership_journal_probe/storage_probe.py --tests
.venv/bin/python benchmarks/ownership_journal_probe/storage_probe.py \
  --pairs 60 --output /tmp/storage-production.json
.venv/bin/python benchmarks/ownership_journal_probe/storage_probe.py \
  --compare-native --pairs 60 --output /tmp/storage-incremental.json
.venv/bin/python benchmarks/ownership_journal_probe/storage_readers.py \
  --output /tmp/storage-readers.json
```

`--compare-native` uses the earlier native retirement algorithm with Python
record tables, loaded from the same rebuilt module. It includes the Journal
cycle-collection correction described below; it does not load the historical
binary. Retirement counters include candidate warmups, the snapshot comparison
and timed renders: 67 native calls for 60 pairs on the default fixture.
The reader diagnostic is untimed and reports the nearest Python caller of the
public record factory, not intervening native operations.

Replay converts all native tables to Python lists. A callback can trigger this
conversion while `capture_slot_call()` is still executing, so the adapter
checks storage again before each transformed mutation. Both successful and
raising callback cases retain the reference behavior. Unsupported custom slot
names fall back before retirement mutation: their hash callbacks could observe
intermediate receiver-map updates, whose grouping differs in the native path.
This guard also applies to the older native-retirement mode.

The new tables and existing Journal implement Python GC traversal and clearing.
Review found that user field values can point back to the native owner, creating
a cycle that reference counting alone cannot reclaim. The focused checks cover
both raw fields and exported record caches. Native traversal visits references
without calling Python, following the [PyO3 GC contract](https://docs.rs/crate/pyo3/0.27.1/source/guide/src/migration.md).

The prototype qualifies normal runtime nonnegative integer indexing, ordered
lookup and immutable snapshot export. It does not provide every list operation.
Its iterator exports a snapshot list, so arbitrary mutation during iteration
of private containers is not equivalent to live Python-list iteration.
Custom record factories/helpers, destructor reentrancy, malformed graphs and
arbitrary mutation of private tables remain outside the experiment's contract.
Numeric retirement falls back for values outside u64; stored queue orders
retain Python integers. Failed mutations are not generally atomic. Production
migration still requires the broader compatibility audit and a portable core.

## Optional native ancestry lookup

`--native-ancestors` moves `_with_ownership_ancestors()` beside stored rows,
avoiding public record exports solely to construct Python relation indexes.
`--compare-storage` compares against the stored-row backend without this query.
The helper preserves historical relations, LIFO traversal, Python set insertion
order and the original string objects. It still builds temporary parent maps.

```bash
.venv/bin/python benchmarks/ownership_journal_probe/check_ancestry.py --seeds 1000
.venv/bin/python benchmarks/ownership_journal_probe/check_retirement.py \
  --storage --native-ancestors --seeds 1000
.venv/bin/python benchmarks/ownership_journal_probe/storage_probe.py --native-ancestors --tests
.venv/bin/python benchmarks/ownership_journal_probe/storage_probe.py \
  --native-ancestors --compare-storage --pairs 60 --output /tmp/ancestry-incremental.json
.venv/bin/python benchmarks/ownership_journal_probe/storage_probe.py \
  --native-ancestors --pairs 60 --output /tmp/ancestry-production.json
.venv/bin/python benchmarks/ownership_journal_probe/storage_readers.py \
  --native-ancestors --output /tmp/ancestry-readers.json
```

The query requires unique invocation IDs, a consistent invocation index and
qualified string/integer relation keys. Selector containers must be exact
tuples and seeds exact sets. Other inputs fall back to Python. A native query
does not mark Python indexes current; before falling back from native retirement
to Python retirement, the adapter explicitly rebuilds them. The benchmark
requires positive native ancestry calls and no ancestry fallback on the default
fixture; requested mode alone is not considered proof of activation.

Two comparisons show median paired savings of 0.699 and 0.469 ms over the
stored-row backend, with 52/60
and 55/60 favorable pairs. The complete backend shows median paired savings
of 0.401 and 0.282 ms versus
production, with only 38/60 and 39/60 favorable pairs. These measurements do not
justify production adoption. The reader diagnostic drops from 2,916 to 2,143
exports. See the research log's thirteenth iteration for raw reports and the
subsequent finding that the default fixture requests this ancestry during an
empty retirement interval.

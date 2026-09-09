# Native ownership retirement experiment

This records the initial experiment design. The current queue-order
representation and numeric fallback are documented in
[`../native_ownership_qualification/queue_orders.md`](../native_ownership_qualification/queue_orders.md).

Repeated renders still take about three times the Django scenario's warm time.
The combined invocation/queue journal saved little while Python kept reading
its immutable records to follow ownership relationships. This experiment moves
the complete component-output retirement calculation beside those native rows.
It remains standalone until correctness and whole-render measurements justify
adoption.

## Prior art

- `packages/py/citry/citry/ownership.py:1775` closes selected component IDs over
  logical and initialization ancestry. `retire_component_output()` at line 1815
  follows component calls and physical regions, retires their records, and
  preserves or rebinds fills used by later output. Those functions are the
  executable reference.
- The record definitions at lines 271, 344, 369, 388 and 463 expose immutable
  snapshots. Queue settlement order and retained earlier snapshots are part
  of the comparison, not merely the final active component set.
- `src/lib.rs` in this experiment already combines invocation/queue capture,
  binding, settlement and batched retirement. It exports NamedTuple rows on
  demand. The original and bulk-retirement modes run relationship calculations in Python and use
  the Python implementation after cache replay materializes its tables.
- `packages/py/citry/tests/test_ownership.py`, `test_ownership_manifest.py`, and
  `test_ext_cache_replay.py` cover nested selections, saved fills, retirement,
  serialization and replay. The research log's third iteration records the
  earlier neutral or small gains from storage changes alone.

## Chosen design

Keep the native invocation/queue journal. When component output is retired,
read the current instance, initialization-edge, fill and region rows into Rust
relationship indexes. This preparation stays inside the timer and happens only
when retirement is needed. The invocation rows are read directly from native
storage, without materializing their Python NamedTuple views.

The Rust calculation finds the same ancestry, selected regions, discarded
calls and components, and later fill occurrences as the reference. It produces
an explicit change list for the Python-owned tables and applies paired native
invocation/queue updates. Python applies the other immutable record changes grouped by table, preserving
the resulting ordinary-record state and receiver lookup updates. Custom record
mutation callbacks are outside this experiment's qualified input types.

Queue settlement must follow the reference's Python integer-set iteration.
Preserve the initial discarded-component iteration and invocation discovery
sequence, then build and iterate a Python set for the selected invocation IDs.
Do not replace that order with Rust HashSet iteration or a numeric sort.

String-valued relationship IDs qualify only when their type is exactly `str`.
Numeric relationship IDs and order values require exact `int` values. Custom
subclasses can change equality, hashing or comparison, so reject those native
attempts before mutation and use the Python path. Invalid row shapes and out-of-range numeric values raise. Table/index
relationships must be consistent; arbitrary malformed graphs are outside this
experiment's qualified inputs. Native order overflow continues to raise; as in the
initial journal, failed mutations are not promised to be atomic. Replay keeps
the existing materialize-and-use-Python fallback.

## Alternatives and what would falsify the design

A native shadow index updated on every capture would avoid conversion during
retirement, but adds work to renders that never retire output. Measure lazy
preparation first. A complete native record store could also avoid the remaining
Python table updates, but must absorb their readers and replay together; the
paired-journal measurements do not establish that larger design's benefit.

Reject or revise this implementation if retained snapshots change after later
updates; if queue order differs, including sparse invocation ID sets; if saved
fills lose their lexical owner or later receiver; if selection, error handling
or replay differs; or if conversion and result-application costs erase the
whole-render gain. Compare randomized consistent graphs as well as the existing
render suites. Record unsupported cases explicitly rather than counting them
as native coverage.

## Files and validation

Add the relationship calculation and adapter under this standalone benchmark's
`src/`, extend its Journal method and `.pyi` stub, and add an explicit harness
mode. The production parser, AST, compiler output, five language implementations,
shipped PyO3 registration, `_rust.pyi`, and Python wrappers are untouched. A
production migration and other language bindings are deferred until evidence
supports adoption.

Run Cargo formatting and Clippy, focused Python ownership/manifest/replay tests,
exact before/after snapshot comparisons, and alternating complete renders with
HTML equality checks. Retain all observations and update the research log.

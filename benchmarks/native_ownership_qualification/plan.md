# Qualify native ownership before integrating the measured candidate

The current combined candidate passes the complete-render screen against
production (eight joint wins, 1.284 ms median paired mean wall saving). Its
focused ownership/manifest/replay suites pass 134 tests. This audit expands the
behavioral evidence and prepares the packaging design, while retaining that
measured implementation until a change has its own validation.

## Existing contract and implementation

`OwnershipGraph` describes itself as a mutable capture collector with an
immutable snapshot result (`ownership.py:624`). All six mutable table fields
are private to that module in production Python sources. Public snapshot
records preserve their current types and fields. `_capture_replay_mutation`
materializes rows into lists; rollback restores those lists. Snapshot import
also materializes native storage through the experimental adapter. Detached
instance import only appends records and already works with RecordTable.

Read the full capture/binding/replay/retirement methods, journal/table adapters,
all native sources and `performance_ownership{,_storage}.md`. Prior measured
plans are `native_combined_capture_probe/plan.md` and its parent plans. PyO3
registration and package requirements are in both relevant AGENTS files,
`crates/citry_core_py/src/lib.rs`, the shipping stub, root Cargo workspace and
`docs/codebase.md`. The retirement relationship calculation already lives in a
391-line Python-independent Rust module; the prototype builds in a separate
workspace and currently has no production packaging.

## Qualification work

Run all non-browser Citry package tests with the combined candidate installed
in the pytest process. Existing child-interpreter checks retain their normal
bootstrap and are not native-backend qualification. Retain the exact installer/runner/native hashes and result. Recheck supported
replay transaction and callback behavior beyond the fixture. Exercise native
numeric boundaries and constructor/update errors to distinguish a missing
supported behavior from arbitrary mutation of private containers. Record actual
counterexamples before choosing fixes. Run relevant checks after each change;
do not infer full production compatibility from the benchmark or 134-test suite.

Native storage may change private list representation. It must preserve normal
public graph methods, snapshot types/values/order and retained-view lifetimes,
callback-visible state, failed-queue handling, source provenance, slot ownership,
replay rollback and object collection. A deliberate exception for private
container or constructor monkeypatching needs a scoped rationale, not an
assumption that the old Python implementation promised every such mutation.

Packaging must extract portable relationship calculation into the Rust workspace
and keep Python object references/calling conventions in the binding. The final
implementation needs one reviewed written structural plan before adding shipped
PyO3 surfaces, matching stubs/wrappers and a complete cross-binding inventory.
The parser/AST/compiler and five template language implementations are separate
contracts; enumerate their status explicitly. Keep benchmark probes usable with
recorded provenance. Do not activate production code until its implementation,
full gate, browser behavior and complete-render gain have been verified.

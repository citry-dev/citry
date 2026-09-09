# Integrate native ownership into the regular build

The combined prototype reduced mean render time by a median 1.329 ms across
process pairs in the pre-extraction eight-pair comparison. Integration must
preserve that benefit while making the ordinary package build responsible for
its code and Python interfaces.

## Prior art

- At `e8f55c7e`, `benchmarks/ownership_journal_probe/src/graph.rs:80` builds
  relationship indexes, selects preserved ancestry and plans retirement without Python.
  `src/retirement.rs:19` converts Python identifiers into numeric handles and
  applies the plan. The calculation and host-object handling already separate.
- `benchmarks/ownership_journal_probe/check_retirement.py:15` constructs
  seeded graphs for sequential comparisons with Python retirement, including
  retained snapshots and unsupported-value fallback.
- `crates/citry_core_py/src/lib.rs:51` registers the shipping extension.
  Its crate-local AGENTS.md requires matching `_rust.pyi` declarations.
- `Cargo.toml:2` lists workspace crates; `scripts/check.py:39` and
  `.github/workflows/rust--tests.yml:62` discover first-party crates for checks.
  `docs/codebase.md:984` describes the workspace and binding architecture.
- `native_combined_capture_probe/adapter.py` composes experimental Python
  method replacements. These installers are qualification tools. Shipping
  activation will use direct runtime code and hand-owned binding declarations.

## Stages and choices

1. Extract the existing relationship calculation into `crates/citry_ownership`.
   Add it to the root workspace and make the standalone probe depend on this
   one implementation. Keep calculation behavior unchanged. Add focused Rust
   tests for preservation, cutoff and fill promotion, then reuse the seeded
   Python differential checks against the rebuilt probe. Commit this area.
2. Add Python reference storage and retirement conversion to `citry_core_py`,
   consuming the shared crate. Mirror the exposed classes/functions in the
   stub and wrapper. Omit experiment-only methods from the shipping surface.
   Build and test through the ordinary package configuration, then commit.
3. Activate through ordinary ownership runtime methods. Preserve snapshot
   types, field references, queue order, callback visibility and replay.
   Compare complete renders against the current shipping implementation,
   including smaller workloads and second renders. Commit the accepted area.
4. Run the repository gate, Linux-target type checking and browser tests on the
   integrated result. Update the research log and report measured limits.

Copying the calculation into the binding would create two owners for the same
behavior. Moving Python object references into the portable crate would make
other hosts depend on Python. The chosen split keeps calculation portable and
reference lifetime management in the binding.

## Contracts and failures

The first stage adds no Python surface. Parser ASTs, compiler output and the
five language implementations do not change. Python registration, stubs and
wrappers move together in stage two; other host ownership bindings remain
unimplemented. The first-stage crate is internal and unpublished.

For this extraction, populate a fresh Graph, call index once, then query it
without changing its rows. Duplicate invocation, fill or region IDs return an
error; discard a graph after that error. Unknown explicit region IDs are
ignored. Cyclic ancestry terminates through visited sets. Numeric handles and
orders use the existing usize/u64 domain. Python conversion rejects unsupported
values before mutation and invokes the existing Python fallback. Stored Python
queue-order references retain arbitrary-precision integers.

A changed retirement plan, snapshot, queue order or fallback behavior falsifies
the extraction. Shipping activation also fails qualification if it changes
callback/replay behavior, leaks retained references or loses the measured
complete-render benefit. Private arbitrary mutation and allocation-failure
atomicity require separate assessment; existing prototype checks do not prove
them.

## Build, evidence and cost

Update workspace manifests/locks and crate documentation. Existing Rust test
discovery includes the new crate without an extra CI job. The publish workflow
uses the binding dependency closure; stage one does not add a shipping edge.
Update every executable probe's source manifest to include the extracted crate
and its manifests, retaining historical reports as evidence of earlier sources.

Focused Rust tests protect the relationship decisions at their cheapest owning
boundary and should take under a second after compilation. Reuse the existing
seeded differential harness to protect host ordering and conversion. Do not add
it as another mandatory CI/release job. Native builds and focused checks run
before timing; independent review can run alongside source preparation. The
full repository/browser checks run at the integrated stage boundary.

This written plan precedes implementation. ExitPlanMode is unavailable in this
session; the user has already authorized the optimization and refactoring work.

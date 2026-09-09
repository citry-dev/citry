# Add ownership storage to the regular Python extension

The shared `citry_ownership` crate now calculates which records survive output
replacement. This stage adds its Python reference storage and conversion to the
regular extension, so the measured candidate can use the package build.

## Prior art

- `crates/citry_ownership/src/lib.rs:80` indexes a fresh graph and calculates
  preservation and retirement. This remains the one portable calculation.
- `benchmarks/ownership_journal_probe/src/lib.rs:25` stores invocation and
  queue fields together, retaining Python orders and cached immutable exports.
  `src/storage.rs:14` stores the other record families; `begin_slot_region`
  copies selected Python field references into a new region row.
- `benchmarks/ownership_journal_probe/src/retirement.rs:131` validates/converts
  input, calculates a plan and applies it. The accepted combined candidate
  uses four native tables and five state values. Its Python-list table mode,
  optional native ancestry query and grouped fill-binding methods belong to
  separate experiments and are not used by that candidate.
- `crates/citry_core_py/src/lib.rs:51` registers `_rust` submodules.
  `packages/py/citry_core/citry_core/_rust.pyi:24` explains their hand-written
  declarations. The `html_transform` wrapper shows direct native re-exports.
- `packages/py/citry_core/pyproject.toml:63` points maturin at the binding
  manifest and configures uv to track crate sources/manifests for rebuilds. The publishing
  workflow builds that dependency closure through the same configuration.

## Chosen boundary

Add `ownership/{mod,storage,retirement}.rs` in the binding crate and register
`_rust.ownership`. Expose `Journal`, `RecordTable` and
`UnsupportedRetirement` through a private `citry_core._ownership` wrapper.
Declare the complete surface in `_rust.pyi` in the same change. Record payloads
are dynamically shaped Python tuples; their owners supply the record factories.
The binding must not import the higher-level `citry` package.

Keep the accepted journal capture/bind/settle/export/setter operations,
`retire_many`, table append/patch/export and `begin_slot_region`. Native
`retire_output` accepts only the four native tables and five state values used
by the candidate, returning the new order, receiver-map updates and a region
promotion flag. Unsupported Python values raise before mutation so the caller
can use Python retirement. Replay will materialize tables in the runtime stage.
Do not ship unused ancestry or grouped fill-binding methods.

The standalone benchmark binding remains as a comparison implementation during
integration. Its portable calculation already shares the new crate. Shipping
runtime code will use the packaged binding directly; the experimental method
installers remain outside the runtime. Archive or consolidate those installers
after activation has a retained baseline and equivalent benchmark coverage.

Copying portable relationships into Python glue would create a second owner.
Loading the standalone artifact from runtime Python would create a second build
and distribution path. Use the regular binding and its existing release profiles.

## Errors and limits

Wrong table/tuple widths raise ValueError. Representable row indexes outside
the stored range raise IndexError; indexes outside the native integer range
raise OverflowError. Journal indexes use unsigned integers and RecordTable
indexes use signed integers. Wrong native table types raise TypeError. Custom numeric/string values and
out-of-range numeric relationships request UnsupportedRetirement before changes.
Stored queue orders remain Python references, including arbitrary-precision
integers. Export errors propagate; a failed export can be retried after fixing
its constructor. Retained exports remain immutable and GC visits raw references
and cached views. Reentrant access during a native mutable borrow is rejected
by PyO3. This internal interface does not promise arbitrary custom record
factories, inconsistent private row writes, transactional allocation failure or
user-defined arithmetic during mutation.

No parser, AST, compiler output or five-language template contract changes.
Python registration, stub, wrapper, binding tests and crate/package pointers
move together. Other host ownership bindings remain unimplemented. Adding the
binding alone does not change ordinary Citry rendering or justify a user-facing
performance release note.

## Verification and falsifiers

Build through maturin with the normal local release configuration, then check
the publishing workflow's `release-wheel` profile with `abi3-py310` enabled.
Record the imported extension path and hash for each build. Run focused
package tests for reference identity, retained views, errors and GC cycles.
These tests protect host lifetime/conversion behavior that pure Rust tests cannot
prove, use synthetic record factories and should take under a second. Reuse the
existing seeded retirement and slot/replay checks with the packaged module, and
run the non-browser Citry selection with that module installed in pytest. Child
interpreters still use ordinary runtime activation at this stage.

Use the existing eight-pair production-reference timing method, recording the
normal extension artifact and all binding/shared-crate sources. Both workers
load the same rebuilt extension. No CPU-heavy checks overlap timing. A changed
snapshot, field identity, queue order, fallback or callback result rejects the
binding. Loss of the complete-render benefit requires investigation before
runtime activation. Repository/browser gates follow the integrated runtime
stage, without adding a new CI or release job for these experiments.

This elaborates stage two of `integration.md` before PyO3 edits. The user has
authorized the work; ExitPlanMode is unavailable in this session.

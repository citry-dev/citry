# Activate packaged ownership storage

The packaged candidate passed complete-render comparisons in both local CPython
and ABI3 builds. This stage puts those operations in ordinary runtime methods.

## Prior art

- `packages/py/citry/citry/ownership.py:627` creates the per-render collector.
  `record_component_invocation`, `bind_instance`, `_append_fill` and
  `capture_slot_call` own record creation and callback ordering.
- `ownership.py:741` captures replay rollback state as Python lists;
  `import_replayed_snapshot` appends remapped records. Slot callbacks can call
  replay, so storage must be checked again after the callback.
- `benchmarks/ownership_journal_probe/storage_probe.py:172` and the combined
  slot/export adapters establish the measured native operations and fallbacks.
- `crates/citry_core_py/src/ownership/` and the matching `_rust.pyi` expose
  native storage. The binding/shared calculation do not change in this stage.
- `packages/py/citry/pyproject.toml:41` pins citry-core to the paired release.
  The currently published dependency need not expose the new internal module.

## Design and alternatives

Create native tables and a shared invocation/queue journal when `_rust` exposes
ownership storage. Otherwise create the existing Python lists. Use a small typed
journal reader for indexed access, iteration and assignment. Store ordinary
record fields directly on hot capture paths and export existing record types
on demand. Retain list branches in the same methods and the existing Python
retirement algorithm. No runtime AST compilation or method replacement is used.

Snapshot import materializes all six tables before replay; rollback restores
lists. Check current tables at callback-adjacent writes. Native retirement
handles supported values; UnsupportedRetirement falls through to the Python
algorithm without discarding state. The absent-capability case uses Python
throughout, allowing the current paired package pin to remain valid. Raising
that pin belongs to the next coordinated package release.

A subclass containing duplicate native/Python implementations would make
callback and fallback behavior harder to keep aligned. A new generic Python
append wrapper would add a Python call to every captured row. Prefer explicit
branches at the existing capture and mutation sites.

## Failures and validation

Keep source errors, failed queues, retired-fill revival, physical wrappers,
retained snapshots and numeric fallback behavior. Preserve Python exceptions
from callbacks, including replay that materializes tables before raising.
Inconsistent private container rewrites remain outside the supported contract;
public capture/replay and snapshot readers are the qualification boundary.

Archive the pre-activation OwnershipGraph source for a benchmark-only Python
reference using the same record types and context variables. Compare fresh
processes, exact snapshots and HTML; include second renders and smaller cases.
Keep all samples with normal GC. Lost complete-render benefit or changed
outputs/fallbacks rejects activation. Add focused runtime tests proving default
native activation, absent-capability fallback and callback/replay transitions.
Then run the repository and browser gates and Linux-target typing. Existing
tests/build outputs cover contracts already owned by the binding; no new
mandatory release job is introduced.

Parser ASTs, compiler output and all five language implementations are unchanged.
There are no new PyO3 surfaces. The runtime, tests, benchmark reference/runners,
research log and appropriate performance release note move together. Other host
ownership bindings and the full release platform matrix remain separate work.

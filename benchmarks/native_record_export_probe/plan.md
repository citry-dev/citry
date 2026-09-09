# Export stored fields through the tuple constructor

## Prior art

`benchmarks/ownership_journal_probe/src/storage.rs::export` builds a tuple of
stored fields, then calls the Python record class with those fields unpacked.
`src/lib.rs::invocation` and `queue` do the same for the combined journal.
All six production factories are NamedTuple classes defined in `ownership.py`.
The local interpreter's `collections.namedtuple` source generates a Python
`__new__` function that repacks its arguments into another tuple and calls
`tuple.__new__`. Its `_make` method also calls `tuple.__new__`, then checks width.
Native table append/assignment already validates width; journal capture and
queue export supply their complete field layouts.

The combined native backend passes a fresh-process screen, but smaller grouped
binding and slot-preparation candidates do not. This experiment keeps those
operations disabled and targets conversion across all six native record types.
Existing retained-row/GC and callback replay checks provide the lifetime contract.

## Design and alternatives

Add an optional tuple-constructor callable to RecordTable and Journal, configured
through an opt-in setter. Ordinary exports keep calling the record factory.
Configured exports call `tuple.__new__(record_class, fields)` directly, using the
already assembled field tuple. Preserve the exact class, field references and
existing immutable export cache. Visit and clear the callable through native GC.
Python configures the four tables and their shared journal when a graph is built.

This deliberately bypasses each NamedTuple class's generated `__new__`. Custom
class constructors, helper-global edits and mutations to constructor definitions
remain unqualified. Do not present this as a generic factory optimization.
The installer supplies the known six production classes; diagnostic wrappers
count direct-constructor calls outside timing. The setter does not invalidate
already cached immutable views and affects subsequent uncached exports only.

Calling `_make` would retain a Python frame and repeat width validation. Direct
CPython memory allocation would require a substantially larger ABI and lifetime
audit. The proposed builtin constructor uses the existing stable Python calling
mechanism and adds no unsafe allocation code.

## Failure modes, verification and scope

A constructor exception propagates before the new immutable cache is stored.
A supplied non-callable fails on export; the experimental setter stores the
value without validating it. Existing cached rows remain readable. Arbitrary
constructor callbacks can return the wrong type or reenter borrowed native
storage; these are not a supported production interface. GC must see references
through constructor closures, including before any immutable export exists.

Compare all six classes, field identity, retained views across patches,
constructor-error/cache behavior and native cycles. Run the existing ownership,
manifest and replay suites with the candidate installed. Compare every reached
fixture snapshot and HTML, and count each family's direct exports outside timing.
Then compare against the existing native backend with the same rebuilt artifact:
eight balanced randomized fresh-process pairs, six warmups, 80 complete renders,
normal GC and all samples retained. Require seven joint wall/CPU wins and at
least 0.25 ms median paired mean wall saving. No builds or CPU-heavy checks
may overlap timing. Constructor microbenchmarks would not establish adoption.

Only the standalone benchmark module, its local stub and opt-in adapter change.
Shipping registration, Python wrapper/stub, parser/AST/compiler and all five
language implementations need no changes. Portable ownership API and production
integration remain deferred. This written plan precedes editing;
ExitPlanMode is unavailable in this session.

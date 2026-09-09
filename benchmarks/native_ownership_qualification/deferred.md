# Allocate native ownership storage when nested capture begins

The accepted native runtime has 1.534 ms median paired process-mean saving in
the large fixture and -6.525 microseconds in the tiny fixture. The tiny fixture has no
nested component invocations: it creates one logical instance, two fills and
one region. Test whether starting with Python lists and converting on the first
nested invocation avoids that cost while retaining the large-fixture gain.

## Prior art and design

`ownership.py` currently allocates a journal, two journal readers and four
record tables in `OwnershipGraph.__init__`. `record_component_invocation`
maintains a monotonic invocation counter. Snapshot imports remap invocation IDs
and materialize storage; rollback restores counters and lists. The previous
iteration's callback tests cover transitions while properties and slots run.

Start every graph with the existing Python lists. Before recording its first
nested invocation, allocate native storage when the core supports it. Copy the
existing instance, ancestry, fill and region rows through `RecordTable.append`,
which preserves their immutable record identities. Decline conversion if either invocation or queue rows already exist. Check
eligibility after source preparation, immediately before consuming the next
invocation ID. Keep counters and indexes unchanged. Construct all
replacement containers before assigning them, so an allocation failure does
not leave half the tables converted.

Use the invocation counter as the boundary, without an additional state flag.
Replayed invocation rows advance that counter and therefore stay on Python
storage. Replay with no invocation rows may still convert when its first call
executes. Rollback may restore the counter to zero; conversion after rollback
must work with the restored rows. Custom ID bindings still materialize the
paired tables as before. Python-only graphs keep recording all ownership.

Keeping only the journal lazy would still allocate four tables for the tiny
fixture. Delaying by a chosen number of rows introduces an arbitrary threshold
and requires copying invocation/queue state too. Try the first nested call
before either alternative.

## Qualification

Compare against the committed eager runtime at `9cc3264`, using both fixtures
and complete snapshots/HTML. Retain all process pairs and GC costs. The purpose
is to remove the tiny regression while keeping the previously measured large
benefit; the large-target 0.25 ms adoption screen is not a requirement for this
small-fixture correction. Require positive median paired wall and CPU savings and at least seven of
eight joint wins on the tiny fixture. Reject median paired wall or CPU
regression exceeding 0.10 ms on the large fixture (about 0.3% of its current
time). Report any smaller observed regression explicitly. This margin is fixed
before timing; it is not a claim that a smaller regression is zero.
Check retained record identities and region state when conversion occurs inside
a slot callback, replay before first invocation, and rollback before conversion.
Adapt existing native qualification setup to enter the new activation boundary,
without silently running two Python variants. Run ordinary ownership contracts,
Linux typing and the final repository/browser checks before accepting and
committing the area. Other bindings and Python-visible native APIs do not change.

# Keep immutable source fields through internal manifest reads

## Prior art and purpose

Iteration 45 delayed source-record creation but exported all 1,077 deferred
records through `OwnershipGraph.snapshot`; four prefix records were already
constructed. It improved process means by a median 0.416 ms but missed the
seven-pair consistency condition. `ownership_manifest.py` captures complete
snapshots at preparation and compares them twice after delayed work. Its
production manifest omits provenance, but still validates referenced source
IDs. Events emission reads only logical instances from another full snapshot.
The source storage and these readers must change together to avoid exports.

Keep source rows as immutable eight-field Python tuples in an isolated native
collector. A private immutable view holds a tuple of those tuples. Internal
manifest reads use that view, check source IDs directly and compare complete
field values for mutation detection. Development provenance and public graph
snapshots materialize the existing public record class. Other graph tables and
all ownership relations, capture IDs, retirement and rendering remain current.
This is a prototype of a broader data flow, not a production migration.

## Design and alternatives

The native source table retains each input field tuple as one Python object,
with an optional cached public record. Prefix append preserves the exact record.
A raw snapshot caches an immutable tuple of field tuples and is invalidated on
append or replacement. Public iteration exports records; the internal view
compares its raw tuple to another internal view, and materializes when compared
to an ordinary public tuple. Every retained object participates in Python GC.
All fields remain Python values; this does not pack strings into bytes or
introduce integer narrowing.

The capture adapter first retains the live append method and record class, then
evaluates arguments in current order. Only afterward does it check the captured
class's `__new__` and `__init__`, so a constructor changed while evaluating order
is observed. Unsupported construction uses the captured constructor with the
original keyword names. Internal reads fall back to the public snapshot when
storage is ordinary Python or the public snapshot method is overridden.

A shared snapshot cached only by the capture-order counter is unsafe because
retirement can change rows without advancing that counter. A graph-wide version
requires auditing every mutation. Comparing complete immutable source values
avoids that new assumption. Adding an independent source-ID set alongside eager
records would retain their creation cost and add another structure to update.

The manifest changes validate the same referenced-ID set in all modes and
materialize source rows while selecting development provenance. Production retains
all source values in its private capture for unchanged-graph checks. Source
changes after capture must still fail closed. The private GraphCapture source
sequence has a different concrete type; direct inspection, equality against
public snapshots, source-ID hash/equality callbacks, record.id overrides,
subclass hooks and arbitrary private mutation need explicit
qualification before adoption.

## Scope and falsifiers

The new PyO3 class is confined to this standalone benchmark crate. It uses
pinned existing PyO3 0.27.1 with abi3-py310 and a separate artifact. There is no
change to the shipped registration, stub, wrapper, parser, compiler, AST or
five LangImpl implementations. A production migration would need the normal
binding, typing and distribution audit; this experiment does not authorize
skipping it.

Check prefix/export identity, immutable captures across append/replacement,
public/raw equality, GC cycles, rollback, constructor changes during argument
evaluation, dangling IDs and post-capture source mutation. Compare full HTML
and every reached complete snapshot, including development output. Count actual
public source exports in an independent diagnostic. Preserve unsupported-case
failures and any semantic differences; passing fixture tests alone is not
production qualification.

If fixture behavior holds, use eight balanced randomized fresh-process pairs,
six initial and 80 measured warm renders, ordinary GC and every observation.
Require seven joint wall/CPU wins and at least 0.25 ms median paired reduction
in process mean wall time before broader qualification. Keep actual second
renders separate. Include source and artifact hashes. Do not retry a failed
screen to seek acceptance. Failure to eliminate exports, a small/inconsistent
whole-render result or required compatibility costs can reject the design.


The counterexample checker demonstrates two production incompatibilities:
internal and public source sequences can materialize equal but distinct record
objects, and direct source-ID reads bypass a changed public record.id descriptor.
A minimal page then succeeds where the reference reports a dangling source ID.
The prototype must not ship with those differences. Custom snapshot descriptor
or __getattribute__ callback counts are also unqualified because override
inspection can read graph.snapshot twice. The performance screen measures
potential benefit before strengthening these contracts; a timing pass alone
cannot justify adoption.

On this fixture, the candidate's internal manifest path in production mode
avoids deferred public source exports, but still allocates one plain field tuple
per deferred occurrence. Fewer public records is not proof of fewer row
allocations or lower retained memory.

# Measure repeated generation of provided payload classes

`Component.provide(key, **data)` calls `make_provided`, which generates a new
`NamedTuple` class and then constructs one payload. The large fixture creates
seven classes per render for two field layouts. A preliminary post-render
collection found 265 unreachable objects, all associated with these classes;
there were no render, component or ownership objects among them.

The source survey covered `citry/provide.py`, its imported factory alias in
`citry/component.py`, `tests/test_provide.py`, the keyword-field contract in
`docs/design/component_provide.md` section 5.1 and the earlier cycle removal
in `docs/design/performance.md` section 10.8. The local Python 3.14 standard
library shows that each `NamedTuple` call generates methods, descriptors,
annotations and a new type. The existing tests require immutable instances;
the generated classes themselves remain mutable and observable.

First measure a bounded class cache keyed by ordered field names. Only exact
dicts with at most 16 exact string keys, each at most 128 characters, qualify.
The cache retains at most 128 classes rather than payload instances. It builds each
class through the original factory using `None` values. Other mappings use
the original path. Invalid field names still reach the original factory on
a miss. A separate diagnostic will count unreachable objects after one render
with automatic GC disabled, then restore GC. That diagnostic is not timing.

This candidate deliberately shares mutable class objects across calls. Class
identity, class attribute changes, descriptor/function mutation, annotations,
constructor replacements, concurrent mutation and callback behavior are not
qualified. A caller can attach arbitrary application objects to a cached class,
so the entry count does not bound retained bytes under mutation. Record concrete
identity and mutation counterexamples. Do not
adopt the experiment as production behavior. A design retaining fresh classes
while reusing preparation would require its own performance and correctness
evidence; this experiment is not an upper bound for it.

Use eight balanced randomized fresh-process pairs with six warmups and 80
complete samples per worker, retaining all GC costs and matching HTML digests,
native hashes and every ownership snapshot reached in the untimed comparison.
Require seven joint wall/CPU wins and 0.25 ms median process-pair mean wall
saving before investing in a compatible design. Budget this screening run to
less than five minutes. Untimed activation must show class-cache hits.

## Follow up while preserving fresh classes

The shared-class candidate passes the screen with eight joint wins and a
0.380 ms median saving. Now isolate the parsing and compilation inside the
standard library's generated constructor. `compile_probe.py` makes private
copies of the current Python factory functions with copied globals; only
their constructor `eval` uses a bounded compiled-code cache. Each call still
creates a fresh function, its namespace, descriptors, annotations and class.
No standard-library module is patched. Cached code is immutable and contains
field names rather than application values. Limit retention to 128 code
objects with source strings of at most 4,096 characters.

Repeat the same process-pair screen once for this different candidate. Check
fresh type identity and class-edit isolation separately. This experiment
depends on private Python factory structure and is not a production design;
different interpreters, replaced factories, custom mapping callbacks, code
object identity, tracing and audit-hook behavior remain unqualified. It will decide
whether avoiding constructor compilation alone warrants further work.

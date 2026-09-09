# Package compact attribute-output cache keys

## Prior art and selected design

The preceding prototype passes the warmed screen at 0.392 ms median paired
mean wall saving and eight joint wins. Actual second renders do not establish
an improvement. `ElementAttrsNode._format` owns the existing output cache;
`citry/attrs.py` owns its formatting eligibility helpers. The original method
is archived beside this plan, with its starting line recorded separately.
`tests/test_attrs_output_cache.py` is the existing behavioral contract.

Add the key builder to the regular extension as `_rust.attrs.output_cache_key`
and expose it through a private `citry_core._attrs` wrapper. Bind the runtime
helper through capability detection on `_rust` so an older core still imports.
Use the same flat key in the Python fallback; every cache entry then has one
private shape. Keep the old bounds and exact-type rules in both implementations.
The formatter's outer guards remain and its miss path formats the tuple's
snapshot. Add ordinary typed source rather than compiling Python at runtime.

Keep one source helper for Python fallback and tests. The native helper accepts
an object, returns a flat tuple on admission and None otherwise. It never calls
application value protocols. Exact integers use their builtin bit_length;
exact strings use Python character counts without UTF-8 conversion. Unsupported
objects remain on the established formatter path. No settings or user API is
added. The private cache format changes; adapt the concurrency test's private
key offset while retaining the same barrier and bound assertions.

The alternative of retaining nested keys on older cores would require two miss
snapshot formats and a tag identifying them. The single shape is easier to
verify. Its performance on older cores must be measured and reported rather
than assumed equal to the old inline loop.

## Contract and downstream inventory

- `crates/citry_core_py/src/attrs.rs`: Python-object key builder.
- `crates/citry_core_py/src/lib.rs`: attrs module registration.
- `citry_core/_rust.pyi` and private `_attrs.py`: matching typed declarations.
- `citry/attrs.py` and `citry/nodes/__init__.py`: capability selection, Python
  fallback and one flat-key miss path.
- Core tests: exact bounds, Unicode/surrogates, signed integers, unsupported
  custom behavior and retained references.
- Runtime tests: both builders, cache helper overrides, input changes at lookup,
  cache bounds under concurrent misses and fresh-process capability fallback.
- Agent package/crate pointers: identify the new binding/wrapper.
- Release notes: describe the observed performance result at the owning package.
- Parser, AST, compiler and all five LangImpl implementations: unchanged. This
  key contains Python objects and type identities; it is binding-specific and
  does not define a portable template format. No Rust-core algorithm is duplicated.

## Qualification and falsifiers

Run relevant core/runtime tests, then full repository and browser gates and
Linux-target mypy. Rebuild the regular ABI3 release-wheel artifact. In fresh
processes compare ordinary production against the archived original formatter
with the same current extension and original helper behavior. Keep the same
8-pair, 6-initial, 80-warm protocol and seven-joint-win/0.25 ms warmed screen.
Report actual second renders separately. Check the tiny fixture: require no
median paired mean regression greater than 0.005 ms on either clock. Measure
the Python fallback against the archived original and disclose its cost; require
no median paired mean regression greater than 0.10 ms on either clock for the
large fixture. These margins are declared before qualification timing.

Source and artifact changes after measurements require new provenance and,
where they affect the measured implementation, new timing. Older-core tests
must establish both import and actual fallback execution. A native admission
count is not a cache-hit count. Full fixture output, all reached snapshots and
mutated-input cache snapshots must match. Any unsupported value executing a
protocol during admission, changed escaping/normalization, stale cached values,
bound violation or unresolved crash rejects the candidate until fixed.

Runtime replacement of private builtins and observation of private cache key
layout are outside the supported API. Public value protocols and extension
callbacks remain live. The native helper does not release the GIL; arbitrary
free-threaded Python qualification is not established by the local ABI3 run.

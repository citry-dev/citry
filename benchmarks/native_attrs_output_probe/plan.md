# Build a compact attribute-output cache key in one native call

## Prior art

`ElementAttrsNode._format` in `citry/nodes/__init__.py:1095` validates primitive
maps and constructs one `(key, type, value)` tuple per attribute, then an outer
tuple for the shared final-output cache. Even hits repeat that loop. Misses
format an immutable snapshot reconstructed from the cache key so concurrent
changes to the input dict cannot cache output under stale values.
`tests/test_attrs_output_cache.py` covers bounds, mutation, helper changes,
concurrency and value protocols. The preceding native contribution merger
missed the whole-render adoption screen; it left this later key construction
and its intermediate tuples in Python. No flat-key native experiment was
found in the research journal.

## Design

Keep the existing outer cache eligibility and formatting-helper guards. Replace
only the inner key-building loop with one native call returning a single tuple:
`(name, type, value, name, type, value, ...)`. This removes per-attribute tuples
and runs primitive classification and bounds checking in Rust. Preserve exact
string keys, exact str/int/bool/None values, the 16-entry bound, 2,048 total
characters and 256-bit integer limit. Type positions distinguish bool and int.
Unsupported input returns None and follows the existing uncached formatter.
Strings remain Python objects, including lone surrogates; no UTF-8 encoding is
required for key construction. Keep the same object references in the tuple.

Cache hits return the existing cached string. Misses reconstruct the dict from
triples at successive offsets and continue the original formatter, helper
recheck, insertion lock and eviction. No attribute expressions, merges, hooks
or validation steps are skipped. The cache key is private; public render output
and the cached string representation do not change. Each comparison starts
with an empty cache and the same warmup count. Both variants load the extension.

The prototype rewrites only this block in a copy of the original method's AST
using live module globals. Production would use ordinary typed source and the
regular extension with an older-core fallback. Replaced type/len builtins,
concurrent custom mutation, private cache inspection and allocation/finalizer
ordering require production qualification; fixture behavior does not prove
them. No claim is made for public mutation of a private cache key format.

A Python flat list would need three appends per attribute or a temporary tuple
for extend, so it does not eliminate the classification loop. A native formatter
would duplicate the already effective output cache. Test native key construction
and the simpler key representation together as one area.

## Acceptance and checks

Compare generated keys against a Python model for ordered maps, type-sensitive
values, Unicode, unsupported subclasses/protocols and exact bounds. Check the
ordinary output-cache suite under the adapter, including input mutation during
lookup. Compare complete fixture HTML and all reached ownership snapshots;
count native key calls and admitted maps in a separate untimed render.
Use eight fresh-process pairs, six initial and 80 measured warm renders,
balanced randomized order and normal GC, retaining every observation. Require
seven joint wall/CPU wins and at least 0.25 ms median paired mean wall saving
before ordinary-source production qualification. Record sources, lockfile and
both native artifacts. Do not run builds or tests during timing.

## Binding scope and reproduction

This unpublished standalone benchmark crate uses the existing PyO3 version and
ABI3 policy. No production parser, AST, compiler, LangImpl, registration, stub
or wrapper changes. Production qualification would cover the regular Python
binding, private wrapper/stub, older-core behavior and affected tests. This key
contains Python types and values and belongs to the binding, not a portable
language-neutral template format; the other host languages have no live Python
attribute-output cache to update.

On this macOS worktree, build from the root with:

```sh
PYO3_PYTHON="$PWD/.venv/bin/python" cargo build --release \
  --manifest-path benchmarks/native_attrs_output_probe/Cargo.toml
```

The adapter loads that crate's release dylib through Python's extension loader.
Other platforms require their corresponding artifact path. Run `check.py` and
`probe.py` with the worktree Python. The probe uses the same eight-pair options
as the preceding attribute experiment.

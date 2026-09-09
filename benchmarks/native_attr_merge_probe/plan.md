# Run the attribute merge loop in one native call

## Prior art

`citry/attrs.py:319` merges validated ordered contributions into a fresh dict,
retaining the first key object and last ordinary value object. It collects
class/style values and calls their normalizers in class-then-style order.
`citry/nodes/__init__.py:1013` calls it after expressions and spread validation.
The final-output cache at `ElementAttrsNode._format` already skips repeated
formatting. Earlier merge-result caching retained keys/values from earlier
renders; its name-position variant did not establish a whole-render benefit.
`crates/citry_html_transform/src` transforms existing HTML and has no equivalent
contribution merger. The current cProfile diagnostic records 505 merge calls,
0.916 ms self and 2.825 ms cumulative instrumented time per large render.

## Experiment and alternatives

Move the contribution loop into one experimental PyO3 function. Admit exact
lists of exact two-item tuples with exact string keys representable in UTF-8.
Return a sentinel for unsupported inputs before running any Python callbacks;
the adapter then calls the original merger. Keep arbitrary values as their
original Python objects. Compute ASCII name identity while preserving the
case-sensitive Citry directive prefixes. Build a fresh Python dict and two
contribution lists, then call the existing Python normalizers in their original
order. Resolve the style normalizer after class normalization, so a callback
changing the style helper remains visible. No previous-render values or merged
outputs are retained.

The adapter guards the identity helper aliases against changes after probe
import. Preinstalled overrides, mutation within helper functions or their
translation table, concurrent mutation, and allocation/finalizer timing remain
unqualified. They require explicit production qualification if timing passes.
Expressions, name validation, hooks, filtering and final formatting stay live.
This boundary can admit structured class/style values without reimplementing
Python normalization or CSS parsing in Rust.

A combined merger/formatter could avoid the intermediate dict but would need
separate behavior for extension hooks and the existing formatting cache.
Rewriting every normalizer in Rust would enlarge the semantic change. Test
this bounded merge operation first; it does not establish an upper bound for
those broader alternatives.

## Verification and acceptance

Before timing, compare ordered results and current key/value identity over
seeded exact-key inputs, structured class/style values, case variants and
case-sensitive directive names. Check fallback for custom keys, iterators,
malformed rows and lone surrogates; compare errors and callback ordering.
Verify full fixture HTML and every reached ownership snapshot. Count native
successes and fallbacks only in a separate untimed render.

Use eight balanced randomized fresh-process pairs, six initial renders and
80 measured warm renders, keeping every sample and normal GC. Require at least
seven joint wall/CPU wins and 0.25 ms median paired mean wall saving to justify
production qualification. Record exact Python/Rust sources, Cargo lockfile and
both loaded artifacts. The separate extension is loaded in both variants.
Do not build or run tests during timing.

## Binding scope

This is an unpublished standalone benchmark crate with the existing pinned
PyO3 version and ABI3 policy. It adds no production parser, AST, compiler,
LangImpl, wrapper or registration changes. If adopted, factor language-neutral
name grouping into an appropriate Rust crate, put Python objects/callbacks in
the regular binding, update registration/stubs/wrapper, and run Rust/Python
checks. JS/PHP/Go/Rust host implementations currently have no live matching
attribute runtime to change; document that scope in the production plan.

## Reproduce on the measured macOS workspace

Build with `PYO3_PYTHON="$PWD/.venv/bin/python" cargo build --release
--manifest-path benchmarks/native_attr_merge_probe/Cargo.toml` from the worktree
root. The adapter loads the resulting macOS `.dylib` through Python's extension
loader; other platforms need their corresponding artifact suffix. Run
`.venv/bin/python benchmarks/native_attr_merge_probe/check.py` for the bounded
comparisons, then `probe.py --pairs 8 --samples 80 --seed 20261003 --output PATH`
with the same interpreter. The activation counter counts native successes and
native unsupported-input returns; it does not count helper-guard fallbacks.
The ordinary fixture uses unchanged helpers.

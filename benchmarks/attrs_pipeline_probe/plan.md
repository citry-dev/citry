# Reuse final attribute output from current primitive contributions

## Prior art

`ElementAttrsNode._resolve` and `_resolve_with_spread` in
`citry/nodes/__init__.py` evaluate expressions and validate spread keys before
calling `_merge_resolved_attrs`. The merged dict then passes framework-key
checks, client-props handling and filtering. `render` chooses extension hooks
and `_format` constructs a second key for the existing output cache.
The preceding diagnostic found 495 output-cache hits in a warm fixture render,
but those hits occur after merging. The earlier merged-dict cache changed
current key/value identity; a cache of final strings at the render boundary
need not expose a previous mapping to callers. Public/direct `_resolve` calls
must still produce the original current-value dict.

## Experimental design

Split copies of the original method ASTs into collection and finishing helpers,
using the original module's live globals. Collection evaluates each current attribute
once and preserves the original spread-key validation and its cache. Finish executes the existing
merge, framework-key checks, client-props handling, filtering, hooks and format
path without evaluating those inputs again. Only the exact ordinary node render
path uses this split; modified resolution/formatting methods use original render.

Between collection and finish, admit at most 16 exact two-item tuples with
exact string keys and exact string, bool or None values, bounded to 2,048 total
characters. Exclude framework directive/event prefixes (`#`, `$`, `@c-`, `:c-`,
`c-$c-`) and data-cev names. Ordinary Alpine keys such as `@click` remain
eligible when the ordinary manager reports no applicable attrs hook. Integer
values are excluded, so bool/int equality cannot collapse cache keys. Store
only an immutable tuple of the already-created contribution pairs and the final
exact string, bounded to 256 entries. No component, context, node or previous
merged dict enters the cache. Ordered duplicate names remain part of the key.
Errors are not cached. Unsupported contributions still finish normally.

Hits require the existing formatting-helper guard plus original merge/class
helper identities and no applicable attrs hook under the ordinary manager.
Check live node methods and exact node/manager types. A hook added or helper
replaced after warmup must use the finish path. Recheck eligibility before
storing a successful string. The original helper identities are captured at
probe import, so preinstalled overrides and function-body/regex/table mutation
remain unqualified. Eligibility reads component/engine/manager state earlier
than the original merge; custom descriptors and side effects from those reads
are an explicit production falsifier. Mutation during callbacks, concurrency,
instance overrides of manager helpers and compiler/node mutation need separate
qualification before adoption. No production behavior is proposed yet.

This is broader than caching the merged dict or moving one loop into Rust:
a hit skips merge allocation/normalization, filtering and the existing output
cache's key construction and lookup. It still evaluates every input. A Rust
key builder would add another boundary before this larger opportunity is
measured, so this first candidate stays in Python.

## Verification and acceptance

Compare full fixture HTML and every ownership snapshot. Count collection calls,
cache hits and finish calls in a separate untimed render, never in timed work.
Check changed primitive values, contribution order, class/style normalization,
uncached invalid values, custom value behavior, cache bounds and post-warm
helper/hook changes. Document counterexamples rather than treating fixture
success as public API qualification.

Use eight balanced randomized fresh-process pairs with six initial renders,
80 measured warm renders, normal GC and all observations retained. Require
seven joint wall/CPU wins and at least 0.25 ms median paired mean wall saving to
justify production qualification. The earlier packaged-key failure shows why
ordinary-source performance must be checked again if this prototype passes.
No native artifact or production source changes. Store source/artifact hashes
and retain the exact measured adapter before any later revision.

# Measure reuse of merged primitive attribute contributions

Element nodes resolve all authored expressions and spreads into an ordered
list of contributions. `_merge_resolved_attrs` then folds HTML name identity,
keeps the first spelling/order and normalizes accumulated class/style values.
The existing final-output cache runs after this work. A preliminary diagnostic
finds 430 of 505 merge calls using only exact string keys with string, bool or
None values, across 96 distinct contribution sequences.

Prior art: `ElementAttrsNode._resolve`, `_resolve_with_spread` and `_format` in
`citry/nodes/__init__.py`; `_merge_resolved_attrs`, class/style normalization
and the helper guards in `citry/attrs.py`; the attribute design document
`docs/design/template_html_attrs.md`; and research areas four, spread-key
validation and the later final-output cache. Expressions, spread iteration,
key validation, client directives and extension hooks must remain live.

The isolated candidate accepts exact lists of at most 16 exact two-item tuples.
Keys must be exact strings; values must be exact strings, bools or None. A
snapshot limits total input text to 2,048 characters and becomes the cache key.
The cache holds at most 256 immutable merged item tuples. Each hit returns a
new dict, preserving callers' ability to mutate the result independently.
Hits can reuse string key/value objects from an earlier equal input, so this
does not preserve current-input object identity for ordinary attributes.
Other inputs use the original merger. Failed merges are not cached.

This prototype does not guard replacement or internal mutation of normalizer
helpers, regular expressions or HTML identity helpers. Such changes can leave
cached results stale and may invalidate the primitive-output retention claim.
The original helpers determine the measured result. Defining-module identities,
live dependency changes, concurrent mutation and custom input behavior need
qualification before production adoption. This is not a speed ceiling for a
different cache or a contract to cache arbitrary application objects.

Use eight balanced randomized fresh-process pairs, each retaining 80 complete
renders after six warmups with normal GC. Require seven joint wall/CPU wins
and 0.25 ms median process-pair mean wall saving to proceed with a guarded
production design. Keep every sample and paired HTML/native hashes; compare
all ownership snapshots reached in the untimed comparison. Record activation
outside timing. Budget the screen to less than five minutes. Focused checks
cover result isolation, contribution order and case, class/style semantics,
fallback values, cache bounds and a changed-helper counterexample.

## Test prepared name positions with live values

The result cache misses the seven-win screen and has concrete string-identity
and changed-normalizer differences. A different candidate prepares only the
name relationships: first output positions, last ordinary-value positions and
the indices contributing to class/style. Its cache key is the ordered name
sequence. Every application reads the current key/value objects and calls the
current normalizers in class-then-style order. Values can be arbitrary objects;
the cache retains no values. Exact list/tuple/key checks and bounds still
apply, with the 2,048-character limit covering names only.

The candidate falls back when any of the three HTML identity helper functions
differs from its probe-import identity. Preinstalled replacements, function-body
or translation-table mutation and concurrent changes remain unqualified. No
production change is proposed yet. Compare this different work reduction once
using the same eight-pair screen. Check current key/value identity, changed
normalizers, identity-helper replacement and structured input mutation alongside
the ordered random comparisons. This is not a guarded version of the rejected
result cache; it retains merge positions instead of normalized output.

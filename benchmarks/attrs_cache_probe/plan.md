# Bounded reuse of final attribute strings

## Prior art

`attrs.py::_format_resolved_attrs_to_str` formats validated, coalesced maps.
`ElementAttrsNode.render` calls it after expression resolution and extension
hooks. Public `format_attrs` reaches it after validation and coalescing.
Existing caches retain validated spread names and normalized class
contributions; they do not memoize complete final maps. The native formatter
experiments in `docs/design/performance.md` improved isolated formatting but
did not establish a production complete-render benefit.

An initial untimed large render reaches 535 final maps. Of these, 525 contain
only exact string keys and exact string, integer, boolean or None values, with
130 distinct ordered maps. That gives 395 within-render repeats. These counts
precede size guards and are a reason to measure, not a speedup prediction.

## Design and falsifiers

Test an opt-in Python LRU around the final formatter. Admit only exact dicts,
at most 16 attributes, exact string keys, exact string/bool/None values and
integers bounded to 256 bits. Preserve attribute order and distinguish bools
from integers in keys. Limit each key to 2,048 total string characters and the
cache to 256 entries. Values with protocols, subclasses, proxies, floats or
structured class/style values remain on the original path. Resolution,
validation and extension callbacks run on every render.

Guard the live formatting helpers and the escaper's backend identities before
using cached results. Rebinding them bypasses the cache because a replacement
may be stateful. This experiment does not promise transparent monkeypatching
of internals within those helpers. Production adoption would require auditing
that boundary and proving invalidation and error behavior separately.

Compare complete renders in 60 alternating pairs after six warmups. Require
identical HTML on every pair, all reached ownership snapshots, positive cache
hit counts and bounds after an untimed render. Retain raw observations and
source hashes. A production proposal requires at least 0.25 ms median paired
saving and at least 45 favorable pairs in each of two fresh processes; reject
this cache if lookup/key construction cancels its savings. Changing the cache
design requires recording that change before another comparison.

The alternative is a native formatting loop, already measured. A per-node
last-value cache could avoid the global LRU but would multiply retained state
by template size; it is not included in this first experiment. This adds no
production code, dependencies or CI gate.

## Broader boundary, after the first measurements

The formatter-only cache has median paired savings of 0.209 and 0.230 ms in two complete-render
comparisons, with 39 and 40 favorable pairs. It misses both acceptance rules.
Test the same bounded keys at `ElementAttrsNode._format` instead. For admitted
primitive values, a cache hit can also skip the nested-render detection scan,
repeated key validation, and leading-space assembly. A miss still runs the
complete original node method. Key validation and coalescing remain on
misses; identical exact keys cannot change validity between calls while the
guarded helpers remain unchanged. Include `validate_keys` in the cache key.
Unsupported values still call the complete original node method with its
original context. Do not cache context objects or node instances.

Use a 256-entry FIFO dictionary at this boundary so a miss can call the
original method without passing the node/context into a memoized function.
This preserves the original tag-specific validation errors. The candidate
includes Python hit/miss counters in its timed path. Change the deterministic
ID start for each pair, keeping the same start within each reference/candidate
pair, to exclude artificial cross-render reuse of generated IDs.

Guard the node's formatter and key-validator aliases too. Both variants use
the imported vanilla runtime. Helpers replaced before cache construction are
not qualified: capturing their identity does not prove they are deterministic.
The formatter-only harness also requires both original formatter aliases to be
identical, so its switch does not erase a pre-existing alias override. Apply
the original two-run threshold to the broader boundary separately.

Review added a guard for the attrs module's direct formatter alias as well as
the node alias. Node caching now admits only exact `ElementAttrsNode` instances;
when key validation is requested, the cached tag name must already be an exact
string. Other objects, subclasses and unresolved/custom tag names run the
original method. Compare the revised guards in final runs; keep earlier reports
as preliminary evidence with their original source hashes.

# Share bounded immutable source-site metadata across root renders

`OwnershipGraph.record_source_location` already shares `_SourceSite` values
within one graph. Each new root graph repeats UTF-8 span validation and
line/column calculation for the same template locations. The earlier
unbounded shared-dictionary experiment saved a median 0.185 ms in 60
shared-process comparisons, with 35 wins. That result predates the normal-GC,
separate-process method now used for qualification.

The prior-art search covered that experiment in `repeated_work_probe.py`,
`record_source_location`, `_SourceSite`, `SourceLocationRecord`, graph snapshot
and replay state, and the research log's fifth iteration. Source sites contain
only template metadata. Each executed occurrence must still receive its own
owner, ID, order, mapping fields and source-location record.

The candidate adds a second cache behind the existing graph-local cache.
Only graph-local misses consult it. A thread-safe `functools.lru_cache` retains
at most 256 immutable sites. Eligible keys contain exact strings for source
text and optional origin, plus an exact two-int tuple for the byte span.
Limit source text to 8,192 characters, origin to 1,024 characters and integer
offsets to 32 bits. Other values use the uncached calculation. This bounds
retention even when callers supply many large or unusual templates; it does
not cap the existing graph-local cache.

Source string conversion and live template-origin lookup remain in the
existing method on every call. Both cache paths use the original calculation
body. Guard the `_SourceSite` identity and constructor methods captured at probe
import so later replacements do not consume cached results. A replacement
installed before probe import would be trusted; any production follow-up
needs originals captured where the type is defined. The cache lock protects
its bookkeeping, not atomicity against concurrent constructor changes. The
copied calculation also runs under probe globals, so overrides of builtins
or exception types in the ownership module are outside this experiment.
Failed span validation must not populate the shared cache. Equal eligible metadata may share one
immutable site across requests, but no graph, owner or occurrence is shared.

Compare eight balanced randomized fresh-process pairs, 80 complete renders
per worker after six warmups, with normal GC and every sample retained.
Require seven joint wall/CPU wins and at least 0.25 ms median process-pair mean
wall saving before production adoption. Compare all paired HTML digests and
native artifacts, and separately compare all reached ownership snapshots.
Untimed activation must establish shared hits and the entry bound. If timing
passes, qualify invalid and Unicode spans, changed source/origin, subclasses,
constructor replacement, callback counts, eviction and concurrent use before
adoption. No production source changes in this experiment.

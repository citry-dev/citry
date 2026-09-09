# Production qualification of cached attribute output

## Prior art and scope

`5bad7af8` records a 0.688 ms median process-pair mean saving for the node
formatting prototype, with seven of eight process pairs jointly faster on wall
and CPU time. Every sample's output digest matches. The preceding shared-heap
diagnostics explain why individual render wins are sensitive to GC scheduling.
`ElementAttrsNode._format`, the helpers in `attrs.py` and `util/html.py`, and
`test_attrs.py` / `test_attrs_template.py` define the behavior to preserve.

An untimed current large render calls `_format` 505 times with
`validate_keys=False` and zero times with it true. Restrict production caching
to this already-validated branch. It covers the measured opportunity and
leaves arbitrary hook-rewritten maps on the complete validation path. No
grammar, AST, compiler output, PyO3 surface or other binding changes are needed.

## Design

Keep a module-local FIFO with at most 256 outputs. Keys contain ordered exact
strings and exact str/int/bool/None values, distinguishing booleans from
integers. Retain the experiment's 16-attribute, 2,048-character and 256-bit
integer bounds. Admit only exact ElementAttrsNode and dict objects. A hit
returns its immutable plain string. A miss runs the existing node code and
stores only a successful exact-string result. Resolution, input callbacks and
the extension-dispatch decision stay live before this boundary.
A cacheable miss formats a dict built from the key's immutable values, so
concurrent input edits cannot associate a result with the wrong key.

Capture original Python helper identities at their defining modules' import,
not on the first cache use. Check the formatter aliases and relevant live
helpers before lookup and again before storing. Preserve stable helper
replacements between calls, including before the first render. Concurrent
replacement-and-restoration and arbitrary changes inside unchanged helpers
are not covered by endpoint identity checks. Enable reuse
only with the known MarkupSafe C escaper; Python/custom backends retain the
ordinary path. Rewriting function code objects or mutating private translation
tables is not an extension contract established by this change. Existing
attribute-identity caches already assume their private tables are stable.

Hits read the dictionary without a lock. Serialize FIFO eviction/insertion
under a reentrant lock so concurrent misses cannot exceed the bound or evict
the same key incorrectly. All retained values and key members are immutable
builtins; no nodes, contexts, component classes or user protocol objects are
retained. The cache lasts for the process, like the existing bounded class and
attribute-name caches. It contains no engine-specific facts. Clearing an
engine need not flush shared immutable formatting results.

## Falsifiers and evidence required

Reject or revise if it changes output/order/types, validation diagnostics,
hook execution, nested-template handling, proxy/protocol calls, helper
replacement behavior or the retention bound. Exercise helpers replaced before
first use and after a warm hit, both validation modes, subclasses, structured
values, oversized values, changing values, independent engines and concurrent
misses. Use the existing suites and focused regression cases for these risks.

Compare the exact pre-change method from `5bad7af8` with the production method
in the isolated-process runner. Keep the existing eight-pair rule: seven joint
wall/CPU wins and at least 0.25 ms median process-pair mean wall saving. Require
matching output digests, active reuse and all reached ownership snapshots.
The prototype's result cannot stand in for this production comparison. Run
the full repository gate and browser suite before the production commit, with
an independent technical and separate prose review. Record all results in the
research log. The uncached/native alternatives remain available if guards and
lifetime management erase the benefit.

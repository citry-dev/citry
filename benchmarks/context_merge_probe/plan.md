# Measure declarative copying of extension context records

The default manager dispatches 546 context-merge calls in one large render.
Each constructs a frozen hook context and invokes Dependencies, Events and
I18n. Their current implementations all perform the same dictionary operation:
read their child `extra` entry and, when nonempty, update their parent entry.
The preliminary count finds 227 empty child `extra` mappings, 319 dependency
updates containing 2,490 items in total, and no Events or I18n updates. Nine
merges share the outer `extra` mapping. Those counts are observations, not
measurements of removable time.

Prior art: `ExtensionManager.on_render_context_merge` and `emit` in
`citry/extension.py`; Dependencies and I18n merge hooks in their `extension.py`
files; Events' hook and `merge_instance_entries` in `events/emission.py`;
`component_render._merge_dependencies`; the extension composition rule in
`CLAUDE.md`; and the earlier hook-subset experiment in research iteration five.
The core currently owns dispatch and each extension owns its merge policy.

The isolated candidate prepares ordered dictionary keys from the three exact
built-in subscriber types on its first merge. Later calls apply the dictionary
updates directly, preserving their order and evaluating each child entry after
the preceding update. No hook context is allocated. Unknown subscriber types
or class hooks changed after probe import reject when preparing the plan.
Replacements already present at import are trusted. Later metadata or hook
changes are deliberately untracked; instance overrides, custom manager dispatch,
context constructors, mutable module constants/helpers and concurrency are
unqualified. This is not production behavior or a bound on another design.

A production design would need a general extension-owned declaration available
to every extension, plus a defined relationship to authored hooks. Putting
special cases for three named extensions into core would violate the repository
composition rule. First measure whether removing the dispatch and context
construction warrants designing that contract. We do not skip duplicate
dictionary updates in this candidate.

Use eight balanced randomized fresh-process pairs, six warmups and 80 complete
samples per worker. Keep normal GC, all observations, matched IDs/hash seeds,
paired HTML digests and native hashes. Require at least seven joint wall/CPU
wins and 0.25 ms median process-pair mean wall saving before further design.
Budget the run to less than five minutes. Compare every ownership snapshot
reached in an untimed render and record actual merge activation separately.
The update/item counters inspect child entries after each complete merge;
they are not exact operation counts for arbitrary cross-key aliasing.
Focused synthetic checks should cover empty/nonempty entries, insertion order,
overwriting, shared mappings and an observable hook override counterexample.

## Follow up with live hook selection

The first candidate passes the screen with seven joint wins and 0.548 ms
median wall saving. `live_probe.py` now resolves each extension's current hook
in dispatch order. An exact bound method whose function matches a known merge
operation takes the dictionary path. Other callbacks run normally, sharing one
hook context allocated only when the first ordinary callback needs it.
This preserves ordinary instance and class hook overrides, including a hook
that changes the next subscriber's method. Use the same timing screen once
and execute those override checks before deciding on a production design.

The probe still infers declarations from three known functions. It is not a
general extension API. Globals/helpers read inside recognized methods,
function-body edits, hook-context constructor changes, preinstalled replacements
and custom manager `emit` overrides remain unqualified. Declared operations
would need an explicit author-owned contract for production, not this inference.

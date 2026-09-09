# Reduce temporary objects for ownership scopes

## Prior art

`ownership.py` uses generator context managers for `active_region`,
`active_invocation_region`, `select_supply` and `slot_site`. They set a context
variable on entry and restore its token on exit. Invocation scopes sometimes
enter another region scope. The retained orchestration profile creates 1,770
contextlib wrappers per page across all features, not just these four methods.
The earlier resume-graph optimization already skips an unchanged active graph;
this experiment addresses the remaining ownership scope representation.
Read the current Python contextlib implementation and the four ownership
methods. The immutable `_SlotSite` and `_SelectedSupply` payloads stay unchanged.

## Experiment

Replace these four factories with small classes using slots. One object holds
the entry arguments and then the token or delegated context manager. Entry
arguments are released on entry, and token/delegate references on exit.
Look up graph rows, component IDs, helpers and context variables at the same
entry/exit stages as the original code. Invocation scopes still call the graph's
live `active_region` override and preserve delegated suppression. Scope objects
support recreation when used as decorators. No per-call compatibility scan,
native extension or production edit is required for this prototype.

Keep unsupported lifecycle behavior explicitly unqualified: abandoning a
manually entered scope can trigger generator cleanup in the original version;
the prototype has no generator finalizer. Direct malformed/repeated protocol
calls, exact traceback frames, unusual delegated context-manager descriptors,
preinstalled factory overrides and subclass assumptions about contextlib
internals need qualification before adoption. Callback-raised StopIteration can also differ: the generator wraps a new
StopIteration from entry or delegated exit into RuntimeError, while the
prototype may propagate it directly. The site scope releases entry arguments
when __enter__ returns; the generator retains its frame locals through the
body, so weakrefs and finalizers can observe different lifetimes even with
ordinary with-blocks. Covered body exceptions, nested restoration, decorator
reuse and copied-context payloads must match the focused checks. This experiment
is not a claim of complete production compatibility.

Inlining context-variable operations at every call site could remove the
manager too, but would duplicate restoration logic and affect user overrides.
Combining scope objects with their payloads would change values retained in
copied contexts. Measure the narrower allocation change first.

## Evidence and decision

Compare entry timing, normal/nested/exceptional restoration, exception identity,
decorator reuse, copied contexts, changed invocation parents before entry and
active-region overrides. Compare full fixture HTML and all reached ownership
snapshots. Run existing ownership/slot tests under the installed adapter.
Count each new scope type in a separate untimed render.

After independent review, run eight balanced randomized fresh-process pairs,
six initial renders and 80 warm samples per process, keeping normal GC and all
observations. Require seven joint wall/CPU wins and at least 0.25 ms median
paired reduction in process mean wall time before production qualification.
Keep actual second-render results separate. Preserve measured source hashes and
the original native artifact. A failed screen ends this candidate's evaluation.

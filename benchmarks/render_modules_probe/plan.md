# Compile the component, node and slot pipeline together

## Prior art and scope

`component_render.py:_render_one` coordinates construction, input hooks, data,
body caching and node execution; `_settle_render` handles child tasks, hooks
and replacement. `nodes/__init__.py` executes template nodes and constructs slot
callbacks, while `slots.py` invokes and normalizes slot inputs. The rendering
contract is in `docs/design/component_rendering.md`; ownership capture remains
in the ordinary runtime qualified by the preceding experiments.

Iteration 8 compiled four isolated transaction functions, saving about 0.5 ms.
Iterations 44 and 48 compiled ownership, saving 0.445 and 0.743 ms respectively
and failing the 1 ms requirement for a new native distribution path. None of
those experiments compiled these three complete modules together. This probes
whether reducing interpreter dispatch across the larger pipeline produces a
useful complete-render gain. It does not claim to remove callback or record work.

## Design and alternatives

Copy the exact three source files into a separate temporary build directory
and compile them under their real module names using the existing isolated
Cython 3.3.0 tools. Keep Python classes and values, with annotation typing and
type inference disabled and binding enabled. An import finder selects the
candidate before Citry is imported and preserves the node package's submodule
search path. Reference workers import ordinary sources. No live module reload,
shipping dependency or source edit is part of this candidate.

Compiling ownership again repeats prior evidence. Individually compiling more
helpers retains their surrounding interpreter work, so this experiment measures
the three-module combination. A larger native data model remains an alternative;
this comparison does not qualify or predict its performance.

The [Cython limitations guide](https://docs.cython.org/en/latest/src/userguide/limitations.html)
documents differences from Python, including stack frames. Such differences
must be recorded, and successful HTML is not a general compatibility guarantee.
Retain compiler/import failures before changing the candidate; do not silently
drop a module from the measured set if it fails.

## Verification and decision

First build and import all three modules, verify actual extension loaders and
compiled entry points, then compare complete HTML and four canonical ownership
snapshots. Record source, generated C, artifact and normal Rust binary hashes.
Run relevant node, slot, render, hook and ownership checks under the candidate;
retain failed cases and inspect their cause. Candidate activation and snapshot
instrumentation run outside the complete-render timer.

The predeclared screen requires at least seven of eight joint wall/CPU wins and
1 ms median paired reduction in process mean warm render time. Each fresh worker
retains six initial and 80 warm renders, normal GC and all samples, with balanced
randomized variant order. Actual second renders are reported separately. No
tests or builds overlap timing. A failed screen ends the candidate; a pass only
supports further callback, mutation, lifetime and distribution qualification.
Even a pass measures the whole combination against production, not incremental
contributions from individual modules or previous Cython experiments.

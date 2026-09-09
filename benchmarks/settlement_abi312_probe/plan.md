# Test the Python 3.12 stable ABI for the complete execution backend

## Prior art and hypothesis

Iteration 50's interpreter-specific compiled pipeline saves 3.132 ms per warm
render. Iteration 51's Python 3.10 stable-ABI target saves only 0.533 ms with
five joint wins, missing both acceptance requirements despite passing its tests
and lifetime checks. This leaves the distribution model unresolved.

The [Cython stable ABI guide](https://docs.cython.org/en/latest/src/userguide/limited_api.html)
states that the Python 3.12 Limited API target enables its vectorcall interface
for faster Python function calls. Test that target for the complete corrected
component-render, node and slot pipeline, using the same reviewed explicit
settlement-state transform. This is architectural distribution qualification,
not a new local rendering algorithm or a reason to sum earlier gains.

## Design and limits

Set `Py_LIMITED_API=0x030C0000` and `py_limited_api=True`, retaining a separate
build directory and `.abi3.so` artifacts. Keep the Python 3.10 ABI and regular
CPython builds intact. Compile the same three sources and record the original,
transformed, generated-C and artifact hashes alongside actual compiler flags.
The finder selects all three modules before Citry imports.

The package supports Python 3.10 onward. An eventual Python 3.12 ABI accelerator
must leave older Python versions on their supported implementation; raising the
package minimum is not part of this design. PyPy and other distributions also
require explicit qualification or fallback. The present experiment runs only
on CPython 3.14 and does not implement wheel selection or qualify other runtimes.
Version-specific wheels remain an alternative if this shared ABI target fails.

## Checks and decision

Require actual ABI3 module paths, compiled entry points and explicit settlement
state. Compare complete HTML and all four canonical ownership snapshots, rerun
the 625-test selection and both lifetime diagnostics, and retain failures rather
than silently changing the candidate. If these checks pass, measure eight
balanced randomized fresh-process pairs against ordinary production, six initial
and 80 warm renders each, with normal GC and all samples. Keep second renders
separate and run no tests/builds during main timing.

The unchanged screen requires seven joint wall/CPU wins and 1 ms median paired
reduction in process mean warm wall time. A pass supports testing the supported
CPython versions, browser integration and wheel packaging. A failure rejects
this ABI target's current implementation without discarding the version-specific
candidate. This comparison does not isolate vectorcall's contribution.

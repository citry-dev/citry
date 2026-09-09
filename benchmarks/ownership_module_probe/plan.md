# Compile ownership recording and updates as one module

## Prior art and purpose

The graph-local source-site cache already handles repeated span calculations
within a render. The bounded shared-site experiment failed its performance
screen. Iteration eight compiled four isolated component transaction functions,
with a small combined gain and unqualified global rebinding. None of those
measurements covers the complete ownership module. The recent native scan and
scope-object experiments also show why fewer individual operations need not
improve complete renders.

Compile the current `citry/ownership.py` as one experimental module, including
record construction, capture, scopes, bindings and updates. Keep Python classes,
objects and dynamic operations; do not introduce C-level field types. The aim
is to measure a larger unit of interpreter work without writing dozens of new
Python-to-Rust calls. This does not propose shipping Cython or replacing Citry's
Rust distribution architecture.

## Build and isolation

Reuse Cython 3.3.0 and setuptools 84.0.0 already installed in the separate
`/tmp/citry-cython-build` directory. Copy the exact current source into a
private build directory and compile an extension named `citry.ownership`.
Use language_level=3, annotation_typing=False, infer_types=False and
binding=True. The [Cython compilation guide](https://docs.cython.org/en/latest/src/userguide/source_files_and_compilation.html)
describes those directives; its [limitations guide](https://docs.cython.org/en/latest/src/userguide/limitations.html)
warns about differences from interpreted Python. Disabling annotation typing
avoids treating existing annotations as new native restrictions; it does not
prove full behavioral equivalence.

A worker installs a finder for that single module before importing Citry.
Reference workers load ordinary Python source; candidate workers load the
compiled module under its real package name. No already-imported module is
swapped or reloaded. The normal Rust ABI3 binary remains unchanged. Record
source, generated C and extension hashes, compiler output, build-tool versions
and interpreter details. Build/import costs stay outside repeat-render timing.
No project dependency, production source, parser/compiler contract or shared
native artifact changes. This remains CPython/version-specific research;
PyPy, older interpreters, browser wheels and introspection are unqualified.

## Verification and decision

First establish that the module imports and the existing benchmark renders.
If it does not, inspect the concrete compiler/runtime incompatibility before
changing anything. Compare canonical full ownership snapshots and HTML across
fresh workers, including four separate reached snapshots. Verify that class
methods come from the intended compiled module. Run the focused ownership
suite under the candidate; retain any source/introspection differences rather
than inferring broad compatibility from fixture success.

If those checks pass, retain eight balanced randomized fresh-process pairs,
six initial renders and 80 measured warm renders each, normal GC and all
samples. Require at least seven joint wall/CPU wins and 1.0 ms median paired
reduction in process mean wall time to justify further qualification. This is
a higher saving requirement than the small-change screen because the earlier
0.5 ms isolated-function result did not justify another native distribution
path. Actual second renders stay separate. No retry to seek a passing result.
Even a pass would require qualifying callbacks, live rebinding, errors,
introspection, lifetime behavior and supported distributions before adoption.

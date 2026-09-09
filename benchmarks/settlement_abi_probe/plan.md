# Measure the compiled pipeline through Python's stable ABI

## Prior art and distribution question

Iteration 50's complete component-render, node and slot pipeline saves 3.132 ms
per warm render on CPython 3.14, passes 4,821 non-browser tests and fixes the
demonstrated settlement closure cycle. Its extensions use the version-specific
CPython API. Citry supports Python 3.10 onward (`packages/py/citry/pyproject.toml`)
and its regular core extension already ships ABI3 builds. A usable execution
backend needs a qualified distribution model, not only a local fast binary.

The [Cython stable ABI guide](https://docs.cython.org/en/latest/src/userguide/limited_api.html)
supports Limited API builds, warns that Python-object-heavy code can lose speed,
and requires testing the actual supported interpreter versions. Its Limited API
vectorcall support starts at Python 3.12. PyPy requires a different build or the
Python implementation. These are reasons to measure this architecture before
choosing packaging; they do not predict Citry's result.

## Candidate

Build exactly the iteration 50 transformed pipeline with `Py_LIMITED_API` set
to `0x030A0000` and setuptools `py_limited_api=True`, targeting CPython 3.10's
stable ABI. Use a separate directory and `.abi3.so` artifact names, preserving
the existing version-specific builds. Reuse the reviewed settlement transform;
do not change algorithms or silently raise the minimum version. Keep all three
module loaders and exact artifact/source hashes in the reports.

First test the Python 3.10 ABI target on the current CPython 3.14 runtime. This
does not qualify running on Python 3.10 or other platforms. A Python 3.12 ABI
target may be a later alternative if the older target loses its useful gain;
it would need explicit fallback for older runtimes and a separate comparison.
Version-specific wheels are another alternative, with a larger build matrix.
No package dependency, release setting or production source changes here.

## Verification and decision

Record build failures and inspect their source before changing the candidate.
Require actual ABI3 loading, compiled entry points and explicit settlement-state
activation; compare complete HTML and all four ownership snapshots. Recheck
the 625 selected contracts and both lifetime diagnostics. If this succeeds,
measure eight balanced randomized fresh-process pairs against ordinary
production, six initial and 80 warm renders each, normal GC and all samples.
No tests or builds overlap the main timing. Keep second renders separate.

Use the same seven-joint-win and 1 ms median paired reduction in process mean
wall time screen as iteration 50. This compares the complete ABI3 pipeline
against production, not an incremental ABI effect isolated from that earlier
run. A pass supports the interpreter/browser/packaging qualification; a failure
rejects this distribution target's current implementation without discarding
the measured version-specific candidate.

# Run the compiled pipeline on the supported stable-ABI interpreters

Iteration 52's Python 3.12 ABI target passes the warm-render screen on CPython
3.14.3. Its next failure boundary is whether those exact binaries import and
preserve rendering behavior on CPython 3.12 and 3.13. Test that boundary before
changing package selection or building more platform artifacts.

Create isolated environments for the two installed interpreters and install
only the runtime/test dependencies needed by the existing 625-test selection,
using versions from the current development environment. Use the optimization
worktree's Python sources and the existing Rust ABI3 extension directly. Preserve
the Cython artifacts from iteration 52 without rebuilding them. Record dependency
versions, interpreter details, artifact paths/hashes and actual entry-point types.

Run the existing selection once per interpreter after selecting all three
compiled modules. Check activation before and after pytest. Reuse both lifetime
diagnostics unchanged in fresh processes for each variant and interpreter, and
compare full-fixture output size and graph release. This does not compare full
HTML across interpreters; the selected tests check expected rendering behavior
on each. Existing tests launching child interpreters keep their normal Python
bootstrap, so those children do not qualify compiled execution.

Accept this local ABI compatibility check only if both selections and lifetime
checks pass with the intended artifacts. Preserve any failure and diagnose it
before expanding qualification. Budget two 625-test runs and four lifetime
comparisons, with no new timing matrix. These checks establish neither portable
wheel tags nor other platforms, free-threaded Python, PyPy or browser behavior.
A failure can reject this shared-ABI distribution path while leaving the earlier
version-specific pipeline available. Production stays unchanged.

## Parked at the user's request

The user parked Cython and ABI exploration before these checks ran. The two
isolated environments were created and their dependency installation logs are
retained. No runtime selection, lifetime comparison, browser test or packaging
work was executed for this plan. This is a deferred plan, not qualification
or a performance result.

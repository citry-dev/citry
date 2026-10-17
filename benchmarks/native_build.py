"""
Refuse to benchmark an unoptimized `citry-core` native extension.

`maturin develop` without `--release` builds the Rust extension in Cargo's
debug profile, which makes every Rust-backed path many times slower. A
benchmark run on that build still finishes and prints plausible numbers, so
each runner calls `require_release_build()` before it measures anything.

Set `CITRY_BENCH_ALLOW_DEBUG_NATIVE=1` to measure a debug build on purpose,
for example while profiling with debug assertions on.
"""

from __future__ import annotations

import os
import sys

from citry_core import _rust

ALLOW_DEBUG_ENV = "CITRY_BENCH_ALLOW_DEBUG_NATIVE"
REBUILD_COMMAND = "cd packages/py/citry_core && ../../../.venv/bin/maturin develop --release"


def require_release_build() -> None:
    """Exit with the rebuild command when the imported extension is a debug build."""
    # Read the attribute the extension sets from its own compile flags; the
    # file size or path of the `.so` cannot tell the two profiles apart.
    profile = _rust.BUILD_PROFILE
    if profile == "release":
        return
    # The override is for a person profiling the debug build on purpose, so
    # the run still says which build it measured. The note goes to stderr
    # because some runners print their JSON report on stdout.
    if os.environ.get(ALLOW_DEBUG_ENV) == "1":
        sys.stderr.write(f"WARNING: measuring a {profile} build of citry_core because {ALLOW_DEBUG_ENV}=1.\n")
        return
    message = (
        f"citry_core is a {profile} build ({_rust.__file__}); its Rust paths run many times "
        "slower, so benchmark numbers would be wrong.\n"
        f"Rebuild it in release mode from the repository root:\n    {REBUILD_COMMAND}\n"
        f"To measure the {profile} build on purpose, set {ALLOW_DEBUG_ENV}=1."
    )
    raise SystemExit(message)

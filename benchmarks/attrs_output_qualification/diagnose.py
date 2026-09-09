"""Inspect cache work and compare the two native key builders in isolation."""

from __future__ import annotations

import hashlib
import importlib.machinery
import importlib.util
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from benchmarks.attrs_output_qualification.probe import scenario  # noqa: E402

from citry import nodes  # noqa: E402
from citry_core import _rust  # noqa: E402


def main() -> None:
    """Keep counts outside timing and isolate native build differences afterward."""
    artifact = ROOT / "benchmarks/native_attrs_output_probe/target/release/libcitry_native_attrs_output_probe.dylib"
    name = "citry_native_attrs_output_probe"
    spec = importlib.util.spec_from_file_location(
        name, artifact, loader=importlib.machinery.ExtensionFileLoader(name, str(artifact))
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load the retained standalone builder")
    standalone = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(standalone)
    module = scenario()
    data = module.gen_render_data()
    for _ in range(6):
        module.render(data)
    maps = []
    counts = {"hits": 0, "misses": 0, "format_str_casts": 0}
    original_builder, original_cache, original_cast = (
        nodes._build_attrs_output_key,
        nodes._attrs_output_cache,
        nodes.cast,
    )

    def capture(values: Any) -> Any:
        key = original_builder(values)
        if key is not None:
            maps.append(values.copy())
        return key

    class CountingCache(dict):
        def get(self, key: Any, default: Any = None) -> Any:
            result = super().get(key, default)
            counts["misses" if result is None else "hits"] += 1
            return result

    def count_cast(kind: Any, value: Any) -> Any:
        if kind == "str" and sys._getframe(1).f_code is nodes.ElementAttrsNode._format.__code__:
            counts["format_str_casts"] += 1
        return original_cast(kind, value)

    nodes._build_attrs_output_key = capture
    nodes._attrs_output_cache = CountingCache(original_cache)
    nodes.cast = count_cast
    try:
        module.render(data)
    finally:
        nodes._build_attrs_output_key, nodes._attrs_output_cache, nodes.cast = (
            original_builder,
            original_cache,
            original_cast,
        )
    if not maps or any(standalone.cache_key(values) != original_builder(values) for values in maps):
        raise RuntimeError("Builder snapshots differ or no maps were captured")

    def batch(function: Any) -> dict[str, float]:
        cpu = time.process_time_ns()
        wall = time.perf_counter_ns()
        for _ in range(40):
            for values in maps:
                function(values)
        return {"wall_ms": (time.perf_counter_ns() - wall) / 40e6, "cpu_ms": (time.process_time_ns() - cpu) / 40e6}

    functions = {"standalone": standalone.cache_key, "packaged": original_builder}
    observations = []
    for index in range(20):
        order = ("standalone", "packaged") if index % 2 == 0 else ("packaged", "standalone")
        observations.append({name: batch(functions[name]) for name in order})
    report = {
        "diagnostic_only": True,
        "counts_from_one_untimed_warm_render": counts,
        "admitted_maps": len(maps),
        "keys_equal": True,
        "micro_scope": "Native key calls only; excludes cache lookup, formatting and the rest of rendering.",
        "median_packaged_minus_standalone_ms_per_fixture_maps": {
            clock: statistics.median(row["packaged"][clock] - row["standalone"][clock] for row in observations)
            for clock in ("wall_ms", "cpu_ms")
        },
        "observations": observations,
        "hashes": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (Path(__file__), artifact, Path(_rust.__file__), ROOT / "crates/citry_core_py/src/attrs.rs")
        },
    }
    (ROOT / "benchmarks/results/performance-render/packaged-attrs-output-diagnosis.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps({key: value for key, value in report.items() if key != "observations"}, indent=2))


if __name__ == "__main__":
    main()

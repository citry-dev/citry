"""Profile work inside selected icon calls after the complete-page timing decision."""

from __future__ import annotations

import argparse
import cProfile
import hashlib
import json
import pstats
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from benchmarks.identity_leaf_probe import adapter as guarded_adapter  # noqa: E402
from benchmarks.leaf_contract_probe import adapter  # noqa: E402
from benchmarks.ownership_journal_probe.probe import scenario  # noqa: E402

from citry import component_render as runtime  # noqa: E402


def worker(variant: str) -> dict[str, Any]:
    """Measure only the selected initial render stage, excluding later settlement."""
    module = scenario()
    if variant == "guarded":
        guarded_adapter.install(module, enabled=True)
    else:
        adapter.install(module, variant != "reference", variant="reuse" if variant == "reuse" else "contract")
    data = module.gen_render_data()
    for _ in range(6):
        module.render(data)
    profiler = cProfile.Profile()
    original = runtime._render_one
    calls = 0

    def observed(element: Any, parent: Any = None, provides: Any = None) -> Any:
        nonlocal calls
        if element.comp_cls is not module.HeroIcon:
            return original(element, parent, provides)
        calls += 1
        profiler.enable()
        try:
            return original(element, parent, provides)
        finally:
            profiler.disable()

    runtime._render_one = observed
    repeats = 8
    try:
        for _ in range(repeats):
            module.render(data)
    finally:
        runtime._render_one = original
    stats = pstats.Stats(profiler)
    rows = []
    for (filename, line, function), (primitive, total, own, cumulative, _) in stats.stats.items():
        rows.append(
            {
                "file": filename.removeprefix(str(ROOT) + "/"),
                "line": line,
                "function": function,
                "primitive_calls_per_page": primitive / repeats,
                "total_calls_per_page": total / repeats,
                "self_ms_per_page": own * 1000 / repeats,
                "inclusive_ms_per_page": cumulative * 1000 / repeats,
            }
        )
    return {
        "variant": variant,
        "selected_calls_per_page": calls / repeats,
        "repeats": repeats,
        "instrumented_selected_ms_per_page": stats.total_tt * 1000 / repeats,
        "rows": sorted(rows, key=lambda row: row["self_ms_per_page"], reverse=True),
    }


def main() -> None:
    """Retain profiler evidence separately from uninstrumented speed measurements."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", choices=("reference", "guarded", "reuse", "contract"))
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(args.worker)))
        return
    results = {}
    for variant in ("reference", "guarded", "reuse", "contract"):
        result = subprocess.run(
            [sys.executable, __file__, "--worker", variant], cwd=ROOT, capture_output=True, text=True, check=True
        )
        results[variant] = json.loads(result.stdout)
    paths = [
        Path(__file__),
        Path(adapter.__file__),
        Path(guarded_adapter.__file__),
        ROOT / "benchmarks/template_function_probe/runtime.py",
        ROOT / "packages/py/citry/citry/component_render.py",
    ]
    print(
        json.dumps(
            {
                "instrumented_not_throughput": True,
                "results": results,
                "hashes": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

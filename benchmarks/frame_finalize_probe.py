"""Compare complete renders with and without the empty-root-marker frame guard."""

from __future__ import annotations

import argparse
import hashlib
import inspect
import itertools
import json
import statistics
import sys
import time
import types
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "packages/py/citry"), str(ROOT / "packages/py/citry_core")]

import citry.component_render as runtime  # noqa: E402
import citry.util.id as ids  # noqa: E402
from benchmarks.utils import get_benchmark_script  # noqa: E402


def main() -> None:
    """Alternate the shipped function and its original unconditional copy."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pairs", type=int, default=60)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.pairs < 1:
        parser.error("--pairs must be positive")
    source = inspect.getsource(runtime._settle_render)
    guarded = """            frame = finalized.frame
            if (
                root_markers
                or type(frame) is not RenderFrame
                or type(frame.root_markers) is not tuple
                or frame.root_markers
            ):
                finalized.frame = replace(finalized.frame, root_markers=root_markers)"""
    unconditional = "            finalized.frame = replace(finalized.frame, root_markers=root_markers)"
    if source.count(guarded) != 1:
        raise RuntimeError("The frame finalization implementation has changed; update this probe")
    scope: dict[str, Any] = {}
    exec(  # noqa: S102
        compile(
            "from __future__ import annotations\n" + source.replace(guarded, unconditional), "frame-reference", "exec"
        ),
        runtime.__dict__,
        scope,
    )
    candidate = runtime._settle_render
    reference = scope["_settle_render"]
    path = ROOT / "packages/py/citry/tests/test_benchmark_citry.py"
    module = types.ModuleType("frame_finalize_scenario")
    module.__file__ = str(path)
    sys.modules[module.__name__] = module
    exec(compile(get_benchmark_script(path), str(path), "exec"), module.__dict__)  # noqa: S102
    data = module.gen_render_data()
    observations = []
    try:
        for variant in (reference, candidate):
            runtime._settle_render = variant
            for _ in range(6):
                module.render(data)
        for pair in range(args.pairs):
            outputs = {}
            for variant in (False, True) if pair % 2 == 0 else (True, False):
                runtime._settle_render = candidate if variant else reference
                ids._id_counter = itertools.count()
                start = time.perf_counter_ns()
                outputs[variant] = module.render(data)
                elapsed = (time.perf_counter_ns() - start) / 1_000_000
                observations.append({"pair": pair, "candidate": variant, "ms": elapsed})
            if outputs[False] != outputs[True]:
                raise RuntimeError(f"Frame guard changed HTML in pair {pair}")
    finally:
        runtime._settle_render = candidate
    medians = {
        name: statistics.median(row["ms"] for row in observations if row["candidate"] == variant)
        for name, variant in (("reference", False), ("candidate", True))
    }
    savings = []
    for pair in range(args.pairs):
        values = {row["candidate"]: row["ms"] for row in observations if row["pair"] == pair}
        savings.append(values[False] - values[True])
    report = {
        "change": "skip empty-to-empty root marker replacement for exact RenderFrame",
        "python": sys.version,
        "candidate_function_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "pairs": args.pairs,
        "all_pairs_html_equal": True,
        "medians_ms": medians,
        "median_paired_saving_ms": statistics.median(savings),
        "favorable_pairs": sum(value > 0 for value in savings),
        "observations": observations,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key != "observations"}, indent=2))


if __name__ == "__main__":
    main()

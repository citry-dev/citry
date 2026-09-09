"""Measure a tuple representation of render frames without changing production."""

from __future__ import annotations

import argparse
import gc
import hashlib
import itertools
import json
import os
import random
import statistics
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, NamedTuple

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "packages/py/citry"), str(ROOT / "packages/py/citry_core")]

from benchmarks.ownership_journal_probe.probe import scenario  # noqa: E402

import citry  # noqa: E402
import citry.citry_render as renders  # noqa: E402
import citry.component_render as components  # noqa: E402
import citry.util.id as ids  # noqa: E402
import citry_core._rust as native  # noqa: E402
from citry.ext.cache import replay  # noqa: E402
from citry.ownership import OwnershipGraph  # noqa: E402

ORIGINAL = renders.RenderFrame
ALIASES = (citry, renders, components, replay)


class TupleFrame(NamedTuple):
    """Store the same fields cheaply; public dataclass compatibility is unproven."""

    render_id: str | None
    class_id: str | None
    class_name: str | None
    is_component_root: bool
    root_markers: tuple[str, ...]


# Keep field capture and replacement live; tuple behavior remains a known difference.
TupleFrame.from_context = classmethod(ORIGINAL.from_context.__func__)
TupleFrame.__dataclass_fields__ = ORIGINAL.__dataclass_fields__


def install(changed: bool) -> None:
    """Switch every runtime import alias found in the prior-art search."""
    for module in ALIASES:
        module.RenderFrame = TupleFrame if changed else ORIGINAL


def capture_counts(module: Any, data: Any) -> dict[str, Any]:
    """Count from_context calls, retaining contexts so their IDs cannot be reused."""
    method = ORIGINAL.from_context.__func__
    rows = []
    contexts = []

    def capture(cls: type, context: Any, *, is_component_root: bool) -> Any:
        frame = method(cls, context, is_component_root=is_component_root)
        contexts.append(context)
        rows.append((id(context), frame))
        return frame

    ORIGINAL.from_context = classmethod(capture)
    try:
        module.render(data)
    finally:
        ORIGINAL.from_context = classmethod(method)
    return {
        "from_context_calls": len(rows),
        "root_flags": dict(Counter(frame.is_component_root for _, frame in rows)),
        "contexts": len({context for context, _ in rows}),
        "distinct_values": len({frame for _, frame in rows}),
        "distinct_context_values": len(set(rows)),
    }


def equivalence() -> dict[str, Any]:
    """Compare the reached fixture snapshots without claiming API compatibility."""
    module = scenario()
    data = module.gen_render_data()
    original_snapshot = OwnershipGraph.snapshot
    traces, outputs = [], []
    try:
        for changed in (False, True):
            install(changed)
            for _ in range(6):
                module.render(data)
            trace = []

            def snapshot(graph: Any, _trace: list[Any] = trace) -> Any:
                result = original_snapshot(graph)
                _trace.append(result)
                return result

            OwnershipGraph.snapshot = snapshot
            ids._id_counter = itertools.count()
            outputs.append(module.render(data))
            OwnershipGraph.snapshot = original_snapshot
            traces.append(trace)
        if not traces[0] or traces[0] != traces[1] or outputs[0] != outputs[1]:
            raise RuntimeError("The frame representation changed fixture HTML or ownership snapshots")
    finally:
        OwnershipGraph.snapshot = original_snapshot
        install(changed=False)
    values = ("render", "class", "Card", True, ())
    baseline, candidate = ORIGINAL(*values), TupleFrame(*values)
    return {
        "snapshots_compared": len(traces[0]),
        "snapshots_equal": True,
        "html_equal": True,
        "counts": capture_counts(module, data),
        "known_public_difference": {
            "reference_is_tuple": isinstance(baseline, tuple),
            "candidate_is_tuple": isinstance(candidate, tuple),
            "cross_representation_equality": baseline == candidate,
        },
    }


def worker(changed: bool, samples: int, id_base: int) -> dict[str, Any]:
    """Include all complete renders and their GC costs on one private heap."""
    ids._id_base = id_base
    ids._id_counter = itertools.count()
    install(changed)
    module = scenario()
    data = module.gen_render_data()
    for _ in range(6):
        module.render(data)
    before = gc.get_stats()
    observations, digests = [], []
    for index in range(samples):
        ids._id_counter = itertools.count((index + 1) * 1_000_000)
        cpu_start = time.process_time_ns()
        start = time.perf_counter_ns()
        output = module.render(data)
        end = time.perf_counter_ns()
        cpu_end = time.process_time_ns()
        observations.append({"ms": (end - start) / 1_000_000, "cpu_ms": (cpu_end - cpu_start) / 1_000_000})
        digests.append(hashlib.sha256(output.encode()).hexdigest())
        del output
    after = gc.get_stats()
    # Inspect a fresh result after timing to prove the selected type is active.
    rendered = module.ProjectPage(**data).render()
    frame_type = type(rendered.frame)
    if frame_type is not (TupleFrame if changed else ORIGINAL):
        raise RuntimeError("The selected frame representation was not active")
    return {
        "candidate": changed,
        "python": sys.version,
        "hash_seed": os.environ.get("PYTHONHASHSEED"),
        "id_base": id_base,
        "gc_enabled": gc.isenabled(),
        "gc_thresholds": gc.get_threshold(),
        "gc_before": before,
        "gc_after": after,
        "native_sha256": hashlib.sha256(Path(native.__file__).read_bytes()).hexdigest(),
        "activation_frame_type": frame_type.__name__,
        "means_ms": {key: statistics.mean(row[key] for row in observations) for key in ("ms", "cpu_ms")},
        "observations": observations,
        "html_digests": digests,
    }


def main() -> None:
    """Retain balanced process comparisons for a representation experiment."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", choices=("reference", "candidate"))
    parser.add_argument("--pairs", type=int, default=8)
    parser.add_argument("--samples", type=int, default=80)
    parser.add_argument("--seed", type=int, default=20260910)
    parser.add_argument("--id-base", type=int, default=123456)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if min(args.pairs, args.samples) < 1:
        parser.error("Pair and sample counts must be positive")
    if args.worker:
        print(json.dumps(worker(args.worker == "candidate", args.samples, args.id_base)))
        return
    if args.output is None:
        parser.error("The parent requires --output")
    checks = equivalence()
    orders = [bool(index % 2) for index in range(args.pairs)]
    random.Random(args.seed).shuffle(orders)  # noqa: S311 - repeatable process order
    pairs = []
    for pair, candidate_first in enumerate(orders):
        variants = {}
        for name in ("candidate", "reference") if candidate_first else ("reference", "candidate"):
            result = subprocess.run(
                [
                    sys.executable,
                    __file__,
                    "--worker",
                    name,
                    "--samples",
                    str(args.samples),
                    "--id-base",
                    str(args.id_base + pair * 10_000_000),
                ],
                cwd=ROOT,
                env={**os.environ, "PYTHONHASHSEED": str(args.seed + pair)},
                capture_output=True,
                text=True,
                check=True,
            )
            variants[name] = json.loads(result.stdout)
        if variants["reference"]["html_digests"] != variants["candidate"]["html_digests"]:
            raise RuntimeError(f"HTML differs in pair {pair}")
        if variants["reference"]["native_sha256"] != variants["candidate"]["native_sha256"]:
            raise RuntimeError("Paired workers loaded different native artifacts")
        savings = {
            key: variants["reference"]["means_ms"][key] - variants["candidate"]["means_ms"][key]
            for key in ("ms", "cpu_ms")
        }
        pairs.append({"pair": pair, "candidate_first": candidate_first, "mean_savings_ms": savings, **variants})
        print(json.dumps({"pair": pair, "mean_savings_ms": savings}), flush=True)
    report = {
        "revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),  # noqa: S607
        "experiment_only": True,
        "order_seed": args.seed,
        "order": "balanced-random",
        "samples_per_process": args.samples,
        "warmups_per_process": 6,
        "equivalence": checks,
        "hashes": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (
                Path(__file__).resolve(),
                Path(renders.__file__),
                Path(components.__file__),
                ROOT / "packages/py/citry/tests/test_benchmark_citry.py",
            )
        },
        "median_process_pair_mean_savings_ms": {
            key: statistics.median(pair["mean_savings_ms"][key] for pair in pairs) for key in ("ms", "cpu_ms")
        },
        "joint_favorable_process_pairs": sum(
            all(value > 0 for value in pair["mean_savings_ms"].values()) for pair in pairs
        ),
        "pairs": pairs,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key != "pairs"}, indent=2))


if __name__ == "__main__":
    main()

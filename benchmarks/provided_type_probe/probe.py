"""Measure reuse of generated provide/inject payload classes by field layout."""

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
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "packages/py/citry"), str(ROOT / "packages/py/citry_core")]

from benchmarks.ownership_journal_probe.probe import scenario  # noqa: E402

import citry.citry_render as renders  # noqa: E402
import citry.component as component_module  # noqa: E402
import citry.component_render as components  # noqa: E402
import citry.provide as provide_module  # noqa: E402
import citry.util.id as ids  # noqa: E402
import citry_core._rust as native  # noqa: E402
from citry import ownership  # noqa: E402
from citry.ownership import OwnershipGraph  # noqa: E402

ORIGINAL = provide_module.make_provided


@lru_cache(maxsize=128)
def payload_type(fields: tuple[str, ...]) -> type:
    """Retain generated classes; edits to those classes can retain application values."""
    return type(ORIGINAL(dict.fromkeys(fields)))


def make_provided(data: dict[str, Any]) -> tuple:
    """Reuse a class for small ordinary mappings; values remain per call."""
    if type(data) is dict and len(data) <= 16 and all(type(key) is str and len(key) <= 128 for key in data):
        return payload_type(tuple(data))(**data)
    return ORIGINAL(data)


def install(changed: bool) -> None:
    """Switch the factory and the alias imported by Component.provide."""
    factory = make_provided if changed else ORIGINAL
    provide_module.make_provided = factory
    component_module.make_provided = factory


def capture_counts(module: Any, data: Any) -> dict[str, Any]:
    """Count class reuse during one separate untimed render."""
    before = payload_type.cache_info()
    module.render(data)
    after = payload_type.cache_info()
    if after.hits <= before.hits or after.currsize > 128:
        raise RuntimeError("The provided-payload class cache was inactive or exceeded its entry bound")
    return {"hits": after.hits - before.hits, "misses": after.misses - before.misses, "entries": after.currsize}


def equivalence() -> dict[str, Any]:
    """Compare every reached ownership snapshot and the fixture HTML."""
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
            raise RuntimeError("Provided-payload reuse changed fixture HTML or ownership snapshots")
    finally:
        OwnershipGraph.snapshot = original_snapshot
        install(changed=False)
    install(changed=True)
    try:
        activation = capture_counts(module, data)
    finally:
        install(changed=False)
    return {
        "snapshots_compared": len(traces[0]),
        "snapshots_equal": True,
        "html_equal": True,
        "activation": activation,
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
    activation = capture_counts(module, data) if changed else None
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
        "activation": activation,
        "means_ms": {key: statistics.mean(row[key] for row in observations) for key in ("ms", "cpu_ms")},
        "observations": observations,
        "html_digests": digests,
    }


def main() -> None:
    """Retain balanced process comparisons for generated payload classes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", choices=("reference", "candidate"))
    parser.add_argument("--pairs", type=int, default=8)
    parser.add_argument("--samples", type=int, default=80)
    parser.add_argument("--seed", type=int, default=20260914)
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
                Path(ownership.__file__),
                Path(provide_module.__file__),
                Path(component_module.__file__),
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

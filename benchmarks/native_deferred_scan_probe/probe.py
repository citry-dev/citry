"""Measure the native deferred scan against the ordinary Python loop."""

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
import types
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "packages/py/citry"), str(ROOT / "packages/py/citry_core")]

from benchmarks.native_deferred_scan_probe.adapter import ARTIFACT, NATIVE, ORIGINAL, install, scan  # noqa: E402
from benchmarks.ownership_journal_probe.storage_probe import TABLES  # noqa: E402
from benchmarks.utils import get_benchmark_script  # noqa: E402

import citry.citry_render as renders  # noqa: E402
import citry.component_render as components  # noqa: E402
import citry.util.id as ids  # noqa: E402
import citry_core._rust as native  # noqa: E402
from citry import (  # noqa: E402
    attrs,
    nodes,
    ownership,
)
from citry.ownership import OwnershipGraph  # noqa: E402

PROBE_ROOT = ROOT / "benchmarks/ownership_journal_probe"
PROBE_ARTIFACT = ARTIFACT


def scenario(size: str = "lg") -> types.ModuleType:
    """Load the existing fixture without executing its pytest wrapper."""
    suffix = "_small" if size == "sm" else ""
    path = ROOT / "packages/py/citry/tests" / f"test_benchmark_citry{suffix}.py"
    module = types.ModuleType("runtime_ownership_scenario")
    module.__file__ = str(path)
    sys.modules[module.__name__] = module
    exec(compile(get_benchmark_script(path), str(path), "exec"), module.__dict__)  # noqa: S102
    return module


def capture_counts(module: Any, data: Any, *, changed: bool) -> dict[str, Any]:
    """Verify the intended containers during one separate untimed render."""
    original_snapshot = OwnershipGraph.snapshot
    tables = []

    def snapshot(graph: Any) -> Any:
        tables.append(
            {
                "nested_invocations": len(graph._component_invocations),
                "types": {
                    name: type(getattr(graph, name)).__name__
                    for name in (*TABLES, "_component_invocations", "_render_queue")
                },
            }
        )
        return original_snapshot(graph)

    OwnershipGraph.snapshot = snapshot
    try:
        module.render(data)
    finally:
        OwnershipGraph.snapshot = original_snapshot
    if not tables:
        raise RuntimeError("The activation check captured no snapshots")
    for table in tables:
        for name, actual in table["types"].items():
            native_expected = table["nested_invocations"] > 0
            expected = ("RecordTable" if name in TABLES else "_JournalRecords") if native_expected else "list"
            if actual != expected:
                raise RuntimeError(f"Unexpected {name} storage: {actual}, expected {expected}")
    expected = scan if changed else ORIGINAL
    if components._scan_deferred is not expected:
        raise RuntimeError("The intended deferred scanner is not active")
    counts = {"native": 0, "fallback": 0}
    original_native = NATIVE.scan

    def counted(items: Any, module: Any) -> Any:
        result = original_native(items, module)
        counts["fallback" if result is None else "native"] += 1
        return result

    NATIVE.scan = counted
    try:
        module.render(data)
    finally:
        NATIVE.scan = original_native
    if changed and not counts["native"]:
        raise RuntimeError("The candidate did not execute the native scanner")
    return {"snapshot_table_types": tables, "scan_calls": counts}


def equivalence(size: str = "lg") -> dict[str, Any]:
    """Compare every reached ownership snapshot and the fixture HTML."""
    module = scenario(size)
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
            raise RuntimeError("Native deferred scanning changed fixture HTML or ownership snapshots")
    finally:
        OwnershipGraph.snapshot = original_snapshot
        install(changed=False)
    install(changed=True)
    try:
        activation = capture_counts(module, data, changed=changed)
    finally:
        install(changed=False)
    return {
        "snapshots_compared": len(traces[0]),
        "snapshots_equal": True,
        "html_equal": True,
        "activation": activation,
    }


def worker(changed: bool, samples: int, id_base: int, size: str) -> dict[str, Any]:
    """Include all complete renders and their GC costs on one private heap."""
    ids._id_base = id_base
    ids._id_counter = itertools.count()
    install(changed)
    module = scenario(size)
    data = module.gen_render_data()
    warmups = []
    for _ in range(6):
        cpu_start = time.process_time_ns()
        start = time.perf_counter_ns()
        output = module.render(data)
        end = time.perf_counter_ns()
        cpu_end = time.process_time_ns()
        warmups.append(
            {
                "ms": (end - start) / 1_000_000,
                "cpu_ms": (cpu_end - cpu_start) / 1_000_000,
                "html_digest": hashlib.sha256(output.encode()).hexdigest(),
            }
        )
        del output
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
    activation = capture_counts(module, data, changed=changed)
    return {
        "candidate": changed,
        "size": size,
        "warmups": warmups,
        "python": sys.version,
        "hash_seed": os.environ.get("PYTHONHASHSEED"),
        "id_base": id_base,
        "gc_enabled": gc.isenabled(),
        "gc_thresholds": gc.get_threshold(),
        "gc_before": before,
        "gc_after": after,
        "native_sha256": hashlib.sha256(Path(native.__file__).read_bytes()).hexdigest(),
        "probe_native_sha256": hashlib.sha256(PROBE_ARTIFACT.read_bytes()).hexdigest(),
        "activation": activation,
        "means_ms": {key: statistics.mean(row[key] for row in observations) for key in ("ms", "cpu_ms")},
        "observations": observations,
        "html_digests": digests,
    }


def main() -> None:
    """Retain balanced process comparisons for native deferred scanning."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", choices=("sm", "lg"), default="lg")
    parser.add_argument("--worker", choices=("reference", "candidate"))
    parser.add_argument("--pairs", type=int, default=8)
    parser.add_argument("--samples", type=int, default=80)
    parser.add_argument("--seed", type=int, default=20260926)
    parser.add_argument("--id-base", type=int, default=123456)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if min(args.pairs, args.samples) < 1:
        parser.error("Pair and sample counts must be positive")
    if args.worker:
        print(json.dumps(worker(args.worker == "candidate", args.samples, args.id_base, args.size)))
        return
    if args.output is None:
        parser.error("The parent requires --output")
    checks = equivalence(args.size)
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
                    "--size",
                    args.size,
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
        if variants["reference"]["probe_native_sha256"] != variants["candidate"]["probe_native_sha256"]:
            raise RuntimeError("Paired workers loaded different native artifacts")
        if [row["html_digest"] for row in variants["reference"]["warmups"]] != [
            row["html_digest"] for row in variants["candidate"]["warmups"]
        ]:
            raise RuntimeError(f"Warmup HTML differs in pair {pair}")
        savings = {
            key: variants["reference"]["means_ms"][key] - variants["candidate"]["means_ms"][key]
            for key in ("ms", "cpu_ms")
        }
        pairs.append({"pair": pair, "candidate_first": candidate_first, "mean_savings_ms": savings, **variants})
        print(json.dumps({"pair": pair, "mean_savings_ms": savings}), flush=True)
    report = {
        "revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),  # noqa: S607
        "experiment_only": True,
        "size": args.size,
        "experiment": "discover current deferred tasks in one native traversal",
        "order_seed": args.seed,
        "order": "balanced-random",
        "samples_per_process": args.samples,
        "warmups_per_process": 6,
        "equivalence": checks,
        "hashes": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (
                Path(__file__).resolve(),
                Path(__file__).with_name("adapter.py"),
                Path(__file__).with_name("plan.md"),
                Path(__file__).with_name("check.py"),
                Path(__file__).with_name("Cargo.toml"),
                Path(__file__).with_name("Cargo.lock"),
                Path(__file__).with_name("build.rs"),
                Path(__file__).parent / "src/lib.rs",
                Path(attrs.__file__),
                Path(nodes.__file__),
                Path(renders.__file__),
                Path(components.__file__),
                Path(ownership.__file__),
                PROBE_ARTIFACT,
                PROBE_ROOT / "probe.py",
                PROBE_ROOT / "storage_probe.py",
                ROOT / "crates/citry_core_py/Cargo.toml",
                ROOT / "crates/citry_core_py/src/lib.rs",
                *sorted((ROOT / "crates/citry_core_py/src/ownership").glob("*.rs")),
                ROOT / "packages/py/citry_core/citry_core/_rust.pyi",
                ROOT / "packages/py/citry_core/citry_core/_ownership.py",
                ROOT / "packages/py/citry_core/pyproject.toml",
                ROOT / "crates/citry_ownership/Cargo.toml",
                ROOT / "crates/citry_ownership/src/lib.rs",
                ROOT / "Cargo.toml",
                ROOT / "Cargo.lock",
                ROOT / "packages/py/citry/tests/test_benchmark_citry.py",
                ROOT / "packages/py/citry/tests/test_benchmark_citry_small.py",
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

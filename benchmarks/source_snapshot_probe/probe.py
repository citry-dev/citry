"""Measure immutable source fields through internal manifest reads."""

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
from dataclasses import replace
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "packages/py/citry"), str(ROOT / "packages/py/citry_core")]

from benchmarks.ownership_module_probe.probe import canonical, digest  # noqa: E402
from benchmarks.source_snapshot_probe import adapter  # noqa: E402
from benchmarks.source_snapshot_probe.adapter import install  # noqa: E402
from benchmarks.utils import get_benchmark_script  # noqa: E402

import citry.citry_render as renders  # noqa: E402
import citry.component_render as components  # noqa: E402
import citry.util.id as ids  # noqa: E402
import citry_core._rust as native  # noqa: E402
from citry import attrs, nodes, ownership  # noqa: E402
from citry.ownership import OwnershipGraph  # noqa: E402
from citry_core import _ownership  # noqa: E402

PROBE_ROOT = ROOT / "benchmarks/ownership_journal_probe"
PROBE_ARTIFACT = adapter.ARTIFACT
NATIVE = _ownership


def scenario(size: str = "lg", mode: str = "production") -> types.ModuleType:
    """Load the existing fixture without executing its pytest wrapper."""
    suffix = "_small" if size == "sm" else ""
    path = ROOT / "packages/py/citry/tests" / f"test_benchmark_citry{suffix}.py"
    module = types.ModuleType("runtime_ownership_scenario")
    module.__file__ = str(path)
    sys.modules[module.__name__] = module
    source = get_benchmark_script(path)
    if mode == "development":
        if source.count("app = Citry()") != 1:
            raise RuntimeError("Cannot select development fixture")
        source = source.replace("app = Citry()", 'app = Citry(mode="development")')
    exec(compile(source, str(path), "exec"), module.__dict__)  # noqa: S102
    return module


def capture_counts(module: Any, data: Any, *, changed: bool) -> dict[str, Any]:
    """Capture internal reads, materializations and complete snapshot contents."""
    original_snapshot = OwnershipGraph.snapshot
    traces, tables = [], []
    exports = 0
    original_getitem = adapter.SourceView.__getitem__
    ids._id_counter = itertools.count()

    def getitem(view: Any, index: Any) -> Any:
        nonlocal exports
        before = len(view.cache)
        result = original_getitem(view, index)
        exports += len(view.cache) - before
        return result

    def capture(graph: Any, result: Any) -> Any:
        table = graph._source_locations
        expected_table = adapter.SourceTable if changed else list
        expected_sources = adapter.SourceView if changed else tuple
        if type(table) is not expected_table or type(result.source_locations) is not expected_sources:
            raise RuntimeError("Unexpected source storage or snapshot view in fixture")
        if len(table) != 1081:
            raise RuntimeError("Unexpected source occurrence count in fixture")
        tables.append(
            {
                "type": type(table).__name__,
                "rows": len(table),
                "native_exported": table.export_count() if type(table) is adapter.SourceTable else None,
            }
        )
        traces.append(result)
        return result

    def public(graph: Any) -> Any:
        return capture(graph, original_snapshot(graph))

    def internal(graph: Any) -> Any:
        return capture(graph, adapter.internal_snapshot(graph))

    if changed:
        for owner in (adapter.ownership_manifest, adapter.emission):
            owner._probe_internal_snapshot = internal
        adapter.SourceView.__getitem__ = getitem
    else:
        OwnershipGraph.snapshot = public
    try:
        output = module.render(data)
    finally:
        OwnershipGraph.snapshot = original_snapshot
        adapter.SourceView.__getitem__ = original_getitem
        for owner in (adapter.ownership_manifest, adapter.emission):
            owner._probe_internal_snapshot = adapter.internal_snapshot
    if len(traces) != 4:
        raise RuntimeError(f"Expected four complete reads, got {len(traces)}")
    snapshots = [
        digest(canonical(replace(result, source_locations=tuple(result.source_locations)))) for result in traces
    ]
    return {
        "source_tables": tables,
        "source_view_exports": exports,
        "snapshot_digests": snapshots,
        "html_digest": hashlib.sha256(output.encode()).hexdigest(),
    }


def equivalence(size: str = "lg") -> dict[str, Any]:
    """Compare public values after internal field snapshots in both modes."""
    results = {}
    for mode in ("production", "development"):
        variants = []
        for changed in (False, True):
            install(changed)
            module = scenario(size, mode)
            data = module.gen_render_data()
            for _ in range(6):
                module.render(data)
            variants.append(capture_counts(module, data, changed=changed))
        for key in ("snapshot_digests", "html_digest"):
            if variants[0][key] != variants[1][key]:
                raise RuntimeError(f"{mode} differs: {key}")
        results[mode] = {"equal": True, "reference": variants[0], "candidate": variants[1]}
    install(changed=False)
    return results


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
    """Retain balanced process comparisons for source-occurrence storage."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", choices=("sm", "lg"), default="lg")
    parser.add_argument("--worker", choices=("reference", "candidate"))
    parser.add_argument("--pairs", type=int, default=8)
    parser.add_argument("--samples", type=int, default=80)
    parser.add_argument("--seed", type=int, default=20261013)
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
        for key in ("snapshot_digests", "html_digest"):
            if variants["reference"]["activation"][key] != variants["candidate"]["activation"][key]:
                raise RuntimeError(f"Paired activation {key} differs")
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
        "experiment": "retain immutable source fields through internal manifest snapshots",
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
                Path(__file__).with_name("counterexamples.py"),
                ROOT / "benchmarks/source_record_storage_probe/check.py",
                ROOT / "benchmarks/source_record_storage_probe/adapter.py",
                Path(__file__).with_name("Cargo.toml"),
                Path(__file__).with_name("Cargo.lock"),
                Path(__file__).with_name("build.rs"),
                Path(__file__).parent / "src/lib.rs",
                Path(adapter.ownership_manifest.__file__),
                Path(adapter.serialize.__file__),
                Path(adapter.emission.__file__),
                Path(adapter.extension.__file__),
                Path(native.__file__),
                ROOT / "benchmarks/ownership_module_probe/probe.py",
                ROOT / "benchmarks/ownership_module_probe/adapter.py",
                Path(attrs.__file__),
                Path(nodes.__file__),
                ROOT / "packages/py/citry/citry/extension.py",
                Path(renders.__file__),
                Path(components.__file__),
                Path(ownership.__file__),
                PROBE_ARTIFACT,
                PROBE_ROOT / "probe.py",
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

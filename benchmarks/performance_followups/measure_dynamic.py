"""Measure the dynamic HTML candidate against the released simple benchmark."""

from __future__ import annotations

# ruff: noqa: S101 - imported qualification module refuses optimized Python.
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
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from benchmarks.performance_followups.dynamic_element import install  # noqa: E402
from benchmarks.performance_followups.presentation import (  # noqa: E402
    baseline,
    callback_counts,
    load,
)


def worker(variant: str, samples: int, qualification: dict[str, Any]) -> dict[str, Any]:
    """Retain every timed output, then check content and callbacks outside timing."""
    if variant == "django":
        return baseline.worker("django", samples)
    expected = qualification[variant]
    if variant == "candidate":
        install()
    module, tree_hash = load()
    assert tree_hash == qualification["scenario_sha256"]
    data = module.gen_render_data()
    baseline.ids._id_base = 123456
    rows, outputs = [], []
    for index in range(6 + samples):
        if index == 6:
            before = gc.get_stats()
        baseline.ids._id_counter = itertools.count(index * 1_000_000)
        cpu = time.process_time_ns()
        wall = time.perf_counter_ns()
        output = module.render(data)
        end_wall = time.perf_counter_ns()
        end_cpu = time.process_time_ns()
        rows.append({"ms": (end_wall - wall) / 1e6, "cpu_ms": (end_cpu - cpu) / 1e6})
        outputs.append(output)
    after = gc.get_stats()
    observed, names = baseline.observe(module, data)
    assert observed["snapshot_counts"] == expected["snapshot_counts"]
    assert manifest_counts(observed["manifests"]) == manifest_counts(expected["manifests"])
    assert observed["generated_ids"] == expected["generated_ids"]
    assert observed["component_calls"] == expected["component_calls"]
    assert callback_counts(module) == qualification["callbacks"]
    projected_hashes = []
    for index, output in enumerate(outputs):
        shifted, _ = baseline.shifted_names(names, set(), index * 1_000_000)
        projected, manifests = baseline.content_projection(output, shifted)
        assert manifest_counts(manifests) == manifest_counts(expected["manifests"])
        projected_hashes.append(hashlib.sha256(projected.encode()).hexdigest())
    assert set(projected_hashes) == {qualification["control"]["projected_sha256"]}
    raw_hashes = [hashlib.sha256(output.encode()).hexdigest() for output in outputs]
    assert len(set(raw_hashes)) == len(outputs)
    return {
        "variant": variant,
        "python": sys.version,
        "scenario_ast_sha256": tree_hash,
        "native_sha256": hashlib.sha256(Path(baseline.native.__file__).read_bytes()).hexdigest(),
        "gc_enabled": gc.isenabled(),
        "gc_before": before,
        "gc_after": after,
        "initial_renders": rows[:6],
        "warm_renders": rows[6:],
        "mean_warm_ms": {key: statistics.mean(r[key] for r in rows[6:]) for key in ("ms", "cpu_ms")},
        "output_bytes": [len(output.encode()) for output in outputs],
        "raw_sha256": raw_hashes,
        "projected_sha256": projected_hashes,
        "activation": observed,
    }


def manifest_counts(manifests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Count every manifest and each graph record collection, so omissions fail."""
    return [
        {
            "delimiters": len(manifest["delimiters"]),
            "graphs": [
                {name: len(value) for name, value in graph.items() if isinstance(value, list)}
                for graph in manifest["graphs"]
            ],
        }
        for manifest in manifests
    ]


def source_hashes(qualification_path: Path) -> dict[str, str]:
    """Bind results to the runtime, native build, fixture and measurement helpers."""
    paths = [Path(__file__).with_name("plan.md"), qualification_path.resolve()]
    for directory in ("packages/py/citry/citry", "packages/py/citry_core/citry_core", "benchmarks"):
        paths.extend((ROOT / directory).rglob("*.py"))
    paths.extend(
        [
            Path(baseline.native.__file__),
            ROOT / "packages/py/citry/tests/test_benchmark_citry.py",
            ROOT / "packages/py/citry/tests/test_benchmark_django.py",
        ]
    )
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", choices=("control", "candidate", "django"))
    parser.add_argument("--samples", type=int, default=80)
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    qualification = json.loads(args.qualification.read_text())
    if args.worker:
        print(json.dumps(worker(args.worker, args.samples, qualification)))
        return
    if args.output is None:
        parser.error("--output is required for a complete measurement")
    before = source_hashes(args.qualification)
    blocks = []
    orders = list(itertools.permutations(("control", "candidate", "django")))
    random.Random(20260910).shuffle(orders)  # noqa: S311 - reproducible balanced process order
    for index, order in enumerate(orders):
        variants = {}
        for variant in order:
            result = subprocess.check_output(
                [
                    sys.executable,
                    __file__,
                    "--worker",
                    variant,
                    "--samples",
                    str(args.samples),
                    "--qualification",
                    str(args.qualification.resolve()),
                ],
                text=True,
                cwd=ROOT,
                env={**os.environ, "PYTHONHASHSEED": str(20260910 + index)},
            )
            variants[variant] = json.loads(result)
        native_hash = before[str(Path(baseline.native.__file__).relative_to(ROOT))]
        assert {v["native_sha256"] for v in variants.values()} == {native_hash}
        blocks.append({"order": order, "hash_seed": 20260910 + index, "variants": variants})
        print(f"Completed block {len(blocks)}/6", file=sys.stderr, flush=True)
    assert source_hashes(args.qualification) == before, "Measured sources changed"
    means = {
        name: {
            key: statistics.mean(b["variants"][name]["mean_warm_ms"][key] for b in blocks) for key in ("ms", "cpu_ms")
        }
        for name in ("control", "candidate", "django")
    }
    savings = {}
    for key in ("ms", "cpu_ms"):
        deltas = [
            b["variants"]["control"]["mean_warm_ms"][key] - b["variants"]["candidate"]["mean_warm_ms"][key]
            for b in blocks
        ]
        mean = statistics.mean(deltas)
        margin = 2.571 * statistics.stdev(deltas) / len(deltas) ** 0.5
        savings[key] = {
            "block_deltas": deltas,
            "mean": mean,
            "paired_95_percent_interval": [mean - margin, mean + margin],
            "percent": 100 * mean / means["control"][key],
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            {
                "source_hashes": before,
                "qualification": qualification,
                "means": means,
                "savings": savings,
                "blocks": blocks,
            }
        )
        + "\n"
    )


if __name__ == "__main__":
    main()

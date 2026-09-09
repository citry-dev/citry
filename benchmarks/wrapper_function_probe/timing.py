"""Measure the fixed Button function against ordinary complete-page rendering."""

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
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "packages/py/citry"), str(ROOT / "packages/py/citry_core")]

from benchmarks.inline_leaf_probe.checks import shifted_names  # noqa: E402
from benchmarks.ownership_journal_probe.probe import scenario  # noqa: E402
from benchmarks.render_structure_probe.census import digest  # noqa: E402
from benchmarks.wrapper_function_probe.adapter import installed  # noqa: E402
from benchmarks.wrapper_function_probe.probe import content_projection, observe  # noqa: E402

import citry.util.id as ids  # noqa: E402
import citry_core._rust as native  # noqa: E402


def worker(variant: str, samples: int) -> dict[str, Any]:
    module = scenario()
    data = module.gen_render_data()
    enabled = variant == "candidate"
    ids._id_base = 123456
    rows, outputs = [], []
    with installed(module, enabled):
        for index in range(6 + samples):
            if index == 6:
                before = gc.get_stats()
            ids._id_counter = itertools.count(index * 1_000_000)
            cpu_start = time.process_time_ns()
            start = time.perf_counter_ns()
            output = module.render(data)
            end = time.perf_counter_ns()
            cpu_end = time.process_time_ns()
            rows.append({"ms": (end - start) / 1e6, "cpu_ms": (cpu_end - cpu_start) / 1e6})
            outputs.append(output)
        after = gc.get_stats()
    observation = observe(module, lambda: module.render(data), enabled)
    if observation["generated_ids"] != (228 if enabled else 342):
        raise AssertionError("Unexpected identity count")
    if observation["candidate_counts"] != ({"callbacks": 114, "outlets": 114} if enabled else {}):
        raise AssertionError("Unexpected wrapper activation")
    expected_counts = {
        "source_locations": 641 if enabled else 1081,
        "component_invocations": 225 if enabled else 339,
        "logical_instances": 228 if enabled else 342,
        "init_ancestry": 225 if enabled else 339,
        "logical_fills": 256 if enabled else 468,
        "physical_regions": 160 if enabled else 274,
        "render_queue": 225 if enabled else 339,
    }
    if observation["snapshot_counts"] != [expected_counts] * 4:
        raise AssertionError("Unexpected full-page graph counts")
    projected_digests, raw_digests = [], []
    for index, output in enumerate(outputs):
        names, _ = shifted_names(observation["names"], set(), index * 1_000_000)
        projected_digests.append(digest(content_projection(output, names)[0]))
        raw_digests.append(hashlib.sha256(output.encode()).hexdigest())
    if set(projected_digests) != {observation["projected_digest"]} or len(set(raw_digests)) != 6 + samples:
        raise AssertionError("Timed output changed or render IDs did not change")
    return {
        "variant": variant,
        "python": sys.version,
        "gc_enabled": gc.isenabled(),
        "gc_before": before,
        "gc_after": after,
        "native_sha256": hashlib.sha256(Path(native.__file__).read_bytes()).hexdigest(),
        "initial_renders": rows[:6],
        "warm_renders": rows[6:],
        "mean_warm_ms": {key: statistics.mean(row[key] for row in rows[6:]) for key in ("ms", "cpu_ms")},
        "raw_digests": raw_digests,
        "projected_digests": projected_digests,
        "activation": {
            key: observation[key]
            for key in (
                "generated_ids",
                "component_calls",
                "candidate_counts",
                "snapshot_counts",
                "browser_graph_counts",
                "bytes",
            )
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", choices=("reference", "candidate"))
    parser.add_argument("--samples", type=int, default=80)
    parser.add_argument("--blocks", type=int, default=8)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if min(args.samples, args.blocks) < 1:
        parser.error("Sample and block counts must be positive")
    if args.worker:
        print(json.dumps(worker(args.worker, args.samples)))
        return
    if args.output is None:
        parser.error("--output is required for the parent")
    paths = [*sorted(Path(__file__).parent.glob("*.py")), Path(__file__).with_name("plan.md")]
    paths.extend(
        ROOT / path
        for path in (
            "benchmarks/leaf_contract_probe/adapter.py",
            "benchmarks/template_function_probe/runtime.py",
            "benchmarks/inline_leaf_probe/checks.py",
            "benchmarks/render_structure_probe/census.py",
            "benchmarks/ownership_journal_probe/probe.py",
            "benchmarks/utils.py",
            "packages/py/citry/tests/test_benchmark_citry.py",
        )
    )
    paths.extend(sorted((ROOT / "packages/py/citry/citry").rglob("*.py")))
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    orders = [("reference", "candidate"), ("candidate", "reference")] * 4
    random.Random(20261101).shuffle(orders)  # noqa: S311 - reproducible pair order
    blocks = []
    for index in range(args.blocks):
        order = orders[index % len(orders)]
        variants = {}
        for variant in order:
            result = subprocess.run(
                [sys.executable, __file__, "--worker", variant, "--samples", str(args.samples)],
                cwd=ROOT,
                env={**os.environ, "PYTHONHASHSEED": str(20261101 + index)},
                capture_output=True,
                text=True,
                check=True,
            )
            variants[variant] = json.loads(result.stdout)
        reference, candidate = variants["reference"], variants["candidate"]
        if reference["projected_digests"] != candidate["projected_digests"]:
            raise AssertionError("Application HTML differs between variants")
        if reference["native_sha256"] != candidate["native_sha256"]:
            raise AssertionError("Native artifacts differ between variants")
        expected_calls = dict(reference["activation"]["component_calls"])
        if expected_calls.pop("Button") != 114 or expected_calls != candidate["activation"]["component_calls"]:
            raise AssertionError("Nonselected component execution changed")
        savings = {key: reference["mean_warm_ms"][key] - candidate["mean_warm_ms"][key] for key in ("ms", "cpu_ms")}
        blocks.append({"order": order, "variants": variants, "saving_ms": savings})
        print(json.dumps({"block": index, "saving_ms": savings}), flush=True)
    for path, expected in hashes.items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
            raise AssertionError(f"Source changed during timing: {path}")
    summary = {
        "median_paired_warm_saving_ms": {
            key: statistics.median(b["saving_ms"][key] for b in blocks) for key in ("ms", "cpu_ms")
        },
        "joint_wins": sum(all(value > 0 for value in b["saving_ms"].values()) for b in blocks),
        "median_paired_warm_ratio": statistics.median(
            b["variants"]["candidate"]["mean_warm_ms"]["ms"] / b["variants"]["reference"]["mean_warm_ms"]["ms"]
            for b in blocks
        ),
        "median_paired_second_saving_ms": statistics.median(
            b["variants"]["reference"]["initial_renders"][1]["ms"]
            - b["variants"]["candidate"]["initial_renders"][1]["ms"]
            for b in blocks
        ),
    }
    args.output.write_text(
        json.dumps(
            {
                "experiment_only": True,
                "retains_all_timed_outputs": True,
                "graph_equality_not_claimed": True,
                "hashes": hashes,
                "summary": summary,
                "blocks": blocks,
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps(summary))


if __name__ == "__main__":
    main()

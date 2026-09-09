"""Measure composed caller-owned templates with immediate or deferred execution."""

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

from benchmarks.composed_function_probe.adapter import installed  # noqa: E402
from benchmarks.composed_function_probe.probe import content_projection, normalized_snapshots, observe  # noqa: E402
from benchmarks.inline_leaf_probe.checks import shifted_names  # noqa: E402
from benchmarks.ownership_journal_probe.probe import scenario  # noqa: E402
from benchmarks.render_structure_probe.census import digest  # noqa: E402

import citry.util.id as ids  # noqa: E402
import citry_core._rust as native  # noqa: E402


def worker(variant: str, samples: int) -> dict[str, Any]:
    module = scenario()
    data = module.gen_render_data()
    ids._id_base = 123456
    rows, outputs = [], []
    with installed(module, variant):
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
    observation = observe(module, lambda: module.render(data), variant)
    expected_functions = {"Button": 114, "Icon": 40, "HeroIcon": 41, "outlets": 154, "svg_replays": 32}
    if observation["candidate_counts"] != (
        expected_functions
        if variant in ("immediate", "deferred")
        else {"callbacks": 114, "outlets": 114}
        if variant == "button"
        else {}
    ):
        raise AssertionError("Unexpected function activation")
    expected_vector = {
        "reference": (1081, 339, 342, 339, 468, 274, 339),
        "button": (641, 225, 228, 225, 256, 160, 225),
        "immediate": (470, 144, 147, 144, 206, 120, 144),
        "deferred": (470, 144, 147, 144, 206, 120, 144),
    }[variant]
    fields = (
        "source_locations",
        "component_invocations",
        "logical_instances",
        "init_ancestry",
        "logical_fills",
        "physical_regions",
        "render_queue",
    )
    if observation["snapshot_counts"] != [dict(zip(fields, expected_vector, strict=True))] * 4:
        raise AssertionError("Unexpected full-page graph counts")
    if observation["generated_ids"] != expected_vector[2]:
        raise AssertionError("Unexpected generated IDs")
    scheduled = {"Button": 114, "Icon": 40, "HeroIcon": 41} if variant == "deferred" else {}
    if observation["scheduled_functions"] != scheduled:
        raise AssertionError("Unexpected scheduled function counts")
    projected_digests, raw_digests = [], []
    for index, output in enumerate(outputs):
        names, _ = shifted_names(observation["names"], set(), index * 1_000_000)
        projected_digests.append(digest(content_projection(output, names)[0]))
        raw_digests.append(hashlib.sha256(output.encode()).hexdigest())
    if set(projected_digests) != {observation["projected_digest"]} or len(set(raw_digests)) != 6 + samples:
        raise AssertionError("Timed output changed or render IDs did not change")
    return {
        "variant": variant,
        "normalized_snapshot_digest": digest(normalized_snapshots(observation)),
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
                "scheduled_functions",
                "snapshot_counts",
                "browser_graph_counts",
                "bytes",
            )
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", choices=("reference", "button", "immediate", "deferred"))
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
            "benchmarks/wrapper_function_probe/adapter.py",
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
    variants_list = ("reference", "button", "immediate", "deferred")
    cyclic = [variants_list[index:] + variants_list[:index] for index in range(4)]
    orders = cyclic + [tuple(reversed(order)) for order in cyclic]
    random.Random(20261102).shuffle(orders)  # noqa: S311 - reproducible pair order
    blocks = []
    for index in range(args.blocks):
        order = orders[index % len(orders)]
        variants = {}
        for variant in order:
            result = subprocess.run(
                [sys.executable, __file__, "--worker", variant, "--samples", str(args.samples)],
                cwd=ROOT,
                env={**os.environ, "PYTHONHASHSEED": str(20261102 + index)},
                capture_output=True,
                text=True,
                check=True,
            )
            variants[variant] = json.loads(result.stdout)
        reference = variants["reference"]
        for name, candidate in variants.items():
            if reference["projected_digests"] != candidate["projected_digests"]:
                raise AssertionError("Application HTML differs between variants")
            if reference["native_sha256"] != candidate["native_sha256"]:
                raise AssertionError("Native artifacts differ between variants")
            expected_calls = dict(reference["activation"]["component_calls"])
            removed = (
                {"Button": 114, "Icon": 40, "HeroIcon": 41}
                if name in ("immediate", "deferred")
                else {"Button": 114}
                if name == "button"
                else {}
            )
            for cls, count in removed.items():
                expected_calls[cls] -= count
                if expected_calls[cls] == 0:
                    del expected_calls[cls]
            if expected_calls != candidate["activation"]["component_calls"]:
                raise AssertionError("Unexpected ordinary component execution counts")
        if variants["immediate"]["normalized_snapshot_digest"] != variants["deferred"]["normalized_snapshot_digest"]:
            raise AssertionError("Composed scheduling variants differ in observed ownership snapshots")
        contrasts = (
            ("reference", "immediate"),
            ("reference", "deferred"),
            ("button", "immediate"),
            ("deferred", "immediate"),
        )
        savings = {
            f"{before}_to_{after}": {
                key: variants[before]["mean_warm_ms"][key] - variants[after]["mean_warm_ms"][key]
                for key in ("ms", "cpu_ms")
            }
            for before, after in contrasts
        }
        blocks.append({"order": order, "variants": variants, "savings_ms": savings})
        print(json.dumps({"block": index, "savings_ms": savings}), flush=True)
    for path, expected in hashes.items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
            raise AssertionError(f"Source changed during timing: {path}")
    summary = {
        f"{before}_to_{after}": {
            "median_paired_warm_saving_ms": {
                key: statistics.median(b["savings_ms"][f"{before}_to_{after}"][key] for b in blocks)
                for key in ("ms", "cpu_ms")
            },
            "joint_wins": sum(
                all(value > 0 for value in b["savings_ms"][f"{before}_to_{after}"].values()) for b in blocks
            ),
            "median_paired_warm_ratio": statistics.median(
                b["variants"][after]["mean_warm_ms"]["ms"] / b["variants"][before]["mean_warm_ms"]["ms"]
                for b in blocks
            ),
            "median_paired_second_saving_ms": statistics.median(
                b["variants"][before]["initial_renders"][1]["ms"] - b["variants"][after]["initial_renders"][1]["ms"]
                for b in blocks
            ),
        }
        for before, after in contrasts
    }
    args.output.write_text(
        json.dumps(
            {
                "experiment_only": True,
                "retains_all_timed_outputs": True,
                "graph_equality_claimed_only_between_composed_variants": True,
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

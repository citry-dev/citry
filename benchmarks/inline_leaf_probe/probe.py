"""Compare complete renders with selected icon functions or ordinary components."""

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
sys.path.insert(0, str(ROOT))

from benchmarks.inline_leaf_probe import adapter, checks, compare  # noqa: E402
from benchmarks.ownership_journal_probe.probe import scenario  # noqa: E402
from benchmarks.render_structure_probe.census import digest  # noqa: E402


def worker(variant: str, samples: int, id_base: int) -> dict[str, Any]:
    """Retain output strings so all projection and validation happen after timing."""
    import citry.util.id as ids  # noqa: PLC0415
    import citry_core._rust as native  # noqa: PLC0415

    module = scenario()
    data = module.gen_render_data()
    ids._id_base = id_base
    rows, outputs = [], []
    before = None
    with checks.installed(module, variant):
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
        observation = checks.observe(module, lambda: module.render(data))
    counts = observation["counts"]
    identities = 0 if variant == "inline" else 41
    if (
        counts.get("selected_calls") != 41
        or counts["selected_identities"] != identities
        or counts["selected_invocations"] != identities
        or counts.get("selected_frames_with_id", 0) != identities
        or counts.get("selected_initializations", 0) != (41 if variant == "reference" else 0)
        or counts["generated_ids"] != (301 if variant == "inline" else 342)
    ):
        raise RuntimeError(f"Unexpected inline activation: {counts}")
    raw_digests, normalized_digests = [], []
    for index, output in enumerate(outputs):
        names, selected = checks.shifted_names(observation["names"], observation["selected"], index * 1_000_000)
        raw_digests.append(hashlib.sha256(output.encode()).hexdigest())
        normalized_digests.append(digest(compare.html(output, names, selected)))
    expected = digest(observation["html"])
    if any(value != expected for value in normalized_digests):
        raise RuntimeError("Timed output differs from the independently observed projected output")
    return {
        "variant": variant,
        "python": sys.version,
        "gc_enabled": gc.isenabled(),
        "gc_before": before,
        "gc_after": after,
        "native_sha256": hashlib.sha256(Path(native.__file__).read_bytes()).hexdigest(),
        "warmups": rows[:6],
        "observations": rows[6:],
        "raw_html_digests": raw_digests,
        "html_digests": normalized_digests,
        "activation": checks.summary(observation),
        "means_ms": {key: statistics.mean(row[key] for row in rows[6:]) for key in ("ms", "cpu_ms")},
    }


VARIANTS = ("reference", "identity", "inline")


def main() -> None:
    """Keep all variants in every block and compare the declared candidate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", choices=VARIANTS)
    parser.add_argument("--samples", type=int, default=80)
    parser.add_argument("--blocks", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20261028)
    parser.add_argument("--id-base", type=int, default=123456)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if min(args.samples, args.blocks) < 1:
        parser.error("Counts must be positive")
    if args.worker:
        print(json.dumps(worker(args.worker, args.samples, args.id_base)))
        return
    if args.output is None:
        parser.error("The parent requires --output")
    orders = [*itertools.permutations(VARIANTS), VARIANTS, VARIANTS[1:] + VARIANTS[:1]]
    random.Random(args.seed).shuffle(orders)  # noqa: S311 - repeatable process order
    blocks = []
    contrasts = (("reference", "inline"), ("identity", "inline"))
    for index in range(args.blocks):
        order = orders[index % len(orders)]
        variants = {}
        for variant in order:
            result = subprocess.run(
                [
                    sys.executable,
                    __file__,
                    "--worker",
                    variant,
                    "--samples",
                    str(args.samples),
                    "--id-base",
                    str(args.id_base + index * 10_000_000),
                ],
                cwd=ROOT,
                env={**os.environ, "PYTHONHASHSEED": str(args.seed + index)},
                capture_output=True,
                text=True,
                check=True,
            )
            variants[variant] = json.loads(result.stdout)
        reference = variants["reference"]
        for variant in variants.values():
            if (
                reference["html_digests"] != variant["html_digests"]
                or reference["native_sha256"] != variant["native_sha256"]
            ):
                raise RuntimeError(f"Projected output or native artifact differs in block {index}")
            if reference["activation"]["graph_digests"] != variant["activation"]["graph_digests"]:
                raise RuntimeError(f"Retained ownership differs in block {index}")
        savings = {
            f"{before}_to_{after}": {
                key: variants[before]["means_ms"][key] - variants[after]["means_ms"][key] for key in ("ms", "cpu_ms")
            }
            for before, after in contrasts
        }
        blocks.append({"block": index, "order": order, "savings_ms": savings, "variants": variants})
        print(json.dumps({"block": index, "savings_ms": savings}), flush=True)
    paths = [
        Path(__file__),
        Path(adapter.__file__),
        Path(checks.__file__),
        Path(compare.__file__),
        ROOT / "benchmarks/leaf_contract_probe/adapter.py",
        Path(__file__).with_name("plan.md"),
        ROOT / "benchmarks/template_function_probe/runtime.py",
        ROOT / "benchmarks/render_structure_probe/census.py",
        ROOT / "benchmarks/ownership_journal_probe/probe.py",
        ROOT / "benchmarks/utils.py",
    ]
    paths.extend(
        ROOT / "packages/py/citry/citry" / name
        for name in (
            "component_render.py",
            "component.py",
            "citry_context.py",
            "citry_render.py",
            "_pure.py",
            "constness.py",
            "nodes/__init__.py",
            "ownership.py",
            "serialize.py",
            "ownership_manifest.py",
            "_protocol/client_graph/canonical.py",
            "_protocol/client_graph/manifests.py",
        )
    )
    paths.append(ROOT / "packages/py/citry/tests/test_benchmark_citry.py")
    report = {
        "experiment_only": True,
        "retains_all_timed_output_strings": True,
        "revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),  # noqa: S607
        "seed": args.seed,
        "samples_per_process": args.samples,
        "initial_renders_per_process": 6,
        "hashes": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        "contrasts": {
            label: {
                "median_paired_saving_ms": {
                    key: statistics.median(b["savings_ms"][label][key] for b in blocks) for key in ("ms", "cpu_ms")
                },
                "joint_wins": sum(all(v > 0 for v in b["savings_ms"][label].values()) for b in blocks),
            }
            for label in blocks[0]["savings_ms"]
        },
        "blocks": blocks,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["contrasts"]))


if __name__ == "__main__":
    main()

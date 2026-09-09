"""Compare attribute-cache throughput in fresh single-variant processes."""

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

from probe import ROOT, candidate_node_formatter, ids, nodes, production_activation, reference_node_formatter, scenario


def worker(*, candidate: bool, samples: int, id_base: int, implementation: str) -> dict[str, Any]:
    """Keep normal GC and time every complete render on one private heap."""
    ids._id_base = id_base
    ids._id_counter = itertools.count()
    original = nodes.ElementAttrsNode._format
    if implementation == "production":
        cache = None
        nodes.ElementAttrsNode._format = original if candidate else reference_node_formatter()
    else:
        changed, cache = candidate_node_formatter(original)
        if candidate:
            nodes.ElementAttrsNode._format = changed
    try:
        module = scenario()
        data = module.gen_render_data()
        for _ in range(6):
            module.render(data)
        before_gc = gc.get_stats()
        observations = []
        digests = []
        for sample in range(samples):
            ids._id_counter = itertools.count((sample + 1) * 1_000_000)
            cpu_start = time.process_time_ns()
            start = time.perf_counter_ns()
            output = module.render(data)
            finished = time.perf_counter_ns()
            cpu_finished = time.process_time_ns()
            observations.append(
                {"ms": (finished - start) / 1_000_000, "cpu_ms": (cpu_finished - cpu_start) / 1_000_000}
            )
            digests.append(hashlib.sha256(output.encode()).hexdigest())
            del output
        after_gc = gc.get_stats()
        if implementation == "production":
            cache_info = production_activation(module, data) if candidate else None
        else:
            cache_info = cache.cache_info()._asdict()
            if candidate and (cache_info["hits"] == 0 or cache_info["currsize"] > 256):
                raise RuntimeError("Cache activation or bound check failed")
        import citry_core._rust as native  # noqa: PLC0415

        return {
            "candidate": candidate,
            "python": sys.version,
            "gc_enabled": gc.isenabled(),
            "gc_thresholds": gc.get_threshold(),
            "gc_before": before_gc,
            "gc_after": after_gc,
            "cache_info": cache_info,
            "means_ms": {key: statistics.mean(row[key] for row in observations) for key in ("ms", "cpu_ms")},
            "medians_ms": {key: statistics.median(row[key] for row in observations) for key in ("ms", "cpu_ms")},
            "id_base": id_base,
            "hash_seed": os.environ.get("PYTHONHASHSEED"),
            "native_sha256": hashlib.sha256(Path(native.__file__).read_bytes()).hexdigest(),
            "html_digests": digests,
            "observations": observations,
        }
    finally:
        nodes.ElementAttrsNode._format = original


def main() -> None:
    """Retain both processes from every preselected pair, including slow ones."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", choices=("reference", "candidate"))
    parser.add_argument("--implementation", choices=("prototype", "production"), default="prototype")
    parser.add_argument("--pairs", type=int, default=8)
    parser.add_argument("--samples", type=int, default=80)
    parser.add_argument("--seed", type=int, default=20260909)
    parser.add_argument("--id-base", type=int, default=123456)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.pairs < 1 or args.samples < 1:
        parser.error("Sample and pair counts must be positive")
    if args.worker:
        print(
            json.dumps(
                worker(
                    candidate=args.worker == "candidate",
                    samples=args.samples,
                    id_base=args.id_base,
                    implementation=args.implementation,
                )
            )
        )
        return
    if args.output is None:
        parser.error("The parent runner requires --output")
    orders = [bool(pair % 2) for pair in range(args.pairs)]
    random.Random(args.seed).shuffle(orders)  # noqa: S311 - reproducible process order
    pairs = []
    for pair, candidate_first in enumerate(orders):
        variants = {}
        for candidate in (True, False) if candidate_first else (False, True):
            name = "candidate" if candidate else "reference"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--worker",
                    name,
                    "--implementation",
                    args.implementation,
                    "--samples",
                    str(args.samples),
                    "--id-base",
                    str(args.id_base + pair * 10_000_000),
                ],
                cwd=ROOT,
                env={**os.environ, "PYTHONHASHSEED": str(args.seed + pair)},
                check=True,
                capture_output=True,
                text=True,
            )
            variants[name] = json.loads(completed.stdout)
        if variants["reference"]["html_digests"] != variants["candidate"]["html_digests"]:
            raise RuntimeError(f"Fresh-process HTML differs in pair {pair}")
        if variants["reference"]["native_sha256"] != variants["candidate"]["native_sha256"]:
            raise RuntimeError("Native artifact changed between paired processes")
        savings = {
            key: variants["reference"]["means_ms"][key] - variants["candidate"]["means_ms"][key]
            for key in ("ms", "cpu_ms")
        }
        pairs.append({"pair": pair, "candidate_first": candidate_first, "mean_savings_ms": savings, **variants})
        print(json.dumps({"pair": pair, "mean_savings_ms": savings}), flush=True)
    report = {
        "implementation": args.implementation,
        "reference": "5bad7af8 ElementAttrsNode._format"
        if args.implementation == "production"
        else "imported runtime",
        "order": "balanced-random",
        "order_seed": args.seed,
        "samples_per_process": args.samples,
        "warmups_per_process": 6,
        "all_pair_html_digests_equal": True,
        "hashes": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (
                Path(__file__).resolve(),
                Path(__file__).with_name("probe.py").resolve(),
                ROOT / "packages/py/citry/tests/test_benchmark_citry.py",
                ROOT / "packages/py/citry/citry/nodes/__init__.py",
                ROOT / "packages/py/citry/citry/attrs.py",
                ROOT / "packages/py/citry/citry/util/html.py",
            )
        },
        "median_process_pair_mean_savings_ms": {
            key: statistics.median(pair["mean_savings_ms"][key] for pair in pairs) for key in ("ms", "cpu_ms")
        },
        "favorable_process_pairs": {
            key: sum(pair["mean_savings_ms"][key] > 0 for pair in pairs) for key in ("ms", "cpu_ms")
        },
        "joint_favorable_process_pairs": sum(
            pair["mean_savings_ms"]["ms"] > 0 and pair["mean_savings_ms"]["cpu_ms"] > 0 for pair in pairs
        ),
        "pairs": pairs,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "pairs"}, indent=2))


if __name__ == "__main__":
    main()

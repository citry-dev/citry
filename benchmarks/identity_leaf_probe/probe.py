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
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from benchmarks.identity_leaf_probe import adapter  # noqa: E402
from benchmarks.ownership_journal_probe.probe import scenario  # noqa: E402
from benchmarks.render_structure_probe.census import canonical, digest  # noqa: E402


def worker(changed: bool, samples: int, id_base: int) -> dict[str, Any]:
    """Keep activation instrumentation outside all initial and warm samples."""
    import citry.util.id as ids  # noqa: PLC0415
    import citry_core._rust as native  # noqa: PLC0415
    from citry.ownership import OwnershipGraph  # noqa: PLC0415

    module = scenario()
    adapter.install(module, changed)
    data = module.gen_render_data()
    ids._id_base = id_base
    ids._id_counter = itertools.count()
    warmups, observations, html_digests = [], [], []
    before = None
    for index in range(6 + samples):
        if index == 6:
            before = gc.get_stats()
        if index >= 6:
            ids._id_counter = itertools.count((index - 5) * 1_000_000)
        cpu_start = time.process_time_ns()
        start = time.perf_counter_ns()
        output = module.render(data)
        end = time.perf_counter_ns()
        cpu_end = time.process_time_ns()
        row = {"ms": (end - start) / 1e6, "cpu_ms": (cpu_end - cpu_start) / 1e6}
        html_digest = hashlib.sha256(output.encode()).hexdigest()
        if index < 6:
            warmups.append({**row, "html_digest": html_digest})
        else:
            observations.append(row)
            html_digests.append(html_digest)
    after = gc.get_stats()
    snapshots = []
    counts: Counter[str] = Counter()
    snapshot = OwnershipGraph.snapshot

    def observed_snapshot(graph: Any) -> Any:
        result = snapshot(graph)
        snapshots.append(digest(canonical(result)))
        return result

    OwnershipGraph.snapshot = observed_snapshot
    from citry import component_render as runtime  # noqa: PLC0415

    original = runtime._render_one
    initializer = module.HeroIcon.__init__

    def observed_render(element: Any, parent: Any = None, provides: Any = None) -> Any:
        if element.comp_cls is module.HeroIcon:
            counts["selected_calls"] += 1
        return original(element, parent, provides)

    def observed_init(self: Any, *args: Any, **kwargs: Any) -> None:
        counts["selected_initializations"] += 1
        initializer(self, *args, **kwargs)

    runtime._render_one = observed_render
    module.HeroIcon.__init__ = observed_init
    try:
        ids._id_counter = itertools.count()
        output = module.render(data)
    finally:
        OwnershipGraph.snapshot = snapshot
        runtime._render_one = original
        module.HeroIcon.__init__ = initializer
    if len(snapshots) != 4 or counts["selected_calls"] != 41:
        raise RuntimeError("Missing ownership captures or selected icon calls")
    if counts["selected_initializations"] != (0 if changed else 41):
        raise RuntimeError("Unexpected selected component initialization count")
    return {
        "candidate": changed,
        "python": sys.version,
        "gc_enabled": gc.isenabled(),
        "gc_before": before,
        "gc_after": after,
        "native_sha256": hashlib.sha256(Path(native.__file__).read_bytes()).hexdigest(),
        "warmups": warmups,
        "observations": observations,
        "html_digests": html_digests,
        "snapshot_digests": snapshots,
        "activation_html_digest": hashlib.sha256(output.encode()).hexdigest(),
        "output_bytes": len(output.encode()),
        "activation_counts": dict(counts),
        "means_ms": {key: statistics.mean(row[key] for row in observations) for key in ("ms", "cpu_ms")},
    }


def main() -> None:
    """Retain every sample from balanced randomized independent process pairs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", choices=("reference", "candidate"))
    parser.add_argument("--samples", type=int, default=80)
    parser.add_argument("--pairs", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20261026)
    parser.add_argument("--id-base", type=int, default=123456)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if min(args.samples, args.pairs) < 1:
        parser.error("Counts must be positive")
    if args.worker:
        print(json.dumps(worker(args.worker == "candidate", args.samples, args.id_base)))
        return
    if args.output is None:
        parser.error("The parent requires --output")
    orders = [bool(index % 2) for index in range(args.pairs)]
    random.Random(args.seed).shuffle(orders)  # noqa: S311 - reproducible process order
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
        for key in (
            "html_digests",
            "snapshot_digests",
            "activation_html_digest",
            "native_sha256",
        ):
            if variants["reference"][key] != variants["candidate"][key]:
                raise RuntimeError(f"Paired {key} differs in process pair {pair}")
        if [row["html_digest"] for row in variants["reference"]["warmups"]] != [
            row["html_digest"] for row in variants["candidate"]["warmups"]
        ]:
            raise RuntimeError("Initial-render HTML differs")
        savings = {
            key: variants["reference"]["means_ms"][key] - variants["candidate"]["means_ms"][key]
            for key in ("ms", "cpu_ms")
        }
        pairs.append({"pair": pair, "candidate_first": candidate_first, "mean_savings_ms": savings, **variants})
        print(json.dumps({"pair": pair, "mean_savings_ms": savings}), flush=True)
    report = {
        "experiment_only": True,
        "revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),  # noqa: S607
        "seed": args.seed,
        "samples_per_process": args.samples,
        "initial_renders_per_process": 6,
        "hashes": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (
                Path(__file__),
                Path(__file__).with_name("adapter.py"),
                Path(__file__).with_name("plan.md"),
                ROOT / "benchmarks/template_function_probe/runtime.py",
                ROOT / "packages/py/citry/citry/serialize.py",
                ROOT / "benchmarks/render_structure_probe/census.py",
                ROOT / "benchmarks/ownership_journal_probe/probe.py",
                ROOT / "benchmarks/utils.py",
                ROOT / "packages/py/citry/citry/component_render.py",
                ROOT / "packages/py/citry/citry/citry_render.py",
                ROOT / "packages/py/citry/citry/nodes/__init__.py",
                ROOT / "packages/py/citry/citry/slots.py",
                ROOT / "packages/py/citry/citry/ownership.py",
                ROOT / "packages/py/citry/tests/test_benchmark_citry.py",
            )
        },
        "median_process_pair_mean_savings_ms": {
            key: statistics.median(pair["mean_savings_ms"][key] for pair in pairs) for key in ("ms", "cpu_ms")
        },
        "joint_favorable_process_pairs": sum(all(x > 0 for x in pair["mean_savings_ms"].values()) for pair in pairs),
        "pairs": pairs,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {key: report[key] for key in ("median_process_pair_mean_savings_ms", "joint_favorable_process_pairs")}
        )
    )


if __name__ == "__main__":
    main()

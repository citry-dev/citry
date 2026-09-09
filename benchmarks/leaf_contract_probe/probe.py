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

from benchmarks.identity_leaf_probe import adapter as guarded_adapter  # noqa: E402
from benchmarks.leaf_contract_probe import adapter  # noqa: E402
from benchmarks.ownership_journal_probe.probe import scenario  # noqa: E402
from benchmarks.render_structure_probe.census import canonical, digest  # noqa: E402


def worker(variant: str, samples: int, id_base: int) -> dict[str, Any]:
    """Keep activation instrumentation outside all initial and warm samples."""
    import citry.util.id as ids  # noqa: PLC0415
    import citry_core._rust as native  # noqa: PLC0415
    from citry.ownership import OwnershipGraph  # noqa: PLC0415

    changed = variant != "reference"
    module = scenario()
    if variant == "guarded":
        guarded_adapter.install(module, enabled=True)
    else:
        adapter.install(module, changed, variant="reuse" if variant == "reuse" else "contract")
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

    lookup = adapter.pure_body_lookup

    def observed_lookup(*args: Any) -> Any:
        result = lookup(*args)
        counts["pure_lookup_calls"] += 1
        if result is not None and result[1] is not None:
            counts["pure_lookup_hits"] += 1
        return result

    adapter.pure_body_lookup = observed_lookup
    runtime._render_one = observed_render
    module.HeroIcon.__init__ = observed_init
    try:
        ids._id_counter = itertools.count()
        output = module.render(data)
    finally:
        OwnershipGraph.snapshot = snapshot
        runtime._render_one = original
        module.HeroIcon.__init__ = initializer
        adapter.pure_body_lookup = lookup
    if len(snapshots) != 4 or counts["selected_calls"] != 41:
        raise RuntimeError("Missing ownership captures or selected icon calls")
    if counts["selected_initializations"] != (0 if changed else 41):
        raise RuntimeError("Unexpected selected component initialization count")
    if variant in ("reuse", "contract") and (counts["pure_lookup_calls"] != 41 or counts["pure_lookup_hits"] != 32):
        raise RuntimeError("Expected icon body reuse is missing")
    return {
        "variant": variant,
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


VARIANTS = ("reference", "guarded", "reuse", "contract")


def main() -> None:
    """Keep all variants in every balanced block and compare the declared candidate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", choices=VARIANTS)
    parser.add_argument("--samples", type=int, default=80)
    parser.add_argument("--blocks", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20261027)
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
    shifts = [index % 4 for index in range(args.blocks)]
    random.Random(args.seed).shuffle(shifts)  # noqa: S311 - repeatable process order
    blocks = []
    contrasts = (("reference", "contract"), ("guarded", "reuse"), ("reuse", "contract"))
    for index, shift in enumerate(shifts):
        order = VARIANTS[shift:] + VARIANTS[:shift]
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
            for key in ("html_digests", "snapshot_digests", "activation_html_digest", "native_sha256"):
                if reference[key] != variant[key]:
                    raise RuntimeError(f"Paired {key} differs in block {index}")
            if [x["html_digest"] for x in reference["warmups"]] != [x["html_digest"] for x in variant["warmups"]]:
                raise RuntimeError("Initial-render output differs")
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
        Path(guarded_adapter.__file__),
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
        )
    )
    paths.append(ROOT / "packages/py/citry/tests/test_benchmark_citry.py")
    report = {
        "experiment_only": True,
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

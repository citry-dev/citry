"""Measure direct text emission against the retained immediate function implementation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import statistics
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "packages/py/citry"), str(ROOT / "packages/py/citry_core")]

from benchmarks.composed_function_probe import probe, timing  # noqa: E402
from benchmarks.function_text_probe.adapter import installed  # noqa: E402


def worker(mode_name: str, samples: int) -> dict[str, Any]:
    """Reuse the same render loop, activation oracle and post-timing output checks."""

    def mode(module: Any, _variant: str, counts: dict[str, int] | None = None) -> Any:
        return installed(module, enabled=mode_name == "candidate", counts=counts)

    with patch.object(timing, "installed", mode), patch.object(probe, "installed", mode):
        result = timing.worker("immediate", samples)
    result["mode"] = mode_name
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", choices=("control", "candidate"))
    parser.add_argument("--samples", type=int, default=80)
    parser.add_argument("--pairs", type=int, default=8)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if min(args.samples, args.pairs) < 1:
        parser.error("Sample and pair counts must be positive")
    if args.worker:
        print(json.dumps(worker(args.worker, args.samples)))
        return
    if args.output is None:
        parser.error("--output is required")
    paths = [*Path(__file__).parent.glob("*.py"), Path(__file__).with_name("plan.md")]
    paths.extend((ROOT / "benchmarks/composed_function_probe").glob("*.py"))
    paths.extend((ROOT / "packages/py/citry/citry").rglob("*.py"))
    paths.extend((ROOT / "packages/py/citry_core/citry_core").rglob("*.py"))
    paths.append(Path(timing.native.__file__))
    paths.extend(
        ROOT / name
        for name in (
            "benchmarks/wrapper_function_probe/adapter.py",
            "benchmarks/leaf_contract_probe/adapter.py",
            "benchmarks/template_function_probe/runtime.py",
            "benchmarks/ownership_journal_probe/probe.py",
            "benchmarks/inline_leaf_probe/checks.py",
            "benchmarks/utils.py",
            "benchmarks/render_structure_probe/census.py",
            "packages/py/citry/tests/test_benchmark_citry.py",
        )
    )
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    orders = [("control", "candidate"), ("candidate", "control")] * 4
    random.Random(20261104).shuffle(orders)  # noqa: S311 - reproducible order
    pairs = []
    for index in range(args.pairs):
        order = orders[index % len(orders)]
        rows = {}
        for mode_name in order:
            result = subprocess.run(
                [sys.executable, __file__, "--worker", mode_name, "--samples", str(args.samples)],
                cwd=ROOT,
                env={**os.environ, "PYTHONHASHSEED": str(20261104 + index)},
                capture_output=True,
                text=True,
                check=True,
            )
            rows[mode_name] = json.loads(result.stdout)
        control, candidate = rows["control"], rows["candidate"]
        for key in ("raw_digests", "projected_digests", "normalized_snapshot_digest", "native_sha256", "activation"):
            if control[key] != candidate[key]:
                raise AssertionError(f"Paired execution differs in {key}")
        saving = {key: control["mean_warm_ms"][key] - candidate["mean_warm_ms"][key] for key in ("ms", "cpu_ms")}
        pairs.append({"order": order, "variants": rows, "savings_ms": saving})
        print(json.dumps({"pair": index, "savings_ms": saving}), flush=True)
    for name, expected in hashes.items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise AssertionError(f"Source changed during timing: {name}")
    summary = {
        "median_paired_warm_saving_ms": {
            key: statistics.median(p["savings_ms"][key] for p in pairs) for key in ("ms", "cpu_ms")
        },
        "joint_wins": sum(all(value > 0 for value in p["savings_ms"].values()) for p in pairs),
        "median_paired_warm_ratio": statistics.median(
            p["variants"]["candidate"]["mean_warm_ms"]["ms"] / p["variants"]["control"]["mean_warm_ms"]["ms"]
            for p in pairs
        ),
        "median_paired_second_saving_ms": statistics.median(
            p["variants"]["control"]["initial_renders"][1]["ms"]
            - p["variants"]["candidate"]["initial_renders"][1]["ms"]
            for p in pairs
        ),
    }
    args.output.write_text(
        json.dumps(
            {
                "experiment_only": True,
                "retains_all_timed_outputs": True,
                "complete_raw_output_digests_equal": True,
                "summary": summary,
                "hashes": hashes,
                "pairs": pairs,
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps(summary))


if __name__ == "__main__":
    main()

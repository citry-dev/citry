"""
Compare second and steady-state renders in alternating fresh processes.

Run with the benchmark dependencies installed and the same release native
extension in both checkouts. Example:

    .venv/bin/python benchmarks/performance_render.py \
        --baseline-root /path/to/baseline --output /tmp/repeat.json

The baseline is a Citry checkout. Django runs from the candidate checkout.
Each subprocess uses the existing scenario without changing inputs or features.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import subprocess
import sys
import time
import types
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent


def measure(root: Path, engine: str, size: str, samples: int) -> dict[str, Any]:
    """Measure one scenario, including first and second render observations."""
    sys.path[:0] = [str(root), str(root / "packages/py/citry"), str(root / "packages/py/citry_core")]
    from benchmarks.utils import get_benchmark_script  # noqa: PLC0415

    suffix = "_small" if size == "sm" else ""
    path = root / "packages/py/citry/tests" / f"test_benchmark_{engine}{suffix}.py"
    module = types.ModuleType("performance_render_scenario")
    module.__file__ = str(path)
    sys.modules[module.__name__] = module
    exec(compile(get_benchmark_script(path), str(path), "exec"), module.__dict__)  # noqa: S102
    data = module.gen_render_data()
    timings = []
    for _ in range(samples + 6):
        start = time.perf_counter_ns()
        html = module.render(data)
        timings.append((time.perf_counter_ns() - start) / 1_000_000)
    result = {
        "root": str(root),
        "engine": engine,
        "size": size,
        "first_ms": timings[0],
        "second_ms": timings[1],
        "warm_median_ms": statistics.median(timings[6:]),
        "warm_samples_ms": timings[6:],
        "output_bytes": len(html.encode()),
        "scenario_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    if engine == "citry":
        import citry  # noqa: PLC0415
        import citry_core._rust as native  # noqa: PLC0415

        if not Path(citry.__file__).is_relative_to(root):
            raise RuntimeError("Citry imports resolved outside the requested checkout.")
        result["native_sha256"] = hashlib.sha256(Path(native.__file__).read_bytes()).hexdigest()
    return result


def main() -> None:
    """Run bounded alternating comparisons and retain all observations."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--samples", type=int, default=20)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    parser.add_argument("--engine", choices=("citry", "django"), default="citry", help=argparse.SUPPRESS)
    parser.add_argument("--size", choices=("sm", "lg"), default="lg", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.rounds < 1 or args.samples < 1:
        parser.error("rounds and samples must be positive")
    if args.worker:
        print(json.dumps(measure(args.root.resolve(), args.engine, args.size, args.samples)))
        return
    if args.baseline_root is None or args.output is None:
        parser.error("--baseline-root and --output are required")
    cases = [
        ("baseline", args.baseline_root.resolve(), "citry"),
        ("candidate", ROOT, "citry"),
        ("django", ROOT, "django"),
    ]
    observations = []
    for size in ("sm", "lg"):
        for round_number in range(args.rounds):
            order = cases if round_number % 2 == 0 else list(reversed(cases))
            for label, root, engine in order:
                command = [
                    sys.executable,
                    __file__,
                    "--worker",
                    "--root",
                    str(root),
                    "--engine",
                    engine,
                    "--size",
                    size,
                    "--samples",
                    str(args.samples),
                ]
                completed = subprocess.run(command, check=True, capture_output=True, text=True)
                observation = json.loads(completed.stdout)
                observation.update(variant=label, round=round_number)
                observations.append(observation)
    native_hashes = {row["native_sha256"] for row in observations if row["engine"] == "citry"}
    if len(native_hashes) != 1:
        raise RuntimeError("Citry comparisons require identical native extension artifacts in both checkouts.")
    report = {"python": sys.version, "rounds": args.rounds, "observations": observations}
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    for size in ("sm", "lg"):
        for label, _, _ in cases:
            rows = [row for row in observations if row["variant"] == label and row["size"] == size]
            second = statistics.median(row["second_ms"] for row in rows)
            warm = statistics.median(row["warm_median_ms"] for row in rows)
            print(f"{size} {label}: second {second:.4f} ms; warm {warm:.4f} ms")


if __name__ == "__main__":
    main()

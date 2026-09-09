"""Refresh the published rendering chart with one balanced cross-engine run."""

from __future__ import annotations

import argparse
import ast
import gzip
import hashlib
import importlib.metadata
import json
import os
import random
import statistics
import subprocess
import sys
import types
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "packages/py/citry"), str(ROOT / "packages/py/citry_core")]

from benchmarks.simple_api_probe import timing  # noqa: E402
from benchmarks.utils import get_benchmark_script  # noqa: E402

VARIANTS = ("ordinary", "simple", "django", "django-components", "jinja2")


def worker(variant: str, samples: int) -> dict:
    """Use the retained-output render loop and validate Citry outside timing."""
    if variant in ("ordinary", "simple", "django"):
        return timing.worker(variant, samples)
    stem = "djc" if variant == "django-components" else "jinja2"
    path = ROOT / f"packages/py/citry/tests/test_benchmark_{stem}.py"

    def load(_variant: str) -> tuple[types.ModuleType, str]:
        tree = ast.parse(get_benchmark_script(path), filename=str(path))
        module = types.ModuleType("simple_api_scenario")
        module.__file__ = str(path)
        sys.modules[module.__name__] = module
        exec(compile(tree, str(path), "exec"), module.__dict__)  # noqa: S102
        return module, hashlib.sha256(ast.dump(tree).encode()).hexdigest()

    # The Django branch of the shared loop omits Citry-specific graph checks.
    # Only scenario loading changes, before any render timer starts.
    with patch.object(timing, "load_scenario", load):
        result = timing.worker("django", samples)
    result["variant"] = variant
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", choices=VARIANTS)
    parser.add_argument("--samples", type=int, default=80)
    parser.add_argument("--blocks", type=int, default=10)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if min(args.samples, args.blocks) < 1:
        parser.error("Samples and blocks must be positive")
    if args.worker:
        print(json.dumps(worker(args.worker, args.samples)))
        return
    if args.output is None:
        parser.error("--output is required")
    paths = [
        p
        for folder in ("benchmarks", "packages/py/citry/citry", "packages/py/citry_core/citry_core")
        for p in (ROOT / folder).rglob("*.py")
    ]
    paths.extend(
        ROOT / f"packages/py/citry/tests/test_benchmark_{stem}.py" for stem in ("citry", "django", "djc", "jinja2")
    )
    paths.append(Path(timing.native.__file__))
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    cyclic = [VARIANTS[i:] + VARIANTS[:i] for i in range(len(VARIANTS))]
    orders = cyclic + [tuple(reversed(order)) for order in cyclic]
    random.Random(20260910).shuffle(orders)  # noqa: S311 - reproducible balanced order
    blocks, captures = [], []
    for index in range(args.blocks):
        variants = {}
        order = orders[index % len(orders)]
        for variant in order:
            process = subprocess.run(
                [sys.executable, __file__, "--worker", variant, "--samples", str(args.samples)],
                cwd=ROOT,
                env={**os.environ, "PYTHONHASHSEED": str(20260910 + index)},
                capture_output=True,
                text=True,
                check=True,
            )
            variants[variant] = json.loads(process.stdout)
        ordinary, simple = variants["ordinary"], variants["simple"]
        if ordinary["projected_sha256"] != simple["projected_sha256"]:
            raise AssertionError("Citry application output differs")
        if ordinary["activation"]["component_calls"] != simple["activation"]["component_calls"]:
            raise AssertionError("Citry component call counts differ")
        if len({value["native_sha256"] for value in variants.values()}) != 1:
            raise AssertionError("Native artifacts differ")
        for variant, result in variants.items():
            activation = result["activation"]
            if activation is not None:
                captures.append(
                    {
                        "block": index,
                        "variant": variant,
                        "snapshots": activation.pop("snapshots"),
                        "manifests": activation.pop("manifests"),
                    }
                )
        blocks.append({"order": order, "variants": variants})
        print(
            json.dumps({"block": index, "warm_ms": {k: v["mean_warm_ms"]["ms"] for k, v in variants.items()}}),
            flush=True,
        )
    for name, expected in hashes.items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise AssertionError(f"Source changed during publication run: {name}")
    summary = {
        variant: {
            "first_ms": statistics.median(b["variants"][variant]["initial_renders"][0]["ms"] for b in blocks),
            "second_ms": statistics.median(b["variants"][variant]["initial_renders"][1]["ms"] for b in blocks),
            "warm_ms": statistics.median(b["variants"][variant]["mean_warm_ms"]["ms"] for b in blocks),
            "output_bytes": sorted({size for b in blocks for size in b["variants"][variant]["output_bytes"]}),
        }
        for variant in VARIANTS
    }
    archive = args.output.with_suffix(".captures.json.gz")
    archive.write_bytes(gzip.compress(json.dumps(captures, separators=(",", ":")).encode(), mtime=0))
    args.output.write_text(
        json.dumps(
            {
                "python": sys.version,
                "package_versions": {
                    name: importlib.metadata.version(name) for name in ("Django", "django-components", "Jinja2")
                },
                "git_revision": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"],  # noqa: S607 - repository metadata
                    cwd=ROOT,
                    text=True,
                ).strip(),
                "retains_all_timed_outputs": True,
                "cross_engine_output_equality_claimed": False,
                "method": (
                    f"{args.blocks} fresh-process blocks, six initial renders and "
                    f"{args.samples} warmed renders per worker."
                ),
                "capture_archive": {"path": str(archive), "sha256": hashlib.sha256(archive.read_bytes()).hexdigest()},
                "hashes": hashes,
                "summary": summary,
                "blocks": blocks,
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

"""Measure the public simple flag on the large page against ordinary Citry and Django."""

from __future__ import annotations

import argparse
import ast
import gc
import gzip
import hashlib
import importlib.metadata
import itertools
import json
import os
import random
import statistics
import subprocess
import sys
import time
import types
from collections import Counter
from pathlib import Path
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "packages/py/citry"), str(ROOT / "packages/py/citry_core")]

from benchmarks.composed_function_probe.probe import content_projection  # noqa: E402
from benchmarks.inline_leaf_probe.checks import shifted_names  # noqa: E402
from benchmarks.render_structure_probe.census import canonical  # noqa: E402
from benchmarks.utils import get_benchmark_script  # noqa: E402

import citry.util.id as ids  # noqa: E402
import citry_core._rust as native  # noqa: E402
from citry import component_render as runtime  # noqa: E402
from citry.ownership import OwnershipGraph  # noqa: E402

SELECTED = {"Button": 114, "Icon": 41, "HeroIcon": 41}


def load_scenario(variant: str) -> tuple[Any, str]:
    """Opt in three authored classes before creation; leave runtime methods untouched."""
    engine = "django" if variant == "django" else "citry"
    path = ROOT / f"packages/py/citry/tests/test_benchmark_{engine}.py"
    tree = ast.parse(get_benchmark_script(path), filename=str(path))
    if variant == "simple":
        found = set()
        for cls in tree.body:
            if not isinstance(cls, ast.ClassDef) or cls.name not in SELECTED:
                continue
            callback = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "template_data")
            if callback.decorator_list or [arg.arg for arg in callback.args.args] != ["self", "kwargs", "slots"]:
                raise AssertionError("Selected callback signature changed")
            if any(isinstance(n, ast.Name) and n.id == "self" for n in ast.walk(callback)):
                raise AssertionError("Selected callback uses its instance")
            callback.args.args.pop(0)
            callback.decorator_list.append(ast.Name(id="staticmethod", ctx=ast.Load()))
            cls.body.insert(
                0, ast.Assign(targets=[ast.Name(id="simple", ctx=ast.Store())], value=ast.Constant(value=True))
            )
            found.add(cls.name)
        if found != set(SELECTED):
            raise AssertionError("Missing audited component classes")
    ast.fix_missing_locations(tree)
    module = types.ModuleType("simple_api_scenario")
    module.__file__ = str(path)
    sys.modules[module.__name__] = module
    exec(compile(tree, str(path), "exec"), module.__dict__)  # noqa: S102
    return module, hashlib.sha256(ast.dump(tree).encode()).hexdigest()


def observe(module: Any, data: Any) -> tuple[dict[str, Any], dict[str, str]]:
    """Count callbacks, component calls and ownership outside the timed section."""
    snapshots, calls, callbacks = [], Counter(), Counter()
    original_snapshot, original_render = OwnershipGraph.snapshot, runtime._render_one_traced
    codes = {getattr(module, name).template_data.__code__: name for name in SELECTED}

    def profile(frame: Any, event: str, _arg: Any) -> None:
        if event == "call" and frame.f_code in codes:
            callbacks[codes[frame.f_code]] += 1

    def snapshot(graph: Any) -> Any:
        value = original_snapshot(graph)
        snapshots.append(value)
        return value

    def render(element: Any, *args: Any, **kwargs: Any) -> Any:
        calls[element.comp_cls.__name__] += 1
        return original_render(element, *args, **kwargs)

    ids._id_counter = itertools.count()
    previous_profile = sys.getprofile()
    try:
        with patch.object(OwnershipGraph, "snapshot", snapshot), patch.object(runtime, "_render_one_traced", render):
            sys.setprofile(profile)
            output = module.render(data)
    finally:
        sys.setprofile(previous_profile)
    names, per_class = {}, Counter()
    for value in snapshots:
        for row in value.logical_instances:
            if row.render_id not in names:
                per_class[row.class_id] += 1
                names[row.render_id] = f"render_{row.class_id}_{per_class[row.class_id]}"
    projected, manifests = content_projection(output, names)
    if dict(callbacks) != SELECTED:
        raise AssertionError(f"Unexpected callback activation: {callbacks}")
    return {
        "callbacks": dict(callbacks),
        "component_calls": dict(calls),
        "generated_ids": next(ids._id_counter),
        "snapshot_counts": [{key: len(getattr(s, key)) for key in s.__dataclass_fields__} for s in snapshots],
        "snapshots": [canonical(s) for s in snapshots],
        "manifests": manifests,
        "projected_sha256": hashlib.sha256(projected.encode()).hexdigest(),
    }, names


def worker(variant: str, samples: int) -> dict[str, Any]:
    """Keep normal GC and every output alive through all measured renders."""
    module, tree_hash = load_scenario(variant)
    data = module.gen_render_data()
    ids._id_base = 123456
    outputs, rows = [], []
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
    activation, projected_hashes = None, []
    if variant != "django":
        activation, names = observe(module, data)
        expected_ids = 146 if variant == "simple" else 342
        if activation["generated_ids"] != expected_ids:
            raise AssertionError(f"Expected {expected_ids} identities")
        for index, output in enumerate(outputs):
            shifted, _ = shifted_names(names, set(), index * 1_000_000)
            projected = content_projection(output, shifted)[0]
            projected_hashes.append(hashlib.sha256(projected.encode()).hexdigest())
        if set(projected_hashes) != {activation["projected_sha256"]}:
            raise AssertionError("Application HTML changed across timed renders")
    raw_hashes = [hashlib.sha256(output.encode()).hexdigest() for output in outputs]
    if variant != "django" and len(set(raw_hashes)) != len(outputs):
        raise AssertionError("Render IDs did not change")
    return {
        "variant": variant,
        "python": sys.version,
        "package_versions": {name: importlib.metadata.version(name) for name in ("Django", "django-components")},
        "scenario_ast_sha256": tree_hash,
        "native_sha256": hashlib.sha256(Path(native.__file__).read_bytes()).hexdigest(),
        "gc_enabled": gc.isenabled(),
        "gc_before": before,
        "gc_after": after,
        "initial_renders": rows[:6],
        "warm_renders": rows[6:],
        "mean_warm_ms": {key: statistics.mean(row[key] for row in rows[6:]) for key in ("ms", "cpu_ms")},
        "output_bytes": [len(output.encode()) for output in outputs],
        "raw_sha256": raw_hashes,
        "projected_sha256": projected_hashes,
        "activation": activation,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", choices=("ordinary", "simple", "django"))
    parser.add_argument("--samples", type=int, default=80)
    parser.add_argument("--blocks", type=int, default=6)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if min(args.samples, args.blocks) < 1:
        parser.error("Sample and block counts must be positive")
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
    paths.extend(ROOT / f"packages/py/citry/tests/test_benchmark_{engine}.py" for engine in ("citry", "django"))
    paths.extend((Path(native.__file__), Path(__file__).with_name("plan.md")))
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    orders = list(itertools.permutations(("ordinary", "simple", "django")))
    random.Random(20260909).shuffle(orders)  # noqa: S311 - reproducible balanced order
    blocks, captures = [], []
    for index in range(args.blocks):
        order, variants = orders[index % len(orders)], {}
        for variant in order:
            result = subprocess.run(
                [sys.executable, __file__, "--worker", variant, "--samples", str(args.samples)],
                cwd=ROOT,
                env={**os.environ, "PYTHONHASHSEED": str(20260909 + index)},
                capture_output=True,
                text=True,
                check=True,
            )
            variants[variant] = json.loads(result.stdout)
        ordinary, simple = variants["ordinary"], variants["simple"]
        if ordinary["projected_sha256"] != simple["projected_sha256"]:
            raise AssertionError("Ordinary and simple application HTML differs")
        if ordinary["activation"]["component_calls"] != simple["activation"]["component_calls"]:
            raise AssertionError("Component call counts differ")
        if len({row["native_sha256"] for row in variants.values()}) != 1:
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
        savings = {key: ordinary["mean_warm_ms"][key] - simple["mean_warm_ms"][key] for key in ("ms", "cpu_ms")}
        blocks.append({"order": order, "variants": variants, "savings_ms": savings})
        print(json.dumps({"block": index, "warm_ms": {k: v["mean_warm_ms"] for k, v in variants.items()}}), flush=True)
    for name, expected in hashes.items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise AssertionError(f"Source changed during timing: {name}")
    summary = {
        "median_paired_warm_saving_ms": {
            key: statistics.median(b["savings_ms"][key] for b in blocks) for key in ("ms", "cpu_ms")
        },
        "joint_wins": sum(all(value > 0 for value in b["savings_ms"].values()) for b in blocks),
        "median_paired_warm_ratio": statistics.median(
            b["variants"]["simple"]["mean_warm_ms"]["ms"] / b["variants"]["ordinary"]["mean_warm_ms"]["ms"]
            for b in blocks
        ),
        "variants": {
            variant: {
                "first_ms": statistics.median(b["variants"][variant]["initial_renders"][0]["ms"] for b in blocks),
                "second_ms": statistics.median(b["variants"][variant]["initial_renders"][1]["ms"] for b in blocks),
                "warm_ms": statistics.median(b["variants"][variant]["mean_warm_ms"]["ms"] for b in blocks),
            }
            for variant in ("ordinary", "simple", "django")
        },
    }
    archive = args.output.with_suffix(".captures.json.gz")
    archive.write_bytes(gzip.compress(json.dumps(captures, separators=(",", ":")).encode(), mtime=0))
    args.output.write_text(
        json.dumps(
            {
                "implementation_commit": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"],  # noqa: S607 - repository metadata
                    cwd=ROOT,
                    text=True,
                ).strip(),
                "retains_all_timed_outputs": True,
                "cross_engine_output_equality_claimed": False,
                "capture_archive": {"path": str(archive), "sha256": hashlib.sha256(archive.read_bytes()).hexdigest()},
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

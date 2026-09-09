"""Locate remaining public-simple work and describe the classes that still do it."""

from __future__ import annotations

import argparse
import ast
import cProfile
import functools
import hashlib
import itertools
import json
import pstats
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "packages/py/citry"), str(ROOT / "packages/py/citry_core")]

from benchmarks.simple_api_probe.timing import load_scenario  # noqa: E402
from benchmarks.utils import get_benchmark_script  # noqa: E402

import citry.component_render as runtime  # noqa: E402
import citry.util.id as ids  # noqa: E402
import citry_core._rust as native  # noqa: E402
from citry.assets import _find_pair_declaration  # noqa: E402
from citry.citry_render import CitryRender, RenderFrame  # noqa: E402


def declarations(module: Any) -> dict[str, Any]:
    """Describe candidates for review; these facts do not establish simple eligibility."""
    result = {}
    tree = ast.parse(get_benchmark_script(module.__file__))
    for node in tree.body:
        cls = getattr(module, getattr(node, "name", ""), None)
        if not isinstance(node, ast.ClassDef) or not isinstance(cls, type) or not hasattr(cls, "citry"):
            continue
        methods = [item for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))]
        callback = next((method for method in methods if method.name == "template_data"), None)
        assets = {}
        for name in ("js", "css", "messages"):
            _owner, inline, file = _find_pair_declaration(cls, name, name + "_file")
            assets[name] = inline is not None or file is not None
        result[node.name] = {
            "simple": cls.simple,
            "pure": cls.pure,
            "transparent": cls.transparent,
            "assets": assets,
            "authored_methods": [method.name for method in methods],
            "data_reads_self": callback is not None
            and any(isinstance(item, ast.Name) and item.id == "self" for item in ast.walk(callback)),
            "data_yields": callback is not None
            and any(isinstance(item, (ast.Yield, ast.YieldFrom)) for item in ast.walk(callback)),
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("variant", choices=("ordinary", "simple"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    paths = [
        p
        for folder in ("benchmarks", "packages/py/citry/citry", "packages/py/citry_core/citry_core")
        for p in (ROOT / folder).rglob("*.py")
    ]
    paths.extend((Path(native.__file__), ROOT / "packages/py/citry/tests/test_benchmark_citry.py"))
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    module, tree_hash = load_scenario(args.variant)
    data = module.gen_render_data()
    ids._id_base = 123456

    def render() -> str:
        ids._id_counter = itertools.count()
        return module.render(data)

    for _ in range(6):
        expected = render()
    profile = cProfile.Profile()
    profile.enable()
    outputs = [render() for _ in range(20)]
    profile.disable()
    if any(output != expected for output in outputs):
        raise AssertionError("Profiling changed complete output")
    stats = pstats.Stats(profile)
    rows = []
    for (file, line, function), (primitive, total, own, cumulative, _callers) in stats.stats.items():
        rows.append(
            {
                "file": file.removeprefix(str(ROOT) + "/"),
                "line": line,
                "function": function,
                "primitive_calls_per_render": primitive / 20,
                "calls_per_render": total / 20,
                "self_ms_per_render": own * 1000 / 20,
                "cumulative_ms_per_render": cumulative * 1000 / 20,
            }
        )
    rows.sort(key=lambda row: -row["self_ms_per_render"])

    constructions, sites = Counter(), Counter()

    def constructor_profile(frame: Any, event: str, _arg: Any) -> None:
        if event != "call" or frame.f_code.co_name != "__init__":
            return
        instance = frame.f_locals.get("self")
        if isinstance(instance, (CitryRender, RenderFrame)) and frame.f_code is getattr(
            type(instance).__init__, "__code__", None
        ):
            constructions[type(instance).__name__] += 1
            caller = frame.f_back
            if caller is not None:
                sites[f"{Path(caller.f_code.co_filename).name}:{caller.f_code.co_name}"] += 1

    previous = sys.getprofile()
    try:
        sys.setprofile(constructor_profile)
        counted = render()
    finally:
        sys.setprofile(previous)
    if counted != expected:
        raise AssertionError("Constructor observation changed complete output")

    totals, counts, slots = defaultdict(float), Counter(), defaultdict(Counter)
    stack: list[list[float]] = []

    def timed(original: Any, phase: str) -> Any:
        @functools.wraps(original)
        def call(value: Any, *args: Any, **kwargs: Any) -> Any:
            cls = (
                value.comp_cls
                if phase == "prepare"
                else (
                    value.context._simple_scope.component_class
                    if value.context._simple_scope is not None
                    else type(value.context.component)
                )
            )
            key = f"{cls.__name__}.{phase}"
            if phase == "prepare":
                slots[cls.__name__][",".join(sorted(value.slots))] += 1
            frame = [0.0]
            stack.append(frame)
            start = time.perf_counter_ns()
            try:
                return original(value, *args, **kwargs)
            finally:
                elapsed = time.perf_counter_ns() - start
                stack.pop()
                totals[key] += elapsed - frame[0]
                counts[key] += 1
                if stack:
                    stack[-1][0] += elapsed

        return call

    with (
        patch.object(runtime, "_render_one", timed(runtime._render_one, "prepare")),
        patch.object(runtime, "_finalize", timed(runtime._finalize, "finish")),
    ):
        for _ in range(10):
            if render() != expected:
                raise AssertionError("Component timing changed complete output")
    if stack:
        raise AssertionError("Unbalanced component timers")
    for name, expected_hash in hashes.items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected_hash:
            raise AssertionError(f"Source changed during diagnosis: {name}")
    result = {
        "diagnostic_only": True,
        "variant": args.variant,
        "scenario_ast_sha256": tree_hash,
        "profiled_renders": 20,
        "python": sys.version,
        "all_observed_raw_outputs_equal": True,
        "instrumented_ms_per_render": stats.total_tt * 1000 / 20,
        "output_bytes": len(expected.encode()),
        "raw_sha256": hashlib.sha256(expected.encode()).hexdigest(),
        "profile": rows,
        "constructions": dict(constructions),
        "constructor_callers": dict(sites),
        "component_phases": {
            key: {"calls_per_render": counts[key] / 10, "exclusive_ms": value / 10 / 1e6}
            for key, value in sorted(totals.items(), key=lambda item: -item[1])
        },
        "observed_input_slots": {
            name: {keys: count / 10 for keys, count in counter.items()} for name, counter in slots.items()
        },
        "declarations": declarations(module),
        "hashes": hashes,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "instrumented_ms": result["instrumented_ms_per_render"],
                "constructions": constructions,
                "top_functions": rows[:12],
                "component_phases": dict(list(result["component_phases"].items())[:15]),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

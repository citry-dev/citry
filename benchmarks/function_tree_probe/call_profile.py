"""Locate remaining call costs and observe composed function results before settlement."""

from __future__ import annotations

import argparse
import cProfile
import hashlib
import itertools
import json
import pstats
import sys
from collections import Counter
from pathlib import Path
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "packages/py/citry"), str(ROOT / "packages/py/citry_core")]

from benchmarks.composed_function_probe.adapter import FunctionElement, FunctionRender, installed  # noqa: E402
from benchmarks.composed_function_probe.probe import content_projection, observe  # noqa: E402
from benchmarks.ownership_journal_probe.probe import scenario  # noqa: E402

import citry.util.id as ids  # noqa: E402
import citry_core._rust as native  # noqa: E402
from citry.citry_render import (  # noqa: E402
    CitryRender,
    DeferredComponent,
    PhysicalRegionPart,
    PhysicalRegionRender,
    Placeholder,
)


def shape(render: CitryRender) -> dict[str, Any]:
    """Describe a function result at construction, before deferred descendants settle."""
    counts: Counter[str] = Counter()
    pending = [render]
    contexts = set()
    extra_keys: Counter[str] = Counter()
    deferred_functions: Counter[str] = Counter()
    while pending:
        part = pending.pop()
        if isinstance(part, str):
            counts["text_parts"] += 1
            counts["text_bytes"] += len(part.encode())
        elif isinstance(part, (PhysicalRegionPart, PhysicalRegionRender)):
            counts["physical_regions"] += 1
            pending.append(part.part)
        elif isinstance(part, CitryRender):
            counts["render_occurrences"] += 1
            counts["component_roots"] += int(part.is_component_root)
            counts["different_frame_owner"] += int(part.frame.render_id != render.frame.render_id)
            counts["different_ownership_graph"] += int(part.context.ownership is not render.context.ownership)
            pending.extend(reversed(part.parts))
            if id(part.context) not in contexts:
                contexts.add(id(part.context))
                counts["error_tainted_contexts"] += int(part.context._error_tainted)
                if part.context.extra:
                    counts["contexts_with_extra"] += 1
                    extra_keys.update(part.context.extra.keys())
        elif isinstance(part, DeferredComponent):
            counts["deferred_components"] += 1
            if type(part.element) is FunctionElement:
                counts["deferred_function_calls"] += 1
                deferred_functions[part.element.comp_cls.__name__] += 1
            else:
                counts["deferred_ordinary_children"] += 1
        elif isinstance(part, Placeholder):
            counts["placeholders"] += 1
        else:
            raise TypeError(f"Unexpected render part: {type(part)!r}")
    obstacles = (
        "physical_regions",
        "component_roots",
        "different_frame_owner",
        "different_ownership_graph",
        "error_tainted_contexts",
        "contexts_with_extra",
        "deferred_components",
        "placeholders",
    )
    return {
        "counts": dict(counts),
        "extra_keys": dict(extra_keys),
        "deferred_functions": dict(deferred_functions),
        "only_finished_text_with_one_owner_and_no_extra": not any(counts[k] for k in obstacles),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("variant", choices=("reference", "immediate", "deferred"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    module = scenario()
    data = module.gen_render_data()
    ids._id_base = 123456

    def render() -> str:
        ids._id_counter = itertools.count()
        return module.render(data)

    with installed(module, args.variant):
        for _ in range(6):
            expected = render()
        profiler = cProfile.Profile()
        outputs = []
        profiler.enable()
        for _ in range(20):
            outputs.append(render())
        profiler.disable()
        if any(output != expected for output in outputs):
            raise AssertionError("Profiling changed rendered output")
        constructions: Counter[str] = Counter()
        functions = []
        original_init = CitryRender.__init__

        def constructed(result: CitryRender, *values: Any, **kwargs: Any) -> None:
            original_init(result, *values, **kwargs)
            constructions[type(result).__name__] += 1
            constructions["renders_with_root_frame" if result.is_component_root else "interior_renders"] += 1
            if type(result) is FunctionRender:
                # This observer is tied to the retained prototype's execute() boundary.
                caller = sys._getframe(1)
                if caller.f_code.co_name != "execute":
                    raise AssertionError("Function construction observer reached an unexpected caller")
                functions.append({"function": caller.f_locals["cls"].__name__, **shape(result)})

        with patch.object(CitryRender, "__init__", constructed):
            if render() != expected:
                raise AssertionError("Construction observation changed rendered output")
    expected_calls = {} if args.variant == "reference" else {"Button": 114, "Icon": 40, "HeroIcon": 41}
    if Counter(row["function"] for row in functions) != expected_calls:
        raise AssertionError("Function result observation missed the expected activation")
    reference = observe(module, render, "reference")
    observation = observe(module, render, args.variant)
    if content_projection(expected, observation["names"])[0] != reference["projected_html"]:
        raise AssertionError("Application output differs from ordinary Citry")
    rows = []
    for (filename, line, name), (primitive, total, own, cumulative, _) in pstats.Stats(profiler).stats.items():
        path = Path(filename)
        rows.append(
            {
                "file": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else filename,
                "line": line,
                "function": name,
                "calls_per_render": total / 20,
                "primitive_calls_per_render": primitive / 20,
                "instrumented_self_ms": own * 50,
                "instrumented_cumulative_ms": cumulative * 50,
            }
        )
    rows.sort(key=lambda row: row["instrumented_self_ms"], reverse=True)
    function_summary = {}
    for name in expected_calls:
        selected = [row for row in functions if row["function"] == name]
        function_summary[name] = {
            "calls": len(selected),
            "text_only_at_creation": sum(r["only_finished_text_with_one_owner_and_no_extra"] for r in selected),
            "obstacle_occurrences": {
                key: sum(r["counts"].get(key, 0) > 0 for r in selected)
                for key in (
                    "physical_regions",
                    "component_roots",
                    "different_frame_owner",
                    "different_ownership_graph",
                    "error_tainted_contexts",
                    "contexts_with_extra",
                    "deferred_components",
                    "deferred_function_calls",
                    "deferred_ordinary_children",
                    "placeholders",
                )
            },
        }
    paths = [Path(__file__), Path(__file__).with_name("plan.md")]
    paths.extend((ROOT / "benchmarks/composed_function_probe").glob("*.py"))
    paths.extend((ROOT / "packages/py/citry/citry").rglob("*.py"))
    paths.extend((ROOT / "packages/py/citry_core/citry_core").rglob("*.py"))
    paths.extend(
        ROOT / name
        for name in (
            "benchmarks/wrapper_function_probe/adapter.py",
            "benchmarks/leaf_contract_probe/adapter.py",
            "benchmarks/template_function_probe/runtime.py",
            "benchmarks/ownership_journal_probe/probe.py",
            "benchmarks/utils.py",
            "benchmarks/render_structure_probe/census.py",
        )
    )
    paths.append(Path(module.__file__))
    report = {
        "diagnostic_only": True,
        "variant": args.variant,
        "samples": 20,
        "warmups": 6,
        "note": "cProfile changes costs; cumulative rows overlap and must not be added or treated as warm wall time.",
        "shape_note": (
            "Shape counts cannot justify text conversion alone: keep merge effects and serialization markers. "
            "Ancestor and nested function records overlap; do not sum them as page-wide allocations."
        ),
        "native_sha256": hashlib.sha256(Path(native.__file__).read_bytes()).hexdigest(),
        "profiled_self_total_ms": sum(r["instrumented_self_ms"] for r in rows),
        "all_checked_outputs_equal": True,
        "constructions": dict(constructions),
        "function_summary": function_summary,
        "function_results_at_creation": functions,
        "rows": rows,
        "hashes": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("variant", "constructions", "function_summary")}, indent=2))
    for row in rows[:25]:
        print(json.dumps(row))


if __name__ == "__main__":
    main()

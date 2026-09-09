"""Measure non-overlapping render phases using the original diagnostic boundaries."""

from __future__ import annotations

import argparse
import functools
import hashlib
import inspect
import itertools
import json
import platform
import statistics
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "packages/py/citry"), str(ROOT / "packages/py/citry_core")]

import citry.citry_render as crr  # noqa: E402
import citry.component_render as cr  # noqa: E402
import citry.serialize as ser  # noqa: E402
import citry.util.id as ids  # noqa: E402
import citry_core._rust as native  # noqa: E402
from benchmarks.ownership_journal_probe.probe import scenario  # noqa: E402
from citry import nodes  # noqa: E402
from citry.component import Component  # noqa: E402
from citry.extension import ExtensionManager  # noqa: E402
from citry.ownership import OwnershipGraph  # noqa: E402
from citry.slots import Slot  # noqa: E402

GROUPS = {
    "Component construction and typed inputs": "Component setup and orchestration",
    "Component generator hooks": "Component setup and orchestration",
    "Queue and replacement tree scans": "Component setup and orchestration",
    "Component lifecycle coordination": "Component setup and orchestration",
    "Component finalization coordination": "Component setup and orchestration",
    "Component lifecycle and remaining orchestration": "Component setup and orchestration",
    "Child inputs and slot-fill preparation": "Child inputs and slots",
    "Slot invocation": "Child inputs and slots",
    "Extension hooks": "Extension hooks and configuration allocation",
    "Extension configuration allocation": "Extension hooks and configuration allocation",
    "Expressions and control flow": "Body traversal, expressions and control flow",
    "Body traversal and result assembly": "Body traversal, expressions and control flow",
}


def main() -> None:
    """Compare ordinary timing with bounded, nested-subtracted operation timers."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=30)
    parser.add_argument("--instrumented-samples", type=int, default=10)
    parser.add_argument("--detail-value-conversion", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if min(args.samples, args.instrumented_samples) < 1:
        parser.error("Sample counts must be positive")
    module = scenario()
    data = module.gen_render_data()
    for _ in range(6):
        module.render(data)
    ordinary = []
    expected = None
    for _ in range(args.samples):
        ids._id_counter = itertools.count()
        start = time.perf_counter_ns()
        element = module.ProjectPage(**data)
        composed = time.perf_counter_ns()
        rendered = element.render()
        settled = time.perf_counter_ns()
        html = rendered.serialize()
        finished = time.perf_counter_ns()
        ordinary.append(
            {
                "compose_ms": (composed - start) / 1_000_000,
                "tree_ms": (settled - composed) / 1_000_000,
                "serialize_ms": (finished - settled) / 1_000_000,
                "total_ms": (finished - start) / 1_000_000,
            }
        )
        if expected is None:
            expected = html
        elif html != expected:
            raise RuntimeError("Ordinary renders changed HTML with deterministic IDs")

    stack: list[list[int]] = []
    totals: dict[str, int] = defaultdict(int)
    counts: dict[str, int] = defaultdict(int)
    patches = []

    def patch(owner: Any, name: str, category: str) -> None:
        original = getattr(owner, name)
        if inspect.isgeneratorfunction(original):
            raise TypeError(f"Cannot time generator creation as execution: {name}")

        @functools.wraps(original)
        def measured(*values: Any, **kwargs: Any) -> Any:
            start = time.perf_counter_ns()
            frame = [0]
            stack.append(frame)
            try:
                return original(*values, **kwargs)
            finally:
                elapsed = time.perf_counter_ns() - start
                stack.pop()
                totals[category] += elapsed - frame[0]
                counts[category] += 1
                if stack:
                    stack[-1][0] += elapsed

        patches.append((owner, name, original))
        setattr(owner, name, measured)

    records = []
    try:
        for name in (
            "record_source_location",
            "record_component_invocation",
            "record_template_fill",
            "bind_instance",
            "bind_supplied_slots",
            "capture_slot_call",
            "selected_region_ids",
            "retire_component_output",
            "settle_component",
            "retire_unselected_after",
            "rebind_slot_region",
            "bind_template_fill_sources",
            "retire_range",
            "release_transient_region_results",
        ):
            patch(OwnershipGraph, name, "Ownership." + name)
        patch(ser, "serialize_render_result", "Nested serialization")
        for name in ("__init__", "_finalize_inputs"):
            patch(Component, name, "Component construction and typed inputs")
        patch(cr, "_normalize_data", "Component construction and typed inputs")
        patch(ExtensionManager, "_init_component_instance", "Extension configuration allocation")
        for name in (
            "on_component_input",
            "on_component_data",
            "on_component_rendered",
            "on_render_context_merge",
            "on_attrs_resolved",
            "on_slot",
        ):
            if hasattr(ExtensionManager, name):
                patch(ExtensionManager, name, "Extension hooks")
        for cls in list(module.__dict__.values()):
            if isinstance(cls, type) and issubclass(cls, Component):
                for name in ("template_data", "js_data", "css_data"):
                    if name in cls.__dict__:
                        patch(cls, name, "Application data callbacks")
        patch(cr, "_send_into_generator", "Component generator hooks")
        patch(nodes.ElementAttrsNode, "render", "Element attributes")
        if args.detail_value_conversion:
            # Slot callbacks convert their result inside the ownership timer;
            # expose that work before attributing the whole bucket to records.
            patch(crr, "_render_value", "Value conversion")
            patch(nodes, "_render_value", "Value conversion")
        patch(nodes.ComponentNode, "render", "Child inputs and slot-fill preparation")
        patch(nodes.SlotNode, "render", "Slot invocation")
        patch(Slot, "__call__", "Slot invocation")
        for cls in (nodes.ExprNode, nodes.IfNode, nodes.ForNode):
            patch(cls, "render", "Expressions and control flow")
        patch(cr, "_render_body", "Body traversal and result assembly")
        for name in (
            "_get_compiled_template",
            "extract_const_vars",
            "pure_body_lookup",
            "_replay_pure_body",
            "_render_and_capture_pure_body",
        ):
            patch(cr, name, "Template and reusable-body cache work")
        for name in ("_scan_deferred", "_contains_deferred", "_render_ids", "_render_selection", "_render_objects"):
            patch(cr, name, "Queue and replacement tree scans")
        patch(cr, "_render_one", "Component lifecycle coordination")
        patch(cr, "_finalize", "Component finalization coordination")
        patch(cr, "render_impl", "Component lifecycle and remaining orchestration")
        for _ in range(args.instrumented_samples):
            ids._id_counter = itertools.count()
            element = module.ProjectPage(**data)
            totals.clear()
            counts.clear()
            start = time.perf_counter_ns()
            rendered = element.render()
            elapsed = time.perf_counter_ns() - start
            if stack:
                raise RuntimeError("Unbalanced diagnostic timer stack")
            records.append(
                {
                    "tree_ms": elapsed / 1_000_000,
                    "phases_ms": {key: value / 1_000_000 for key, value in totals.items()},
                    "calls": dict(counts),
                }
            )
            if rendered.serialize() != expected:
                raise RuntimeError("Instrumented rendering changed HTML")
    finally:
        for owner, name, original in reversed(patches):
            setattr(owner, name, original)
    mean_tree = statistics.mean(row["tree_ms"] for row in records)
    categories = {key for row in records for key in row["phases_ms"]}
    phases = {
        key: {
            "mean_ms": statistics.mean(row["phases_ms"].get(key, 0) for row in records),
            "mean_calls": statistics.mean(row["calls"].get(key, 0) for row in records),
        }
        for key in sorted(categories)
    }
    groups: dict[str, float] = defaultdict(float)
    for key, value in phases.items():
        group = "Ownership tracking" if key.startswith("Ownership.") else GROUPS.get(key, key)
        groups[group] += value["mean_ms"]
    # Match the original report: outer wrapper/assignment time belongs to orchestration.
    unattributed = mean_tree - sum(groups.values())
    groups["Component setup and orchestration"] += unattributed
    report = {
        "revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),  # noqa: S607
        "detail_value_conversion": args.detail_value_conversion,
        "python": sys.version,
        "platform": platform.platform(),
        "native_sha256": hashlib.sha256(Path(native.__file__).read_bytes()).hexdigest(),
        "scenario_sha256": hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
        "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "ordinary_samples": ordinary,
        "ordinary_medians_ms": {key: statistics.median(row[key] for row in ordinary) for key in ordinary[0]},
        "ordinary_mean_tree_ms": statistics.mean(row["tree_ms"] for row in ordinary),
        "instrumented_samples": records,
        "mean_instrumented_tree_ms": mean_tree,
        "phases": phases,
        "groups": {
            key: {"mean_ms": value, "share_percent": value / mean_tree * 100}
            for key, value in sorted(groups.items(), key=lambda item: -item[1])
        },
        "outer_time_included_in_orchestration_ms": unattributed,
        "all_outputs_equal": True,
        "output_bytes": len(expected.encode()),
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {key: report[key] for key in ("ordinary_medians_ms", "mean_instrumented_tree_ms", "groups")}, indent=2
        )
    )


if __name__ == "__main__":
    main()

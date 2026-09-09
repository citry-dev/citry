"""Inventory component cases and their current work without timing instrumentation."""

from __future__ import annotations

import hashlib
import itertools
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from benchmarks.ownership_journal_probe.probe import scenario  # noqa: E402
from benchmarks.render_structure_probe.census import canonical, digest  # noqa: E402


def observe(module: Any, inputs: Any, *, instrumented: bool) -> dict[str, Any]:
    """Keep live references until classification so object IDs cannot be recycled."""
    import citry.component_render as rendering  # noqa: PLC0415
    import citry.util.id as ids  # noqa: PLC0415
    from citry.citry_context import CitryContext  # noqa: PLC0415
    from citry.citry_render import CitryRender, RenderFrame, _PhysicalRegion  # noqa: PLC0415
    from citry.component import Component  # noqa: PLC0415
    from citry.ext.dependencies.scripts import has_component_asset  # noqa: PLC0415
    from citry.extension import ExtensionConfig, ExtensionManager  # noqa: PLC0415
    from citry.nodes import ComponentNode, SlotNode  # noqa: PLC0415
    from citry.ownership import OwnershipGraph  # noqa: PLC0415
    from citry.ownership_manifest import _render_parts_use_alpine  # noqa: PLC0415

    components: dict[int, Any] = {}
    rows: dict[int, dict[str, Any]] = {}
    work: dict[int, Counter[str]] = defaultdict(Counter)
    settled: list[tuple[int, Any]] = []
    unattributed: Counter[str] = Counter()
    watched = {
        ComponentNode.render.__code__: "nested_component_tags",
        SlotNode.render.__code__: "slot_outlets",
        OwnershipGraph.record_source_location.__code__: "source_occurrences",
        OwnershipGraph.record_template_fill.__code__: "template_fills",
        OwnershipGraph.capture_slot_call.__code__: "slot_captures",
        CitryContext.__init__.__code__: "context_constructions",
        RenderFrame.from_context.__func__.__code__: "frame_snapshots",
        ExtensionConfig.__init__.__code__: "base_config_initializations",
        ExtensionManager.on_component_input.__code__: "input_dispatches",
        ExtensionManager.on_component_data.__code__: "data_dispatches",
        ExtensionManager.on_component_rendered.__code__: "finish_dispatches",
    }

    def profile(frame: Any, event: str, result: Any) -> None:
        code = frame.f_code
        local = frame.f_locals
        if event == "call" and code is rendering._render_one.__code__:
            parent = local.get("parent")
            if parent is not None:
                components[id(parent)] = parent
                work[id(parent)]["child_render_calls_with_parent"] += 1
        elif event == "call" and code in watched:
            component = local.get("component")
            context = local.get("context")
            if component is None and context is not None:
                component = context.component
            if component is not None:
                key = id(component)
                components[key] = component
                work[key][watched[code]] += 1
            else:
                # Slot capture has no context argument, so do not guess which component owns the call.
                unattributed[watched[code]] += 1
        elif event == "return" and code is rendering._render_one.__code__ and result is not None:
            component = local["component"]
            cls = type(component)
            key = id(component)
            components[key] = component
            rows[key] = {
                "class": cls.__name__,
                "module": cls.__module__,
                "parent_class": type(component.parent).__name__ if component.parent is not None else None,
                "supplied_slots": len(component.raw_slots),
                "kwargs_count": len(component.raw_kwargs),
                "kwargs_schema": cls.Kwargs is not None,
                "slots_schema": cls.Slots is not None,
                "custom_init": cls.__init__ is not Component.__init__,
                "custom_template_data": cls.template_data is not Component.template_data,
                "custom_js_data": cls.js_data is not Component.js_data,
                "custom_css_data": cls.css_data is not Component.css_data,
                "custom_on_render": cls.on_render is not Component.on_render,
                "js_data_nonempty": bool(local.get("js_data")),
                "css_data_nonempty": bool(local.get("css_data")),
                "data_callbacks_reached": "js_data" in local and "css_data" in local,
                "pure": bool(cls.pure),
                "transparent": bool(cls.transparent),
                "client_tag_bindings": bool(component._component_tag_client_bindings),
                "inherited_provides": bool(component._provides_inherited),
                "own_provides": bool(component._provides_own),
                "context_extra_keys_after_body": sorted(local["context"].extra),
                "extensions": [
                    type(ext).__module__ + "." + type(ext).__name__ for ext in cls.citry.extensions._extensions
                ],
            }
        elif event == "return" and code is rendering._finalize.__code__ and result is not None:
            component = result.context.component
            if component is not None:
                settled.append((id(component), result))

    original_snapshot = OwnershipGraph.snapshot
    snapshots = []

    def snapshot(graph: Any) -> Any:
        result = original_snapshot(graph)
        snapshots.append(digest(canonical(result)))
        return result

    ids._id_base = 123456
    ids._id_counter = itertools.count()
    OwnershipGraph.snapshot = snapshot
    try:
        if instrumented:
            sys.setprofile(profile)
        output = module.render(inputs)
    finally:
        sys.setprofile(None)
        OwnershipGraph.snapshot = original_snapshot
    if len(snapshots) != 4:
        raise RuntimeError("Expected four full ownership snapshot observations")
    if instrumented:
        alpine = _render_parts_use_alpine([(render, render.frame.render_id) for _key, render in settled])
        alpine_by_component = defaultdict(bool)
        # Separate a component's own output from content placed in captured slot regions.
        own_parts = []
        for _key, render in settled:
            chunks = []
            pending = list(reversed(render.parts))
            while pending:
                part = pending.pop()
                # Render-shaped physical wrappers must stop before the CitryRender branch.
                if isinstance(part, _PhysicalRegion):
                    continue
                if isinstance(part, str):
                    chunks.append(part)
                elif isinstance(part, CitryRender) and (
                    not part.is_component_root or part.frame.render_id in (None, render.frame.render_id)
                ):
                    pending.extend(reversed(part.parts))
            own_parts.append(("".join(chunks), None))
        own_alpine = _render_parts_use_alpine(own_parts)
        own_alpine_by_component = defaultdict(bool)
        for (key, _render), uses_alpine in zip(settled, own_alpine, strict=True):
            own_alpine_by_component[key] |= uses_alpine
        finalized = Counter()
        child_frames: dict[int, set[str]] = defaultdict(set)
        for (key, _render), uses_alpine in zip(settled, alpine, strict=True):
            alpine_by_component[key] |= uses_alpine
            finalized[key] += 1
            # Physical child frames also reveal rendered values inserted through expressions.
            pending = list(_render.parts)
            seen = set()
            while pending:
                part = pending.pop()
                if id(part) in seen:
                    continue
                seen.add(id(part))
                if isinstance(part, _PhysicalRegion):
                    pending.append(part.part)
                elif isinstance(part, CitryRender):
                    if part.is_component_root and part.frame.render_id not in (None, _render.frame.render_id):
                        child_frames[key].add(part.frame.render_id)
                    else:
                        pending.extend(part.parts)
        for key, row in rows.items():
            cls = type(components[key])
            row.update(
                js_asset=has_component_asset("js", cls),
                css_asset=has_component_asset("css", cls),
                external_dependencies=bool(cls.get_dependencies()),
                observed_direct_alpine=alpine_by_component[key],
                observed_alpine_outside_slot_regions=own_alpine_by_component[key],
                finalizations_observed=finalized[key],
                observed_direct_child_frames=len(child_frames[key]),
                work=dict(work[key]),
            )
            client = any(
                row[name]
                for name in (
                    "js_asset",
                    "css_asset",
                    "external_dependencies",
                    "js_data_nonempty",
                    "css_data_nonempty",
                    "client_tag_bindings",
                    "observed_direct_alpine",
                )
            )
            has_slots = row["supplied_slots"] > 0 or work[key]["slot_outlets"] > 0
            has_children = (
                work[key]["nested_component_tags"] > 0
                or work[key]["child_render_calls_with_parent"] > 0
                or bool(child_frames[key])
            )
            if client:
                case = "observed_client_or_asset_work"
            elif has_slots:
                case = "slots_without_observed_client_or_asset_work"
            elif has_children:
                case = "nested_calls_without_slots_or_observed_client_or_asset_work"
            else:
                case = "observed_plain_leaf"
            row["case"] = case
    groups: dict[str, Counter[str]] = defaultdict(Counter)
    classes: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows.values():
        group = groups[row["case"]]
        group["occurrences"] += 1
        group.update(row["work"])
        for name in ("custom_init", "custom_template_data", "custom_on_render", "kwargs_schema", "pure"):
            group[name] += row[name]
        classes[row["case"]][row["class"]] += 1
    return {
        "instrumented": instrumented,
        "html_digest": hashlib.sha256(output.encode()).hexdigest(),
        "output_bytes": len(output.encode()),
        "snapshot_digests": snapshots,
        "components": list(rows.values()),
        "unattributed_work": dict(unattributed),
        "groups": {name: dict(counts) for name, counts in sorted(groups.items())},
        "group_classes": {name: dict(counts) for name, counts in sorted(classes.items())},
    }


def main() -> None:
    """Compare the census with an ordinary render under each retained input case."""
    import citry_core._rust as native  # noqa: PLC0415

    module = scenario()
    data = module.gen_render_data()
    for _ in range(6):
        module.render(data)
    cases = []
    for label, inputs in (("large", data), ("one_output", {**data, "outputs": data["outputs"][:1]})):
        reference = observe(module, inputs, instrumented=False)
        measured = observe(module, inputs, instrumented=True)
        for key in ("html_digest", "output_bytes", "snapshot_digests"):
            if reference[key] != measured[key]:
                raise RuntimeError(f"Census changed {key} in {label}")
        cases.append({"name": label, "reference": reference, "census": measured})
    report = {
        "diagnostic_only": True,
        "classification_is_observed_not_proven": True,
        "python": sys.version,
        "native_sha256": hashlib.sha256(Path(native.__file__).read_bytes()).hexdigest(),
        "revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),  # noqa: S607
        "cases": cases,
        "hashes": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (
                Path(__file__),
                Path(__file__).with_name("plan.md"),
                ROOT / "benchmarks/render_structure_probe/census.py",
                ROOT / "benchmarks/ownership_journal_probe/probe.py",
                ROOT / "benchmarks/utils.py",
                ROOT / "packages/py/citry/tests/test_benchmark_citry.py",
                *sorted((ROOT / "packages/py/citry/citry").rglob("*.py")),
            )
        },
    }
    path = ROOT / "benchmarks/results/repeat-render/component-cases-census.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            [
                {"name": row["name"], "groups": row["census"]["groups"], "classes": row["census"]["group_classes"]}
                for row in cases
            ],
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

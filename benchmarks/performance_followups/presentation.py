"""Qualify the remaining presentation declarations through the public simple API."""

from __future__ import annotations

# ruff: noqa: S101 - benchmark assertions are enabled explicitly below.
import ast
import hashlib
import json
import sys
import types
from collections import Counter
from pathlib import Path
from typing import Any

if not __debug__:
    raise RuntimeError("Run benchmark verification without Python optimization")

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "packages/py/citry"), str(ROOT / "packages/py/citry_core")]

from benchmarks.simple_api_probe import timing as baseline  # noqa: E402
from benchmarks.utils import get_benchmark_script  # noqa: E402

CANDIDATES = (
    "MenuList",
    "Table",
    "Breadcrumbs",
    "ListComponent",
    "TabsStatic",
    "ProjectStatusUpdates",
    "ProjectOutputBadge",
    "ProjectOutputs",
    "ProjectOutputsSummary",
    "ProjectInfo",
    "ProjectNotes",
    "Navbar",
    "ProjectPage",
)


def load(extra: tuple[str, ...] = ()) -> tuple[Any, str]:
    """Change authored declarations before class creation, without patching runtime code."""
    path = ROOT / "packages/py/citry/tests/test_benchmark_citry.py"
    tree = ast.parse(get_benchmark_script(path), filename=str(path))
    selected = set(baseline.SELECTED) | set(extra)
    found = set()
    for cls in tree.body:
        if not isinstance(cls, ast.ClassDef) or cls.name not in selected:
            continue
        callback = next((n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "template_data"), None)
        if callback is not None:
            if callback.decorator_list or [arg.arg for arg in callback.args.args] != ["self", "kwargs", "slots"]:
                raise AssertionError(f"Unexpected callback signature: {cls.name}")
            if any(isinstance(n, ast.Name) and n.id == "self" for n in ast.walk(callback)):
                raise AssertionError(f"Instance-dependent callback: {cls.name}")
            callback.args.args.pop(0)
            callback.decorator_list.append(ast.Name(id="staticmethod", ctx=ast.Load()))
        cls.body.insert(
            0, ast.Assign(targets=[ast.Name(id="simple", ctx=ast.Store())], value=ast.Constant(value=True))
        )
        found.add(cls.name)
    if found != selected:
        raise AssertionError(f"Missing declarations: {selected - found}")
    ast.fix_missing_locations(tree)
    module = types.ModuleType("presentation_followup_scenario")
    module.__file__ = str(path)
    sys.modules[module.__name__] = module
    exec(compile(tree, str(path), "exec"), module.__dict__)  # noqa: S102
    return module, hashlib.sha256(ast.dump(tree).encode()).hexdigest()


def qualify() -> dict[str, Any]:
    """Require real declaration/template validation and unchanged application content."""
    baseline.ids._id_base = 123456
    control, control_hash = load()
    control_state, _ = baseline.observe(control, control.gen_render_data())
    control_callbacks = callback_counts(control)
    results = {}
    eligible = []
    for name in CANDIDATES:
        try:
            module, tree_hash = load((name,))
            state, _ = baseline.observe(module, module.gen_render_data())
            if state["projected_sha256"] != control_state["projected_sha256"]:
                raise AssertionError("Application content differs")
            if substantive_calls(state) != substantive_calls(control_state):
                raise AssertionError("Component invocation counts differ")
            if state["component_calls"].get("TemplateRoot", 0) != int(name == "ProjectPage"):
                raise AssertionError("Unexpected transparent root count")
            if callback_counts(module) != control_callbacks:
                raise AssertionError("Application data callback counts differ")
            eligible.append(name)
            results[name] = {"eligible": True, "identities": state["generated_ids"], "scenario_sha256": tree_hash}
        except Exception as exc:  # noqa: BLE001 - qualification records each rejected declaration
            results[name] = {"eligible": False, "error": f"{type(exc).__name__}: {exc}"}
    module, tree_hash = load(tuple(eligible))
    combined, _ = baseline.observe(module, module.gen_render_data())
    assert combined["projected_sha256"] == control_state["projected_sha256"]
    assert substantive_calls(combined) == substantive_calls(control_state)
    assert combined["component_calls"].get("TemplateRoot", 0) == 1
    assert callback_counts(module) == control_callbacks
    return {
        "eligible": eligible,
        "declarations": results,
        "combined_scenario_sha256": tree_hash,
        "control_scenario_sha256": control_hash,
        "control": control_state,
        "combined": combined,
        "callbacks": control_callbacks,
    }


def substantive_calls(state: dict[str, Any]) -> dict[str, int]:
    """A simple root adds one transparent TemplateRoot; other calls must agree."""
    return {name: count for name, count in state["component_calls"].items() if name != "TemplateRoot"}


def callback_counts(module: Any) -> dict[str, int]:
    """Count every authored data callback in an additional, untimed render."""
    codes = {}
    for name, cls in vars(module).items():
        if not isinstance(cls, type) or cls.__module__ != module.__name__:
            continue
        callback = cls.__dict__.get("template_data")
        if callback is not None:
            codes[cls.template_data.__code__] = name
    counts = Counter()

    def profile(frame: types.FrameType, event: str, _arg: Any) -> None:
        if event == "call" and frame.f_code in codes:
            counts[codes[frame.f_code]] += 1

    data = module.gen_render_data()
    previous = sys.getprofile()
    try:
        sys.setprofile(profile)
        module.render(data)
    finally:
        sys.setprofile(previous)
    return dict(counts)


if __name__ == "__main__":
    print(json.dumps(qualify()))

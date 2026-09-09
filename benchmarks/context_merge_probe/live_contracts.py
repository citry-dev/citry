"""Check ordered dictionary operations and live hook overrides."""

from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from live_probe import DECLARATIONS, MANAGER, ORIGINAL, ROOT, merge_context


def manager() -> Any:
    """Build only the manager state read by these merge implementations."""
    value = MANAGER.__new__(MANAGER)
    value.citry = object()
    value._hook_extensions_cache = {
        "on_render_context_merge": tuple(cls.__new__(cls) for cls in DECLARATIONS),
    }
    return value


def observe(changed: bool, pair: tuple[dict, dict], *, override: bool = False) -> dict[str, Any]:
    """Run one merge on copied mappings while preserving alias relationships."""
    parent, child = (SimpleNamespace(extra=extra) for extra in deepcopy(pair))
    owner = manager()
    calls = []
    if override:
        extension = owner._hook_extensions_cache["on_render_context_merge"][0]

        def replaced(context: Any) -> None:
            calls.append("instance override")
            context.parent_context.extra["application"] = "hook ran"

        extension.on_render_context_merge = replaced
    (merge_context if changed else ORIGINAL)(owner, parent, child)
    return {"parent": parent.extra, "child": child.extra, "calls": calls}


def ordered(value: Any) -> Any:
    """Retain dictionary order in comparisons, since dict equality ignores it."""
    if type(value) is dict:
        return [(key, ordered(item)) for key, item in value.items()]
    if type(value) is list:
        return [ordered(item) for item in value]
    return value


def sequential_override(changed: bool) -> dict[str, Any]:
    """Let an earlier hook replace the next callback before it is resolved."""
    owner = manager()
    extensions = owner._hook_extensions_cache["on_render_context_merge"]
    calls, contexts = [], []

    def second(context: Any) -> None:
        calls.append("second")
        contexts.append(context)

    def first(context: Any) -> None:
        calls.append("first")
        contexts.append(context)
        extensions[1].on_render_context_merge = second

    extensions[0].on_render_context_merge = first
    (merge_context if changed else ORIGINAL)(owner, SimpleNamespace(extra={}), SimpleNamespace(extra={}))
    return {"calls": calls, "shared_context": len(contexts) == 2 and contexts[0] is contexts[1]}


def late_class_override(changed: bool) -> dict[str, Any]:
    """Replace a class hook after the same manager has already merged once."""
    owner = manager()
    callback = merge_context if changed else ORIGINAL
    callback(owner, SimpleNamespace(extra={}), SimpleNamespace(extra={}))
    cls = next(iter(DECLARATIONS))
    original = cls.on_render_context_merge
    calls = []

    def replacement(self: Any, context: Any) -> None:  # noqa: ARG001
        calls.append("class override")
        context.parent_context.extra["class_change"] = True

    cls.on_render_context_merge = replacement
    parent = SimpleNamespace(extra={})
    try:
        callback(owner, parent, SimpleNamespace(extra={}))
    finally:
        cls.on_render_context_merge = original
    return {"calls": calls, "parent": parent.extra}


def main() -> None:
    """Record focused mapping and callback equivalence without claiming production qualification."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    keys = tuple(DECLARATIONS.values())
    shared_outer = {keys[0]: {"same": 1}}
    shared_inner = {"same": 1}
    cases = {
        "empty": ({}, {}),
        "all_extensions": ({}, {key: {"item": index} for index, key in enumerate(keys)}),
        "overwrite_and_order": (
            {keys[0]: {"old": 1, "collision": 2}},
            {keys[0]: {"collision": 3, "new": 4}},
        ),
        "shared_outer": (shared_outer, shared_outer),
        "shared_inner": ({keys[0]: shared_inner}, {keys[0]: shared_inner}),
    }
    checks = {}
    for name, pair in cases.items():
        reference = ordered(observe(False, pair))  # noqa: FBT003
        candidate = ordered(observe(True, pair))  # noqa: FBT003
        if reference != candidate:
            raise RuntimeError(f"Declarative context merging changed {name}")
        checks[name] = {"equal": True, "result": reference}
    counterexample = {
        "reference": observe(False, ({}, {}), override=True),  # noqa: FBT003
        "candidate": observe(True, ({}, {}), override=True),  # noqa: FBT003
    }
    if counterexample["reference"] != counterexample["candidate"]:
        raise RuntimeError("Live merge dispatch omitted an instance override")
    sequence = {name: sequential_override(name == "candidate") for name in ("reference", "candidate")}
    late_class = {name: late_class_override(name == "candidate") for name in ("reference", "candidate")}
    if sequence["reference"] != sequence["candidate"] or late_class["reference"] != late_class["candidate"]:
        raise RuntimeError("Live merge dispatch changed hook replacement behavior")
    report = {
        "production_qualified": False,
        "checks": checks,
        "instance_override": counterexample,
        "sequential_override": sequence,
        "late_class_override": late_class,
        "hashes": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (Path(__file__).resolve(), Path(__file__).with_name("live_probe.py"))
        },
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

"""
Check the candidate's dispatch rules with each interpreter's own typing code.

This uses the real conversion function source with small Python-only stand-ins
for Citry objects. It qualifies protocol dispatch, not the full native runtime.
"""

from __future__ import annotations

import argparse
import ast
import html
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

ROOT = Path(__file__).resolve().parents[2]


class Escaped(str):
    """Keep escaping observable in both text and output type."""

    __slots__ = ()


class Render:
    """Match the production render's absence of an instance dictionary."""

    __slots__ = ("__weakref__", "context", "frame", "parts")


class Element:
    """Stand in for the element dispatch type without loading a native module."""


class Region:
    """Stand in for a non-render structural output type."""


class Slot:
    """Stand in for the earlier slot dispatch type."""


@runtime_checkable
class ComponentLike(Protocol):
    """Use the host interpreter's actual protocol implementation."""

    def __citry_element__(self, engine: Any) -> Any: ...


def resolve(value: Any, engine: Any) -> Any:
    """Keep resolver exceptions and missing-method errors observable."""
    return value.__citry_element__(engine)


def member(self: Any, engine: Any) -> Any:  # noqa: ARG001
    """Signal that dynamic component behavior was reached."""
    raise LookupError("resolver reached")


def outcome(function: Any, value: Any) -> Any:
    """Compare identity for renders and type/text for scalar results or errors."""
    try:
        result = function(value)
    except Exception as error:  # noqa: BLE001 - exception parity is under test
        return "error", type(error), str(error)
    return ("identity", result is value) if isinstance(result, Render) else ("result", type(result), result)


def main() -> None:
    """Run representative static, dynamic, rebound and registered cases."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--production", action="store_true")
    args = parser.parse_args()
    source_path = ROOT / "packages/py/citry/citry/citry_render.py"
    source = source_path.read_text()
    tree = ast.parse(source)
    node = next(item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == "_render_value")
    function_source = ast.get_source_segment(source, node)
    if not args.production and "_DEFAULT_VALUE_TYPES" in function_source:
        parser.error("Prototype mode requires a pre-production checkout; use --production for current code")
    production_source = function_source
    if args.production:
        source = subprocess.check_output(
            ["git", "show", "49852e7:packages/py/citry/citry/citry_render.py"],  # noqa: S607
            cwd=ROOT,
            text=True,
        )
        node = next(
            item
            for item in ast.parse(source).body
            if isinstance(item, ast.FunctionDef) and item.name == "_render_value"
        )
        function_source = ast.get_source_segment(source, node)
    probe_path = Path(__file__).with_name("probe.py")
    snippet_node = next(
        item
        for item in ast.parse(probe_path.read_text()).body
        if isinstance(item, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "SNIPPET" for target in item.targets)
    )
    snippet = ast.literal_eval(snippet_node.value)
    scope = {
        "CitryRender": Render,
        "CitryElement": Element,
        "PhysicalRegionPart": Region,
        "Slot": Slot,
        "ComponentLike": ComponentLike,
        "const_value": lambda value: value,
        "escape": lambda value: Escaped(html.escape(str(value))),
        "_resolve_component_like": resolve,
        "_probe_render": Render,
        "_probe_element": Element,
        "_probe_region_part": Region,
        "_probe_component_like": ComponentLike,
        "_DEFAULT_VALUE_TYPES": (ComponentLike, Element, Render, Region),
    }
    original_scope, changed_scope = {}, {}
    exec("from __future__ import annotations\n" + function_source, scope, original_scope)  # noqa: S102
    changed_source = (
        production_source
        if args.production
        else function_source.replace(
            "    if isinstance(value, ComponentLike):", snippet + "    if isinstance(value, ComponentLike):"
        )
    )
    exec("from __future__ import annotations\n" + changed_source, scope, changed_scope)  # noqa: S102
    original, changed = original_scope["_render_value"], changed_scope["_render_value"]
    checked = []

    def check(label: str, value: Any) -> None:
        expected, actual = outcome(original, value), outcome(changed, value)
        if expected != actual:
            raise AssertionError((label, expected, actual))
        checked.append(label)

    check("text", "<&")
    check("render", Render())
    check("integer", 1)

    class Child(Render):
        pass

    child = Child()
    child.__citry_element__ = lambda engine: member(child, engine)
    check("instance-member", child)
    Child.__citry_element__ = member
    check("subclass-member", Child())
    Render.__citry_element__ = member
    check("added-class-member", Render())
    del Render.__citry_element__
    check("removed-class-member", Render())
    Render.__getattr__ = (
        lambda self, name: (lambda engine: member(self, engine)) if name == "__citry_element__" else None
    )
    check("dynamic-getattr", Render())
    del Render.__getattr__

    def getattribute(self: Any, name: str) -> Any:
        if name == "__citry_element__":
            return lambda engine: member(self, engine)
        return object.__getattribute__(self, name)

    Render.__getattribute__ = getattribute
    check("dynamic-getattribute", Render())
    del Render.__getattribute__
    for name in ("CitryRender", "PhysicalRegionPart"):
        saved = scope[name]
        scope[name] = str
        check("rebound-" + name, "<&")
        scope[name] = saved
    # Registration must be last because ABC state survives class member removal.
    ComponentLike.register(str)
    check("registered-str", "<&")
    ComponentLike.register(Render)
    check("registered-render", Render())
    print(
        json.dumps(
            {
                "python": sys.version,
                "production": args.production,
                "dispatch_cases": checked,
                "native_runtime_tested": False,
            }
        )
    )


if __name__ == "__main__":
    main()

"""Show why pending work captured before later node execution can become stale."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from citry import Citry, CitryContext, CitryRender, Component  # noqa: E402
from citry.citry_render import DeferredComponent  # noqa: E402
from citry.component_render import _render_body, _scan_deferred  # noqa: E402
from citry.nodes import Node  # noqa: E402


def main() -> None:
    """Exercise three mutations through the existing body-render entry point."""
    engine = Citry()

    class Parent(Component):
        citry = engine

    class First(Component):
        citry = engine

    class Second(Component):
        citry = engine

    def run_case(operation: str) -> dict[str, Any]:
        parent = Parent._create_instance()
        context = CitryContext(component=parent)
        first = DeferredComponent(First(), parent)
        second = DeferredComponent(Second(), parent)
        fragment = CitryRender(parts=[] if operation == "append" else [first], context=context)
        captured = []

        class Emit(Node):
            def render(self, context: CitryContext) -> CitryRender:
                # Model discovery when construction first emits this fragment.
                captured.extend(_scan_deferred(fragment))
                return fragment

        class Mutate(Node):
            def render(self, context: CitryContext) -> str:
                # A later custom node can legally hold the same mutable result.
                if operation == "append":
                    fragment.parts.append(first)
                elif operation == "remove":
                    fragment.parts.clear()
                else:
                    fragment.parts[0] = second
                return ""

        result = CitryRender(parts=_render_body([Emit(), Mutate()], context), context=context)
        actual = _scan_deferred(result)

        def targets(tasks: list[Any]) -> list[str]:
            return [task.deferred.element.comp_cls.__name__ for task in tasks]

        before, after = targets(captured), targets(actual)
        expected = {"append": ([], ["First"]), "remove": (["First"], []), "replace": (["First"], ["Second"])}
        if (before, after) != expected[operation]:
            raise RuntimeError(f"Unexpected mutation behavior: {operation}")
        return {"mutation": operation, "captured_during_emission": before, "discovered_after_body": after}

    rows = [run_case(operation) for operation in ("append", "remove", "replace")]
    report = {
        "diagnostic_only": True,
        "cases": rows,
        "hashes": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (
                Path(__file__),
                ROOT / "packages/py/citry/citry/component_render.py",
                ROOT / "packages/py/citry/citry/citry_render.py",
            )
        },
    }
    path = ROOT / "benchmarks/results/performance-render/render-structure-mutation-boundary.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()

"""Check borrowed-fragment mutations, render cleanup and constructor exposure."""

from __future__ import annotations

import hashlib
import itertools
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from benchmarks.producer_schedule_probe import adapter  # noqa: E402

from citry import Citry, CitryContext, CitryRender, Component, Extension  # noqa: E402
from citry import component_render as cr  # noqa: E402
from citry.citry_render import DeferredComponent  # noqa: E402
from citry.nodes import Node  # noqa: E402


def mutation(changed: bool, operation: str) -> dict[str, Any]:
    """Run mutation nodes inside a real initial component body and scheduler."""
    fragments = {}

    class Emit(Node):
        def render(self, context: CitryContext) -> CitryRender:
            first = DeferredComponent(First(), context.component)
            second = DeferredComponent(Second(), context.component)
            result = CitryRender(parts=[] if operation == "append" else [first], context=context)
            fragments.update(result=result, first=first, second=second)
            return result

    class Mutate(Node):
        def render(self, context: CitryContext) -> str:
            result = fragments["result"]
            if operation == "append":
                result.parts.append(fragments["first"])
            elif operation == "remove":
                result.parts.clear()
            else:
                result.parts[0] = fragments["second"]
            return ""

    class Insert(Extension):
        name = "insert"

        def on_template_compiled(self, ctx: Any) -> None:
            if ctx.component_class is Parent:
                ctx.nodes[:] = [Emit(), Mutate()]

    engine = Citry(extensions=[Insert])
    counter = itertools.count(1)
    engine.id_generator = lambda: f"c{next(counter)}"

    class First(Component):
        citry = engine
        template = """
            <b>first</b>
        """

    class Second(Component):
        citry = engine
        template = """
            <i>second</i>
        """

    class Parent(Component):
        citry = engine
        template = """
            body
        """

    adapter.install(changed)
    result = Parent().render()
    return {"html": result.serialize(deps_strategy="ignore"), "scope_released": adapter.SCOPE.get() is None}


def constructor(changed: bool) -> dict[str, Any]:
    """A constructor can append pending work before the initial result returns."""
    engine = Citry()

    class Child(Component):
        citry = engine
        template = """
            child
        """

    class Parent(Component):
        citry = engine
        template = """
            before
        """

    class ExposedRender(CitryRender):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            if self.is_component_root and type(self.context.component) is Parent:
                self.parts.append(DeferredComponent(Child(), self.context.component))

    adapter.install(changed)
    original = cr.CitryRender
    cr.CitryRender = ExposedRender
    try:
        result = Parent().render()
        return {"has_pending_child": cr._contains_deferred(result), "scope_released": adapter.SCOPE.get() is None}
    finally:
        cr.CitryRender = original


def error_cleanup(changed: bool) -> dict[str, Any]:
    """The execution context must be released when rendering raises."""
    engine = Citry()

    class Broken(Component):
        citry = engine

        def template_data(self, kwargs: Any, slots: Any) -> Any:
            raise ValueError("intentional scheduling-scope failure")

    adapter.install(changed)
    try:
        Broken().render()
    except ValueError:
        return {"raised": True, "scope_released": adapter.SCOPE.get() is None}
    raise RuntimeError("The error fixture unexpectedly returned")


def main() -> None:
    rows = []
    try:
        for operation in ("append", "remove", "replace"):
            reference, candidate = (
                mutation(changed=False, operation=operation),
                mutation(changed=True, operation=operation),
            )
            if reference != candidate:
                raise RuntimeError(f"Borrowed mutation differs: {operation}")
            rows.append({"case": operation, "reference": reference, "candidate": candidate, "matches": True})
        for name, callback in (("constructor_exposure", constructor), ("error_cleanup", error_cleanup)):
            reference, candidate = callback(changed=False), callback(changed=True)
            rows.append(
                {"case": name, "reference": reference, "candidate": candidate, "matches": reference == candidate}
            )
    finally:
        adapter.install(changed=False)
    report = {
        "experiment_only": True,
        "production_compatible": all(row["matches"] for row in rows),
        "cases": rows,
        "hashes": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (Path(__file__), Path(__file__).with_name("adapter.py"), Path(cr.__file__))
        },
    }
    path = ROOT / "benchmarks/results/repeat-render/producer-schedule-contracts.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()

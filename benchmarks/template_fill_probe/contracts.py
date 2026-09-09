"""Expose callable changes after eligibility and helper identity checks."""

from __future__ import annotations

import hashlib
import itertools
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from benchmarks.template_fill_probe import adapter  # noqa: E402

from citry import Citry, Component, ownership  # noqa: E402


def render_case(changed: bool, operation: str) -> dict[str, Any]:
    """Use actual slot outlets so selection happens between preparation and invocation."""
    engine = Citry()
    counter = itertools.count(1)
    engine.id_generator = lambda: f"c{next(counter)}"

    class Child(Component):
        citry = engine
        template = """
            <c-slot>fallback</c-slot>
        """

    class Parent(Component):
        citry = engine
        template = """
            <c-child>supplied</c-child>
        """

    original_selection = ownership._SelectedSupply
    original_render = adapter.CONTENT._render

    def replacement(ctx: Any) -> Any:
        return ctx.fallback()

    def select(**kwargs: Any) -> Any:
        # Selection constructs this record after the shortcut's eligibility check.
        kwargs["slot"].content_func = replacement
        return original_selection(**kwargs)

    class EqualCallable:
        __hash__ = None

        def __eq__(self, other: object) -> bool:
            return True

        def __call__(self, ctx: Any) -> str:
            return "replacement"

    adapter.install(changed)
    adapter.COUNTS = Counter()
    if operation == "selection_replaces_content":
        ownership._SelectedSupply = select
    elif operation == "equal_helper":
        adapter.CONTENT._render = EqualCallable()
    try:
        component = Child(slots={"default": replacement}) if operation == "python_fallback" else Parent()
        try:
            html = component.render().serialize(deps_strategy="ignore")
            result = {"html": html}
        except (AttributeError, TypeError, RuntimeError) as error:
            result = {"error_type": type(error).__name__, "error": str(error)}
        return {"result": result, "activation": dict(adapter.COUNTS)}
    finally:
        ownership._SelectedSupply = original_selection
        adapter.CONTENT._render = original_render
        adapter.COUNTS = None


def main() -> None:
    rows = []
    try:
        for operation in ("ordinary_template", "python_fallback", "selection_replaces_content", "equal_helper"):
            reference = render_case(changed=False, operation=operation)
            candidate = render_case(changed=True, operation=operation)
            rows.append(
                {
                    "case": operation,
                    "reference": reference,
                    "candidate": candidate,
                    "matches": reference["result"] == candidate["result"],
                }
            )
    finally:
        adapter.install(changed=False)
    report = {
        "experiment_only": True,
        "production_compatible": all(row["matches"] for row in rows),
        "cases": rows,
        "hashes": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (Path(__file__), Path(adapter.__file__), Path(ownership.__file__))
        },
    }
    path = ROOT / "benchmarks/results/performance-render/template-fill-contracts.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()

"""Check whether a shared output buffer preserves extension merge contexts."""

from __future__ import annotations

# ruff: noqa: S101 - output_buffer imports the explicit assertion guard.
import json
from typing import Any

from benchmarks.performance_followups.output_buffer import ORIGINAL_BODY, install, runtime

from citry import Citry, Component, Extension


def _run(candidate: bool) -> dict[str, Any]:
    """Record public merge-hook inputs for an ordinary child inside simple loops."""
    runtime._render_body = ORIGINAL_BODY
    if candidate:
        install()
    merges: list[dict[str, Any]] = []

    class Observe(Extension):
        name = "observe"

        def on_render_context_merge(self, ctx: Any) -> None:
            merges.append(
                {
                    "parent_class": type(ctx.parent_context.component).__name__,
                    "child_class": type(ctx.child_context.component).__name__,
                    "parent_item": ctx.parent_context.variables.get("item"),
                    "child_item": ctx.child_context.variables.get("item"),
                }
            )

    app = Citry(extensions=[Observe])

    class Child(Component):
        citry = app
        template = """
            <b>{{ value }}</b>
        """

    class SimpleList(Component):
        citry = app
        simple = True
        template = """
            <c-for each="item in items">
                <c-if cond="True"><c-Child c-value="item" /></c-if>
            </c-for>
        """

    class Page(Component):
        citry = app
        template = """
            <main><c-SimpleList c-items="[1, 2]" /></main>
        """

    output = str(Page())
    return {"merges": merges, "output": output}


def run(candidate: bool) -> dict[str, Any]:
    """Restore the caller's body walker even when the witness raises."""
    previous = runtime._render_body
    try:
        return _run(candidate=candidate)
    finally:
        runtime._render_body = previous


if __name__ == "__main__":
    control = run(candidate=False)
    candidate = run(candidate=True)
    assert control["merges"] != candidate["merges"]
    print(json.dumps({"control": control, "candidate": candidate, "preserves_merge_contract": False}))

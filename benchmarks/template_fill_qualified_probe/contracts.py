"""Expose callable changes after eligibility and helper identity checks."""

from __future__ import annotations

import hashlib
import itertools
import json
import subprocess
import sys
from collections import Counter
from contextlib import ExitStack, contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from benchmarks.template_fill_qualified_probe import adapter  # noqa: E402

from citry import Citry, Component, nodes, ownership, slots  # noqa: E402


def render_case(changed: bool, operation: str) -> dict[str, Any]:
    """Use actual slot outlets so selection happens between preparation and invocation."""
    retained = {}
    events = Counter()

    engine = Citry()
    counter = itertools.count(1)
    engine.id_generator = lambda: f"c{next(counter)}"

    class Child(Component):
        citry = engine

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            if operation == "bind_fill_data":
                self.provide("fixture", value=True)
            if operation == "provided_key_mutation":
                self.provide("right", 1)
            if operation == "capture_replaces_content":
                # A rollback leaves ordinary Python record lists, as replay supports.
                try:
                    with self._ownership_graph.replay_transaction():
                        raise ValueError("materialize graph storage")
                except ValueError:
                    pass
            return {}

        template = """
            <c-slot>fallback</c-slot>
        """

    class Parent(Component):
        citry = engine

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"marker": "supplied"}

        template = """
            <c-child>{{ marker }}</c-child>
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

    class ProvidedKey(str):
        __slots__ = ()

        def __hash__(self) -> int:
            return hash("right")

        def __eq__(self, other: object) -> bool:
            selected = ownership._SELECTED_SUPPLY.get()
            if selected is not None:
                events["provided_key_mutation"] += 1
                selected.slot.content_func._fallback_var = "marker"
            return str.__eq__(self, other)

    adapter.install(changed)
    adapter.COUNTS = Counter()
    try:
        with ExitStack() as patches:
            if operation == "selection_replaces_content":
                patches.enter_context(patch.object(ownership, "_SelectedSupply", select))
            elif operation == "equal_helper":
                patches.enter_context(patch.object(adapter.CONTENT, "_render", EqualCallable()))
            elif operation in {"slot_init", "content_init", "slot_new", "content_new", "normalize_data"}:
                target, name = {
                    "slot_init": (slots.Slot, "__init__"),
                    "content_init": (adapter.CONTENT, "__init__"),
                    "slot_new": (slots.Slot, "__new__"),
                    "content_new": (adapter.CONTENT, "__new__"),
                    "normalize_data": (slots, "_normalize_slot_data"),
                }[operation]
                original = getattr(target, name)

                def observed(*args: Any, **kwargs: Any) -> Any:
                    events[operation] += 1
                    return object.__new__(args[0]) if name == "__new__" else original(*args, **kwargs)

                patches.enter_context(
                    patch.object(target, name, staticmethod(observed) if name == "__new__" else observed)
                )
            elif operation == "bind_fill_data":

                def bind(*_args: Any, **_kwargs: Any) -> dict[str, str]:
                    events[operation] += 1
                    return {"marker": "replacement"}

                patches.enter_context(patch.object(nodes, "_bind_fill_data", bind))
            elif operation == "capture_replaces_content":
                original_capture = ownership.OwnershipGraph._capture_python_slot_region

                def capture(graph: Any, slot: Any, fill_id: Any) -> Any:
                    result = original_capture(graph, slot, fill_id)
                    events[operation] += 1
                    if (
                        type(slot.content_func) is adapter.CONTENT
                        and type(slot.content_func._context.component) is Parent
                    ):
                        slot.content_func = replacement
                    return result

                patches.enter_context(patch.object(ownership.OwnershipGraph, "_capture_python_slot_region", capture))
            elif operation == "retained_context":
                original_outlet = nodes.SlotNode.render

                def outlet(node: Any, context: Any) -> Any:
                    retained.update(node=node, context=context)
                    return original_outlet(node, context)

                patches.enter_context(patch.object(nodes.SlotNode, "render", outlet))
            elif operation == "error_context_replaces_content":
                original_error_context = nodes.add_slot_to_error_message

                @contextmanager
                def error_context(*args: Any, **kwargs: Any) -> Any:
                    selected = ownership._SELECTED_SUPPLY.get()
                    if selected is not None:
                        selected.slot.content_func = replacement
                    with original_error_context(*args, **kwargs):
                        yield

                patches.enter_context(patch.object(nodes, "add_slot_to_error_message", error_context))
            elif operation == "slot_context_getattribute":

                def getattribute(instance: Any, name: str) -> Any:
                    if name == "provides":
                        raise RuntimeError("slot context observed")
                    return object.__getattribute__(instance, name)

                patches.enter_context(patch.object(slots.SlotContext, "__getattribute__", getattribute))
            component = Child(slots={"default": replacement}) if operation == "python_fallback" else Parent()
            try:
                provides = {ProvidedKey("left"): True} if operation == "provided_key_mutation" else None
                html = component.render(provides=provides).serialize(deps_strategy="ignore")
                result = {"html": html}
                if operation == "retained_context":
                    # The outlet needs its receiver context, not the fill's lexical context.
                    context = retained["context"]
                    result["inactive_graph"] = ownership.current_ownership_graph() is None
                    result["retained_html"] = retained["node"].render(context).serialize(deps_strategy="ignore")
            except (AttributeError, TypeError, RuntimeError) as error:
                result = {"error_type": type(error).__name__, "error": str(error)}
            result["events"] = dict(events)
        return {"result": result, "activation": dict(adapter.COUNTS)}
    finally:
        ownership._SelectedSupply = original_selection
        adapter.CONTENT._render = original_render
        adapter.COUNTS = None


def main() -> None:
    rows = []
    try:
        for operation in (
            "ordinary_template",
            "python_fallback",
            "selection_replaces_content",
            "equal_helper",
            "slot_init",
            "content_init",
            "slot_new",
            "content_new",
            "normalize_data",
            "bind_fill_data",
            "capture_replaces_content",
            "retained_context",
            "error_context_replaces_content",
            "slot_context_getattribute",
            "provided_key_mutation",
        ):
            # Assigning and deleting inherited __new__ can alter CPython's type slots.
            # Fresh workers prevent one constructor probe from contaminating the next.
            results = [
                json.loads(
                    subprocess.check_output([sys.executable, __file__, operation, variant], cwd=ROOT, text=True)
                )
                for variant in ("reference", "candidate")
            ]
            reference, candidate = results
            reference_result = reference["result"]
            if operation == "slot_context_getattribute":
                if reference_result.get("error_type") != "RuntimeError":
                    raise RuntimeError("The context-attribute probe did not raise its intended error")
            elif "error_type" in reference_result:
                raise RuntimeError(
                    f"The reference fixture failed before its assertion: {operation}: {reference_result}"
                )
            if operation in {
                "slot_init",
                "content_init",
                "slot_new",
                "content_new",
                "normalize_data",
                "bind_fill_data",
                "capture_replaces_content",
                "provided_key_mutation",
            } and not reference_result["events"].get(operation):
                raise RuntimeError(f"The helper probe did not activate: {operation}")
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
        "all_recorded_cases_match": all(row["matches"] for row in rows),
        "cases": rows,
        "hashes": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (Path(__file__), Path(adapter.__file__), Path(ownership.__file__))
        },
    }
    path = ROOT / "benchmarks/results/repeat-render/template-fill-qualified-contracts.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    if len(sys.argv) == 3:
        print(json.dumps(render_case(changed=sys.argv[2] == "candidate", operation=sys.argv[1])))
    else:
        main()

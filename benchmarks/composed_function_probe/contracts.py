"""Check composed function inputs, lexical ownership, error cleanup and execution order."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "packages/py/citry"), str(ROOT / "packages/py/citry_core")]

from benchmarks.composed_function_probe.adapter import installed  # noqa: E402
from benchmarks.composed_function_probe.probe import compare, content_projection, observe  # noqa: E402
from benchmarks.ownership_journal_probe.probe import scenario  # noqa: E402
from benchmarks.render_structure_probe.census import digest  # noqa: E402

from citry import Component, Const  # noqa: E402

VARIANTS = ("reference", "button", "immediate", "deferred")


def records(row: dict[str, Any], table: str) -> list[dict[str, Any]]:
    """Read named fields from the retained final ownership snapshot."""
    return [dict(record["fields"]) for record in dict(row["snapshots"][-1]["fields"])[table]["tuple"]]


def main() -> None:
    module = scenario()

    class Host(Component):
        citry = module.app

        class Kwargs:
            rows: list

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"rows": kwargs.rows}

        template = """
<main><c-for each="row in rows">
    <c-Button c-attrs="row['button']">
        <c-Icon c-bind="row['icon']">{{ row['label'] }}</c-Icon>
    </c-Button>
</c-for></main>
"""

    class Child(Component):
        citry = module.app
        template = """
<b>ordinary child</b>
"""

    class Receiver(Component):
        citry = module.app
        template = """
<section><c-slot name="body" /></section>
"""

    class SourceCaller(Component):
        citry = module.app
        template = """
<c-receiver><c-fill name="body">
    <c-Button><c-Icon name="home"><c-child /><c-slot /></c-Icon></c-Button>
</c-fill></c-receiver>
"""

    class Root(Component):
        citry = module.app
        template = """
<c-source-caller><i>root content</i></c-source-caller>
"""

    inputs = [
        [],
        [{"button": {}, "icon": {"name": "home"}, "label": 'first <>&"'}],
        [
            {"button": {"title": "one"}, "icon": {"name": "home", "href": "/a?x=1&y=2"}, "label": "one"},
            {"button": {"title": "two"}, "icon": {"name": "home", "variant": "solid"}, "label": "two"},
        ],
        [
            {
                "button": {"class": ["a", {"b": True}]},
                "icon": {"name": Const(Const("home")), "size": 18, "svg_attrs": {"title": '"<&'}},
                "label": "changed",
            }
        ],
    ]
    compared = {}
    for index, values in enumerate(inputs):
        rows = {v: observe(module, lambda values=values: str(Host(rows=values)), v) for v in VARIANTS}
        for variant in VARIANTS[1:]:
            compare(rows["reference"], rows[variant], variant)
        for variant in ("immediate", "deferred"):
            counts = rows[variant]["candidate_counts"]
            for name in ("Button", "Icon", "HeroIcon"):
                if counts.get(name, 0) != len(values):
                    raise AssertionError("Composed input fixture did not activate each selected template")
        compared[f"inputs_{index}"] = rows["reference"]["projected_digest"]

    class Formatting(Component):
        citry = module.app

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"space": " \n "}

        template = """
<main>
    <c-Button>
    </c-Button>
    <c-Icon name="home">
    </c-Icon>
    <c-Button>{{ space }}</c-Button>
    <c-Icon name="home">{{ space }}</c-Icon>
    <c-Button /><c-Icon name="home" />
</main>
"""

    # Static formatting is absent content; expression results remain content even when whitespace.
    formatting = {v: observe(module, lambda: str(Formatting()), v) for v in VARIANTS}
    for variant in ("immediate", "deferred"):
        compare(formatting["reference"], formatting[variant], variant)
    formatting_result = {
        v: {"matches_reference": r["projected_digest"] == formatting["reference"]["projected_digest"]}
        for v, r in formatting.items()
    }
    if formatting_result["button"]["matches_reference"]:
        raise AssertionError("The unchanged iteration 65 control unexpectedly handled formatting-only content")
    ownership = {}
    for variant in VARIANTS:
        row = observe(module, lambda: str(Root()), variant)
        if variant == "reference":
            reference = row
        else:
            compare(reference, row, variant)
        if variant in ("immediate", "deferred"):
            instances = records(row, "logical_instances")
            child = next(r for r in instances if r["class_id"] == Child.class_id)
            source = next(r for r in instances if r["class_id"] == SourceCaller.class_id)
            receiver = next(r for r in instances if r["class_id"] == Receiver.class_id)
            invocation = next(
                r for r in records(row, "component_invocations") if r["target_render_id"] == child["render_id"]
            )
            region = next(
                r for r in records(row, "physical_regions") if r["id"] == invocation["physical_parent_region_id"]
            )
            if (
                child["logical_parent_render_id"] != source["render_id"]
                or invocation["source_render_id"] != source["render_id"]
            ):
                raise AssertionError("Ordinary child lost its source owner")
            if (
                region["receiver_render_id"] != receiver["render_id"]
                or region["lexical_owner_render_id"] != source["render_id"]
            ):
                raise AssertionError("Ordinary child lost its physical supplied-slot region")
            ownership[variant] = {
                "logical_parent": "SourceCaller",
                "invocation_source": "SourceCaller",
                "physical_receiver": "Receiver",
                "physical_lexical_owner": "SourceCaller",
            }

    class Recovery(Component):
        citry = module.app

        def on_render(self) -> Any:
            _, error = yield
            if error is not None:
                return "<p>recovered</p>"
            return None

        template = """
<c-Button><c-Icon name="home" variant="invalid" /></c-Button>
"""

    class BrokenBody(Component):
        citry = module.app
        template = """
<c-Button><c-Icon name="home">{{ 1 / 0 }}</c-Icon></c-Button>
"""

    cleanup = {}
    for variant in ("immediate", "deferred"):
        with installed(module, variant):
            hot = [content_projection(str(Host(rows=values)), {})[0] for values in inputs]
            if [digest(text) for text in hot] != [compared[f"inputs_{i}"] for i in range(len(inputs))]:
                raise AssertionError("Prepared templates changed output across roots")
            recovered = content_projection(str(Recovery()), {})[0]
            if recovered != "<p>recovered</p>":
                raise AssertionError("Ancestor did not recover selected function error")
            try:
                str(BrokenBody())
            except ZeroDivisionError:
                pass
            else:
                raise AssertionError("Expected nested body error")
            if content_projection(str(Host(rows=inputs[1])), {})[0] != hot[1]:
                raise AssertionError("Nested error left stale function state")
            cleanup[variant] = {"hot_roots": len(hot), "ancestor_recovered": True, "nested_error_reset": True}

    rejected = {}
    for label, template in (
        ("named_fill", '<c-Button><c-fill name="default">body</c-fill></c-Button>'),
        ("key", '<c-Icon name="home" #c-key="\'key\'" />'),
        ("client_binding", '<c-Button @click="count++" />'),
        ("svg_body", '<c-heroicons name="home">body</c-heroicons>'),
        ("svg_alpine", "<c-Icon name=\"home\" c-svg_attrs=\"{'x-data': '{}'}\" />"),
    ):
        cls = type(label, (Component,), {"citry": module.app, "template": template})
        for variant in ("immediate", "deferred"):
            with installed(module, variant):
                try:
                    str(cls())
                except TypeError:
                    rejected[f"{label}/{variant}"] = "TypeError"
                else:
                    raise AssertionError(f"Accepted unsupported {label}/{variant}")

    events = []
    parent_phases = []

    class Sibling(Component):
        citry = module.app

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            events.append("sibling")
            return {}

        template = """
<span>sibling</span>
"""

    class OrderedChild(Component):
        citry = module.app

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            events.append("child")
            return {}

        template = """
<span>child</span>
"""

    class OrderHost(Component):
        citry = module.app

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            def mark(value: str) -> str:
                events.append(value)
                return ""

            return {"mark": mark}

        def on_render(self) -> Any:
            parent_phases.append("before")
            yield
            parent_phases.append("after")

        template = """
<c-sibling />
<c-Button><c-Icon name="home">{{ mark('content') }}<c-ordered-child /></c-Icon></c-Button>
"""

    originals = {cls: cls.template_data for cls in (module.Button, module.Icon, module.HeroIcon)}

    def callback(name: str, original: Any) -> Any:
        def data(self: Any, kwargs: Any, slots: Any) -> Any:
            events.append(name)
            return original(self, kwargs, slots)

        return data

    orders = {}
    phases = {}
    completion_counts = {}
    original_completed = module.app.extensions.on_component_rendered
    completed = []

    def component_completed(component: Any, render: Any, error: Any) -> Any:
        if type(component) is OrderHost:
            completed.append(component.id)
        return original_completed(component, render, error)

    try:
        for cls, original in originals.items():
            cls.template_data = callback(cls.__name__.lower(), original)
        for variant in VARIANTS:
            events.clear()
            parent_phases.clear()
            completed.clear()
            with (
                patch.object(module.app.extensions, "on_component_rendered", component_completed),
                installed(module, variant),
            ):
                str(OrderHost())
            orders[variant] = list(events)
            phases[variant] = list(parent_phases)
            completion_counts[variant] = len(completed)
            if parent_phases != ["before", "after"]:
                raise AssertionError("Caller hooks did not run exactly once around the whole subtree")
            if len(completed) != 1:
                raise AssertionError("Function finalization duplicated caller completion hooks")
    finally:
        for cls, original in originals.items():
            cls.template_data = original
    expected = ["sibling", "button", "icon", "content", "heroicon", "child"]
    if orders["reference"] != expected or orders["deferred"] != expected:
        raise AssertionError(f"Deferred execution changed callback order: {orders!r}")
    if orders["immediate"] != ["button", "icon", "heroicon", "content", "sibling", "child"]:
        raise AssertionError(f"Unexpected immediate callback order: {orders!r}")
    paths = [Path(__file__), Path(__file__).with_name("adapter.py"), Path(__file__).with_name("probe.py")]
    print(
        json.dumps(
            {
                "compared": compared,
                "formatting_only_and_dynamic_whitespace": formatting_result,
                "ownership": ownership,
                "cleanup": cleanup,
                "rejected": rejected,
                "callback_and_content_order": orders,
                "caller_hook_phases": phases,
                "caller_completion_hook_counts": completion_counts,
                "hashes": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

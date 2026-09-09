"""Check wrapper scope, ordinary nested content, rejected inputs and changed callback order."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "packages/py/citry"), str(ROOT / "packages/py/citry_core")]

from benchmarks.ownership_journal_probe.probe import scenario  # noqa: E402
from benchmarks.render_structure_probe.census import digest  # noqa: E402
from benchmarks.wrapper_function_probe.adapter import installed  # noqa: E402
from benchmarks.wrapper_function_probe.probe import compare, content_projection, observe  # noqa: E402

from citry import Component, Const, Markup  # noqa: E402


def main() -> None:
    module = scenario()

    class Host(Component):
        citry = module.app

        class Kwargs:
            values: dict
            label: str

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"values": kwargs.values, "label": kwargs.label}

        template = """
<main><c-Button c-bind="values">{{ label }}</c-Button></main>
"""

    class Child(Component):
        citry = module.app
        template = """
<b class="ordinary-child">child</b>
"""

    class ContentHost(Component):
        citry = module.app
        template = """
<section><c-Button><c-child /><c-slot /></c-Button></section>
"""

    class ContentCaller(Component):
        citry = module.app
        template = """
<c-content-host><i>caller content</i></c-content-host>
"""

    class Nested(Component):
        citry = module.app
        template = """
<c-Button><c-Button link href="/inner">nested</c-Button></c-Button>
"""

    class Recovery(Component):
        citry = module.app

        def on_render(self) -> Any:
            _, error = yield
            if error is not None:
                return '<p class="recovered">recovered</p>'
            return None

        template = """
<c-Button variant="invalid" />
"""

    inputs = [
        ({}, 'first <>&"'),
        ({"href": "/one?x=1&y=2", "attrs": {"title": '"<&', "class": ["a", {"b": True}]}}, "link"),
        ({"href": "/one", "disabled": True, "attrs": {"style": {"color": "red"}}}, "disabled"),
        ({"variant": Const(Const("plain")), "attrs": {"title": "changed"}}, "changed"),
    ]
    compared = {}
    for index, (values, label) in enumerate(inputs):

        def call(values: Any = values, label: str = label) -> str:
            return str(Host(values=values, label=label))

        reference = observe(module, call, enabled=False)
        candidate = observe(module, call, enabled=True)
        compare(reference, candidate)
        compared[f"inputs_{index}"] = candidate["projected_digest"]
    for label, cls in (("ordinary_child_and_caller_slot", ContentCaller), ("nested_wrappers", Nested)):
        reference = observe(module, lambda cls=cls: str(cls()), enabled=False)
        candidate = observe(module, lambda cls=cls: str(cls()), enabled=True)
        compare(reference, candidate)
        compared[label] = candidate["projected_digest"]
    recovered = []
    for enabled in (False, True):
        with installed(module, enabled):
            recovered.append(content_projection(str(Recovery()), {})[0])
    if recovered != ['<p class="recovered">recovered</p>'] * 2:
        raise AssertionError(f"Ancestor recovery differs: {recovered!r}")

    rejected = {}
    for name, template in (
        ("named_fill", '<c-Button><c-fill name="default">text</c-fill></c-Button>'),
        ("key", "<c-Button #c-key=\"'key'\" />"),
        ("client_binding", '<c-Button @click="count++" />'),
    ):
        cls = type(name, (Component,), {"citry": module.app, "template": template})
        with installed(module, enabled=True):
            try:
                str(cls())
            except TypeError as error:
                rejected[name] = str(error)
            else:
                raise AssertionError(f"Accepted unsupported {name}")
    cycle: dict[str, Any] = {}
    cycle["value"] = cycle
    for name, value in (("markup", Markup("html")), ("object", object()), ("cycle", cycle)):
        with installed(module, enabled=True):
            try:
                str(Host(values={"attrs": {"title": value}}, label="label"))
            except (TypeError, ValueError) as error:
                rejected[name] = type(error).__name__
            else:
                raise AssertionError(f"Accepted unsupported {name}")

    events = []

    class Sibling(Component):
        citry = module.app

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            events.append("sibling")
            return {}

        template = """
<span>sibling</span>
"""

    class OrderHost(Component):
        citry = module.app
        template = """
<c-sibling /><c-Button>button</c-Button>
"""

    with installed(module, enabled=True):
        try:
            Host(values={}, label="label").render(template_globals={"value": 1})
        except TypeError:
            rejected["globals"] = "TypeError"
        else:
            raise AssertionError("Accepted render globals")
        hot_outputs = [content_projection(str(Host(values=values, label=label)), {})[0] for values, label in inputs]

        class BrokenBody(Component):
            citry = module.app
            template = """
<c-Button>{{ 1 / 0 }}</c-Button>
"""

        try:
            str(BrokenBody())
        except ZeroDivisionError:
            pass
        else:
            raise AssertionError("Expected supplied-body error")
        after_error = content_projection(str(Host(values=inputs[0][0], label=inputs[0][1])), {})[0]
    for index, output in enumerate(hot_outputs):
        if digest(output) != compared[f"inputs_{index}"]:
            raise AssertionError("Prepared wrapper changed output across root calls")
    if after_error != hot_outputs[0]:
        raise AssertionError("Supplied-body error left stale wrapper state")

    original_data = module.Button.template_data

    def data(self: Any, kwargs: Any, slots: Any) -> Any:
        events.append("button")
        return original_data(self, kwargs, slots)

    orders = []
    module.Button.template_data = data
    try:
        for enabled in (False, True):
            events.clear()
            with installed(module, enabled):
                str(OrderHost())
            orders.append(list(events))
    finally:
        module.Button.template_data = original_data
    if orders != [["sibling", "button"], ["button", "sibling"]]:
        raise AssertionError(f"Unexpected callback ordering: {orders!r}")

    paths = [Path(__file__), Path(__file__).with_name("adapter.py"), Path(__file__).with_name("probe.py")]
    print(
        json.dumps(
            {
                "compared": compared,
                "ancestor_recovery": recovered,
                "body_error_reset": True,
                "hot_outputs_match": True,
                "rejected": rejected,
                "callback_order_reference_then_candidate": orders,
                "hashes": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

"""The removed ``$c-props`` boundary and native Vue component bindings."""

from __future__ import annotations

from typing import Any

import pytest

from citry import Citry, Component, Extension
from citry._vue.capture import render_prepared_direct
from citry._vue.direct_capture import assemble_typed_render
from citry.constness import const_value


def _render_html(
    template: str,
    data: dict[str, Any] | None = None,
    *,
    extensions: tuple[type[Extension], ...] = (),
) -> str:
    """Render one small authored template through the ordinary HTML path."""
    registry = Citry(extensions=extensions)

    class Child(Component):
        citry = registry
        template = "<span>child</span>"

    class Page(Component):
        citry = registry

        def template_data(self, kwargs, slots):
            return dict(data or {})

    Page.template = template
    return Page().render().serialize(deps_strategy="ignore")


def _assemble(root: Component):
    return assemble_typed_render(
        render_prepared_direct(root),
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )


def _assert_authored_prop_binding(compile_input, *, name: str, value: str) -> None:
    assert len(compile_input.local_calls) == 1
    bindings = compile_input.local_calls[0]["bindings"]
    assert len(bindings) == 1
    binding = bindings[0]
    assert {key: binding[key] for key in ("kind", "name", "value")} == {
        "kind": "prop",
        "name": name,
        "value": value,
    }
    source = compile_input.template.encode()
    assert source[binding["sourceStart"] : binding["sourceEnd"]].decode() == f'{name}="{value}"'


class TestRemovedClientPropsBoundary:
    @pytest.mark.parametrize(
        ("template", "data"),
        [
            ('<c-child $c-props="{ count: clientCount }" />', None),
            ('<c-child c-$c-props="clientProps" />', {"clientProps": "{ count: clientCount }"}),
        ],
    )
    def test_authored_legacy_boundary_forms_are_rejected(self, template, data):
        with pytest.raises(SyntaxError, match=r"\$c-props.*was removed; use native Vue"):
            _render_html(template, data)

    @pytest.mark.parametrize("value", ["{ count: clientCount }", None, False])
    def test_runtime_spreads_cannot_manufacture_or_remove_the_legacy_key(self, value):
        with pytest.raises(RuntimeError, match=r"\$c-props.*was removed; use native Vue :prop or v-bind"):
            _render_html(
                '<c-child c-bind="attrs" />',
                {"attrs": {"$c-props": value}},
            )

    def test_case_variant_remains_a_runtime_error(self):
        with pytest.raises(RuntimeError, match=r"directive names are lowercase.*\$C-PROPS"):
            _render_html(
                '<c-child c-bind="attrs" />',
                {"attrs": {"$C-PROPS": None}},
            )

    def test_extension_injected_legacy_key_is_still_rejected(self):
        class InjectLegacyKey(Extension):
            name = "inject_legacy_client_props"

            def on_attrs_resolved(self, ctx):
                return {**ctx.attrs, "$c-props": "{ count: clientCount }"}

        with pytest.raises(RuntimeError, match=r"\$c-props.*only valid on a Citry component tag"):
            _render_html('<div c-bind="{}">plain</div>', extensions=(InjectLegacyKey,))

    def test_longer_similarly_named_key_remains_an_ordinary_html_attribute(self):
        output = _render_html(
            '<div c-bind="attrs">plain</div>',
            {"attrs": {"$c-props-extra": "ordinary"}},
        )

        assert output.strip() == '<div $c-props-extra="ordinary" data-cid-c1="">plain</div>'


class TestNativeVueComponentBindings:
    def test_authored_prop_stays_out_of_typed_python_kwargs(self):
        registry = Citry(autodiscover=False)
        received: list[tuple[str, dict[str, Any]]] = []

        class Child(Component):
            citry = registry

            class Kwargs:
                title: str

            template = "<span>child</span>"

            def template_data(self, kwargs, slots):
                received.append(
                    (
                        kwargs.title,
                        {key: const_value(value) for key, value in self.raw_kwargs.items()},
                    )
                )
                return {}

        class Parent(Component):
            citry = registry
            template = '<c-child title="ok" :count="clientCount" #c-key="\'child\'" />'

        assembly = _assemble(Parent())
        parent = next(item for item in assembly.view.occurrences if item.type_key == Parent.class_id)
        compile_input = assembly.compile_inputs[parent.definition_id]

        assert received == [("ok", {"title": "ok"})]
        _assert_authored_prop_binding(compile_input, name=":count", value="clientCount")

    def test_dynamic_selector_forwards_authored_prop_to_selected_target(self):
        registry = Citry(autodiscover=False)
        received: list[dict[str, Any]] = []

        class Child(Component):
            citry = registry
            template = "<span>child</span>"

            def template_data(self, kwargs, slots):
                received.append({key: const_value(value) for key, value in self.raw_kwargs.items()})
                return {}

        class Parent(Component):
            citry = registry
            template = '<c-component c-is="target" :title="clientTitle" #c-key="\'selected\'" />'

            def template_data(self, kwargs, slots):
                return {"target": "child"}

        assembly = _assemble(Parent())
        parent = next(item for item in assembly.view.occurrences if item.type_key == Parent.class_id)
        compile_input = assembly.compile_inputs[parent.definition_id]

        assert received == [{}]
        _assert_authored_prop_binding(compile_input, name=":title", value="clientTitle")

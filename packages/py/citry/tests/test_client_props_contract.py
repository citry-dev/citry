"""Server-side A0 contract for the ``$c-props`` boundary directive."""

from __future__ import annotations

from typing import Any

import pytest

from citry import Citry, Component
from citry.constness import const_value
from citry.extension import Extension


def _render_with_capture(
    parent_template: str,
    data: dict[str, Any] | None = None,
) -> tuple[str, list[list[tuple[str, Any]]]]:
    """Render one child tag and capture its component-tag client bindings."""
    c = Citry()
    captured: list[list[tuple[str, Any]]] = []

    class Child(Component):
        citry = c
        template = """
          <span>child</span>
        """

        def template_data(self, kwargs, slots):
            captured.append(
                [
                    (client_binding.key, client_binding.payload.expression)
                    for client_binding in self._component_tag_client_bindings
                ]
            )
            return {}

    class Page(Component):
        citry = c

        def template_data(self, kwargs, slots):
            return dict(data or {})

    Page.template = parent_template
    return Page().render().serialize(deps_strategy="ignore"), captured


class TestComponentBoundaryForms:
    def test_direct_form_round_trips_as_one_raw_boundary_value(self):
        output, captured = _render_with_capture(
            """
              <c-child $c-props="{ count: localCount }" />
            """
        )

        assert output.strip() == '<span data-cid-c2="" data-cid-c1="">child</span>'
        assert captured == [[("$c-props", "{ count: localCount }")]]

    def test_server_dynamic_form_supplies_the_complete_expression(self):
        _, captured = _render_with_capture(
            """
              <c-child c-$c-props="expression" />
            """,
            {"expression": "{ count: serverChoice }"},
        )

        assert captured == [[("$c-props", "{ count: serverChoice }")]]

    def test_spread_key_supplies_the_complete_expression(self):
        _, captured = _render_with_capture(
            """
              <c-child c-bind="attrs" />
            """,
            {"attrs": {"$c-props": "{ count: spreadChoice }"}},
        )

        assert captured == [[("$c-props", "{ count: spreadChoice }")]]

    def test_last_spread_contribution_wins(self):
        _, captured = _render_with_capture(
            """
              <c-child
                $c-props="first"
                c-bind="second"
                c-bind="third"
              />
            """,
            {
                "second": {"$c-props": "second"},
                "third": {"$c-props": "third"},
            },
        )

        assert captured == [[("$c-props", "third")]]

    def test_removal_and_readdition_follow_source_order(self):
        _, captured = _render_with_capture(
            """
              <c-child
                $c-props="first"
                title="hello"
                c-bind="remove"
                c-bind="add"
              />
            """,
            {
                "remove": {"$c-props": None},
                "add": {"$c-props": "last"},
            },
        )

        assert captured == [[("$c-props", "last")]]

    @pytest.mark.parametrize("removed", [None, False])
    def test_dynamic_none_and_false_contribute_no_value(self, removed):
        _, captured = _render_with_capture(
            """
              <c-child c-$c-props="removed" />
            """,
            {"removed": removed},
        )

        assert captured == [[]]

    @pytest.mark.parametrize("removed", [None, False])
    def test_spread_none_and_false_remove_the_direct_value(self, removed):
        _, captured = _render_with_capture(
            """
              <c-child $c-props="first" c-bind="attrs" />
            """,
            {"attrs": {"$c-props": removed}},
        )

        assert captured == [[]]

    @pytest.mark.parametrize("invalid", [True, 1, "", "   "])
    def test_server_dynamic_form_rejects_invalid_values(self, invalid):
        with pytest.raises(TypeError, match=r"\$c-props.*non-empty client expression string"):
            _render_with_capture(
                """
                  <c-child c-$c-props="invalid" />
                """,
                {"invalid": invalid},
            )

    @pytest.mark.parametrize("invalid", [True, 1, "", "   "])
    def test_spread_form_rejects_invalid_values(self, invalid):
        with pytest.raises(TypeError, match=r"\$c-props.*non-empty client expression string"):
            _render_with_capture(
                """
                  <c-child c-bind="attrs" />
                """,
                {"attrs": {"$c-props": invalid}},
            )

    def test_static_dynamic_component_forwards_to_selected_target(self):
        _, captured = _render_with_capture(
            """
              <c-component is="child" $c-props="staticTarget" />
            """
        )

        assert captured == [[("$c-props", "staticTarget")]]

    def test_runtime_dynamic_component_forwards_to_selected_target(self):
        _, captured = _render_with_capture(
            """
              <c-component c-is="target" c-$c-props="expression" />
            """,
            {"target": "child", "expression": "dynamicTarget"},
        )

        assert captured == [[("$c-props", "dynamicTarget")]]

    def test_typed_python_kwargs_exclude_the_boundary_directive(self):
        c = Citry()
        captured: list[tuple[str, dict[str, Any]]] = []

        class Child(Component):
            citry = c

            class Kwargs:
                title: str

            template = """
              <span>{{ title }}</span>
            """

            def template_data(self, kwargs, slots):
                captured.append(
                    (
                        kwargs.title,
                        {key: const_value(value) for key, value in self.raw_kwargs.items()},
                    )
                )
                return {"title": kwargs.title}

        class Page(Component):
            citry = c
            template = """
              <c-child title="ok" $c-props="{ count: 1 }" />
            """

        assert Page().render().serialize(deps_strategy="ignore").strip() == (
            '<span data-cid-c2="" data-cid-c1="">ok</span>'
        )
        assert captured == [("ok", {"title": "ok"})]

    def test_longer_spread_key_remains_an_ordinary_python_kwarg(self):
        _, captured = _render_with_capture(
            """
              <c-child c-bind="attrs" />
            """,
            {"attrs": {"$c-props-extra": "ordinary"}},
        )

        assert captured == [[]]


class TestPlainElementDiagnostics:
    @pytest.mark.parametrize(
        "template",
        [
            '<div $c-props="{ count: 1 }"></div>',
            '<div c-$c-props="expression"></div>',
            '<c-element is="div" $c-props="{ count: 1 }" />',
        ],
    )
    def test_literal_forms_fail_during_template_parse(self, template):
        with pytest.raises(
            SyntaxError,
            match=r"client props directive and belongs on a Citry component tag",
        ):
            _render_with_capture(template, {"expression": "{ count: 1 }"})

    def test_plain_element_spread_rejects_an_active_dynamic_key(self):
        with pytest.raises(RuntimeError, match=r"\$c-props.*only valid on a Citry component tag"):
            _render_with_capture(
                """
                  <div c-bind="attrs">plain</div>
                """,
                {"attrs": {"$c-props": "{ count: 1 }"}},
            )

    @pytest.mark.parametrize("removed", [None, False])
    def test_plain_element_spread_allows_removed_dynamic_key(self, removed):
        output, captured = _render_with_capture(
            """
              <div c-bind="attrs">plain</div>
            """,
            {"attrs": {"$c-props": removed}},
        )

        assert output.strip() == '<div data-cid-c1="">plain</div>'
        assert captured == []

    def test_static_c_element_spread_rejects_an_active_dynamic_key(self):
        with pytest.raises(RuntimeError, match=r"\$c-props.*only valid on a Citry component tag"):
            _render_with_capture(
                """
                  <c-element is="section" c-bind="attrs">plain</c-element>
                """,
                {"attrs": {"$c-props": "{ count: 1 }"}},
            )

    def test_dynamic_c_element_spread_rejects_an_active_dynamic_key(self):
        with pytest.raises(RuntimeError, match=r"\$c-props.*only valid on a Citry component tag"):
            _render_with_capture(
                """
                  <c-element c-is="tag" c-bind="attrs">plain</c-element>
                """,
                {
                    "tag": "section",
                    "attrs": {"$c-props": "{ count: 1 }"},
                },
            )

    @pytest.mark.parametrize("removed", [None, False])
    @pytest.mark.parametrize(
        ("template", "extra_data", "expected"),
        [
            (
                '<c-element is="section" c-bind="attrs">plain</c-element>',
                {},
                '<section data-cid-c1="">plain</section>',
            ),
            (
                '<c-element c-is="tag" c-bind="attrs">plain</c-element>',
                {"tag": "section"},
                '<section data-cid-c1="">plain</section>',
            ),
        ],
    )
    def test_c_element_spread_allows_removed_dynamic_key(self, template, extra_data, expected, removed):
        output, _ = _render_with_capture(
            template,
            {**extra_data, "attrs": {"$c-props": removed}},
        )

        assert output.strip() == expected

    @pytest.mark.parametrize("value", ["{ count: 1 }", None, False])
    @pytest.mark.parametrize(
        ("template", "extra_data"),
        [
            ('<c-child c-bind="attrs" />', {}),
            ('<div c-bind="attrs">plain</div>', {}),
            ('<c-element is="section" c-bind="attrs">plain</c-element>', {}),
            (
                '<c-element c-is="tag" c-bind="attrs">plain</c-element>',
                {"tag": "section"},
            ),
        ],
    )
    def test_spread_case_variants_are_runtime_errors_before_serialization(self, template, extra_data, value):
        with pytest.raises(RuntimeError, match=r"client directive names are lowercase.*\$C-PROPS"):
            _render_with_capture(
                template,
                {**extra_data, "attrs": {"$C-PROPS": value}},
            )

    def test_longer_spread_key_remains_an_ordinary_html_attribute(self):
        output, _ = _render_with_capture(
            """
              <div c-bind="attrs">plain</div>
            """,
            {"attrs": {"$c-props-extra": "ordinary"}},
        )

        assert output.strip() == '<div $c-props-extra="ordinary" data-cid-c1="">plain</div>'

    @pytest.mark.parametrize(
        "injected",
        [
            {"$c-props": "{ count: 1 }"},
            {"$C-PROPS": None},
        ],
    )
    @pytest.mark.parametrize(
        "template",
        [
            '<div c-bind="{}">plain</div>',
            "<c-element c-is=\"'section'\">plain</c-element>",
        ],
    )
    def test_post_extension_validation_rejects_injected_directive_keys(self, injected, template):
        class Injector(Extension):
            name = "client_props_injector"

            def on_attrs_resolved(self, ctx):
                return {**ctx.attrs, **injected}

        c = Citry(extensions=[Injector])

        class Page(Component):
            citry = c

        Page.template = template

        with pytest.raises(RuntimeError, match=r"\$c-props|\$C-PROPS"):
            Page().render().serialize()

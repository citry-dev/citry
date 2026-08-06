"""
Tests for fill collection at the component boundary (docs/design/component_slots.md
section 4) and the Python ``slots=`` channel (section 9).

The receiving components consume their slots through ``template_data(kwargs,
slots)`` plus ``{{ slot_var }}`` / ``{{ slot_var(data) }}`` expressions, which
also exercises the same normalized ``Slot`` values consumed by ``<c-slot>``.
"""

# These tests intentionally exercise Python's confusable NFKC identifier
# normalization with the Kelvin sign.
# ruff: noqa: RUF001

import pytest

from citry import Citry, CitryContext, Component, Const, Slot, SlotInput
from citry.nodes import ExprNode, FillSink, Node, collect_fills_from_body


def _make_citry():
    return Citry()


class TestPythonSlotsChannel:
    def test_slots_kwarg_extracted_from_call(self):
        c = _make_citry()

        class Page(Component):
            citry = c
            template = "<p>x</p>"

        element = Page(title="x", slots={"header": "Hi"})
        assert element.kwargs == {"title": "x"}
        assert element.slots == {"header": "Hi"}

    def test_no_slots_kwarg_means_empty(self):
        c = _make_citry()

        class Page(Component):
            citry = c
            template = "<p>x</p>"

        assert Page().slots == {}

    def test_python_slots_render_via_template_data(self):
        c = _make_citry()

        class Page(Component):
            citry = c
            template = "<div>{{ header }}</div>"

            def template_data(self, kwargs, slots):
                return {"header": slots["header"]}

        assert str(Page(slots={"header": "Hi"})) == '<div data-cid-c1="">Hi</div>'

    def test_python_slots_are_normalized_to_slot_instances(self):
        c = _make_citry()
        seen = {}

        class Page(Component):
            citry = c
            template = "<p>x</p>"

            def template_data(self, kwargs, slots):
                seen.update(slots)
                return {}

        str(Page(slots={"header": "Hi", "footer": lambda _ctx: "F"}))
        assert isinstance(seen["header"], Slot)
        assert isinstance(seen["footer"], Slot)
        assert seen["header"].slot_name == "header"
        assert seen["header"].component_name == "Page"

    def test_typed_slots_class(self):
        c = _make_citry()

        class Page(Component):
            citry = c
            template = "<div>{{ h }}</div>"

            class Slots:
                header: SlotInput

            def template_data(self, kwargs, slots):
                return {"h": slots.header}

        assert str(Page(slots={"header": "Hi"})) == '<div data-cid-c1="">Hi</div>'


class TestImplicitDefaultSlot:
    def _card(self, c):
        class Card(Component):
            citry = c
            template = "<div>{{ body }}</div>"

            def template_data(self, kwargs, slots):
                return {"body": slots.get("default", "EMPTY")}

        return Card

    def test_body_content_fills_default_slot(self):
        c = _make_citry()
        self._card(c)

        class Page(Component):
            citry = c
            template = "<c-card>Hello!</c-card>"

        assert str(Page()) == '<div data-cid-c2="" data-cid-c1="">Hello!</div>'

    def test_default_body_renders_in_parent_scope(self):
        c = _make_citry()
        self._card(c)

        class Page(Component):
            citry = c
            template = "<c-card>Hello {{ name }}!</c-card>"

            def template_data(self, kwargs, slots):
                return {"name": "Jo"}

        # `name` comes from Page's scope; Card has no `name` variable.
        assert str(Page()) == '<div data-cid-c2="" data-cid-c1="">Hello Jo!</div>'

    def test_whitespace_only_body_makes_no_slot(self):
        c = _make_citry()
        self._card(c)

        class Page(Component):
            citry = c
            template = "<c-card>\n   \n</c-card>"

        assert str(Page()) == '<div data-cid-c2="" data-cid-c1="">EMPTY</div>'

    def test_no_body_makes_no_slot(self):
        c = _make_citry()
        self._card(c)

        class Page(Component):
            citry = c
            template = "<c-card />"

        assert str(Page()) == '<div data-cid-c2="" data-cid-c1="">EMPTY</div>'

    def test_implicit_fill_slot_metadata(self):
        c = _make_citry()
        seen = {}

        class Capture(Component):
            citry = c
            template = "x"

            def template_data(self, kwargs, slots):
                seen.update(slots)
                return {}

        class Page(Component):
            citry = c
            template = "<c-capture>BODY</c-capture>"

        str(Page())
        slot = seen["default"]
        assert slot.component_name == "capture"
        assert slot.slot_name == "default"
        assert slot.contents == ["BODY"]
        assert slot.extra == {}
        assert slot.source_position is not None

    def test_template_comment_inside_implicit_fill_is_ignored(self):
        c = _make_citry()
        self._card(c)

        class Page(Component):
            citry = c
            template = "<c-card>Main{# hidden note #}</c-card>"

        assert str(Page()) == '<div data-cid-c2="" data-cid-c1="">Main</div>'


class TestNamedFills:
    def _card(self, c):
        class Card(Component):
            citry = c
            template = "<div>{{ h }}|{{ f }}</div>"

            def template_data(self, kwargs, slots):
                return {"h": slots.get("header", ""), "f": slots.get("footer", "")}

        return Card

    @pytest.mark.parametrize(
        "fill_attrs",
        [
            'name="a" c-name="\'b\'"',
            'c-name="\'b\'" name="a"',
        ],
    )
    def test_static_and_dynamic_fill_names_are_mutually_exclusive(self, fill_attrs):
        c = _make_citry()

        class Card(Component):
            citry = c
            template = "<div>{{ a }}|{{ b }}</div>"

            def template_data(self, kwargs, slots):
                return {"a": slots.get("a", ""), "b": slots.get("b", "")}

        class Page(Component):
            citry = c
            template = f"<c-card><c-fill {fill_attrs}>X</c-fill></c-card>"

        with pytest.raises(SyntaxError, match="must have only one"):
            str(Page())

    def test_named_fills_collected(self):
        c = _make_citry()
        self._card(c)

        class Page(Component):
            citry = c
            template = '<c-card><c-fill name="header">H</c-fill><c-fill name="footer">F</c-fill></c-card>'

        assert str(Page()) == '<div data-cid-c2="" data-cid-c1="">H|F</div>'

    def test_whitespace_between_fills_dropped(self):
        c = _make_citry()
        self._card(c)

        class Page(Component):
            citry = c
            template = '<c-card>\n  <c-fill name="header">H</c-fill>\n  <c-fill name="footer">F</c-fill>\n</c-card>'

        assert str(Page()) == '<div data-cid-c2="" data-cid-c1="">H|F</div>'

    def test_fill_body_renders_in_parent_scope(self):
        c = _make_citry()
        self._card(c)

        class Page(Component):
            citry = c
            template = '<c-card><c-fill name="header">{{ greeting }}</c-fill></c-card>'

            def template_data(self, kwargs, slots):
                return {"greeting": "Yo"}

        assert str(Page()) == '<div data-cid-c2="" data-cid-c1="">Yo|</div>'

    def test_fill_slot_metadata(self):
        c = _make_citry()
        seen = {}

        class Card(Component):
            citry = c
            template = "<p>x</p>"

            def template_data(self, kwargs, slots):
                seen.update(slots)
                return {}

        class Page(Component):
            citry = c
            template = '<c-card><c-fill name="header">H</c-fill></c-card>'

        str(Page())
        slot = seen["header"]
        assert isinstance(slot, Slot)
        assert slot.slot_name == "header"
        assert slot.component_name == "card"
        assert slot.contents == ["H"]
        assert slot.extra == {}
        assert slot.source_position is not None


class TestFillsUnderControlFlow:
    def _card(self, c):
        class Card(Component):
            citry = c
            template = "<div>{{ h }}</div>"

            def template_data(self, kwargs, slots):
                return {"h": slots.get("header", "NONE")}

        return Card

    def test_fill_in_taken_if_branch_collected(self):
        c = _make_citry()
        self._card(c)

        class Page(Component):
            citry = c
            template = '<c-card><c-if cond="flag"><c-fill name="header">ON</c-fill></c-if></c-card>'

            def template_data(self, kwargs, slots):
                return {"flag": True}

        assert str(Page()) == '<div data-cid-c2="" data-cid-c1="">ON</div>'

    def test_fill_in_untaken_if_branch_not_collected(self):
        c = _make_citry()
        self._card(c)

        class Page(Component):
            citry = c
            template = '<c-card><c-if cond="flag"><c-fill name="header">ON</c-fill></c-if></c-card>'

            def template_data(self, kwargs, slots):
                return {"flag": False}

        assert str(Page()) == '<div data-cid-c2="" data-cid-c1="">NONE</div>'

    def test_else_branch_fill_collected(self):
        c = _make_citry()
        self._card(c)

        class Page(Component):
            citry = c
            template = (
                '<c-card><c-if cond="flag"><c-fill name="header">A</c-fill></c-if>'
                '<c-else><c-fill name="header">B</c-fill></c-else></c-card>'
            )

            def template_data(self, kwargs, slots):
                return {"flag": False}

        assert str(Page()) == '<div data-cid-c2="" data-cid-c1="">B</div>'

    def test_dynamic_fills_in_loop(self):
        c = _make_citry()

        class Card(Component):
            citry = c
            template = "<div>{{ a }}|{{ b }}</div>"

            def template_data(self, kwargs, slots):
                return {"a": slots.get("a", ""), "b": slots.get("b", "")}

        class Page(Component):
            citry = c
            template = '<c-card><c-for each="s in names"><c-fill c-name="s">F-{{ s }}</c-fill></c-for></c-card>'

            def template_data(self, kwargs, slots):
                return {"names": ["a", "b"]}

        # Each fill closes over its own iteration, so the bodies differ.
        assert str(Page()) == '<div data-cid-c2="" data-cid-c1="">F-a|F-b</div>'

    def test_loop_variable_captured_per_component(self):
        c = _make_citry()

        class Card(Component):
            citry = c
            template = "<li>{{ h }}</li>"

            def template_data(self, kwargs, slots):
                return {"h": slots["header"]}

        class Page(Component):
            citry = c
            template = '<c-for each="x in items"><c-card><c-fill name="header">{{ x }}</c-fill></c-card></c-for>'

            def template_data(self, kwargs, slots):
                return {"items": [1, 2]}

        # The fill body is rendered later (the child renders through the
        # queue), but each closure captured its own iteration's `x`.
        assert str(Page()) == '<li data-cid-c2="" data-cid-c1="">1</li><li data-cid-c3="" data-cid-c1="">2</li>'

    def test_duplicate_dynamic_fill_names_raise(self):
        c = _make_citry()

        class Card(Component):
            citry = c
            template = "<p>x</p>"

        class Page(Component):
            citry = c
            template = '<c-card><c-for each="s in names"><c-fill c-name="s">X</c-fill></c-for></c-card>'

            def template_data(self, kwargs, slots):
                return {"names": ["dup", "dup"]}

        with pytest.raises(RuntimeError, match="Multiple fills target the same slot name 'dup'"):
            str(Page())

    @pytest.mark.parametrize(
        ("names", "expected"),
        [
            (("a", "b"), "A|B"),
            (("dup", "dup"), None),
        ],
    )
    def test_identical_dynamic_fill_expressions_use_resolved_names(self, names, expected):
        c = _make_citry()

        class Card(Component):
            citry = c
            template = """
                <div>{{ a }}|{{ b }}</div>
            """

            def template_data(self, kwargs, slots):
                return {"a": slots.get("a", ""), "b": slots.get("b", "")}

        remaining_names = iter(names)

        class Page(Component):
            citry = c
            template = """
                <c-card>
                    <c-fill c-name="next_name()">A</c-fill>
                    <c-fill c-name="next_name()">B</c-fill>
                </c-card>
            """

            def template_data(self, kwargs, slots):
                return {"next_name": lambda: next(remaining_names)}

        if expected is None:
            with pytest.raises(RuntimeError, match="Multiple fills target the same slot name 'dup'"):
                str(Page())
        else:
            assert expected in str(Page())


class TestFillProps:
    def test_c_bind_spread_supplies_name(self):
        c = _make_citry()

        class Card(Component):
            citry = c
            template = "<div>{{ h }}</div>"

            def template_data(self, kwargs, slots):
                return {"h": slots.get("header", "")}

        class Page(Component):
            citry = c
            template = '<c-card><c-fill c-bind="props">X</c-fill></c-card>'

            def template_data(self, kwargs, slots):
                return {"props": {"name": "header"}}

        assert str(Page()) == '<div data-cid-c2="" data-cid-c1="">X</div>'

    @pytest.mark.parametrize(
        "fill_attrs",
        [
            'name="header" c-bind="props"',
            'c-bind="props" name="header"',
        ],
    )
    def test_c_bind_none_does_not_replace_static_fill_name(self, fill_attrs):
        c = _make_citry()

        class Card(Component):
            citry = c
            template = """
                <div>{{ header }}</div>
            """

            def template_data(self, kwargs, slots):
                return {"header": slots.get("header", "")}

        class Page(Component):
            citry = c
            template = f"""
                <c-card><c-fill {fill_attrs}>FILLED</c-fill></c-card>
            """

            def template_data(self, kwargs, slots):
                return {"props": None}

        assert "FILLED" in str(Page())

    def test_c_bind_none_as_only_fill_name_reaches_missing_name_error(self):
        c = _make_citry()

        class Card(Component):
            citry = c
            template = """
                <p>x</p>
            """

        class Page(Component):
            citry = c
            template = """
                <c-card><c-fill c-bind="props">X</c-fill></c-card>
            """

            def template_data(self, kwargs, slots):
                return {"props": None}

        with pytest.raises(RuntimeError, match="'name' must resolve to a non-empty string"):
            str(Page())

    def test_c_bind_unsupported_key_raises(self):
        c = _make_citry()

        class Card(Component):
            citry = c
            template = "<p>x</p>"

        class Page(Component):
            citry = c
            template = '<c-card><c-fill c-bind="props">X</c-fill></c-card>'

            def template_data(self, kwargs, slots):
                return {"props": {"name": "h", "bogus": 1}}

        with pytest.raises(RuntimeError, match="unsupported key 'bogus'"):
            str(Page())

    def test_c_bind_non_string_key_raises(self):
        c = _make_citry()

        class Card(Component):
            citry = c
            template = """
                <p>x</p>
            """

        class Page(Component):
            citry = c
            template = """
                <c-card><c-fill c-bind="props">X</c-fill></c-card>
            """

            def template_data(self, kwargs, slots):
                return {"props": {1: "value"}}

        with pytest.raises(TypeError, match=r"c-bind' on <c-fill> must use string keys"):
            str(Page())

    def test_boolean_name_is_rejected_during_parse(self):
        c = _make_citry()

        class Card(Component):
            citry = c
            template = "<p>x</p>"

        class Page(Component):
            citry = c
            template = "<c-card><c-fill name>X</c-fill></c-card>"

        with pytest.raises(SyntaxError, match="static 'name' must have a non-empty value"):
            str(Page())

    def test_data_var_must_be_identifier(self):
        c = _make_citry()

        class Card(Component):
            citry = c
            template = "<p>x</p>"

        class Page(Component):
            citry = c
            template = '<c-card><c-fill name="h" data="not valid">X</c-fill></c-card>'

        with pytest.raises(SyntaxError, match="Invalid <c-fill> data binding"):
            str(Page())

    def test_same_data_and_fallback_var_raises(self):
        c = _make_citry()

        class Card(Component):
            citry = c
            template = "<p>x</p>"

        class Page(Component):
            citry = c
            template = '<c-card><c-fill name="h" data="d" fallback="d">X</c-fill></c-card>'

        with pytest.raises(SyntaxError, match="Cannot define variable 'd' more than once"):
            str(Page())

    @pytest.mark.parametrize(("binding_attr", "binding_name"), [("data", "d"), ("fallback", "f")])
    def test_static_fill_binding_cannot_reuse_captured_context_name(self, binding_attr, binding_name):
        c = _make_citry()

        class Card(Component):
            citry = c
            template = '<c-slot name="item" />'

        class Page(Component):
            citry = c
            template = f'<c-card><c-fill name="item" {binding_attr}="{binding_name}">X</c-fill></c-card>'

            def template_data(self, kwargs, slots):
                return {binding_name: Const("outer")}

        with pytest.raises(
            RuntimeError,
            match=rf"Cannot define variable '{binding_name}'.*Variable shadowing is not allowed",
        ):
            str(Page())

    @pytest.mark.parametrize("binding_key", ["data", "fallback"])
    def test_spread_fill_binding_cannot_reuse_captured_context_name(self, binding_key):
        c = _make_citry()

        class Card(Component):
            citry = c
            template = '<c-slot name="item" />'

        class Page(Component):
            citry = c
            template = '<c-card><c-fill c-bind="props">X</c-fill></c-card>'

            def template_data(self, kwargs, slots):
                return {"props": {"name": "item", binding_key: "taken"}, "taken": "outer"}

        with pytest.raises(RuntimeError, match=r"Cannot define variable 'taken'.*Variable shadowing is not allowed"):
            str(Page())

    @pytest.mark.parametrize(
        ("fill_attrs", "props"),
        [
            ('name="item" data="outer" c-bind="props"', {"data": "local"}),
            ('name="item" c-bind="props" data="local"', {"data": "outer"}),
            ('name="item" data="local" c-bind="props"', None),
        ],
    )
    def test_only_effective_spread_binding_name_is_checked(self, fill_attrs, props):
        c = _make_citry()

        class Card(Component):
            citry = c
            template = '<c-slot name="item" c-value="\'slot\'" />'

        class Page(Component):
            citry = c
            template = f'<c-card><c-fill {fill_attrs}>{{{{ local["value"] }}}}</c-fill></c-card>'

            def template_data(self, kwargs, slots):
                return {"outer": "already present", "props": props}

        assert str(Page()) == "slot"

    def test_spread_none_value_disables_earlier_static_binding(self):
        c = _make_citry()

        class Card(Component):
            citry = c
            template = '<c-slot name="item" />'

        class Page(Component):
            citry = c
            template = '<c-card><c-fill name="item" data="d" c-bind="props">{{ d }}</c-fill></c-card>'

            def template_data(self, kwargs, slots):
                return {"d": "outer", "props": {"data": None}}

        assert str(Page()) == "outer"


class TestScopedSlotData:
    def test_fill_data_var_receives_slot_data(self):
        c = _make_citry()

        class Card(Component):
            citry = c
            template = "<div>{{ item(payload) }}</div>"

            def template_data(self, kwargs, slots):
                return {"item": slots["item"], "payload": {"user": "Jo"}}

        class Page(Component):
            citry = c
            template = '<c-card><c-fill name="item" data="d">U={{ d.user }}</c-fill></c-card>'

        assert str(Page()) == '<div data-cid-c2="" data-cid-c1="">U=Jo</div>'

    def test_fill_data_combines_with_parent_scope(self):
        c = _make_citry()

        class Card(Component):
            citry = c
            template = "<div>{{ item(payload) }}</div>"

            def template_data(self, kwargs, slots):
                return {"item": slots["item"], "payload": {"n": 2}}

        class Page(Component):
            citry = c
            template = '<c-card><c-fill name="item" data="d">{{ prefix }}{{ d.n }}</c-fill></c-card>'

            def template_data(self, kwargs, slots):
                return {"prefix": "no."}

        # `prefix` is Page's variable; `d` is the slot data from Card.
        assert str(Page()) == '<div data-cid-c2="" data-cid-c1="">no.2</div>'

    def test_fill_fallback_var_receives_fallback(self):
        c = _make_citry()

        class Card(Component):
            citry = c
            template = "<div>{{ item(payload, fb) }}</div>"

            def template_data(self, kwargs, slots):
                return {"item": slots["item"], "payload": {}, "fb": Slot("FALLBACK")}

        class Page(Component):
            citry = c
            template = '<c-card><c-fill name="item" fallback="f">[{{ f }}]</c-fill></c-card>'

        assert str(Page()) == '<div data-cid-c2="" data-cid-c1="">[FALLBACK]</div>'

    def test_fill_invoked_repeatedly_with_different_data(self):
        c = _make_citry()

        class Card(Component):
            citry = c
            template = '<ul><c-for each="u in users"><li>{{ item({"user": u}) }}</li></c-for></ul>'

            def template_data(self, kwargs, slots):
                return {"item": slots["item"], "users": ["A", "B"]}

        class Page(Component):
            citry = c
            template = '<c-card><c-fill name="item" data="d">Hi {{ d.user }}</c-fill></c-card>'

        assert str(Page()) == '<ul data-cid-c2="" data-cid-c1=""><li>Hi A</li><li>Hi B</li></ul>'

    def test_outer_scope_variable_resolves_on_every_slot_iteration(self):
        c = _make_citry()

        class Feed(Component):
            citry = c
            template = '<ul><c-for each="obj in objects"><li><c-slot name="inner" c-obj="obj" /></li></c-for></ul>'

            def template_data(self, kwargs, slots):
                return {"objects": ["OBJECT1", "OBJECT2"]}

        class Page(Component):
            citry = c
            template = '<c-feed><c-fill name="inner" data="d">{{ outer }} {{ d.obj }}</c-fill></c-feed>'

            def template_data(self, kwargs, slots):
                return {"outer": "OUTER_SCOPE_VARIABLE"}

        # Feed invokes the same slot once per <c-for> iteration. The fill
        # body's captured scope (Page's `outer`) stays intact on every
        # invocation, alongside that iteration's slot data.
        assert str(Page()) == (
            '<ul data-cid-c2="" data-cid-c1="">'
            "<li>OUTER_SCOPE_VARIABLE OBJECT1</li><li>OUTER_SCOPE_VARIABLE OBJECT2</li></ul>"
        )

    def test_fill_data_destructures_fields_aliases_and_rest(self):
        c = _make_citry()

        class Card(Component):
            citry = c
            template = '<c-slot name="item" alpha="A" beta="B" gamma="G" />'

        class Page(Component):
            citry = c
            template = """
              <c-card>
                <c-fill
                  name="item"
                  data="{ alpha, beta as renamed, **rest }"
                >
                  {{ alpha }}|{{ renamed }}|{{ rest.gamma }}
                </c-fill>
              </c-card>
            """

        assert str(Page()).strip() == "A|B|G"

    def test_fill_data_allows_rest_only_and_empty_rest(self):
        c = _make_citry()

        class Card(Component):
            citry = c
            template = '<c-slot name="item" />'

        class Page(Component):
            citry = c
            template = """
              <c-card>
                <c-fill name="item" data="{ **rest }">
                  {{ rest == {} }}
                </c-fill>
              </c-card>
            """

        assert str(Page()).strip() == "True"

    def test_fill_data_uses_python_identifier_normalization(self):
        c = _make_citry()

        class Card(Component):
            citry = c
            template = '<c-slot name="item" value="V" />'

        class Page(Component):
            citry = c
            template = """
              <c-card>
                <c-fill name="item" data="{ value as K }">
                  {{ K }}
                </c-fill>
              </c-card>
              <c-card>
                <c-fill name="item" data="K">
                  {{ K.value }}
                </c-fill>
              </c-card>
            """

        assert "".join(str(Page()).split()) == "VV"

    def test_fill_data_keeps_source_mapping_keys_literal(self):
        c = _make_citry()

        class Card(Component):
            citry = c
            template = '<c-slot name="item" K="V" />'

        class Page(Component):
            citry = c
            template = """
              <c-card>
                <c-fill name="item" data="{ K }">
                  {{ K }}
                </c-fill>
              </c-card>
            """

        assert str(Page()).strip() == "V"

    def test_normalized_fill_target_cannot_shadow_an_existing_variable(self):
        c = _make_citry()

        class Card(Component):
            citry = c
            template = '<c-slot name="item" value="V" />'

        class Page(Component):
            citry = c
            template = """
              <c-card>
                <c-fill name="item" data="{ value as K }">
                  body
                </c-fill>
              </c-card>
            """

            def template_data(self, kwargs, slots):
                return {"K": "outer"}

        with pytest.raises(RuntimeError, match="variable name is already taken"):
            str(Page())

    def test_fill_data_reports_a_missing_source_field(self):
        c = _make_citry()

        class Card(Component):
            citry = c
            template = '<c-slot name="item" present="yes" />'

        class Page(Component):
            citry = c
            template = """
              <c-card>
                <c-fill name="item" data="{ missing }">
                  {{ missing }}
                </c-fill>
              </c-card>
            """

        with pytest.raises(RuntimeError, match=r"requested slot-data field 'missing'.*'present'"):
            str(Page())

    @pytest.mark.parametrize("binding", ["{ alpha }", "{ value as alpha }", "{ **alpha }"])
    def test_each_destructured_target_obeys_shadowing_rules(self, binding):
        c = _make_citry()

        class Card(Component):
            citry = c
            template = '<c-slot name="item" alpha="A" value="V" />'

        class Page(Component):
            citry = c
            template = f"""
              <c-card>
                <c-fill name="item" data="{binding}">
                  body
                </c-fill>
              </c-card>
            """

            def template_data(self, kwargs, slots):
                return {"alpha": "outer"}

        with pytest.raises(RuntimeError, match="variable name is already taken"):
            str(Page())

    def test_direct_and_spread_data_bindings_follow_rightmost_provider_order(self):
        c = _make_citry()

        class Card(Component):
            citry = c
            template = '<c-slot name="item" alpha="A" />'

        class Page(Component):
            citry = c
            template = """
              <c-card>
                <c-fill name="item" data="{ alpha }" c-bind="whole_binding">
                  {{ whole.alpha }}
                </c-fill>
              </c-card>
              <c-card>
                <c-fill c-bind="whole_binding" name="item" data="{ alpha }">
                  {{ alpha }}
                </c-fill>
              </c-card>
            """

            def template_data(self, kwargs, slots):
                return {"whole_binding": {"data": "whole"}}

        assert "".join(str(Page()).split()) == "AA"

    def test_dynamic_spread_cannot_introduce_a_destructuring_pattern(self):
        c = _make_citry()

        class Card(Component):
            citry = c
            template = '<c-slot name="item" alpha="A" />'

        class Page(Component):
            citry = c
            template = '<c-card><c-fill c-bind="binding">body</c-fill></c-card>'

            def template_data(self, kwargs, slots):
                return {"binding": {"name": "item", "data": "{ alpha }"}}

        with pytest.raises(RuntimeError, match="cannot be supplied dynamically"):
            str(Page())


class TestComponentsInsideSlotContent:
    def test_component_inside_fill_renders(self):
        c = _make_citry()

        class Inner(Component):
            citry = c
            template = "<span>IN</span>"

        class Card(Component):
            citry = c
            template = "<div>{{ h }}</div>"

            def template_data(self, kwargs, slots):
                return {"h": slots["header"]}

        class Page(Component):
            citry = c
            template = '<c-card><c-fill name="header"><c-inner /></c-fill></c-card>'

        # Render order: Page (c1), Card (c2), then the deferred Inner found
        # inside the invoked fill content (c3).
        assert str(Page()) == '<div data-cid-c2="" data-cid-c1=""><span data-cid-c3="">IN</span></div>'

    def test_component_inside_default_slot_renders(self):
        c = _make_citry()

        class Inner(Component):
            citry = c
            template = "<span>IN</span>"

        class Card(Component):
            citry = c
            template = "<div>{{ body }}</div>"

            def template_data(self, kwargs, slots):
                return {"body": slots["default"]}

        class Page(Component):
            citry = c
            template = "<c-card>before <c-inner /> after</c-card>"

        assert str(Page()) == '<div data-cid-c2="" data-cid-c1="">before <span data-cid-c3="">IN</span> after</div>'

    def test_three_level_slot_passthrough(self):
        c = _make_citry()

        class Leaf(Component):
            citry = c
            template = "<i>LEAF</i>"

        class Mid(Component):
            citry = c
            template = "<b>{{ body }}</b>"

            def template_data(self, kwargs, slots):
                return {"body": slots["default"]}

        class Card(Component):
            citry = c
            template = "<div>{{ h }}</div>"

            def template_data(self, kwargs, slots):
                return {"h": slots["header"]}

        class Page(Component):
            citry = c
            template = '<c-card><c-fill name="header"><c-mid><c-leaf /></c-mid></c-fill></c-card>'

        # Page (c1) -> Card (c2) -> Mid found in Card's fill content (c3) ->
        # Leaf found in Mid's default-slot content (c4).
        assert str(Page()) == (
            '<div data-cid-c2="" data-cid-c1=""><b data-cid-c3=""><i data-cid-c4="">LEAF</i></b></div>'
        )

    def test_inner_component_slot_left_unfilled_keeps_its_own_default(self):
        # A fill applies only to the component it is written on: an inner
        # component of the same class, mounted inside that fill, renders its
        # own slot default rather than inheriting the outer fill.
        c = Citry()

        class Card(Component):
            citry = c
            template = '<div><c-slot name="footer">card-default-footer</c-slot></div>'

        class Page(Component):
            citry = c
            template = '<c-card><c-fill name="footer">WWW<c-card /></c-fill></c-card>'

        assert str(Page()) == (
            '<div data-cid-c2="" data-cid-c1="">WWW<div data-cid-c3="">card-default-footer</div></div>'
        )

    def test_same_fill_names_at_two_nesting_depths_stay_separate(self):
        c = _make_citry()

        class Card(Component):
            citry = c
            template = (
                "<section><h1>{{ name }}</h1>"
                '<header><c-slot name="header">Default header</c-slot></header>'
                '<main><c-slot name="main">Default main</c-slot></main>'
                '<footer><c-slot name="footer">Default footer</c-slot></footer></section>'
            )

            def template_data(self, kwargs, slots):
                return {"name": kwargs["name"]}

        class Page(Component):
            citry = c
            template = (
                '<c-card name="Igor">'
                '<c-fill name="header">'
                '<c-card name="Joe2">'
                '<c-fill name="header">Name2: {{ name }}</c-fill>'
                '<c-fill name="main">Day2: {{ day }}</c-fill>'
                '<c-fill name="footer">XYZ</c-fill>'
                "</c-card>"
                "</c-fill>"
                '<c-fill name="footer">WWW</c-fill>'
                "</c-card>"
            )

            def template_data(self, kwargs, slots):
                return {"name": "Jannete", "day": "Monday"}

        # Each depth's fills go to their own card: the inner card gets its
        # own header/main/footer, while the outer card keeps its default
        # main. All fill bodies are written in Page's template, so they
        # close over Page's scope: `{{ name }}` in the innermost fill is
        # Page's "Jannete", not the inner card's `name` kwarg ("Joe2"),
        # even though that kwarg is in the inner card's own scope (each
        # card's <h1> shows its own).
        assert str(Page()) == (
            '<section data-cid-c2="" data-cid-c1=""><h1>Igor</h1>'
            '<header><section data-cid-c3=""><h1>Joe2</h1>'
            "<header>Name2: Jannete</header><main>Day2: Monday</main><footer>XYZ</footer></section></header>"
            "<main>Default main</main><footer>WWW</footer></section>"
        )


class TestSiblingFillIsolation:
    """
    Sibling calls of one slotted component each collect their own fills
    (the django-components multi-component and instance-isolation contract).
    """

    def test_sibling_calls_do_not_share_fills(self):
        c = _make_citry()

        class Panel(Component):
            citry = c
            template = (
                "<section>"
                '<header><c-slot name="header">Default header</c-slot></header>'
                '<main><c-slot name="main">Default main</c-slot></main>'
                '<footer><c-slot name="footer">Default footer</c-slot></footer>'
                "</section>"
            )

        class Page(Component):
            citry = c
            template = (
                '<c-panel><c-fill name="header">Override header</c-fill></c-panel>'
                '<c-panel><c-fill name="main">Override main</c-fill></c-panel>'
                '<c-panel><c-fill name="footer">Override footer</c-fill></c-panel>'
            )

        element = Page()
        # Each sibling call collects only its own fill: the filled slot is
        # overridden while the other two keep their fallbacks, and no fill
        # bleeds into an earlier or later sibling.
        assert str(element) == (
            '<section data-cid-c2="" data-cid-c1="">'
            "<header>Override header</header><main>Default main</main><footer>Default footer</footer></section>"
            '<section data-cid-c3="" data-cid-c1="">'
            "<header>Default header</header><main>Override main</main><footer>Default footer</footer></section>"
            '<section data-cid-c4="" data-cid-c1="">'
            "<header>Default header</header><main>Default main</main><footer>Override footer</footer></section>"
        )
        # Rendering the same element again repeats the output with fresh ids
        # only: no fill state carries across renders.
        assert str(element) == (
            '<section data-cid-c6="" data-cid-c5="">'
            "<header>Override header</header><main>Default main</main><footer>Default footer</footer></section>"
            '<section data-cid-c7="" data-cid-c5="">'
            "<header>Default header</header><main>Override main</main><footer>Default footer</footer></section>"
            '<section data-cid-c8="" data-cid-c5="">'
            "<header>Default header</header><main>Default main</main><footer>Override footer</footer></section>"
        )


class TestCollectFillsDispatch:
    """
    Fill collection dispatches through ``Node.collect_fills`` (open dispatch,
    docs/design/component_slots.md section 4.4), so node kinds an extension injects can
    take part without the collector knowing about them.
    """

    def test_base_node_rejected_in_fill_group(self):
        sink = FillSink("card")
        with pytest.raises(RuntimeError, match=r"Tag \(Node\) cannot appear next to '<c-fill>'"):
            Node().collect_fills(CitryContext(), sink)

    def test_expr_node_rejected_with_friendly_message(self):
        node = ExprNode("src", (0, 0), "x", ("x",))
        with pytest.raises(RuntimeError, match="Expression cannot appear next to '<c-fill>'"):
            node.collect_fills(CitryContext(), sink=FillSink("card"))

    def test_text_beside_fills_rejected_by_body_walk(self):
        sink = FillSink("card")
        with pytest.raises(RuntimeError, match="Text cannot appear next to '<c-fill>'"):
            collect_fills_from_body(["not whitespace"], CitryContext(), sink)

    def test_custom_node_can_register_fills(self):
        # An extension-style node participates by overriding collect_fills.
        class AutoHeader(Node):
            def collect_fills(self, context, sink):
                sink.add("header", Slot("auto"))

        sink = FillSink("card")
        collect_fills_from_body(["  ", AutoHeader()], CitryContext(), sink)
        assert sink.fills["header"]() == "auto"

    def test_sink_rejects_duplicate_names(self):
        sink = FillSink("card")
        sink.add("header", Slot("a"))
        with pytest.raises(RuntimeError, match="Multiple fills target the same slot name 'header'"):
            sink.add("header", Slot("b"))

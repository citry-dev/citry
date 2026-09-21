"""
Tests for authored metadata in the typed prepared Vue render.

Element ``#c-key`` values are carried by generated prepared-data bindings;
component ``#c-key`` values stay in typed call frames and affect generated
occurrence identities. ``#c-ignore`` remains parsed syntax but is explicitly
unsupported by prepared rendering. The plain ``key`` attribute and ``key`` /
``c-key`` component inputs remain ordinary HTML and component inputs.
"""

import json

import pytest

from citry import Citry, Component
from citry._vue.capture import render_prepared_direct
from citry._vue.direct_capture import UnsupportedPreparedView, assemble_typed_render
from citry.citry_render import CitryRender
from citry.constness import Const


def _assemble_render(render: CitryRender):
    return assemble_typed_render(
        render,
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )


def _assemble(component: Component):
    return _assemble_render(render_prepared_direct(component))


def _renders(render: CitryRender):
    yield render
    for part in render.parts:
        if isinstance(part, CitryRender):
            yield from _renders(part)


def _component_keys(render: CitryRender) -> list[str | None]:
    return [
        metadata.call.explicit_key
        for item in _renders(render)
        if (metadata := item.frame.prepared_occurrence) is not None and metadata.call is not None
    ]


def _element_keys(assembly, occurrence) -> list[object]:
    compile_input = assembly.compile_inputs[occurrence.definition_id]
    keys = [item["keyBindingKey"] for item in compile_input.element_bindings if item["keyBindingKey"] is not None]
    return [occurrence.prepared_data[key] for key in keys]


def _called_occurrence_ids(occurrence) -> list[str]:
    values = [item["id"] for item in occurrence.prepared_data.get("calls", {}).values()]
    values.extend(child_id for run in occurrence.prepared_data.get("callRuns", {}).values() for child_id in run)
    return values


class TestElementKey:
    def test_key_on_plain_element(self):
        c = Citry()

        class Page(Component):
            citry = c
            template = '<div #c-key="ident">x</div>'

            def template_data(self, kwargs, slots):
                return {"ident": kwargs["ident"]}

        assembly = _assemble(Page(ident=7))
        root = assembly.view.occurrences[0]
        compile_input = assembly.compile_inputs[root.definition_id]

        assert _element_keys(assembly, root) == ["7"]
        assert ':key="preparedData.citryKey0"' in compile_input.template
        assert "data-citry-key" not in compile_input.template

    def test_key_inside_c_for_evaluates_per_item(self):
        c = Citry()

        class KeyedList(Component):
            citry = c
            template = '<ul><c-for each="item in items"><li #c-key="item">x</li></c-for></ul>'

            def template_data(self, kwargs, slots):
                return {"items": kwargs["items"]}

        assembly = _assemble(KeyedList(items=[1, 2]))
        root = assembly.view.occurrences[0]
        compile_input = assembly.compile_inputs[root.definition_id]

        assert _element_keys(assembly, root) == ["1", "2"]
        assert compile_input.template.count(':key="preparedData.citryKey') == 2

    def test_key_value_stays_in_prepared_data_not_compiled_template(self):
        c = Citry()

        class Page(Component):
            citry = c
            template = '<div #c-key="raw">x</div>'

            def template_data(self, kwargs, slots):
                return {"raw": "a<b>&c"}

        assembly = _assemble(Page())
        root = assembly.view.occurrences[0]
        compile_input = assembly.compile_inputs[root.definition_id]

        assert _element_keys(assembly, root) == ["a<b>&c"]
        assert "a<b>&c" not in compile_input.template
        assert "data-citry-key" not in compile_input.template

    def test_none_element_key_is_carried_as_null(self):
        c = Citry()

        class Page(Component):
            citry = c
            template = '<div #c-key="missing">x</div>'

            def template_data(self, kwargs, slots):
                return {"missing": None}

        assembly = _assemble(Page())
        root = assembly.view.occurrences[0]

        assert _element_keys(assembly, root) == [None]

    @pytest.mark.parametrize(
        ("value", "rendered"),
        [
            (False, "False"),
            (0, "0"),
            ("", ""),
        ],
    )
    def test_non_none_falsy_element_key_is_preserved(self, value, rendered):
        c = Citry()

        class Page(Component):
            citry = c
            template = '<div #c-key="key">x</div>'

            def template_data(self, kwargs, slots):
                return {"key": kwargs["key"]}

        assembly = _assemble(Page(key=value))
        root = assembly.view.occurrences[0]

        assert _element_keys(assembly, root) == [rendered]

    def test_optional_keys_inside_c_for_omit_only_none(self):
        c = Citry()

        class KeyedList(Component):
            citry = c
            template = '<ul><c-for each="item in items"><li #c-key="item">x</li></c-for></ul>'

            def template_data(self, kwargs, slots):
                return {"items": kwargs["items"]}

        assembly = _assemble(KeyedList(items=[None, False, 0, ""]))
        root = assembly.view.occurrences[0]

        assert _element_keys(assembly, root) == [None, "False", "0", ""]

    def test_none_element_key_survives_const_precomputation(self):
        c = Citry()

        class Page(Component):
            citry = c
            template = '<div #c-key="key">x</div>'

            def template_data(self, kwargs, slots):
                return {"key": Const(None)}

        for _ in range(2):
            assembly = _assemble(Page())
            root = assembly.view.occurrences[0]
            assert _element_keys(assembly, root) == [None]


class TestElementIgnore:
    def test_ignore_is_explicitly_unsupported_in_prepared_vue(self):
        c = Citry()

        class Page(Component):
            citry = c
            template = "<div><p #c-ignore>chart</p></div>"

        with pytest.raises(ValueError, match="prepared Vue rendering does not yet support #c-ignore"):
            render_prepared_direct(Page())


class TestComponentKey:
    def test_single_root_child_key_lives_in_prepared_call_data(self):
        c = Citry()

        class Row(Component):
            citry = c
            template = "<span>{{ label }}</span>"

            def template_data(self, kwargs, slots):
                return {"label": kwargs.get("label", "?")}

        class Parent(Component):
            citry = c
            template = '<div><c-Row #c-key="1" c-label="\'one\'" /></div>'

        rendered = render_prepared_direct(Parent())
        assembly = _assemble_render(rendered)
        root = assembly.view.occurrences[0]
        child = next(item for item in assembly.view.occurrences if item.parent_id == root.id)

        assert _component_keys(rendered) == ["1"]
        assert _called_occurrence_ids(root) == [child.id]
        assert child.parent_id == root.id
        call_key = next(iter(root.prepared_data["calls"]))
        assert f':key="preparedData.calls.{call_key}.key"' in assembly.compile_inputs[root.definition_id].template

    def test_multi_root_child_stays_one_prepared_call(self):
        c = Citry()

        class TwoRoots(Component):
            citry = c
            template = "<div>a</div><p>b</p>"

        class Parent(Component):
            citry = c
            template = "<section><c-TwoRoots #c-key=\"'k1'\" /></section>"

        rendered = render_prepared_direct(Parent())
        assembly = _assemble_render(rendered)
        root = assembly.view.occurrences[0]
        child = next(item for item in assembly.view.occurrences if item.parent_id == root.id)

        assert _component_keys(rendered) == ["k1"]
        assert _called_occurrence_ids(root) == [child.id]
        assert assembly.compile_inputs[root.definition_id].local_calls
        assert assembly.compile_inputs[child.definition_id].template == "<div>a</div><p>b</p>"

    def test_keyed_children_inside_c_for_reorder_by_explicit_identity(self):
        c = Citry()

        class Row(Component):
            citry = c
            template = "<span>{{ label }}</span>"

            def template_data(self, kwargs, slots):
                return {"label": kwargs.get("label", "?")}

        class Parent(Component):
            citry = c
            template = '<ul><c-for each="item in items"><c-Row #c-key="item" c-label="item" /></c-for></ul>'

            def template_data(self, kwargs, slots):
                return {"items": kwargs["items"]}

        identities_by_order = []
        for items in (["a", "b"], ["b", "a"]):
            rendered = render_prepared_direct(Parent(items=items))
            assembly = _assemble_render(rendered)
            root = assembly.view.occurrences[0]
            children = [item for item in assembly.view.occurrences if item.parent_id == root.id]
            call_keys = _component_keys(rendered)
            call_ids = _called_occurrence_ids(root)

            assert call_keys == items
            assert call_ids == [item.id for item in children]
            assert len(set(call_ids)) == 2
            assert len(assembly.compile_inputs[root.definition_id].local_call_runs) == 1
            identities_by_order.append(dict(zip(call_keys, call_ids, strict=True)))

        assert identities_by_order[0] == identities_by_order[1]

    def test_duplicate_explicit_keys_in_one_loop_are_rejected(self):
        c = Citry()

        class Row(Component):
            citry = c
            template = "<span>x</span>"

        class Parent(Component):
            citry = c
            template = '<c-for each="item in items"><c-Row #c-key="item" /></c-for>'

            def template_data(self, kwargs, slots):
                return {"items": kwargs["items"]}

        with pytest.raises(UnsupportedPreparedView, match="duplicate explicit #c-key"):
            _assemble(Parent(items=["same", "same"]))

    def test_component_key_is_kept_out_of_prepared_wire_and_compile_source(self):
        c = Citry()

        class Row(Component):
            citry = c
            template = "<span>x</span>"

        class Parent(Component):
            citry = c
            template = '<section><c-Row #c-key="raw" /></section>'

            def template_data(self, kwargs, slots):
                return {"raw": '</script><x>&"π'}

        rendered = render_prepared_direct(Parent())
        assembly = _assemble_render(rendered)
        root = assembly.view.occurrences[0]
        child = next(item for item in assembly.view.occurrences if item.parent_id == root.id)
        prepared_wire_data = json.dumps([item.prepared_data for item in assembly.view.occurrences])
        compiled_templates = "".join(item.template for item in assembly.compile_inputs.values())

        assert _component_keys(rendered) == ['</script><x>&"π']
        assert _called_occurrence_ids(root) == [child.id]
        assert '</script><x>&"π' not in prepared_wire_data
        assert '</script><x>&"π' not in compiled_templates
        assert "<" not in prepared_wire_data

    def test_none_key_omits_component_key(self):
        c = Citry()

        class Row(Component):
            citry = c
            template = "<span>x</span>"

        class Parent(Component):
            citry = c
            template = '<section><c-Row #c-key="key" /></section>'

            def template_data(self, kwargs, slots):
                return {"key": None}

        rendered = render_prepared_direct(Parent())
        assembly = _assemble_render(rendered)
        root = assembly.view.occurrences[0]
        child = next(item for item in assembly.view.occurrences if item.parent_id == root.id)

        assert _component_keys(rendered) == [None]
        assert _called_occurrence_ids(root) == [child.id]

    @pytest.mark.parametrize(
        ("value", "rendered"),
        [
            (False, "False"),
            (0, "0"),
            ("", ""),
        ],
    )
    def test_non_none_falsy_component_key_is_preserved(self, value, rendered):
        c = Citry()

        class Row(Component):
            citry = c
            template = "<span>x</span>"

        class Parent(Component):
            citry = c
            template = '<section><c-Row #c-key="key" /></section>'

            def template_data(self, kwargs, slots):
                return {"key": kwargs["key"]}

        component_render = render_prepared_direct(Parent(key=value))
        assembly = _assemble_render(component_render)
        root = assembly.view.occurrences[0]
        child = next(item for item in assembly.view.occurrences if item.parent_id == root.id)

        assert _component_keys(component_render) == [rendered]
        assert _called_occurrence_ids(root) == [child.id]

    def test_key_survives_constant_body_capture(self):
        # A constant body can be precomputed while the invocation identity
        # stays in its typed call frame.
        c = Citry()

        class Row(Component):
            citry = c
            template = "<span>x</span>"

        class Parent(Component):
            citry = c
            template = "<div><c-Row #c-key=\"'k'\">{{ label }}</c-Row></div>"

            def template_data(self, kwargs, slots):
                return {"label": Const("hi")}

        for _ in range(2):
            rendered = render_prepared_direct(Parent())
            assembly = _assemble_render(rendered)
            root = assembly.view.occurrences[0]
            child = next(item for item in assembly.view.occurrences if item.parent_id == root.id)

            assert _component_keys(rendered) == ["k"]
            assert _called_occurrence_ids(root) == [child.id]

    def test_transparent_component_key_reaches_native_subtree_identity(self):
        c = Citry()

        class Page(Component):
            citry = c
            template = '<c-provide key="theme" c-data="{}" #c-key="\'p\'"><span>x</span></c-provide>'

        rendered = render_prepared_direct(Page())
        assembly = _assemble_render(rendered)
        root = assembly.view.occurrences[0]
        compile_input = assembly.compile_inputs[root.definition_id]

        assert _component_keys(rendered) == ["p"]
        assert compile_input.template.count(":key=") == 1
        assert "<span" in compile_input.template

    def test_key_on_dynamic_component_belongs_to_the_selected_target_range(self):
        c = Citry()

        class Row(Component):
            citry = c
            template = "<span>x</span>"

        class Page(Component):
            citry = c
            template = '<c-component c-is="target" #c-key="\'k\'" />'

            def template_data(self, kwargs, slots):
                return {"target": Row}

        rendered = render_prepared_direct(Page())
        assembly = _assemble_render(rendered)
        root = assembly.view.occurrences[0]
        child = next(item for item in assembly.view.occurrences if item.parent_id == root.id)

        assert _component_keys(rendered) == ["k", "k"]
        assert child.type_key == Row.class_id
        assert _called_occurrence_ids(root) == [child.id]

    def test_component_and_its_root_element_have_independent_keys(self):
        c = Citry()

        class Row(Component):
            citry = c
            template = "<span #c-key=\"'own'\">x</span>"

        class Page(Component):
            citry = c
            template = "<c-Row #c-key=\"'component'\" />"

        rendered = render_prepared_direct(Page())
        assembly = _assemble_render(rendered)
        root = assembly.view.occurrences[0]
        child = next(item for item in assembly.view.occurrences if item.parent_id == root.id)

        assert _component_keys(rendered) == ["component"]
        assert _element_keys(assembly, child) == ["own"]
        assert _called_occurrence_ids(root) == [child.id]

    def test_empty_component_can_be_keyed(self):
        c = Citry()

        class Blank(Component):
            citry = c
            template = ""

        class Page(Component):
            citry = c
            template = "<main>before<c-Blank #c-key=\"'empty'\" />after</main>"

        rendered = render_prepared_direct(Page())
        assembly = _assemble_render(rendered)
        root = assembly.view.occurrences[0]
        child = next(item for item in assembly.view.occurrences if item.parent_id == root.id)

        assert _component_keys(rendered) == ["empty"]
        assert _called_occurrence_ids(root) == [child.id]


class TestComponentIgnore:
    def test_source_range_ignore_is_explicitly_unsupported_in_prepared_vue(self):
        c = Citry()

        class Child(Component):
            citry = c
            template = "<span>child</span>"

        class Page(Component):
            citry = c
            template = "<c-child #c-ignore />"

        with pytest.raises(TypeError, match="component #c-ignore is unsupported in prepared Vue"):
            render_prepared_direct(Page())


class TestTemplateAuthoredOnly:
    def test_key_via_element_spread_is_render_error(self):
        c = Citry()

        class Page(Component):
            citry = c
            template = '<div c-bind="attrs">x</div>'

            def template_data(self, kwargs, slots):
                return {"attrs": {"#c-key": "5"}}

        with pytest.raises(
            RuntimeError,
            match=r"'#c-key' arrived on <div> through an attribute spread or a dynamic attribute\. "
            r"'#c-\*' framework attributes are template-authored only: "
            r"write the attribute directly on the tag in the template\.",
        ):
            Page().render().serialize()

    def test_key_via_component_spread_is_render_error(self):
        c = Citry()

        class Row(Component):
            citry = c
            template = "<span>x</span>"

        class Page(Component):
            citry = c
            template = '<c-Row c-bind="attrs" />'

            def template_data(self, kwargs, slots):
                return {"attrs": {"#c-key": "5"}}

        with pytest.raises(
            RuntimeError,
            match=r"'#c-key' arrived on <c-row> through an attribute spread or a dynamic attribute\. "
            r"'#c-\*' framework attributes are template-authored only: "
            r"write the attribute directly on the component tag in the template\.",
        ):
            Page().render().serialize()

    def test_none_key_via_element_spread_is_still_render_error(self):
        c = Citry()

        class Page(Component):
            citry = c
            template = '<div c-bind="attrs">x</div>'

            def template_data(self, kwargs, slots):
                return {"attrs": {"#c-key": None}}

        with pytest.raises(RuntimeError, match=r"'#c-key' arrived on <div> through an attribute spread"):
            Page().render().serialize()

    def test_none_key_via_component_spread_is_still_render_error(self):
        c = Citry()

        class Row(Component):
            citry = c
            template = "<span>x</span>"

        class Page(Component):
            citry = c
            template = '<c-Row c-bind="attrs" />'

            def template_data(self, kwargs, slots):
                return {"attrs": {"#c-key": None}}

        with pytest.raises(RuntimeError, match=r"'#c-key' arrived on <c-row> through an attribute spread"):
            Page().render().serialize()

    def test_ignore_via_spread_is_render_error(self):
        c = Citry()

        class Page(Component):
            citry = c
            template = '<div c-bind="attrs">x</div>'

            def template_data(self, kwargs, slots):
                return {"attrs": {"#c-ignore": True}}

        with pytest.raises(RuntimeError, match=r"'#c-ignore' arrived on <div>"):
            Page().render().serialize()


class TestChannelErrorsSurfaceAtTemplateLoad:
    # The parse-time rules live in the Rust suite; these two lock that the
    # errors surface through Python template loading with their message.
    def test_ignore_on_reserved_structural_tag(self):
        c = Citry()

        class Page(Component):
            citry = c
            template = '<c-if cond="True" #c-ignore>x</c-if>'

        # The message carries the attribute's real template location.
        with pytest.raises(
            SyntaxError,
            match=r"'#c-ignore' is not supported on '<c-if>' \(line 1, column 19\)",
        ):
            Page().render().serialize()

    def test_unknown_meta_name(self):
        c = Citry()

        class Page(Component):
            citry = c
            template = '<div #c-frobnicate="1">x</div>'

        with pytest.raises(
            SyntaxError,
            match=r"Unknown '#c-\*' attribute '#c-frobnicate'.*'#c-key' and '#c-ignore'",
        ):
            Page().render().serialize()


class TestOrdinaryKeyStaysOrdinary:
    # The channel reserves nothing outside its `#c-` prefix: the plain `key`
    # HTML attribute and the `key` / `c-key` component inputs behave exactly
    # as before.
    def test_plain_key_attribute_on_elements(self):
        c = Citry()

        class Page(Component):
            citry = c
            template = '<input key="" /><input key="v" />'

        # The ordinary empty value stays an ordinary empty attribute value.
        assert Page().render().serialize() == '<input key="" data-cid-c1=""/><input key="v" data-cid-c1=""/>'

    def test_key_and_c_key_component_inputs(self):
        c = Citry()

        class Guarded(Component):
            citry = c
            template = "<i>{{ key }}</i>"

            def template_data(self, kwargs, slots):
                return {"key": kwargs.get("key")}

        class StaticPage(Component):
            citry = c
            template = '<c-Guarded key="plain" />'

        class DynamicPage(Component):
            citry = c
            template = '<c-Guarded c-key="1 + 1" />'

        assert StaticPage().render().serialize() == '<i data-cid-c2="" data-cid-c1="">plain</i>'
        assert DynamicPage().render().serialize() == '<i data-cid-c4="" data-cid-c3="">2</i>'

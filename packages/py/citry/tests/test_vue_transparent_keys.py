from __future__ import annotations

import re

import pytest

from citry import Citry, Component
from citry._vue.capture import render_prepared_direct
from citry._vue.compiler import NativeCompiler
from citry._vue.direct_capture import UnsupportedPreparedView, assemble_typed_render


def _assemble(component: Component):
    return assemble_typed_render(
        render_prepared_direct(component),
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )


def _root(assembly):
    occurrence = next(item for item in assembly.view.occurrences if item.id == assembly.view.root_id)
    return occurrence, assembly.compile_inputs[occurrence.definition_id]


def _compile(occurrence, compile_input):
    return NativeCompiler().compile(
        compile_input.template,
        type_key=occurrence.type_key,
        local_calls=compile_input.local_calls,
        element_bindings=compile_input.element_bindings,
        local_call_runs=compile_input.local_call_runs,
        dynamic_elements=compile_input.dynamic_elements,
        template_context_names=compile_input.template_context_names,
        opaque_html_sites=compile_input.opaque_html_sites,
        runtime_event_sites=compile_input.runtime_event_sites,
    )


@pytest.mark.parametrize(
    "body",
    ["", "plain text", "<span>one root</span>", "<span>first</span><b>second</b>"],
    ids=["empty", "text", "single-root", "multi-root"],
)
def test_keyed_transparent_call_compiles_a_keyed_fragment_for_each_body_shape(body: str) -> None:
    registry = Citry(autodiscover=False)

    class Page(Component):
        citry = registry
        template = '<main><c-provide key="theme" c-data="{}" #c-key="\'\'">' + body + "</c-provide></main>"

    assembly = _assemble(Page())
    root, compile_input = _root(assembly)
    [binding] = compile_input.element_bindings
    key = binding["keyBindingKey"]

    assert binding["attrsBindingKey"] is None
    assert type(key) is str
    assert compile_input.template.count('<template v-if="true" :key="$citryPrepared.') == 1
    assert '<template v-if="false"></template></template>' in compile_input.template
    assert root.prepared_data[key].startswith("citryTransparent")
    assert binding["sourceStart"] == len(b"<main>")
    opening_end = compile_input.template.index(">", binding["sourceStart"]) + 1
    assert binding["sourceEnd"] == len(compile_input.template[:opening_end].encode())

    compiled = _compile(root, compile_input)
    assert f"createElementBlock(_Fragment, {{ key: _ctx.$citryPrepared.{key} }}" in compiled.javascript


def test_unkeyed_transparent_call_remains_unwrapped() -> None:
    registry = Citry(autodiscover=False)

    class Page(Component):
        citry = registry
        template = '<main><c-provide key="theme" c-data="{}"><span>plain</span></c-provide></main>'

    assembly = _assemble(Page())
    root, compile_input = _root(assembly)

    assert "citryKey0" not in root.prepared_data
    assert "citryTransparent" not in compile_input.template
    assert ':key="$citryPrepared.' not in compile_input.template


def test_empty_keyed_transparent_call_preserves_an_independently_keyed_child() -> None:
    registry = Citry(autodiscover=False)

    class Child(Component):
        citry = registry
        template = '<span class="child">child</span>'

    class Page(Component):
        citry = registry
        template = (
            '<main><c-provide key="theme" c-data="{}" #c-key="\'outer\'">'
            "<c-Child #c-key=\"'inner'\" />"
            "</c-provide></main>"
        )

    assembly = _assemble(Page())
    root, compile_input = _root(assembly)
    [call] = compile_input.local_calls
    local_id = call["localId"]
    [child] = [item for item in assembly.view.occurrences if item.type_key == Child.class_id]
    wrapper_key = compile_input.element_bindings[0]["keyBindingKey"]

    assert compile_input.template.count(":key=") == 2
    assert f':key="$citryPrepared.calls.{local_id}.key"' in compile_input.template
    assert root.prepared_data["citryKey0"].startswith("citryTransparent")
    assert child.parent_id == root.id
    compiled = _compile(root, compile_input)
    assert f"key: _ctx.$citryPrepared.{wrapper_key}" in compiled.javascript
    assert f"key: _ctx.$citryPrepared.calls.{local_id}.key" in compiled.javascript


def test_duplicate_transparent_sibling_keys_are_rejected() -> None:
    registry = Citry(autodiscover=False)

    class Page(Component):
        citry = registry
        template = (
            '<c-for each="value in values">'
            '<c-provide key="theme" c-data="{}" #c-key="value"><span>{{ value }}</span></c-provide>'
            "</c-for>"
        )

        def template_data(self, kwargs, slots):
            return {"values": kwargs["values"]}

    rendered = render_prepared_direct(Page(values=["same", "same"]))
    with pytest.raises(UnsupportedPreparedView, match="duplicate explicit #c-key"):
        assemble_typed_render(
            rendered,
            revision=0,
            tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
        )


def test_descendant_placement_identity_follows_transparent_key_across_reorder() -> None:
    registry = Citry(autodiscover=False)

    class Child(Component):
        citry = registry
        template = "<p>{{ value }}</p>"

        def template_data(self, kwargs, slots):
            return kwargs

    class Page(Component):
        citry = registry
        template = (
            '<c-for each="value in values">'
            '<c-provide key="theme" c-data="{}" #c-key="value">'
            '<c-Child c-value="value" />'
            "</c-provide></c-for>"
        )

        def template_data(self, kwargs, slots):
            return {"values": kwargs["values"]}

    def keyed(values: list[str]) -> dict[str, tuple[str, str | None]]:
        assembly = _assemble(Page(values=values))
        return {
            item.prepared_data["citryText0"]: (item.id, item.placement_key)
            for item in assembly.view.occurrences
            if item.type_key == Child.class_id
        }

    assert keyed(["a", "b"]) == keyed(["b", "a"])


def test_keyed_transparent_slot_identity_is_independent_of_root_occurrence() -> None:
    registry = Citry(autodiscover=False)

    class Child(Component):
        citry = registry
        template = "<p>child</p>"

    class Page(Component):
        citry = registry
        template = (
            '<main><c-provide key="theme" c-data="{}" #c-key="\'wrapper\'">'
            '<c-slot name="first"><c-Child #c-key="\'first\'" /></c-slot>'
            '<c-slot name="second"><c-Child #c-key="\'second\'" /></c-slot>'
            "</c-provide></main>"
        )

    def identities(root_id: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
        assembly = assemble_typed_render(
            render_prepared_direct(Page()),
            revision=0,
            root_occurrence_id=root_id,
            tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
        )
        root = next(item for item in assembly.view.occurrences if item.id == root_id)
        template = assembly.compile_inputs[root.definition_id].template
        slot_ids = tuple(re.findall(r"citrySlot[0-9a-f]+", template))
        children = tuple(item.placement_key for item in assembly.view.occurrences if item.type_key == Child.class_id)
        assert all(placement_key is not None for placement_key in children)
        return slot_ids, tuple(placement_key for placement_key in children if placement_key is not None)

    first = identities("citryOccurrenceFirst")
    second = identities("citryOccurrenceSecond")

    assert first == second
    assert len(set(first[0])) == 2


def test_keyed_transparent_wrapper_survives_component_cache_replay() -> None:
    registry = Citry(autodiscover=False)
    data_calls = 0

    class Page(Component):
        citry = registry
        template = (
            '<main><c-provide key="theme" c-data="{}" #c-key="\'cached\'"><span>cached body</span></c-provide></main>'
        )

        class Cache:
            enabled = True

        def template_data(self, kwargs, slots):
            nonlocal data_calls
            data_calls += 1
            return {}

    assemblies = [_assemble(Page()), _assemble(Page())]
    assert data_calls == 1

    for assembly in assemblies:
        root, compile_input = _root(assembly)
        assert root.prepared_data["citryKey0"].startswith("citryTransparent")
        assert '<template v-if="true" :key="$citryPrepared.citryKey0">' in compile_input.template
        assert compile_input.element_bindings[0]["keyBindingKey"] == "citryKey0"
        _compile(root, compile_input)


def test_keyed_transparent_wrapper_in_supplied_slot_keeps_lexical_key_owner() -> None:
    registry = Citry(autodiscover=False)

    class Child(Component):
        citry = registry
        template = "<strong>child</strong>"

    class Receiver(Component):
        citry = registry
        template = '<article><c-slot name="body" /></article>'

    class Caller(Component):
        citry = registry
        template = (
            "<c-Receiver #c-key=\"'receiver'\">"
            '<c-fill name="body"><c-provide key="theme" c-data="{}" #c-key="\'slot\'">'
            "<c-Child #c-key=\"'child'\" />"
            "</c-provide></c-fill></c-Receiver>"
        )

    assembly = _assemble(Caller())
    root, compile_input = _root(assembly)
    receiver = next(item for item in assembly.view.occurrences if item.type_key == Receiver.class_id)
    child = next(item for item in assembly.view.occurrences if item.type_key == Child.class_id)

    assert root.prepared_data["citryKey0"].startswith("citryTransparent")
    assert ':key="$citryPrepared.citryKey0"' in compile_input.template
    assert compile_input.element_bindings[0]["keyBindingKey"] == "citryKey0"
    assert child.parent_id == receiver.id
    assert receiver.parent_id == root.id
    _compile(root, compile_input)


def test_slot_names_inside_keyed_rows_follow_the_row_key_across_reorder() -> None:
    registry = Citry(autodiscover=False)

    class Table(Component):
        citry = registry
        template = """
            <table><tbody>
              <tr c-for="row in rows" #c-key="row" c-data-row="row">
                <td><c-slot name="cell" c-row="row" /></td>
              </tr>
            </tbody></table>
        """

        def template_data(self, kwargs, slots):
            return {"rows": kwargs["rows"]}

    class Page(Component):
        citry = registry
        template = """
            <c-table c-rows="rows">
              <c-fill name="cell" data="{ row }"><input c-name="row" /></c-fill>
            </c-table>
        """

        def template_data(self, kwargs, slots):
            return {"rows": kwargs["rows"]}

    def outlets(rows: list[str]) -> tuple[str, dict[str, str]]:
        # The slot names stay positional, so the compiled template does not
        # depend on the rows. Each outlet's Vue key, sent as data, follows its
        # row key, so a moved row keeps its slot content.
        assembly = _assemble(Page(rows=rows))
        table = next(item for item in assembly.view.occurrences if item.type_key == Table.class_id)
        template = assembly.compile_inputs[table.definition_id].template
        row_keys = [
            table.prepared_data[name] for name in re.findall(r':key="\$citryPrepared\.(citryKey\d+)"', template)
        ]
        names = re.findall(r'name="(citrySlot[0-9a-f]+)"', template)
        slot_keys = table.prepared_data["slotKeys"]
        assert len(row_keys) == len(names) == len(rows)
        assert template.count(':key="$citryPrepared.slotKeys[') == len(rows)
        return template, {row: slot_keys[name] for row, name in zip(row_keys, names, strict=True)}

    template, first = outlets(["a", "b"])
    reordered_template, reordered = outlets(["b", "a"])
    assert reordered_template == template
    assert reordered == first
    assert len(set(first.values())) == 2

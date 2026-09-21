from __future__ import annotations

import xml.etree.ElementTree as ET
from collections import UserDict
from dataclasses import replace

import pytest

from citry import Citry, Component, Const, Extension, Slot
from citry._vue.capture import (
    PreparedDynamicElementOpen,
    PreparedElementOpen,
    PreparedStaticRun,
    PreparedTextValue,
    prepared_browser_binding,
    render_prepared,
    render_prepared_direct,
)
from citry._vue.compiler import NativeCompiler
from citry._vue.direct import DirectCallRunRender, DirectPythonComponentRender, DirectSlotRender
from citry._vue.direct_capture import UnsupportedPreparedView, assemble_typed_render
from citry._vue.document import typed_document_shell
from citry._vue.leaf_program import PreparedLeafProgram, typed_leaf_parts
from citry._vue.prepared import PreparedOccurrence
from citry.citry_element import CitryElement
from citry.citry_render import CitryRender, RenderFrame
from citry.client_directives import ComponentTagClientBinding, ComponentTagClientBindingKind
from citry.ext.events.renderers import dispatcher_for


def _view(render):
    return assemble_typed_render(
        render,
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    ).view


def test_deferred_slots_in_call_run_forward_one_fill_per_member_to_lexical_owner() -> None:
    registry = Citry()
    declarations: list[Slot] = []

    class Declaration(Component):
        citry = registry
        template = """
          <c-slot />
        """

        def template_data(self, kwargs, slots):
            declarations.append(slots["default"])
            return {}

        def on_render(self):
            result, error = yield
            if error is not None:
                raise error
            return CitryRender(parts=[], context=result.context)

    class Receiver(Component):
        citry = registry
        template = """
          <section>{{ content }}</section>
        """

        def template_data(self, kwargs, slots):
            declaration = declarations[{"a": 0, "b": 1}[kwargs["key"]]]
            return {"content": Slot(lambda _: declaration())}

    class Root(Component):
        citry = registry
        template = """
          <c-Declaration><b v-text="label">first</b></c-Declaration>
          <c-Declaration><i v-text="label">second</i></c-Declaration>
          <c-for each="key in keys">
            <c-Receiver #c-key="key" c-key="key" />
          </c-for>
        """

        def template_data(self, kwargs, slots):
            return {"keys": ["a", "b"]}

        def js_data(self, kwargs, slots):
            return {"label": "lexical"}

    assembly = assemble_typed_render(
        render_prepared_direct(Root()),
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )
    root = next(item for item in assembly.view.occurrences if item.id == assembly.view.root_id)
    compiler_input = assembly.compile_inputs[root.definition_id]
    receiver_tag = "x-" + Receiver.class_id.lower().replace("_", "-")
    receiver_calls = compiler_input.template.split(f"<{receiver_tag}")[1:]
    assert len(receiver_calls) == 2
    assert all(call.split(f"</{receiver_tag}>", 1)[0].count("<template v-slot:") == 1 for call in receiver_calls)
    assert compiler_input.local_call_runs == ()
    assert sum(call["typeKey"] == Receiver.class_id for call in compiler_input.local_calls) == 2
    assert compiler_input.template.count('v-text="label"') == 2


def test_ctabs_transparent_projection_puts_nested_calls_in_physical_definition() -> None:
    import citry_ui

    registry = Citry(autodiscover=False)
    registry.register_library(citry_ui)

    class Leaf(Component):
        citry = registry
        name = "projection-leaf"
        template = "<em>leaf</em>"

    class Page(Component):
        citry = registry
        template = """
            <c-CTabs default_value="one" aria_label="Example">
              <c-CTab value="one"><span>One <c-projection-leaf #c-key="'tab-one'" /></span></c-CTab>
              <c-CTabPanel value="one"><p>Panel one <c-projection-leaf #c-key="'panel-one'" /></p></c-CTabPanel>
              <c-CTab value="two"><span>Two <c-projection-leaf #c-key="'tab-two'" /></span></c-CTab>
              <c-CTabPanel value="two"><p>Panel two <c-projection-leaf #c-key="'panel-two'" /></p></c-CTabPanel>
            </c-CTabs>
        """

    assembly = assemble_typed_render(
        render_prepared_direct(Page()),
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )
    page = next(item for item in assembly.view.occurrences if item.type_key == Page.class_id)
    physical = next(item for item in assembly.view.occurrences if item.type_key.startswith("CInternalTabs_"))
    page_input = assembly.compile_inputs[page.definition_id]
    physical_input = assembly.compile_inputs[physical.definition_id]

    # Declaration components remain calls in the lexical page slot. Their
    # projected child output is assembled into CInternalTabs, so its nested
    # calls must use the physical definition's preparedData.calls table.
    assert not any(call["typeKey"] == Leaf.class_id for call in page_input.local_calls)
    leaf_calls = [call for call in physical_input.local_calls if call["typeKey"] == Leaf.class_id]
    assert len(leaf_calls) == 4
    assert len(physical.prepared_data["calls"]) == 4
    assert all(physical.prepared_data["calls"][call["localId"]]["parentId"] == physical.id for call in leaf_calls)


def test_repeated_forwarded_multi_slot_fills_keep_nested_calls_with_the_lexical_caller() -> None:
    registry = Citry(autodiscover=False)

    class Leaf(Component):
        citry = registry
        name = "forwarded-leaf"
        template = "<i>leaf</i>"

    class Inner(Component):
        citry = registry
        name = "forwarded-inner"
        template = (
            '<article><header><c-slot name="header" /></header><section><c-slot name="body" /></section></article>'
        )

    class Wrapper(Component):
        citry = registry
        name = "forwarded-wrapper"
        template = (
            "<c-forwarded-inner #c-key=\"'inner'\">"
            '<c-fill name="header"><c-slot name="header" /></c-fill>'
            '<c-fill name="body"><c-slot name="body" /></c-fill>'
            "</c-forwarded-inner>"
        )

    class Root(Component):
        citry = registry
        template = """
            <main>
              <c-forwarded-wrapper #c-key="'one'">
                <c-fill name="header"><h3>One <c-forwarded-leaf #c-key="'header'" /></h3></c-fill>
                <c-fill name="body"><p>One <c-forwarded-leaf #c-key="'body'" /></p></c-fill>
              </c-forwarded-wrapper>
              <c-forwarded-wrapper #c-key="'two'">
                <c-fill name="header"><h3>Two <c-forwarded-leaf #c-key="'header'" /></h3></c-fill>
                <c-fill name="body"><p>Two <c-forwarded-leaf #c-key="'body'" /></p></c-fill>
              </c-forwarded-wrapper>
            </main>
        """

    assembly = assemble_typed_render(
        render_prepared_direct(Root()),
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )
    root = next(item for item in assembly.view.occurrences if item.type_key == Root.class_id)
    root_input = assembly.compile_inputs[root.definition_id]
    wrappers = [item for item in assembly.view.occurrences if item.type_key == Wrapper.class_id]
    assert len(wrappers) == 2
    assert len([call for call in root_input.local_calls if call["typeKey"] == Leaf.class_id]) == 4
    assert len([call for call in root_input.local_calls if call["typeKey"] == Wrapper.class_id]) == 2
    assert all(
        len(assembly.compile_inputs[wrapper.definition_id].local_calls) == 1
        and assembly.compile_inputs[wrapper.definition_id].local_calls[0]["typeKey"] == Inner.class_id
        for wrapper in wrappers
    )
    assert all(
        not assembly.compile_inputs[wrapper.definition_id].template.count("<x-forwarded-leaf") for wrapper in wrappers
    )


def test_native_compiler_authenticates_generic_browser_binding_operand() -> None:
    opening = '<p :title="$probe(preparedData.citryBinding0)">'
    compiled = NativeCompiler().compile(
        opening + "initial</p>",
        type_key="BrowserBinding",
        element_bindings=(
            {
                "sourceStart": 0,
                "sourceEnd": len(opening.encode()),
                "attrsBindingKey": None,
                "keyBindingKey": None,
                "browserBindingKeys": ["citryBinding0"],
            },
        ),
    )
    assert "preparedData.citryBinding0" in compiled.javascript

    underscored_opening = '<p :title="$probe_helper(preparedData.citryBinding0, () => ({name}))">'
    underscored = NativeCompiler().compile(
        underscored_opening + "initial</p>",
        type_key="BrowserBindingUnderscoredHelper",
        element_bindings=(
            {
                "sourceStart": 0,
                "sourceEnd": len(underscored_opening.encode()),
                "attrsBindingKey": None,
                "keyBindingKey": None,
                "browserBindingKeys": ["citryBinding0"],
            },
        ),
    )
    assert "$probe_helper" in underscored.javascript

    with pytest.raises(ValueError, match="browser binding does not match"):
        NativeCompiler().compile(
            '<p :title="$probe(preparedData.citryBinding0extra)">initial</p>',
            type_key="BrowserBindingMismatch",
            element_bindings=(
                {
                    "sourceStart": 0,
                    "sourceEnd": len(b'<p :title="$probe(preparedData.citryBinding0extra)">'),
                    "attrsBindingKey": None,
                    "keyBindingKey": None,
                    "browserBindingKeys": ["citryBinding0"],
                },
            ),
        )

    for invalid_expression in (
        "$probe(preparedData['citryBinding0'])",
        "$probe(other.citryBinding0)",
        "$probe(preparedData.citryBinding0, namedThunk)",
        "$probe(preparedData.citryBinding0, (...values) => values)",
        "preparedData.citryBinding0",
    ):
        opening = f'<p :title="{invalid_expression}">'
        with pytest.raises(ValueError, match="browser binding does not match"):
            NativeCompiler().compile(
                opening + "initial</p>",
                type_key="BrowserBindingAstMismatch",
                element_bindings=(
                    {
                        "sourceStart": 0,
                        "sourceEnd": len(opening.encode()),
                        "attrsBindingKey": None,
                        "keyBindingKey": None,
                        "browserBindingKeys": ["citryBinding0"],
                    },
                ),
            )
    literal_opening = "<p :title=\"$probe('preparedData.citryBinding0')\">"
    with pytest.raises(ValueError, match="browser binding does not match"):
        NativeCompiler().compile(
            literal_opening + "initial</p>",
            type_key="BrowserBindingLiteralMismatch",
            element_bindings=(
                {
                    "sourceStart": 0,
                    "sourceEnd": len(literal_opening.encode()),
                    "attrsBindingKey": None,
                    "keyBindingKey": None,
                    "browserBindingKeys": ["citryBinding0"],
                },
            ),
        )


def test_generic_browser_bindings_assemble_from_leaf_typed_fallback() -> None:
    registry = Citry()

    class Root(Component):
        citry = registry
        template = '<p c-title="title">{{ value }}</p>'

        def template_data(self, kwargs, slots):
            return {"title": "initial", "value": "initial"}

    rendered = render_prepared_direct(Root())
    leaf = rendered.parts[0]
    while isinstance(leaf, CitryRender):
        leaf = leaf.parts[0]
    assert isinstance(leaf, PreparedLeafProgram)
    parts = typed_leaf_parts(leaf)
    parts = [
        replace(
            part,
            browser_bindings=(
                prepared_browser_binding(helper="$probe", operand="attr-id", target="attribute", name="title"),
            ),
        )
        if isinstance(part, PreparedElementOpen)
        else replace(
            part,
            browser_binding=prepared_browser_binding(helper="$probe", operand="text-id", target="text"),
        )
        if isinstance(part, PreparedTextValue)
        else part
        for part in parts
    ]
    object.__setattr__(leaf, "cached_typed_parts", tuple(parts))
    assembly = assemble_typed_render(
        rendered,
        revision=0,
        tag_for_type=lambda key: "x-" + key.lower().replace("_", "-"),
        template_context_names=("$probe",),
    )
    compile_input = next(iter(assembly.compile_inputs.values()))
    assert ':title="$probe(preparedData.citryBinding' in compile_input.template
    assert "{{ $probe(preparedData.citryBinding" in compile_input.template
    compiled = NativeCompiler().compile(
        compile_input.template,
        type_key="BrowserBindingLeaf",
        element_bindings=compile_input.element_bindings,
    )
    assert "$probe" in compiled.javascript


def test_direct_render_builds_relationships_without_an_ownership_module() -> None:
    registry = Citry()

    class Child(Component):
        citry = registry
        template = "<p>child</p>"

    class Root(Component):
        citry = registry
        template = "<main><c-Child /></main>"

    rendered = render_prepared_direct(Root())
    assert not hasattr(rendered.context, "ownership")
    assert len(_view(rendered).occurrences) == 2


def test_slot_free_keyed_component_run_keeps_one_and_two_member_definition_stable() -> None:
    registry = Citry()

    class Child(Component):
        citry = registry

        class Kwargs:
            value: int

        template = "<p>{{ value }}</p>"

    class Root(Component):
        citry = registry

        class Kwargs:
            values: list[int]

        template = '<main><c-for each="value in values"><c-Child #c-key="value" c-value="value" /></c-for></main>'

        def template_data(self, kwargs, slots):
            return {"values": kwargs.values}

    assemblies = [
        assemble_typed_render(
            render_prepared_direct(Root(values=list(range(count)))),
            revision=0,
            tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
        )
        for count in (0, 1, 2)
    ]
    roots = [next(item for item in assembly.view.occurrences if item.parent_id is None) for assembly in assemblies]
    inputs = [assembly.compile_inputs[root.definition_id] for assembly, root in zip(assemblies, roots, strict=True)]
    assert len({root.definition_id for root in roots}) == 1
    assert inputs[0] == inputs[1] == inputs[2]
    assert len(inputs[0].local_call_runs) == 1
    assert [len(root.prepared_data["callRuns"]["citryRun0"]) for root in roots] == [0, 1, 2]
    assert all(root.prepared_data["calls"] == {} for root in roots)
    for assembly, root in zip(assemblies, roots, strict=True):
        children = [item.id for item in assembly.view.occurrences if item.parent_id == root.id]
        assert root.prepared_data["callRuns"]["citryRun0"] == children
    assert all(
        "callRuns" not in occurrence.prepared_data
        for assembly in assemblies
        for occurrence in assembly.view.occurrences
        if occurrence.parent_id is not None
    )
    assert "preparedData.calls[citryOccurrenceId]" not in inputs[0].template
    assert ':key="citryOccurrenceId"' in inputs[0].template
    assert '<component v-for="citryOccurrenceId in preparedData.callRuns.citryRun0"' in inputs[0].template
    with NativeCompiler() as compiler:
        compiled = compiler.compile(
            inputs[0].template,
            type_key=roots[0].type_key,
            local_calls=inputs[0].local_calls,
            element_bindings=inputs[0].element_bindings,
            local_call_runs=inputs[0].local_call_runs,
        )
    assert compiled.local_call_runs[0]["runId"] == "citryRun0"
    assert compiled.local_call_runs[0]["collectionExpression"] == "preparedData.callRuns.citryRun0"
    assert compiled.local_call_runs[0]["idExpression"] == "citryOccurrenceId"
    assert compiled.local_call_runs[0]["keyExpression"] == "citryOccurrenceId"
    assert compiled.local_calls == ()


def test_component_run_calls_custom_tag_mapper_twice_per_member_in_render_order() -> None:
    registry = Citry()

    class Child(Component):
        citry = registry
        template = "<p>child</p>"

    class Root(Component):
        citry = registry
        template = '<c-for each="value in values"><c-Child #c-key="value" /></c-for>'

        def template_data(self, kwargs, slots):
            return {"values": ["first", "second", "third"]}

    mapped_types: list[str] = []

    def tag_for_type(type_key: str) -> str:
        mapped_types.append(type_key)
        return "x-" + type_key.lower().replace("_", "-")

    assembly = assemble_typed_render(
        render_prepared_direct(Root()),
        revision=0,
        tag_for_type=tag_for_type,
    )
    root = next(item for item in assembly.view.occurrences if item.parent_id is None)
    children = [item for item in assembly.view.occurrences if item.parent_id == root.id]
    assert len(children) == 3
    assert mapped_types == [
        root.type_key,
        children[0].type_key,
        children[0].type_key,
        children[1].type_key,
        children[1].type_key,
        children[2].type_key,
        children[2].type_key,
    ]


def test_component_run_rejects_custom_tag_mapper_changing_on_second_member_check() -> None:
    registry = Citry()

    class Child(Component):
        citry = registry
        template = "<p>child</p>"

    class Root(Component):
        citry = registry
        template = '<c-for each="value in values"><c-Child #c-key="value" /></c-for>'

        def template_data(self, kwargs, slots):
            return {"values": ["only"]}

    child_calls = 0

    def tag_for_type(type_key: str) -> str:
        nonlocal child_calls
        if type_key.startswith("Child_"):
            child_calls += 1
            return f"x-child-{child_calls}"
        return "x-root"

    with pytest.raises(UnsupportedPreparedView, match="component tag mapping is not deterministic"):
        assemble_typed_render(
            render_prepared_direct(Root()),
            revision=0,
            tag_for_type=tag_for_type,
        )
    assert child_calls == 2


def test_component_run_does_not_hide_duplicate_render_object() -> None:
    registry = Citry()

    class Child(Component):
        citry = registry
        template = "<p>child</p>"

    class Root(Component):
        citry = registry
        template = "<main><c-Child #c-key=\"'one'\" /></main>"

    rendered = render_prepared_direct(Root())
    child = next(part for part in rendered.parts if type(part) is CitryRender)
    rendered.parts.append(child)
    with pytest.raises(
        UnsupportedPreparedView,
        match=r"duplicate explicit #c-key|render occurrence appears more than once",
    ):
        _view(rendered)


def test_component_run_proof_mismatch_falls_back_to_ordinary_calls() -> None:
    registry = Citry()

    class Child(Component):
        citry = registry

        class Kwargs:
            value: int

        template = "<p>{{ value }}</p>"

    class Root(Component):
        citry = registry
        template = '<c-for each="value in values"><c-Child #c-key="value" c-value="value" /></c-for>'

        def template_data(self, kwargs, slots):
            return {"values": [1, 2]}

    rendered = render_prepared_direct(Root())
    wrapper = next(part for part in rendered.parts if isinstance(part, DirectCallRunRender))
    wrapper.child_type_key = "DifferentType_000000"
    assembly = assemble_typed_render(
        rendered,
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )
    root = next(item for item in assembly.view.occurrences if item.parent_id is None)
    compiler_input = assembly.compile_inputs[root.definition_id]
    assert len(compiler_input.local_calls) == 2
    assert compiler_input.local_call_runs == ()


def test_empty_branch_and_unresolved_zero_loop_keep_general_execution_semantics() -> None:
    registry = Citry()

    class Child(Component):
        citry = registry
        template = "<p>child</p>"

    class EmptyBranch(Component):
        citry = registry
        template = '<c-for each="value in values"><c-Child #c-key="value" /></c-for><c-empty><i>empty</i></c-empty>'

        def template_data(self, kwargs, slots):
            return {"values": []}

    class Missing(Component):
        citry = registry
        template = '<c-for each="value in values"><c-NotRegistered #c-key="value" /></c-for>'

        def template_data(self, kwargs, slots):
            return {"values": []}

    empty = assemble_typed_render(
        render_prepared_direct(EmptyBranch()),
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )
    empty_root = next(item for item in empty.view.occurrences if item.parent_id is None)
    assert empty.compile_inputs[empty_root.definition_id].local_call_runs == ()
    assert "<i>empty</i>" in empty.compile_inputs[empty_root.definition_id].template
    missing = assemble_typed_render(
        render_prepared_direct(Missing()),
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )
    missing_root = next(item for item in missing.view.occurrences if item.parent_id is None)
    assert missing.compile_inputs[missing_root.definition_id].local_call_runs == ()


@pytest.mark.parametrize("values", [[], [1]])
def test_component_loop_inside_selected_fill_stays_on_general_call_path(values: list[int]) -> None:
    registry = Citry()

    class Leaf(Component):
        citry = registry

        class Kwargs:
            value: int

        template = "<b>{{ value }}</b>"

    class Receiver(Component):
        citry = registry
        template = "<article><c-slot /></article>"

    class Root(Component):
        citry = registry

        class Kwargs:
            values: list[int]

        template = (
            '<c-Receiver #c-key="\'receiver\'"><c-fill name="default">'
            '<c-for each="value in values"><c-Leaf #c-key="value" c-value="value" /></c-for>'
            "</c-fill></c-Receiver>"
        )

        def template_data(self, kwargs, slots):
            return {"values": kwargs.values}

    assembly = assemble_typed_render(
        render_prepared_direct(Root(values=values)),
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )
    assert all(not item.local_call_runs for item in assembly.compile_inputs.values())


def test_assembly_accepts_a_generated_safe_subtree_anchor() -> None:
    registry = Citry()

    class Root(Component):
        citry = registry
        template = "<p>subtree</p>"

    anchor = "citryOccurrenceParentMounted1"
    assembly = assemble_typed_render(
        render_prepared_direct(Root()),
        revision=2,
        root_occurrence_id=anchor,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )
    assert assembly.view.root_id == anchor
    assert set(assembly.render_to_occurrence.values()) == {anchor}
    assert set(assembly.compile_inputs) == {assembly.view.definitions[0].id}


def test_python_slot_without_authored_source_keeps_nested_authored_slot_relations() -> None:
    registry = Citry()

    class Receiver(Component):
        citry = registry
        template = "<article><c-slot /></article>"

        def js_data(self, kwargs, slots):
            return {"label": "receiver-value"}

    class Content(Component):
        citry = registry
        template = '<c-Receiver #c-key="\'receiver\'"><span v-text="label">initial</span></c-Receiver>'

        def js_data(self, kwargs, slots):
            return {"label": "caller-value"}

    class Host(Component):
        citry = registry
        template = "<main><c-slot /></main><aside><c-slot /></aside>"

    rendered = render_prepared_direct(Host(slots={"default": Content()}))
    # The Python-provided outer Slot has no authored fill source, while the
    # nested template body in Content does and must keep its own relation.
    assert not any(isinstance(part, DirectSlotRender) for part in rendered.parts)
    contents = [part for part in rendered.parts if isinstance(part, DirectPythonComponentRender)]
    assert len(contents) == 2
    for content in contents:
        receiver = next(
            part for part in content.parts if isinstance(part, CitryRender) and part.frame.is_component_root
        )
        nested = next(part for part in receiver.parts if isinstance(part, DirectSlotRender))
        assert nested.fill_source.lexical_render_id == content.frame.render_id

    assembly = assemble_typed_render(
        rendered,
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )
    content_occurrences = [item for item in assembly.view.occurrences if item.type_key == contents[0].frame.class_id]
    assert len(content_occurrences) == 2
    assert len({item.id for item in content_occurrences}) == 2
    content_occurrence = content_occurrences[0]
    content_template = assembly.compile_inputs[content_occurrence.definition_id].template
    assert 'v-text="label"' in content_template
    assert "caller-value" not in content_template
    assert "receiver-value" not in content_template
    occurrence_types = {item.definition_id: item.type_key for item in assembly.view.occurrences}
    for definition_id, compile_input in assembly.compile_inputs.items():
        NativeCompiler().compile(
            compile_input.template,
            type_key=occurrence_types[definition_id],
            local_calls=compile_input.local_calls,
            local_call_runs=compile_input.local_call_runs,
            element_bindings=compile_input.element_bindings,
            dynamic_elements=compile_input.dynamic_elements,
            template_context_names=compile_input.template_context_names,
        )


def test_direct_supplied_fill_and_invoked_fallback_keep_distinct_lexical_owners() -> None:
    registry = Citry()

    class Receiver(Component):
        citry = registry
        template = '<article><c-slot name="body"><i>{{ label }}</i></c-slot></article>'

        def template_data(self, kwargs, slots):
            return {"label": "receiver"}

    class Caller(Component):
        citry = registry
        template = (
            "<c-Receiver #c-key=\"'one'\">"
            '<c-fill name="body" fallback="fallback"><b>{{ label }}:{{ fallback }}</b></c-fill>'
            "</c-Receiver>"
        )

        def template_data(self, kwargs, slots):
            return {"label": "caller"}

    rendered = render_prepared_direct(Caller())
    receiver = next(part for part in rendered.parts if hasattr(part, "frame") and part.frame.is_component_root)
    outer = next(part for part in receiver.parts if isinstance(part, DirectSlotRender))
    nested = [part for part in outer.parts if isinstance(part, DirectSlotRender)]
    assert outer.fill_source.lexical_render_id == rendered.frame.render_id
    assert nested
    assert nested[0].fill_source.lexical_render_id == receiver.frame.render_id
    assembly = assemble_typed_render(
        rendered,
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
        template_context_names=("$i18n", "$probe"),
    )
    definitions = {item.id: item for item in assembly.view.definitions}
    caller = next(item for item in assembly.view.occurrences if item.type_key == rendered.frame.class_id)
    receiver_occurrence = next(item for item in assembly.view.occurrences if item.type_key == receiver.frame.class_id)
    caller_template = assembly.compile_inputs[caller.definition_id].template
    receiver_template = assembly.compile_inputs[receiver_occurrence.definition_id].template
    assert "v-slot:['citrySlot" in caller_template
    assert '="{ $i18n, $probe }"' in caller_template
    assert "preparedData.selectedSlots" in receiver_template
    assert ':$i18n="$i18n"' in receiver_template
    assert ':$probe="$probe"' in receiver_template
    assert assembly.compile_inputs[caller.definition_id].template_context_names == ("$i18n", "$probe")
    for occurrence in (caller, receiver_occurrence):
        compile_input = assembly.compile_inputs[occurrence.definition_id]
        NativeCompiler().compile(
            compile_input.template,
            type_key=occurrence.type_key,
            local_calls=compile_input.local_calls,
            element_bindings=compile_input.element_bindings,
            local_call_runs=compile_input.local_call_runs,
            dynamic_elements=compile_input.dynamic_elements,
            template_context_names=compile_input.template_context_names,
        )
    assert not hasattr(definitions[caller.definition_id], "children")


def test_direct_template_slot_rejects_use_after_session_close() -> None:
    saved = []

    class Keep(Extension):
        name = "keep"

        def on_component_input(self, ctx):
            if type(ctx.component).__name__ == "Receiver":
                saved.extend(ctx.component.raw_slots.values())

    registry = Citry(extensions=[Keep])

    class Receiver(Component):
        citry = registry
        template = "<c-slot />"

    class Caller(Component):
        citry = registry
        template = "<c-Receiver>body</c-Receiver>"

    render_prepared_direct(Caller())
    assert len(saved) == 1
    with pytest.raises(RuntimeError, match="session closed"):
        saved[0]()


def test_direct_template_slot_supports_python_callable_expression() -> None:
    registry = Citry(autodiscover=False)

    class Receiver(Component):
        citry = registry
        template = "<article>{{ content }}</article>"

        def template_data(self, kwargs, slots):
            return {"content": slots["default"]}

    class Caller(Component):
        citry = registry
        template = "<c-Receiver #c-key=\"'receiver'\"><b>content</b></c-Receiver>"

    rendered = render_prepared_direct(Caller())
    receiver = next(part for part in rendered.parts if isinstance(part, CitryRender))
    pending = list(receiver.parts)
    selected = None
    while pending:
        part = pending.pop()
        if isinstance(part, DirectSlotRender):
            selected = part
            break
        if isinstance(part, CitryRender):
            pending.extend(part.parts)
        fallback_parts = getattr(part, "fallback_parts", ())
        pending.extend(fallback_parts)
    assert selected is not None
    assert selected.receiver_render_id == receiver.frame.render_id
    assert selected.fill_source.lexical_render_id == rendered.frame.render_id

    assembly = assemble_typed_render(
        rendered,
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )
    caller = next(item for item in assembly.view.occurrences if item.type_key == Caller.class_id)
    receiver_occurrence = next(item for item in assembly.view.occurrences if item.type_key == Receiver.class_id)
    assert "v-slot:['citrySlot" in assembly.compile_inputs[caller.definition_id].template
    assert 'name="citrySlot' in assembly.compile_inputs[receiver_occurrence.definition_id].template


def test_python_component_expressions_receive_distinct_positional_calls() -> None:
    registry = Citry(autodiscover=False)

    class Child(Component):
        citry = registry
        template = "<span>{{ label }}</span>"

    class Caller(Component):
        citry = registry
        template = "<main>{{ first }}{{ second }}</main>"

        def template_data(self, kwargs, slots):
            return {
                "first": Child(label="one"),
                "second": Child(label="two"),
            }

    assembly = assemble_typed_render(
        render_prepared_direct(Caller()),
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )
    caller = next(item for item in assembly.view.occurrences if item.type_key == Caller.class_id)
    children = [item for item in assembly.view.occurrences if item.type_key == Child.class_id]
    calls = assembly.compile_inputs[caller.definition_id].local_calls
    assert len(children) == 2
    assert len(calls) == 2
    assert calls[0]["localId"] != calls[1]["localId"]


def test_simple_dynamic_element_keeps_typed_boundaries_in_python_expression() -> None:
    registry = Citry(autodiscover=False)

    class Label(Component):
        citry = registry
        simple = True
        template = '<c-element c-is="tag" c-bind="attrs">{{ text }}</c-element>'

    class Caller(Component):
        citry = registry
        template = "<main>{{ label }}</main>"

        def template_data(self, kwargs, slots):
            return {"label": Label(tag="span", attrs={"title": "typed"}, text="value")}

    rendered = render_prepared_direct(Caller())
    assembly = assemble_typed_render(
        rendered,
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )
    caller = next(item for item in assembly.view.occurrences if item.type_key == Caller.class_id)
    compile_input = assembly.compile_inputs[caller.definition_id]
    assert compile_input.dynamic_elements
    assert "citry-dynamic-" in compile_input.template


def test_direct_template_slot_callable_may_render_none_without_raw_markup() -> None:
    registry = Citry(autodiscover=False)

    class Receiver(Component):
        citry = registry
        template = "<article>{{ content }}</article>"

        def template_data(self, kwargs, slots):
            return {"content": slots["default"]}

    class Caller(Component):
        citry = registry
        template = "<c-Receiver #c-key=\"'receiver'\">{{ nothing }}</c-Receiver>"

        def template_data(self, kwargs, slots):
            return {"nothing": None}

    assembly = assemble_typed_render(
        render_prepared_direct(Caller()),
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )
    assert len(assembly.view.occurrences) == 2


def test_direct_template_slot_supports_python_call_during_template_data() -> None:
    registry = Citry(autodiscover=False)

    class Receiver(Component):
        citry = registry
        template = "<article>{{ content }}</article>"

        def template_data(self, kwargs, slots):
            return {"content": slots["default"]({"label": "ready"})}

    class Caller(Component):
        citry = registry
        template = (
            "<c-Receiver #c-key=\"'receiver'\">"
            '<c-fill name="default" data="d"><b>{{ d.label }}</b></c-fill>'
            "</c-Receiver>"
        )

    rendered = render_prepared_direct(Caller())
    assembly = assemble_typed_render(
        rendered,
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )
    caller = next(item for item in assembly.view.occurrences if item.type_key == Caller.class_id)
    receiver = next(item for item in assembly.view.occurrences if item.type_key == Receiver.class_id)
    assert "v-slot:['citrySlot" in assembly.compile_inputs[caller.definition_id].template
    assert "<b>" in assembly.compile_inputs[caller.definition_id].template
    assert 'name="citrySlot' in assembly.compile_inputs[receiver.definition_id].template


def test_direct_callable_slot_maps_transparent_receiver_to_physical_owner() -> None:
    registry = Citry(autodiscover=False)

    class TransparentReceiver(Component):
        citry = registry
        transparent = True
        template = "<article>{{ content }}</article>"

        def template_data(self, kwargs, slots):
            return {"content": slots["default"]({})}

    class Caller(Component):
        citry = registry
        template = "<c-TransparentReceiver><b>content</b></c-TransparentReceiver>"

    assembly = assemble_typed_render(
        render_prepared_direct(Caller()),
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )
    assert len(assembly.view.occurrences) == 1
    root = assembly.view.occurrences[0]
    assert "<b>content</b>" in assembly.compile_inputs[root.definition_id].template


def test_flattened_projection_namespaces_lexical_text_after_physical_key() -> None:
    registry = Citry(autodiscover=False)

    class Physical(Component):
        citry = registry
        name = "physical"
        template = "<section>{{ own }}<c-slot /></section>"

        def template_data(self, kwargs, slots):
            return {"own": "physical"}

    class Transparent(Component):
        citry = registry
        name = "transparent"
        transparent = True
        template = "<c-Physical><c-slot /></c-Physical>"

    class Root(Component):
        citry = registry
        template = "<c-Transparent><b>{{ lexical }}</b></c-Transparent>"

        def template_data(self, kwargs, slots):
            return {"lexical": "lexical"}

    assembly = assemble_typed_render(
        render_prepared_direct(Root()),
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )
    physical = next(item for item in assembly.view.occurrences if item.type_key == Physical.class_id)
    root = next(item for item in assembly.view.occurrences if item.type_key == Root.class_id)
    projected_keys = [key for key in physical.prepared_data if key.startswith("citryTextp")]

    assert physical.prepared_data["citryText0"] == "physical"
    assert len(projected_keys) == 1
    assert physical.prepared_data[projected_keys[0]] == "lexical"
    assert root.prepared_data[projected_keys[0]] == "lexical"
    assert f"preparedData.{projected_keys[0]}" in assembly.compile_inputs[root.definition_id].template


def test_component_call_preserves_native_vue_props_events_and_refs() -> None:
    registry = Citry(autodiscover=False)

    class Child(Component):
        citry = registry
        template = "<button>child</button>"

    class Parent(Component):
        citry = registry
        template = '<c-Child :disabled="blocked" @change="changed($event)" ref="childRoot" #c-key="\'child\'" />'

    assembly = assemble_typed_render(
        render_prepared_direct(Parent()),
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )
    parent = next(item for item in assembly.view.occurrences if item.type_key == Parent.class_id)
    compile_input = assembly.compile_inputs[parent.definition_id]
    assert ':disabled="blocked"' in compile_input.template
    assert '@change="changed($event)"' in compile_input.template
    assert 'ref="childRoot"' in compile_input.template
    assert [item["kind"] for item in compile_input.local_calls[0]["bindings"]] == [
        "prop",
        "event",
        "ref-static",
    ]
    with NativeCompiler() as compiler:
        compiled = compiler.compile(
            compile_input.template,
            type_key=Parent.class_id,
            local_calls=compile_input.local_calls,
            element_bindings=compile_input.element_bindings,
            local_call_runs=compile_input.local_call_runs,
        )
    assert compiled.local_calls[0]["bindings"] == compile_input.local_calls[0]["bindings"]
    assert 'ref: "childRoot"' in compiled.javascript
    assert "changed($event)" in compiled.javascript


def test_component_call_binding_metadata_uses_utf8_spans_and_rejects_fabrication() -> None:
    registry = Citry(autodiscover=False)

    class Child(Component):
        citry = registry
        template = "child"

    class Parent(Component):
        citry = registry
        template = '<p>ž</p><c-Child v-bind="childProps" :ref="setChild" #c-key="\'child\'" />'

    assembly = assemble_typed_render(
        render_prepared_direct(Parent()),
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )
    parent = next(item for item in assembly.view.occurrences if item.type_key == Parent.class_id)
    compile_input = assembly.compile_inputs[parent.definition_id]
    call = compile_input.local_calls[0]
    assert [item["kind"] for item in call["bindings"]] == ["props-object", "ref-expression"]
    encoded = compile_input.template.encode()
    for binding in call["bindings"]:
        assert encoded[binding["sourceStart"] : binding["sourceEnd"]].decode().startswith(binding["name"])

    fabricated_call = {**call, "bindings": [{**call["bindings"][0], "value": "other"}, call["bindings"][1]]}
    with NativeCompiler() as compiler, pytest.raises(ValueError, match="mismatched local calls"):
        compiler.compile(
            compile_input.template,
            type_key=Parent.class_id,
            local_calls=(fabricated_call,),
            element_bindings=compile_input.element_bindings,
            local_call_runs=compile_input.local_call_runs,
        )


def test_component_call_rejects_a_hook_fabricated_binding_with_identical_source() -> None:
    class ReplaceBinding(Extension):
        name = "replace_binding"

        def on_component_input(self, ctx):
            if ctx.component._component_tag_client_bindings:
                ctx.component._component_tag_client_bindings = tuple(
                    replace(binding) for binding in ctx.component._component_tag_client_bindings
                )

    registry = Citry(autodiscover=False, extensions=[ReplaceBinding])

    class Child(Component):
        citry = registry
        template = "child"

    class Parent(Component):
        citry = registry
        template = '<c-Child :disabled="blocked" />'

    rendered = render_prepared_direct(Parent())
    with pytest.raises(UnsupportedPreparedView, match="authenticated authored parser record"):
        assemble_typed_render(
            rendered,
            revision=0,
            tag_for_type=lambda key: "x-" + key.lower().replace("_", "-"),
        )


def test_component_call_rejects_publicly_fabricated_binding_metadata() -> None:
    registry = Citry(autodiscover=False)

    class Child(Component):
        citry = registry
        template = "child"

    class Parent(Component):
        citry = registry
        template = "{{ child }}"

        def template_data(self, kwargs, slots):
            return {
                "child": CitryElement(
                    Child,
                    {},
                    component_tag_client_bindings=(
                        ComponentTagClientBinding(
                            ComponentTagClientBindingKind.PROP,
                            ":disabled",
                            "blocked",
                            ':disabled="blocked"',
                            (0, 19),
                        ),
                    ),
                )
            }

    with pytest.raises(UnsupportedPreparedView):
        assemble_typed_render(
            render_prepared_direct(Parent()),
            revision=0,
            tag_for_type=lambda key: "x-" + key.lower().replace("_", "-"),
        )


def test_component_call_accepts_single_quoted_spaced_unicode_binding_source() -> None:
    registry = Citry(autodiscover=False)

    class Child(Component):
        citry = registry
        template = "child"

    class Parent(Component):
        citry = registry
        template = "<p>ž</p><c-Child :disabled = 'blocked' />"

    assembly = assemble_typed_render(
        render_prepared_direct(Parent()),
        revision=0,
        tag_for_type=lambda key: "x-" + key.lower().replace("_", "-"),
    )
    parent = next(item for item in assembly.view.occurrences if item.type_key == Parent.class_id)
    assert ':disabled="blocked"' in assembly.compile_inputs[parent.definition_id].template


@pytest.mark.parametrize(
    ("template", "data"),
    [
        ('<c-Child c-bind="bindings" />', {"bindings": {":disabled": "blocked"}}),
        ('<c-Child c-:disabled="binding" />', {"binding": "blocked"}),
        ('<c-Child :disabled="{{ binding }}" />', {"binding": "blocked"}),
    ],
)
def test_component_call_rejects_executable_bindings_from_runtime_data(template, data) -> None:
    registry = Citry(autodiscover=False)

    class Child(Component):
        citry = registry
        template = "child"

    class Parent(Component):
        citry = registry

        def template_data(self, kwargs, slots):
            return data

    Parent.template = template

    with pytest.raises(RuntimeError, match=r"must be authored directly|cannot use template interpolation"):
        render_prepared_direct(Parent())


def test_component_call_emits_citry_identity_after_authored_vue_bindings() -> None:
    registry = Citry(autodiscover=False)

    class Child(Component):
        citry = registry
        template = "child"

    class Parent(Component):
        citry = registry
        template = '<c-Child v-bind="props" #c-key="\'child\'" />'

    assembly = assemble_typed_render(
        render_prepared_direct(Parent()),
        revision=0,
        tag_for_type=lambda key: "x-" + key.lower().replace("_", "-"),
    )
    parent = next(item for item in assembly.view.occurrences if item.type_key == Parent.class_id)
    compile_input = assembly.compile_inputs[parent.definition_id]
    source = compile_input.template
    assert source.index('v-bind="props"') < source.index(":citry-id=") < source.index(":key=")
    with NativeCompiler() as compiler:
        compiled = compiler.compile(
            source,
            type_key=Parent.class_id,
            local_calls=compile_input.local_calls,
            element_bindings=compile_input.element_bindings,
            local_call_runs=compile_input.local_call_runs,
        )
    merge_start = "_mergeProps(_ctx.props, {"
    assert merge_start in compiled.javascript
    assert compiled.javascript.index(merge_start) < compiled.javascript.index('"citry-id":')


def test_component_boundary_citry_event_compiles_to_vue_dispatch_metadata() -> None:
    registry = Citry(secret="component-event", autodiscover=False)  # noqa: S106
    registry.set_mounted_prefix("/citry")

    class Child(Component):
        citry = registry
        template = "child"

    class Parent(Component):
        citry = registry

        class SaveArgs:
            text: str

        template = """<c-Child @c-change.prevent='save({text: "hello"})' />"""

        class Events:
            def save(self, data: Parent.SaveArgs):
                return Parent()

    dispatcher_for(registry)
    assembly = assemble_typed_render(
        render_prepared_direct(Parent()),
        revision=0,
        tag_for_type=lambda key: "x-" + key.lower().replace("_", "-"),
    )
    parent = next(item for item in assembly.view.occurrences if item.type_key == Parent.class_id)
    compile_input = assembly.compile_inputs[parent.definition_id]
    assert "v-on:change.prevent" in compile_input.template
    assert "$citryEvents.dispatchComponent" in compile_input.template
    assert "{text: &quot;hello&quot;}" in compile_input.template
    assert [item["kind"] for item in compile_input.local_calls[0]["bindings"]] == ["event"]
    bindings = parent.prepared_data["eventBindings"]
    assert len(bindings) == 1
    assert next(iter(bindings.values()))["handler"] == "save"
    with NativeCompiler() as compiler:
        compiled = compiler.compile(
            compile_input.template,
            type_key=Parent.class_id,
            local_calls=compile_input.local_calls,
            element_bindings=compile_input.element_bindings,
            local_call_runs=compile_input.local_call_runs,
            dynamic_elements=compile_input.dynamic_elements,
        )
    assert "$citryEvents.dispatchComponent" in compiled.javascript
    assert '"hello"' in compiled.javascript


def test_direct_dom_event_preserves_double_quotes_in_authored_args() -> None:
    registry = Citry(secret="direct-dom-event-quotes", autodiscover=False)  # noqa: S106

    class Child(Component):
        citry = registry
        template = "child"

    class Parent(Component):
        citry = registry

        class SaveArgs:
            text: str

        class Events:
            def save(self, data: Parent.SaveArgs):
                return None

        template = """<button @c-click='save({text: "hello"})'>save</button><c-Child />"""

    dispatcher_for(registry)
    assembly = assemble_typed_render(
        render_prepared_direct(Parent()),
        revision=0,
        tag_for_type=lambda key: "x-" + key.lower().replace("_", "-"),
    )
    parent = next(item for item in assembly.view.occurrences if item.type_key == Parent.class_id)
    compile_input = assembly.compile_inputs[parent.definition_id]
    assert "{text: &quot;hello&quot;}" in compile_input.template
    assert "$citryEvents.dispatchComponent" not in compile_input.template
    assert "$citryEvents.dispatch(" in compile_input.template
    with NativeCompiler() as compiler:
        compiled = compiler.compile(
            compile_input.template,
            type_key=Parent.class_id,
            local_calls=compile_input.local_calls,
            element_bindings=compile_input.element_bindings,
            local_call_runs=compile_input.local_call_runs,
            dynamic_elements=compile_input.dynamic_elements,
        )
    assert '"hello"' in compiled.javascript


def test_timed_component_boundary_citry_event_is_explicitly_unsupported() -> None:
    registry = Citry(secret="component-event-timing", autodiscover=False)  # noqa: S106

    class Child(Component):
        citry = registry
        template = "child"

    class Parent(Component):
        citry = registry
        template = '<c-Child @c-change.debounce.25ms="save" />'

        class Events:
            def save(self):
                return None

    dispatcher_for(registry)
    with pytest.raises(UnsupportedPreparedView, match="timed component-boundary Events bindings are unsupported"):
        assemble_typed_render(
            render_prepared_direct(Parent()),
            revision=0,
            tag_for_type=lambda key: "x-" + key.lower().replace("_", "-"),
        )


def test_polling_component_boundary_citry_event_is_explicitly_unsupported() -> None:
    registry = Citry(secret="component-event-polling", autodiscover=False)  # noqa: S106

    class Child(Component):
        citry = registry
        template = "child"

    class Parent(Component):
        citry = registry
        template = '<c-Child @c-poll.5s="refresh" />'

        class Events:
            def refresh(self):
                return None

    dispatcher_for(registry)
    with pytest.raises(UnsupportedPreparedView, match="component-boundary polling is unsupported"):
        assemble_typed_render(
            render_prepared_direct(Parent()),
            revision=0,
            tag_for_type=lambda key: "x-" + key.lower().replace("_", "-"),
        )


def test_empty_component_loop_with_vue_binding_stays_on_general_path() -> None:
    registry = Citry(autodiscover=False)

    class Child(Component):
        citry = registry
        template = "child"

    class Parent(Component):
        citry = registry
        template = '<c-Child c-for="item in items" :disabled="blocked" #c-key="item" />'

        def template_data(self, kwargs, slots):
            return {"items": [], "blocked": True}

    rendered = render_prepared_direct(Parent())
    assert not any(isinstance(part, DirectCallRunRender) for part in rendered.parts)


def test_empty_component_loop_with_c_bind_stays_on_general_path() -> None:
    registry = Citry(autodiscover=False)

    class Child(Component):
        citry = registry
        template = "child"

    class Parent(Component):
        citry = registry
        template = '<c-Child c-for="item in items" c-bind="bindings" #c-key="item" />'

        def template_data(self, kwargs, slots):
            return {"items": [], "bindings": {"value": 1}}

    rendered = render_prepared_direct(Parent())
    assert not any(isinstance(part, DirectCallRunRender) for part in rendered.parts)


@pytest.mark.parametrize("tag", ["section", "textarea", "title", "my-widget"])
def test_dynamic_element_uses_definition_scoped_native_alias(tag: str) -> None:
    registry = Citry(autodiscover=False)

    class App(Component):
        citry = registry
        template = '<c-element c-is="tag" class="probe">hello</c-element>'

        def template_data(self, kwargs, slots):
            return {"tag": tag}

    assembly = assemble_typed_render(
        render_prepared_direct(App()),
        revision=0,
        tag_for_type=lambda key: "x-" + key.lower().replace("_", "-"),
    )
    occurrence = assembly.view.occurrences[0]
    compile_input = assembly.compile_inputs[occurrence.definition_id]
    assert len(compile_input.dynamic_elements) == 1
    declaration = compile_input.dynamic_elements[0]
    assert declaration["tag"] == tag
    assert declaration["alias"] in compile_input.template
    with NativeCompiler() as compiler:
        compiled = compiler.compile(
            compile_input.template,
            type_key=App.class_id,
            local_calls=compile_input.local_calls,
            element_bindings=compile_input.element_bindings,
            local_call_runs=compile_input.local_call_runs,
            dynamic_elements=compile_input.dynamic_elements,
        )
    assert compiled.dynamic_elements == compile_input.dynamic_elements
    assert "resolveComponent" not in compiled.javascript


def test_dynamic_element_attrs_stay_in_occurrence_data_and_forged_parts_reject() -> None:
    registry = Citry(autodiscover=False)

    class App(Component):
        citry = registry
        template = '<c-element c-is="tag" c-title="title">x</c-element>'

        def template_data(self, kwargs, slots):
            return {"tag": "section", "title": kwargs["title"]}

    def compile_value(title: str):
        assembly = assemble_typed_render(
            render_prepared_direct(App(title=title)),
            revision=0,
            tag_for_type=lambda key: "x-" + key.lower().replace("_", "-"),
        )
        occurrence = assembly.view.occurrences[0]
        return assembly, assembly.compile_inputs[occurrence.definition_id]

    first_assembly, first = compile_value("first")
    second_assembly, second = compile_value("second")
    assert first.template == second.template
    assert "first" not in first.template
    assert "second" not in second.template
    assert first_assembly.view.occurrences[0].prepared_data["citryAttrs0"] == {"title": "first"}
    assert second_assembly.view.occurrences[0].prepared_data["citryAttrs0"] == {"title": "second"}

    rendered = render_prepared_direct(App(title="safe"))
    pending = [rendered]
    replaced = False
    while pending and not replaced:
        current = pending.pop()
        for index, part in enumerate(current.parts):
            if isinstance(part, PreparedDynamicElementOpen):
                with pytest.raises(TypeError):
                    part.attrs["v-html"] = "bad"
                current.parts[index] = PreparedDynamicElementOpen(tag="input", attrs={"title": "bad"}, is_void=False)
                replaced = True
                break
            if isinstance(part, CitryRender):
                pending.append(part)
    assert replaced
    with pytest.raises(UnsupportedPreparedView, match="producer provenance"):
        assemble_typed_render(
            rendered,
            revision=0,
            tag_for_type=lambda key: "x-" + key.lower().replace("_", "-"),
        )


def test_dynamic_element_void_and_nested_same_tag_keep_exact_alias_structure() -> None:
    registry = Citry(autodiscover=False)

    class App(Component):
        citry = registry
        template = '<c-element c-is="outer"><c-element c-is="inner">x</c-element></c-element><c-element c-is="void" />'

        def template_data(self, kwargs, slots):
            return {"outer": "section", "inner": "section", "void": "input"}

    assembly = assemble_typed_render(
        render_prepared_direct(App()), revision=0, tag_for_type=lambda key: "x-" + key.lower().replace("_", "-")
    )
    occurrence = assembly.view.occurrences[0]
    compile_input = assembly.compile_inputs[occurrence.definition_id]
    aliases = [item["alias"] for item in compile_input.dynamic_elements]
    assert len(aliases) == len(set(aliases)) == 3
    assert compile_input.template.index(f"</{aliases[1]}>") < compile_input.template.index(f"</{aliases[0]}>")
    assert f"</{aliases[2]}>" in compile_input.template
    assert f'<{aliases[2]} v-bind="preparedData.' in compile_input.template


def test_dynamic_element_rejects_tag_dependent_vue_directives() -> None:
    registry = Citry(autodiscover=False)

    class App(Component):
        citry = registry
        template = '<c-element c-is="tag" v-model="value" />'

        def template_data(self, kwargs, slots):
            return {"tag": "input"}

    with pytest.raises(TypeError, match="tag-dependent or executable"):
        render_prepared_direct(App())


def test_dynamic_element_uses_evaluated_key_as_occurrence_data() -> None:
    registry = Citry(autodiscover=False)

    class App(Component):
        citry = registry
        template = '<c-element c-is="tag" #c-key="key">x</c-element>'

        def template_data(self, kwargs, slots):
            return {"tag": "section", "key": kwargs["key"]}

    assembly = assemble_typed_render(
        render_prepared_direct(App(key="row")),
        revision=0,
        tag_for_type=lambda key: "x-" + key.lower().replace("_", "-"),
    )
    occurrence = assembly.view.occurrences[0]
    compile_input = assembly.compile_inputs[occurrence.definition_id]
    assert occurrence.prepared_data["citryKey0"] == "row"
    assert occurrence.prepared_data["citryAttrs0"] == {}
    assert ':key="preparedData.citryKey0"' in compile_input.template
    assert compile_input.element_bindings[0]["keyBindingKey"] == "citryKey0"

    class Conflict(Component):
        citry = registry
        template = '<c-element c-is="tag" :key="browserKey" #c-key="key" />'

        def template_data(self, kwargs, slots):
            return {"tag": "section", "key": "server"}

        def js_data(self, kwargs, slots):
            return {"browserKey": "browser"}

    with pytest.raises(UnsupportedPreparedView, match="#c-key conflicts"):
        assemble_typed_render(
            render_prepared_direct(Conflict()),
            revision=0,
            tag_for_type=lambda key: "x-" + key.lower().replace("_", "-"),
        )


def test_dynamic_element_still_rejects_c_ignore() -> None:
    registry = Citry(autodiscover=False)

    class App(Component):
        citry = registry
        template = '<c-element c-is="tag" #c-ignore>x</c-element>'

        def template_data(self, kwargs, slots):
            return {"tag": "section"}

    with pytest.raises(TypeError, match="#c-ignore"):
        render_prepared_direct(App())


def test_dynamic_element_preserves_authored_event_and_property_source() -> None:
    registry = Citry(autodiscover=False)

    class App(Component):
        citry = registry
        template = '<c-element c-is="tag" @click.stop="count += 1" :title="label" c-class="klass">x</c-element>'

        def template_data(self, kwargs, slots):
            return {"tag": "section", "klass": "data"}

        def js_data(self, kwargs, slots):
            return {"count": 0, "label": "hello"}

    assembly = assemble_typed_render(
        render_prepared_direct(App()),
        revision=0,
        tag_for_type=lambda key: "x-" + key.lower().replace("_", "-"),
    )
    occurrence = assembly.view.occurrences[0]
    compile_input = assembly.compile_inputs[occurrence.definition_id]
    assert '@click.stop="count += 1"' in compile_input.template
    assert ':title="label"' in compile_input.template
    assert occurrence.prepared_data["citryAttrs0"] == {"class": "data"}
    with NativeCompiler() as compiler:
        compiled = compiler.compile(
            compile_input.template,
            type_key=App.class_id,
            local_calls=compile_input.local_calls,
            element_bindings=compile_input.element_bindings,
            local_call_runs=compile_input.local_call_runs,
            dynamic_elements=compile_input.dynamic_elements,
        )
    assert "count += 1" in compiled.javascript


@pytest.mark.parametrize("binding", ['v-bind="attrs"', ':[name]="value"'])
def test_evaluated_key_conflicts_with_unbounded_vue_attribute_targets(binding: str) -> None:
    registry = Citry(autodiscover=False)

    class Ordinary(Component):
        citry = registry
        template = f'<div #c-key="key" {binding}></div>'

        def template_data(self, kwargs, slots):
            return {"key": "row"}

        def js_data(self, kwargs, slots):
            return {"attrs": {}, "name": "title", "value": "browser"}

    class Dynamic(Component):
        citry = registry
        template = f'<c-element c-is="tag" #c-key="key" {binding}></c-element>'

        def template_data(self, kwargs, slots):
            return {"tag": "div", "key": "row"}

        def js_data(self, kwargs, slots):
            return {"attrs": {}, "name": "title", "value": "browser"}

    expected = "object v-bind" if binding.startswith("v-bind=") else "dynamic-argument"
    for component in (Ordinary(), Dynamic()):
        with pytest.raises(UnsupportedPreparedView, match=expected):
            assemble_typed_render(
                render_prepared_direct(component),
                revision=0,
                tag_for_type=lambda key: "x-" + key.lower().replace("_", "-"),
            )


def test_ordinary_object_binding_without_a_prepared_key_remains_supported() -> None:
    registry = Citry(autodiscover=False)

    class App(Component):
        citry = registry
        template = '<main><div v-bind="attrs"></div></main>'

        def js_data(self, kwargs, slots):
            return {"attrs": {"title": "browser"}}

    assembly = assemble_typed_render(
        render_prepared_direct(App()),
        revision=0,
        tag_for_type=lambda key: "x-" + key.lower().replace("_", "-"),
    )
    occurrence = assembly.view.occurrences[0]
    assert 'v-bind="attrs"' in assembly.compile_inputs[occurrence.definition_id].template


def test_dynamic_element_rejects_source_data_target_collision_and_executable_spread() -> None:
    registry = Citry(autodiscover=False)

    class Collision(Component):
        citry = registry
        template = '<c-element c-is="tag" :title="label" c-title="title" />'

        def template_data(self, kwargs, slots):
            return {"tag": "section", "title": "server"}

        def js_data(self, kwargs, slots):
            return {"label": "browser"}

    with pytest.raises(UnsupportedPreparedView, match="target the same HTML name"):
        assemble_typed_render(
            render_prepared_direct(Collision()),
            revision=0,
            tag_for_type=lambda key: "x-" + key.lower().replace("_", "-"),
        )

    class Forged(Component):
        citry = registry
        template = '<c-element c-is="tag" c-bind="attrs" />'

        def template_data(self, kwargs, slots):
            return {"tag": "section", "attrs": {"@click": "attack()"}}

    with pytest.raises(RuntimeError, match="must be authored directly"):
        render_prepared_direct(Forged())


def test_dynamic_element_authored_bindings_keep_supplied_slot_lexical_owner() -> None:
    registry = Citry(autodiscover=False)

    class Receiver(Component):
        citry = registry
        template = "<section><c-slot /></section>"

        def js_data(self, kwargs, slots):
            return {"label": "receiver"}

    class Caller(Component):
        citry = registry
        template = (
            '<c-Receiver><c-element c-is="\'button\'" :title="label" @click="label += \'!\'">'
            "go"
            "</c-element></c-Receiver>"
        )

        def js_data(self, kwargs, slots):
            return {"label": "caller"}

    assembly = assemble_typed_render(
        render_prepared_direct(Caller()),
        revision=0,
        tag_for_type=lambda key: "x-" + key.lower().replace("_", "-"),
    )
    caller = next(item for item in assembly.view.occurrences if item.type_key == Caller.class_id)
    receiver = next(item for item in assembly.view.occurrences if item.type_key == Receiver.class_id)
    assert len(assembly.view.occurrences) == 2
    caller_template = assembly.compile_inputs[caller.definition_id].template
    receiver_template = assembly.compile_inputs[receiver.definition_id].template
    assert ':title="label"' in caller_template
    assert "@click=\"label += '!'\"" in caller_template
    assert "go" in caller_template
    assert ':title="label"' not in receiver_template
    caller_selections = caller.prepared_data.get("selectedSlots", {})
    nested_selection_keys = [key for key in caller_selections if key in caller_template]
    assert nested_selection_keys == []


def test_dynamic_element_preserves_only_authored_bindings_unchanged_by_hooks() -> None:
    class Remove(Extension):
        name = "remove_dynamic_vue"

        def on_attrs_resolved(self, ctx):
            ctx.attrs.pop("@click", None)

    remove_registry = Citry(autodiscover=False, extensions=[Remove])

    class Removed(Component):
        citry = remove_registry
        template = '<c-element c-is="tag" @click="save()" :title="label" />'

        def template_data(self, kwargs, slots):
            return {"tag": "section"}

        def js_data(self, kwargs, slots):
            return {"label": "safe"}

    removed_assembly = assemble_typed_render(
        render_prepared_direct(Removed()),
        revision=0,
        tag_for_type=lambda key: "x-" + key.lower().replace("_", "-"),
    )
    removed = removed_assembly.view.occurrences[0]
    removed_template = removed_assembly.compile_inputs[removed.definition_id].template
    assert "@click" not in removed_template
    assert ':title="label"' in removed_template

    class Rewrite(Extension):
        name = "rewrite_dynamic_vue"

        def on_attrs_resolved(self, ctx):
            ctx.attrs.pop("@click", None)
            ctx.attrs[":title"] = "attacker()"

    registry = Citry(autodiscover=False, extensions=[Rewrite])

    class App(Component):
        citry = registry
        template = '<c-element c-is="tag" @click="save()" :title="label" />'

        def template_data(self, kwargs, slots):
            return {"tag": "section"}

        def js_data(self, kwargs, slots):
            return {"label": "safe"}

    with pytest.raises(TypeError, match=r"tag-dependent or executable.*:title"):
        render_prepared_direct(App())


def test_prepared_hook_attributes_keep_json_boolean_semantics() -> None:
    class Rewrite(Extension):
        name = "rewrite_boolean_attrs"

        def on_attrs_resolved(self, ctx):
            attrs = dict(ctx.attrs)
            attrs.update({"data-true": True, "data-false": False, "data-none": None})
            return attrs

    registry = Citry(autodiscover=False, extensions=[Rewrite])

    class App(Component):
        citry = registry
        template = '<div hidden c-bind="attrs">ok</div>'

        def template_data(self, kwargs, slots):
            return {"attrs": {"data-value": "kept"}}

    assembly = assemble_typed_render(
        render_prepared_direct(App()),
        revision=0,
        tag_for_type=lambda key: "x-" + key.lower().replace("_", "-"),
    )
    occurrence = assembly.view.occurrences[0]
    attr_values = next(
        value
        for value in occurrence.prepared_data.values()
        if type(value) is dict and value.get("data-value") == "kept"
    )

    assert attr_values == {"data-value": "kept", "data-true": True}
    assert " hidden" in assembly.compile_inputs[occurrence.definition_id].template


def test_prepared_root_markers_project_to_multi_roots_and_child_physical_roots() -> None:
    class MarkParent(Extension):
        name = "mark_parent"

        def on_component_data(self, ctx):
            if type(ctx.component).__name__ == "Parent":
                ctx.context._add_root_markers(['data-probe="own"', "data-flag"])

    registry = Citry(autodiscover=False, extensions=[MarkParent])

    class Child(Component):
        citry = registry
        template = '<main id="child-root"></main><aside id="child-second"><span></span></aside>'

    class Parent(Component):
        citry = registry
        template = "<c-Child />"

    assembly = assemble_typed_render(
        render_prepared_direct(Parent()),
        revision=0,
        tag_for_type=lambda key: "x-" + key.lower().replace("_", "-"),
    )
    child = next(item for item in assembly.view.occurrences if item.type_key == Child.class_id)
    marker_values = [
        value for key, value in child.prepared_data.items() if key.startswith("citryAttrs") and "data-probe" in value
    ]
    assert marker_values == [{"data-probe": "own", "data-flag": ""}]
    child_template = assembly.compile_inputs[child.definition_id].template
    assert child_template.count('v-bind="preparedData.citryAttrs') == 2
    child_input = assembly.compile_inputs[child.definition_id]
    with NativeCompiler() as compiler:
        compiled = compiler.compile(
            child_input.template,
            type_key=Child.class_id,
            local_calls=child_input.local_calls,
            element_bindings=child_input.element_bindings,
            local_call_runs=child_input.local_call_runs,
            dynamic_elements=child_input.dynamic_elements,
        )
    assert compiled.javascript.count("preparedData.citryAttrs") >= 2


def test_prepared_root_markers_follow_static_depth_across_typed_descendants() -> None:
    class MarkParent(Extension):
        name = "mark_parent"

        def on_component_data(self, ctx):
            if type(ctx.component).__name__ == "Parent":
                ctx.context._add_root_markers(['data-probe="root"'])

    registry = Citry(autodiscover=False, extensions=[MarkParent])

    class Child(Component):
        citry = registry
        template = "<p>child</p>"

    class Parent(Component):
        citry = registry
        template = (
            '<div title="a &lt; b"><c-Child #c-key="\'nested\'" />'
            '<c-element c-is="tag">nested dynamic</c-element></div>'
            "<c-Child #c-key=\"'sibling'\" />"
        )

        def template_data(self, kwargs, slots):
            return {"tag": "section"}

    assembly = assemble_typed_render(
        render_prepared_direct(Parent()),
        revision=0,
        tag_for_type=lambda key: "x-" + key.lower().replace("_", "-"),
    )
    children = [item for item in assembly.view.occurrences if item.type_key == Child.class_id]
    assert len(children) == 2
    marked = [
        item
        for item in children
        if any(type(value) is dict and value.get("data-probe") == "root" for value in item.prepared_data.values())
    ]
    assert len(marked) == 1
    parent = next(item for item in assembly.view.occurrences if item.type_key == Parent.class_id)
    template = assembly.compile_inputs[parent.definition_id].template
    assert template.count('v-bind="preparedData.citryAttrs') == 2
    marker_maps = [
        value for value in parent.prepared_data.values() if type(value) is dict and value.get("data-probe") == "root"
    ]
    assert marker_maps == [{"data-probe": "root"}]


def test_prepared_root_markers_follow_a_root_slot_to_its_physical_fill() -> None:
    class MarkParent(Extension):
        name = "mark_slot_parent"

        def on_component_data(self, ctx):
            if type(ctx.component).__name__ == "Parent":
                ctx.context._add_root_markers(['data-slot-probe="yes"'])

    registry = Citry(autodiscover=False, extensions=[MarkParent])

    class Receiver(Component):
        citry = registry
        template = "<c-slot />"

    class Parent(Component):
        citry = registry
        template = '<c-Receiver><main id="fill-root">fill</main></c-Receiver>'

    assembly = assemble_typed_render(
        render_prepared_direct(Parent()),
        revision=0,
        tag_for_type=lambda key: "x-" + key.lower().replace("_", "-"),
    )
    parent = next(item for item in assembly.view.occurrences if item.type_key == Parent.class_id)
    assert any(
        value == {"data-slot-probe": "yes"}
        for key, value in parent.prepared_data.items()
        if key.startswith("citryAttrs")
    )
    assert "data-slot-probe" not in assembly.compile_inputs[parent.definition_id].template
    assert 'v-bind="preparedData.citryAttrs' in assembly.compile_inputs[parent.definition_id].template


@pytest.mark.parametrize("marker", ["key", 'ref="root"', ':data-probe="value"'])
def test_prepared_root_markers_reject_non_data_attribute_channels(marker: str) -> None:
    class InvalidMarker(Extension):
        name = "invalid_marker"

        def on_component_data(self, ctx):
            ctx.context._add_root_markers([marker])

    registry = Citry(autodiscover=False, extensions=[InvalidMarker])

    class Root(Component):
        citry = registry
        template = "<div>root</div>"

    with pytest.raises(UnsupportedPreparedView, match=r"root marker.*unsafe"):
        assemble_typed_render(
            render_prepared_direct(Root()),
            revision=0,
            tag_for_type=lambda key: "x-" + key.lower().replace("_", "-"),
        )


def test_prepared_root_marker_rejects_authored_attribute_collision() -> None:
    class Marker(Extension):
        name = "marker"

        def on_component_data(self, ctx):
            ctx.context._add_root_markers(['DATA-PROBE="extension"'])

    registry = Citry(autodiscover=False, extensions=[Marker])

    class Root(Component):
        citry = registry
        template = '<div data-probe="authored">root</div>'

    with pytest.raises(UnsupportedPreparedView, match="root marker conflicts"):
        assemble_typed_render(
            render_prepared_direct(Root()),
            revision=0,
            tag_for_type=lambda key: "x-" + key.lower().replace("_", "-"),
        )


@pytest.mark.parametrize("dynamic", [False, True])
@pytest.mark.parametrize("binding", [':data-probe="value"', 'v-bind="attrs"', ':[name]="value"'])
def test_prepared_root_marker_rejects_vue_target_collisions_and_ambiguity(
    dynamic: bool,
    binding: str,
) -> None:
    class Marker(Extension):
        name = "marker"

        def on_component_data(self, ctx):
            ctx.context._add_root_markers(['data-probe="extension"'])

    registry = Citry(autodiscover=False, extensions=[Marker])

    class Root(Component):
        citry = registry
        template = f'<c-element c-is="tag" {binding}></c-element>' if dynamic else f"<div {binding}></div>"

        def template_data(self, kwargs, slots):
            return {"tag": "div"}

        def js_data(self, kwargs, slots):
            return {"value": "browser", "attrs": {}, "name": "other"}

    with pytest.raises(UnsupportedPreparedView, match="root marker conflicts"):
        assemble_typed_render(
            render_prepared_direct(Root()),
            revision=0,
            tag_for_type=lambda key: "x-" + key.lower().replace("_", "-"),
        )


def test_dynamic_element_rejects_bare_object_event_binding() -> None:
    registry = Citry(autodiscover=False)

    class App(Component):
        citry = registry
        template = '<c-element c-is="tag" v-on="handlers"></c-element>'

        def template_data(self, kwargs, slots):
            return {"tag": "button"}

    with pytest.raises(TypeError, match="tag-dependent or executable"):
        render_prepared_direct(App())


@pytest.mark.parametrize("tag", ["script", "style", "template"])
def test_dynamic_element_rejects_unsafe_or_semantically_different_raw_tags(tag: str) -> None:
    registry = Citry(autodiscover=False)

    class App(Component):
        citry = registry
        template = '<c-element c-is="tag">x</c-element>'

        def template_data(self, kwargs, slots):
            return {"tag": tag}

    with pytest.raises(UnsupportedPreparedView, match="script/style/template"):
        assemble_typed_render(
            render_prepared_direct(App()),
            revision=0,
            tag_for_type=lambda key: "x-" + key.lower().replace("_", "-"),
        )


def test_dynamic_element_tag_revision_keeps_alias_shape_and_changes_definition_identity() -> None:
    registry = Citry(autodiscover=False)

    class App(Component):
        citry = registry
        template = '<c-element c-is="tag" data-kind="probe">x</c-element>'

        def template_data(self, kwargs, slots):
            return {"tag": kwargs["tag"]}

    def compile_tag(tag: str):
        assembly = assemble_typed_render(
            render_prepared_direct(App(tag=tag)),
            revision=0,
            tag_for_type=lambda key: "x-" + key.lower().replace("_", "-"),
        )
        occurrence = assembly.view.occurrences[0]
        value = assembly.compile_inputs[occurrence.definition_id]
        with NativeCompiler() as compiler:
            return value, compiler.compile(
                value.template,
                type_key=App.class_id,
                local_calls=value.local_calls,
                element_bindings=value.element_bindings,
                local_call_runs=value.local_call_runs,
                dynamic_elements=value.dynamic_elements,
            )

    section_input, section = compile_tag("section")
    article_input, article = compile_tag("article")
    assert section_input.template == article_input.template
    assert section.dynamic_elements[0]["tag"] == "section"
    assert article.dynamic_elements[0]["tag"] == "article"
    assert section.id != article.id


def test_server_resolved_dynamic_element_is_not_a_vue_runtime_requirement() -> None:
    registry = Citry(autodiscover=False)
    registry.set_mounted_prefix("/citry")

    class App(Component):
        citry = registry
        template = '<c-element c-is="tag">x</c-element>'

        def template_data(self, kwargs, slots):
            return {"tag": "section"}

    rendered = render_prepared_direct(App())
    from citry._vue.serialization import vue_serialization_requirements

    assert vue_serialization_requirements(rendered) == frozenset()


@pytest.mark.parametrize("body", ["one", "<b>one</b><i>two</i>"])
def test_direct_slot_hook_receives_whole_selected_render_and_wraps_once(body: str) -> None:
    seen = []

    class Identity(Extension):
        name = "identity"

        def on_slot_rendered(self, ctx):
            seen.append(ctx.result)
            return ctx.result

    registry = Citry(extensions=[Identity])

    class Receiver(Component):
        citry = registry
        template = "<section><c-slot /></section>"

    class Caller(Component):
        citry = registry
        template = f"<c-Receiver>{body}</c-Receiver>"

    rendered = render_prepared_direct(Caller())
    receiver = next(part for part in rendered.parts if hasattr(part, "frame") and part.frame.is_component_root)
    wrapper = next(part for part in receiver.parts if isinstance(part, DirectSlotRender))
    assert len(seen) == 1
    assert seen[0] is wrapper.selected
    assert not any(isinstance(part, DirectSlotRender) for part in wrapper.parts)
    _view(rendered)


def test_direct_three_component_forward_keeps_fill_in_root_lexical_definition() -> None:
    registry = Citry(autodiscover=False)

    class Inner(Component):
        citry = registry
        name = "inner"
        template = '<article><c-slot name="body" /></article>'

    class Wrapper(Component):
        citry = registry
        name = "wrapper"
        template = '<c-inner #c-key="\'inner\'"><c-fill name="body"><c-slot name="body" /></c-fill></c-inner>'

    class Root(Component):
        citry = registry
        template = (
            '<c-wrapper #c-key="\'wrapper\'"><c-fill name="body"><strong>{{ label }}</strong></c-fill></c-wrapper>'
        )

        def template_data(self, kwargs, slots):
            return {"label": "root lexical"}

    assembly = assemble_typed_render(
        render_prepared_direct(Root()),
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )
    root = next(item for item in assembly.view.occurrences if item.id == assembly.view.root_id)
    root_input = assembly.compile_inputs[root.definition_id]
    assert root.prepared_data["citryText0"] == "root lexical"
    wrapper_id = root.prepared_data["calls"][root_input.local_calls[0]["localId"]]["id"]
    wrapper = next(item for item in assembly.view.occurrences if item.id == wrapper_id)
    wrapper_template = assembly.compile_inputs[wrapper.definition_id].template
    root_sites = set(__import__("re").findall(r"v-slot:\['(citrySlot[^']+)'\]", root_input.template))
    forwarded_sites = set(__import__("re").findall(r'<slot name="(citrySlot[^"]+)"', wrapper_template))
    assert root_sites & forwarded_sites


def test_direct_repeated_outlets_have_distinct_sites_and_shared_fill_source() -> None:
    registry = Citry()

    class Mirror(Component):
        citry = registry
        template = '<c-slot name="body" /><c-slot name="body" />'

    class Root(Component):
        citry = registry
        template = '<c-Mirror #c-key="\'mirror\'"><c-fill name="body"><b>x</b></c-fill></c-Mirror>'

    rendered = render_prepared_direct(Root())
    receiver = next(part for part in rendered.parts if hasattr(part, "frame") and part.frame.is_component_root)
    regions = [part for part in receiver.parts if isinstance(part, DirectSlotRender)]
    assert len(regions) == 2
    assert regions[0].execution_index != regions[1].execution_index
    assert regions[0].fill_source is regions[1].fill_source
    assembly = assemble_typed_render(
        rendered,
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )
    root = next(item for item in assembly.view.occurrences if item.id == assembly.view.root_id)
    template = assembly.compile_inputs[root.definition_id].template
    sites = __import__("re").findall(r"v-slot:\['(citrySlot[^']+)'\]", template)
    assert len(sites) == 2
    assert len(set(sites)) == 2


def test_direct_slot_hook_repeat_gets_fresh_nested_execution() -> None:
    class Repeat(Extension):
        name = "repeat"

        def on_slot_rendered(self, ctx):
            repeated = ctx.slot()
            return CitryRender(parts=[ctx.result, repeated], context=ctx.result.context)

    registry = Citry(extensions=[Repeat])

    class Root(Component):
        citry = registry
        template = "<c-slot><b>fallback</b></c-slot>"

    rendered = render_prepared_direct(Root())
    outer = next(part for part in rendered.parts if isinstance(part, DirectSlotRender))
    nested = next(part for part in outer.parts if isinstance(part, DirectSlotRender))
    assert nested.execution_index != outer.execution_index
    assert nested.parent_execution is not None
    assert nested.parent_execution.index == outer.execution_index
    _view(rendered)


def test_direct_keyed_reorder_keeps_occurrence_identity_by_key() -> None:
    registry = Citry()

    class Row(Component):
        citry = registry
        template = "<p>{{ value }}</p>"

        def template_data(self, kwargs, slots):
            return kwargs

    class Root(Component):
        citry = registry
        template = '<c-for each="value in values"><c-Row #c-key="value" c-value="value" /></c-for>'

        def template_data(self, kwargs, slots):
            return kwargs

    def identities(values):
        view = _view(render_prepared_direct(Root(values=values)))
        root = next(item for item in view.occurrences if item.id == view.root_id)
        run_ids = root.prepared_data["callRuns"]["citryRun0"]
        children = {item.id: item for item in view.occurrences if item.parent_id == root.id}
        assert len(run_ids) == len(children) == 2
        assert all(occurrence_id in children for occurrence_id in run_ids)
        return run_ids, dict(zip(values, run_ids, strict=True))

    first_order, first_ids = identities(["a", "b"])
    second_order, second_ids = identities(["b", "a"])
    assert len(first_order) == len(second_order) == 2
    assert second_order == list(reversed(first_order))
    assert first_ids == second_ids


def test_direct_mode_rejects_static_typed_parent_but_reuses_direct_parent() -> None:
    registry = Citry()
    nested_calls = 0

    class Leaf(Component):
        citry = registry
        template = "leaf"

        def template_data(self, kwargs, slots):
            nonlocal nested_calls
            nested_calls += 1
            return {}

    class DirectInsideHtml(Component):
        citry = registry
        template = "root"

        def template_data(self, kwargs, slots):
            render_prepared_direct(Leaf())
            return {}

    with pytest.raises(RuntimeError, match="another prepared-render mode"):
        DirectInsideHtml().render()
    assert nested_calls == 0

    class GraphInsideDirect(Component):
        citry = registry
        template = "root"

        def template_data(self, kwargs, slots):
            render_prepared(Leaf())
            return {}

    render_prepared_direct(GraphInsideDirect())
    assert nested_calls == 1


def test_discarded_hook_slot_execution_does_not_change_stable_prepared_identity() -> None:
    discard = False

    class MaybeDiscard(Extension):
        name = "maybe_discard"

        def on_slot_rendered(self, ctx):
            if discard:
                ctx.slot()
            return ctx.result

    registry = Citry(extensions=[MaybeDiscard])

    class Root(Component):
        citry = registry
        template = "<c-slot><b>selected</b></c-slot>"

    first = _view(render_prepared_direct(Root()))
    discard = True
    second = _view(render_prepared_direct(Root()))
    assert first.root_id == second.root_id
    assert first.definitions == second.definitions
    assert first.occurrences == second.occurrences


def test_direct_rebinds_selected_slot_result_to_current_receiver_sibling() -> None:
    saved = None

    class Relocate(Extension):
        name = "relocate"

        def on_slot_rendered(self, ctx):
            nonlocal saved
            if saved is None:
                saved = ctx.slot()
                return ctx.result
            return saved

    registry = Citry(extensions=[Relocate])

    class Receiver(Component):
        citry = registry
        template = "<c-slot />"

    class Root(Component):
        citry = registry
        template = "<c-Receiver #c-key=\"'a'\">A</c-Receiver><c-Receiver #c-key=\"'b'\">B</c-Receiver>"

    rendered = render_prepared_direct(Root())
    receivers = [part for part in rendered.parts if hasattr(part, "frame") and part.frame.is_component_root]
    second = next(part for part in receivers[1].parts if isinstance(part, DirectSlotRender))
    assert second.receiver_render_id == receivers[1].frame.render_id
    assert second.selected is saved.selected
    _view(rendered)


def test_direct_rebound_slot_rejects_a_mismatched_receiver_identity() -> None:
    saved = None

    class Relocate(Extension):
        name = "relocate"

        def on_slot_rendered(self, ctx):
            nonlocal saved
            if saved is None:
                saved = ctx.slot()
                return ctx.result
            return saved

    registry = Citry(extensions=[Relocate])

    class Receiver(Component):
        citry = registry
        template = "<c-slot />"

    class Root(Component):
        citry = registry
        template = "<c-Receiver #c-key=\"'a'\">A</c-Receiver><c-Receiver #c-key=\"'b'\">B</c-Receiver>"

    rendered = render_prepared_direct(Root())
    receivers = [part for part in rendered.parts if hasattr(part, "frame") and part.frame.is_component_root]
    second = next(part for part in receivers[1].parts if isinstance(part, DirectSlotRender))
    second.receiver_render_id = rendered.frame.render_id
    with pytest.raises(
        UnsupportedPreparedView,
        match=r"moved outside its receiver|moved across unrelated receivers|crossed physical",
    ):
        _view(rendered)


@pytest.mark.parametrize("anchor", ["", 0, False])
def test_assembly_rejects_falsey_explicit_subtree_anchor(anchor) -> None:
    registry = Citry()

    class Root(Component):
        citry = registry
        template = "root"

    with pytest.raises((TypeError, ValueError), match="root occurrence"):
        assemble_typed_render(
            render_prepared_direct(Root()),
            revision=0,
            root_occurrence_id=anchor,
            tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
        )


def test_separate_component_sites_with_same_explicit_key_publish_distinct_vue_keys() -> None:
    registry = Citry()

    class Leaf(Component):
        citry = registry
        template = "leaf"

    class Root(Component):
        citry = registry
        template = "<c-Leaf #c-key=\"'same'\" /><c-Leaf #c-key=\"'same'\" />"

    view = _view(render_prepared_direct(Root()))
    root = next(item for item in view.occurrences if item.id == view.root_id)
    calls = list(root.prepared_data["calls"].values())
    assert len(calls) == 2
    assert {call["key"] for call in calls} == {call["id"] for call in calls}
    assert len({call["key"] for call in calls}) == 2


def test_repeated_same_component_site_with_same_explicit_key_is_rejected() -> None:
    registry = Citry()

    class Leaf(Component):
        citry = registry
        template = "leaf"

    class Root(Component):
        citry = registry
        template = '<c-for each="value in values"><c-Leaf #c-key="\'same\'" /></c-for>'

        def template_data(self, kwargs, slots):
            return {"values": (1, 2)}

    with pytest.raises(Exception, match="duplicate explicit #c-key"):
        _view(render_prepared_direct(Root()))


def test_document_layout_assembles_only_logical_body_occurrences() -> None:
    registry = Citry()

    class HeadOnly(Component):
        citry = registry
        template = "<meta name=discarded>"

    class BodyChild(Component):
        citry = registry
        template = "<button :title=\"'ready'\">body</button>"

    class Layout(Component):
        citry = registry
        template = "<!doctype html><html><head><c-HeadOnly /></head><body><c-slot /></body></html>"

    class Page(Component):
        citry = registry
        template = "<c-Layout><c-BodyChild #c-key=\"'body'\" /></c-Layout>"

    rendered = render_prepared_direct(Page())
    assembly = assemble_typed_render(
        rendered,
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )
    types = {occurrence.type_key for occurrence in assembly.view.occurrences}
    assert Page.class_id in types
    assert Layout.class_id in types
    assert BodyChild.class_id in types
    assert HeadOnly.class_id not in types
    for compiler_input in assembly.compile_inputs.values():
        assert "<!doctype" not in compiler_input.template.lower()
        assert "<html" not in compiler_input.template.lower()
        assert "<head" not in compiler_input.template.lower()
        assert "<body" not in compiler_input.template.lower()
    shell = typed_document_shell(rendered, '<div id="host"></div>')
    assert shell is not None
    assert shell.html == (
        '<!doctype html><html><head><meta name=discarded></head><body><div id="host"></div></body></html>'
    )


def test_slot_fallback_component_is_compiled_once_outside_supplied_slot_branch() -> None:
    registry = Citry()

    class Leaf(Component):
        citry = registry
        template = '<i c-title="label">{{ label }}</i>'

        def template_data(self, kwargs, slots):
            return {"label": "fallback"}

    class Receiver(Component):
        citry = registry
        template = "<c-slot><c-Leaf #c-key=\"'fallback'\" /></c-slot>"

    rendered = render_prepared_direct(Receiver())
    assembly = assemble_typed_render(
        rendered,
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )
    root = next(item for item in assembly.view.occurrences if item.id == assembly.view.root_id)
    compiler_input = assembly.compile_inputs[root.definition_id]
    assert compiler_input.template.count("<slot ") == 1
    assert len(compiler_input.local_calls) == 1
    assert compiler_input.template.count("preparedData.calls.") == 2


def test_fragment_metadata_uses_utf8_byte_offsets_through_nested_fill_rebasing() -> None:
    registry = Citry()

    class Leaf(Component):
        citry = registry
        template = '<button c-title="label">{{ label }}</button>'

        def template_data(self, kwargs, slots):
            return {"label": "žluťoučký"}

    class Receiver(Component):
        citry = registry
        template = '<article><c-slot name="body" /></article>'

    class Root(Component):
        citry = registry
        template = "<p>€</p><c-Receiver #c-key=\"'receiver'\"><b>ž</b><c-Leaf #c-key=\"'leaf'\" /></c-Receiver>"

    assembly = assemble_typed_render(
        render_prepared_direct(Root()),
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )
    occurrences = {item.id: item for item in assembly.view.occurrences}
    referenced: dict[str, list[str]] = {item.id: [] for item in assembly.view.occurrences}
    for owner in assembly.view.occurrences:
        compiler_input = assembly.compile_inputs[owner.definition_id]
        encoded = compiler_input.template.encode()
        for metadata in (*compiler_input.local_calls, *compiler_input.element_bindings):
            selected = encoded[metadata["sourceStart"] : metadata["sourceEnd"]]
            assert selected.startswith(b"<")
            assert selected.endswith(b">")
        for call in compiler_input.local_calls:
            binding = owner.prepared_data["calls"][call["localId"]]
            child = occurrences[binding["id"]]
            assert binding["parentId"] == child.parent_id == owner.id
            assert binding["key"] == child.id
            referenced[child.id].append(owner.id)
    assert referenced[assembly.view.root_id] == []
    assert all(referenced[item.id] == [item.parent_id] for item in assembly.view.occurrences if item.parent_id)


def test_static_runs_keep_authored_vue_attributes_visible_to_requirement_detection() -> None:
    registry = Citry()

    class Root(Component):
        citry = registry
        template = '<section><p v-if="false">hidden</p><b>static</b></section>'

    rendered = Root().render()
    leaves = [part for part in rendered.parts if not isinstance(part, CitryRender)]
    assert any(isinstance(part, PreparedElementOpen) and part.tag == "p" for part in leaves)
    assert any(isinstance(part, PreparedStaticRun) for part in leaves)
    assembly = assemble_typed_render(
        rendered,
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )
    compiler_input = assembly.compile_inputs[assembly.view.definitions[0].id]
    assert '<p v-if="false">hidden</p>' in compiler_input.template


def test_static_runs_preserve_self_closing_svg_siblings() -> None:
    registry = Citry()

    class Root(Component):
        citry = registry
        template = "<svg><path/><circle/></svg>"

    html = Root().render().serialize(deps_strategy="ignore")
    assert html.startswith("<svg data-cid-")
    assert html.endswith("><path></path><circle></circle></svg>")
    assert [child.tag for child in ET.fromstring(html)] == ["path", "circle"]  # noqa: S314
    assembly = assemble_typed_render(
        render_prepared_direct(Root()),
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )
    assert assembly.compile_inputs[assembly.view.definitions[0].id].template == (
        "<svg><path></path><circle></circle></svg>"
    )


def test_assembly_detaches_each_ingress_value_once_and_owns_prepared_containers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import citry._vue.prepared as prepared_module

    registry = Citry()
    attrs = UserDict({"title": ["original", (1, 2)]})
    server = {"nested": {"value": "server"}}

    class Root(Component):
        citry = registry
        template = '<c-for each="item in items"><div c-bind="attrs"></div></c-for>'

        def template_data(self, kwargs, slots):
            return {"attrs": attrs, "items": (1, 2)}

    rendered = Root().render()
    calls = 0
    original_detach = prepared_module._detach_object

    def counted_detach(value, name):
        nonlocal calls
        calls += 1
        return original_detach(value, name)

    monkeypatch.setattr(prepared_module, "_detach_object", counted_detach)
    assembly = assemble_typed_render(
        rendered,
        revision=0,
        server_data={rendered.frame.render_id: server},
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )
    occurrence = assembly.view.occurrences[0]
    attrs_keys = [
        item["attrsBindingKey"] for item in assembly.compile_inputs[occurrence.definition_id].element_bindings
    ]
    assert calls == 1
    assert occurrence.server_data == {"nested": {"value": "server"}}
    assert len(attrs_keys) == 1
    loop_records = occurrence.prepared_data["citryLoop0"]
    assert [record[attrs_keys[0]] for record in loop_records] == [
        {"title": ["original", [1, 2]]},
        {"title": ["original", [1, 2]]},
    ]
    assert loop_records[0][attrs_keys[0]] is not loop_records[1][attrs_keys[0]]

    server["nested"]["value"] = "mutated"
    attrs["title"][0] = "mutated"
    assert occurrence.server_data == {"nested": {"value": "server"}}
    assert all(record[attrs_keys[0]] == {"title": ["original", [1, 2]]} for record in loop_records)
    loop_records[0][attrs_keys[0]]["title"][0] = "first only"
    assert loop_records[1][attrs_keys[0]] == {"title": ["original", [1, 2]]}


@pytest.mark.parametrize("bad", [float("nan"), float("inf")])
def test_assembly_rejects_nonfinite_prepared_values(bad: float) -> None:
    registry = Citry()

    class Root(Component):
        citry = registry
        template = '<div c-title="value"></div>'

        def template_data(self, kwargs, slots):
            return {"value": bad}

    with pytest.raises(ValueError, match="finite numbers"):
        assemble_typed_render(
            Root().render(),
            revision=0,
            tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
        )


def test_assembly_rejects_cycles_in_prepared_values() -> None:
    registry = Citry()
    attrs: dict[str, object] = {}
    attrs["title"] = attrs

    class Root(Component):
        citry = registry
        template = '<div c-bind="attrs"></div>'

        def template_data(self, kwargs, slots):
            return {"attrs": attrs}

    with pytest.raises(ValueError, match="must not contain a cycle"):
        assemble_typed_render(
            Root().render(),
            revision=0,
            tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
        )


def test_builder_owned_manifest_matches_strict_public_occurrence_freeze() -> None:
    registry = Citry(secret="strict-owned-oracle-secret", autodiscover=False)  # noqa: S106

    class Receiver(Component):
        citry = registry
        template = '<article><c-slot name="body"><i>fallback</i></c-slot></article>'

    class Root(Component):
        citry = registry
        template = (
            '<c-Receiver #c-key="\'receiver\'"><c-fill name="body"><button>{{ label }}</button></c-fill></c-Receiver>'
        )

        def template_data(self, kwargs, slots):
            return {"label": "Save"}

    assembly = assemble_typed_render(
        render_prepared_direct(Root()),
        revision=3,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )
    strict = tuple(
        PreparedOccurrence(
            item.id,
            item.type_key,
            item.definition_id,
            item.server_data,
            item.prepared_data,
            item.parent_id,
            item.placement_key,
        )
        for item in assembly.view.occurrences
    )
    assert strict == assembly.view.occurrences
    all_prepared = [item.prepared_data for item in assembly.view.occurrences]
    assert any("calls" in item for item in all_prepared)
    assert any("selectedSlots" in item for item in all_prepared)

    manifest = {
        "calls": {"citryCall0": {"id": "child", "key": "child", "parentId": "root"}},
        "selectedSlots": {"citrySlot0": "supplied"},
        "eventBindings": {
            "citryEvent0": {
                "id": "citryEvent0",
                "event": "click",
                "handler": "save",
                "args": None,
                "prevent": False,
                "stop": False,
                "self": False,
                "once": False,
                "key": None,
                "debounce": None,
                "throttle": None,
            }
        },
    }
    owned = PreparedOccurrence._from_assembly("root", "Root", "definition", {}, manifest, None, None)
    strict_manifest = PreparedOccurrence("root", "Root", "definition", {}, manifest, None, None)
    assert owned == strict_manifest


def test_leaf_program_reuses_nested_loop_source_and_records_each_occurrence() -> None:
    registry = Citry()

    class Leaf(Component):
        citry = registry
        template = (
            '<article c-bind="attrs"><h2>{{ title }}</h2>'
            '<c-if cond="groups"><ul><li c-for="group in groups">'
            '<span c-for="item in group">{{ item }}</span>'
            "</li></ul></c-if><c-else><p>empty</p></c-else></article>"
        )

        def template_data(self, kwargs, slots):
            return kwargs

    class Root(Component):
        citry = registry
        template = (
            '<main><c-Leaf #c-key="\'a\'" c-attrs="attrs_a" c-title="title_a" c-groups="groups_a" />'
            '<c-Leaf #c-key="\'b\'" c-attrs="attrs_b" c-title="title_b" c-groups="groups_b" /></main>'
        )

        def template_data(self, kwargs, slots):
            return {
                "attrs_a": {"data-id": "a"},
                "title_a": "A",
                "groups_a": [["a1", "a2"]],
                "attrs_b": {"data-id": "b"},
                "title_b": "B",
                "groups_b": [],
            }

    rendered = Root().render()
    children = [part for part in rendered.parts if isinstance(part, CitryRender)]
    assert all(isinstance(child.parts[0], PreparedLeafProgram) for child in children), [
        child.parts for child in children
    ]
    html = rendered.serialize(deps_strategy="ignore")
    assert "<h2>A</h2>" in html
    assert "<span>a1</span><span>a2</span>" in html
    assert "<h2>B</h2>" in html
    assert "<p>empty</p>" in html
    assembly = assemble_typed_render(
        rendered,
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )
    leaves = [item for item in assembly.view.occurrences if item.type_key == Leaf.class_id]
    assert len(leaves) == 2
    assert leaves[0].definition_id == leaves[1].definition_id
    compiler_input = assembly.compile_inputs[leaves[0].definition_id]
    assert compiler_input.template.count('v-for="preparedData in preparedData.citryLoop') == 2
    assert {item.prepared_data["citryText0"] for item in leaves} == {"A", "B"}
    with NativeCompiler() as compiler:
        compiled = compiler.compile(
            compiler_input.template,
            type_key=Leaf.class_id,
            element_bindings=compiler_input.element_bindings,
        )
    assert "_renderList" in compiled.javascript


def test_leaf_program_excludes_document_shells_and_keyed_python_loops() -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class Document(Component):
        citry = registry
        template = "<!doctype html><html><head></head><body>{{ label }}</body></html>"

        def template_data(self, kwargs, slots):
            return {"label": "body"}

    class KeyedLoop(Component):
        citry = registry
        template = '<ul><li c-for="item in items" key="authored">{{ item }}</li></ul>'

        def template_data(self, kwargs, slots):
            return {"items": ["a", "b"]}

    class NestedDocument(Component):
        citry = registry
        template = '<section><c-if cond="True"><html><head></head><body>{{ label }}</body></html></c-if></section>'

        def template_data(self, kwargs, slots):
            return {"label": "body"}

    assert not any(isinstance(part, PreparedLeafProgram) for part in Document().render().parts)
    assert not any(isinstance(part, PreparedLeafProgram) for part in KeyedLoop().render().parts)
    assert not any(isinstance(part, PreparedLeafProgram) for part in NestedDocument().render().parts)


def test_leaf_program_preserves_svg_self_closing_siblings() -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class Svg(Component):
        citry = registry
        template = '<svg><path c-if="shown" d="a"/><circle c-for="item in items" c-r="item"/></svg>'

        def template_data(self, kwargs, slots):
            return {"shown": True, "items": [1, 2]}

    rendered = Svg().render()
    program = rendered.parts[0]
    assert isinstance(program, PreparedLeafProgram)
    assert "<path" in program.fragment.template
    assert "</path>" not in program.fragment.template
    assert "</circle>" not in program.fragment.template
    html = rendered.serialize(deps_strategy="ignore")
    assert '<path d="a"></path><circle r="1"></circle><circle r="2"></circle></svg>' in html
    assert [child.tag for child in ET.fromstring(html)] == ["path", "circle", "circle"]  # noqa: S314


def test_leaf_program_does_not_duplicate_static_attribute_overridden_by_dynamic_value() -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class Styled(Component):
        citry = registry
        template = '<p class="base" c-class="dynamic" c-if="True">x</p>'

        def template_data(self, kwargs, slots):
            return {"dynamic": "selected"}

    rendered = Styled().render()
    program = rendered.parts[0]
    assert isinstance(program, PreparedLeafProgram)
    assert 'class="base"' not in program.fragment.template
    assert rendered.serialize(deps_strategy="ignore").count('class="base selected"') == 1


def test_leaf_program_structured_expression_falls_back_without_reevaluation() -> None:
    registry = Citry(autodiscover=False, extensions=[])
    calls = 0

    class Child(Component):
        citry = registry
        template = "<strong>child</strong>"

    class Leaf(Component):
        citry = registry
        template = "<section>{{ value }}</section>"

        def template_data(self, kwargs, slots):
            nonlocal calls
            calls += 1
            return {"value": Child()}

    rendered = Leaf().render()
    assert calls == 1
    assemble_typed_render(
        rendered,
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )
    assert calls == 1
    assert not any(isinstance(part, PreparedLeafProgram) for part in rendered.parts)
    html = rendered.serialize(deps_strategy="ignore")
    assert "<strong" in html
    assert ">child</strong>" in html


def test_scalar_slot_value_becomes_typed_text_once_and_assembles() -> None:
    from citry import Slot

    registry = Citry(autodiscover=False, extensions=[])
    calls = 0

    def content(_ctx):
        nonlocal calls
        calls += 1
        return "selected"

    class Leaf(Component):
        citry = registry
        template = "<section>prefix {{ body }} suffix</section>"

        def template_data(self, kwargs, slots):
            return {"body": Slot(content)}

    rendered = Leaf().render()
    assert calls == 1
    assert "prefix selected suffix" in rendered.serialize(deps_strategy="ignore")
    assemble_typed_render(
        rendered,
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )
    assert calls == 1


def test_transparent_wrapper_rejects_component_context_without_class_identity() -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class Root(Component):
        citry = registry
        template = "<main>plain</main>"

    rendered = render_prepared_direct(Root())
    transparent = CitryRender(
        parts=list(rendered.parts),
        context=rendered.context,
        frame=RenderFrame(
            render_id=None,
            class_id=None,
            class_name=None,
            is_component_root=False,
            root_markers=(),
        ),
        render_target="prepared",
    )
    wrapped = CitryRender(
        parts=[transparent], context=rendered.context, frame=rendered.frame, render_target="prepared"
    )
    with pytest.raises(
        UnsupportedPreparedView,
        match="prepared transparent render has no class in the encoding engine",
    ):
        assemble_typed_render(
            wrapped,
            revision=0,
            tag_for_type=lambda type_key: f"c-{type_key.split('_', 1)[0].lower()}",
        )


def test_leaf_program_simple_component_value_preserves_typed_output_once() -> None:
    registry = Citry(autodiscover=False, extensions=[])
    calls = 0

    class Child(Component):
        citry = registry
        simple = True
        template = "<b>child</b>"

    class Leaf(Component):
        citry = registry
        template = "<section>prefix {{ value }} suffix</section>"

        def template_data(self, kwargs, slots):
            nonlocal calls
            calls += 1
            return {"value": Child()}

    rendered = Leaf().render()
    assert calls == 1
    assert not any(isinstance(part, PreparedLeafProgram) for part in rendered.parts)
    assembly = assemble_typed_render(
        rendered,
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )
    root = next(item for item in assembly.view.occurrences if item.id == assembly.view.root_id)
    assert "prefix <b>child</b> suffix" in assembly.compile_inputs[root.definition_id].template
    assert calls == 1


def test_leaf_program_preserves_generator_and_body_interleaving() -> None:
    registry = Citry(autodiscover=False, extensions=[])
    events: list[str] = []

    def items():
        for value in ("a", "b"):
            events.append(f"yield:{value}")
            yield value

    def show(value):
        from citry.citry_render import _VALUE_CONTEXT

        assert _VALUE_CONTEXT.get().variables["item"] == value
        events.append(f"body:{value}")
        return value

    class Leaf(Component):
        citry = registry
        template = '<p c-for="item in items">{{ show(item) }}</p>'

        def template_data(self, kwargs, slots):
            return {"items": items(), "show": show}

    rendered = Leaf().render()
    assert isinstance(rendered.parts[0], PreparedLeafProgram)
    assert events == ["yield:a", "body:a", "yield:b", "body:b"]
    html = rendered.serialize(deps_strategy="ignore")
    assert ">a</p>" in html
    assert ">b</p>" in html


def test_leaf_program_cache_does_not_hide_node_tracing(caplog: pytest.LogCaptureFixture) -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class Leaf(Component):
        citry = registry
        template = '<p c-for="item in items">{{ item }}</p>'

        def template_data(self, kwargs, slots):
            return {"items": ["a", "b"]}

    assert isinstance(Leaf().render().parts[0], PreparedLeafProgram)
    with caplog.at_level(5, logger="citry"):
        traced = Leaf().render()
    assert not any(isinstance(part, PreparedLeafProgram) for part in traced.parts)
    assert any("ForNode" in record.message for record in caplog.records)


def test_leaf_program_compiles_constant_and_fixed_name_attribute_plans() -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class Leaf(Component):
        citry = registry
        template = (
            '<section c-for="item in items"><i data-kind="constant"></i>'
            '<input type="text" c-title="item[\'title\']" c-hidden="item[\'hidden\']"/></section>'
        )

        def template_data(self, kwargs, slots):
            return {"items": [{"title": "A", "hidden": True}, {"title": "B", "hidden": None}]}

    rendered = Leaf().render()
    program = rendered.parts[0]
    assert isinstance(program, PreparedLeafProgram)
    assert program.resolved_opens
    assert all(type(value) is dict for value in program.resolved_opens.values())
    html = rendered.serialize(deps_strategy="ignore")
    assert '<i data-kind="constant"></i><input type="text" title="A" hidden/>' in html
    assert '<i data-kind="constant"></i><input type="text" title="B"/>' in html


def test_leaf_program_keeps_class_merging_on_general_attribute_resolver() -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class Leaf(Component):
        citry = registry
        template = '<p class="base" c-class="extra" c-if="True">x</p>'

        def template_data(self, kwargs, slots):
            return {"extra": "selected"}

    program = Leaf().render().parts[0]
    assert isinstance(program, PreparedLeafProgram)
    assert all(isinstance(value, PreparedElementOpen) for value in program.resolved_opens.values())


def test_leaf_program_retains_resolved_spread_data_in_typed_opens() -> None:
    registry = Citry(autodiscover=False, extensions=[])
    attrs = {"id": "second", "CLASS": "selected", "hidden": False}

    class Leaf(Component):
        citry = registry
        template = '<p ID="first" class="base" c-bind="attrs" c-if="True">x</p>'

        def template_data(self, kwargs, slots):
            return {"attrs": attrs}

    rendered = Leaf().render()
    program = rendered.parts[0]
    assert isinstance(program, PreparedLeafProgram)
    assert program.resolved_opens
    assert all(isinstance(value, PreparedElementOpen) for value in program.resolved_opens.values())
    assert 'ID="second"' in rendered.serialize(deps_strategy="ignore")
    assert 'class="base selected"' in rendered.serialize(deps_strategy="ignore")
    assert "hidden" not in program.prepared_data["citryAttrs0"]


def test_leaf_program_spread_keeps_separate_static_and_prepared_snapshots() -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class Leaf(Component):
        citry = registry
        template = '<p c-bind="attrs" c-if="True">x</p>'

        def template_data(self, kwargs, slots):
            return {"attrs": {"title": "original"}}

    rendered = Leaf().render()
    program = rendered.parts[0]
    assert isinstance(program, PreparedLeafProgram)
    assert rendered.serialize(deps_strategy="ignore").count('title="original"') == 1
    program.prepared_data["citryAttrs0"]["title"] = "prepared mutation"
    assert rendered.serialize(deps_strategy="ignore").count('title="original"') == 1


def test_leaf_program_spread_structured_fallback_uses_resolved_values_and_authored_spans_once() -> None:
    registry = Citry(autodiscover=False, extensions=[])
    calls = 0
    template_source = '<p title="old" c-bind="spread()">{{ structured() }}</p>'

    def structured():
        from citry.citry_render import _VALUE_CONTEXT

        context = _VALUE_CONTEXT.get()
        return CitryRender(parts=[PreparedStaticRun("<b>structured</b>")], context=context)

    def spread():
        nonlocal calls
        calls += 1
        return {"title": "resolved", "data-extra": "value"}

    class Leaf(Component):
        citry = registry
        template = template_source

        def template_data(self, kwargs, slots):
            return {"spread": spread, "structured": structured}

    rendered = Leaf().render()
    assert calls == 1
    assert not any(isinstance(part, PreparedLeafProgram) for part in rendered.parts)
    opening = next(part for part in rendered.parts if isinstance(part, PreparedElementOpen))
    assert opening.authored_attrs == ()
    spans = {attr.name: attr.span for attr in opening.attrs}
    assert all(attr.origin == "data" for attr in opening.attrs)
    assert spans["title"][0] == template_source.encode().index(b"title")
    assert spans["data-extra"][0] == template_source.encode().index(b"c-bind")
    assert calls == 1


def test_leaf_program_defers_reserved_dynamic_attribute_error_to_selected_branch() -> None:
    registry = Citry(autodiscover=False, extensions=[])
    calls = 0

    def probe():
        nonlocal calls
        calls += 1
        return "forbidden"

    class Leaf(Component):
        citry = registry
        template = '<c-if cond="selected"><p c-data-cev-bind="probe()">x</p></c-if><c-else>safe</c-else>'

        def template_data(self, kwargs, slots):
            return {"selected": kwargs.get("selected", False), "probe": probe}

    assert "safe" in Leaf(selected=False).render().serialize(deps_strategy="ignore")
    assert calls == 0
    with pytest.raises(RuntimeError, match="reserved internal Events namespace"):
        Leaf(selected=True).render()
    assert calls == 0


def test_compiled_attribute_plan_evaluates_once_and_matches_assembled_data() -> None:
    registry = Citry(autodiscover=False, extensions=[])
    calls = 0

    def title(value):
        nonlocal calls
        calls += 1
        return value

    class Leaf(Component):
        citry = registry
        template = '<p c-for="item in items" c-title="title(item)">{{ item }}</p>'

        def template_data(self, kwargs, slots):
            return {"items": [Const("A"), Const("B")], "title": title}

    rendered = Leaf().render()
    program = rendered.parts[0]
    assert isinstance(program, PreparedLeafProgram)
    assert calls == 2
    records = program.prepared_data["citryLoop0"]
    assert [record["citryAttrs0"] for record in records] == [{"title": "A"}, {"title": "B"}]
    assembly = assemble_typed_render(
        rendered,
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )
    occurrence = assembly.view.occurrences[0]
    assert occurrence.prepared_data["citryLoop0"] == records
    assert calls == 2


def test_compiled_attribute_plan_uses_general_case_insensitive_merge_and_custom_hook_paths() -> None:
    class Rewriter(Extension):
        name = "rewriter"

        def on_attrs_resolved(self, ctx):
            return {**ctx.attrs, "data-hook": "yes"}

    plain = Citry(autodiscover=False, extensions=[])
    hooked = Citry(autodiscover=False, extensions=[Rewriter])

    class Collision(Component):
        citry = plain
        template = '<p ID="first" c-bind="attrs" c-if="True">x</p>'

        def template_data(self, kwargs, slots):
            return {"attrs": {"id": "second"}}

    class Hooked(Component):
        citry = hooked
        template = '<p c-title="\'value\'" c-if="True">x</p>'

    collision = Collision().render()
    program = collision.parts[0]
    assert isinstance(program, PreparedLeafProgram)
    assert all(isinstance(value, PreparedElementOpen) for value in program.resolved_opens.values())
    assert 'ID="second"' in collision.serialize(deps_strategy="ignore")
    assert not any(isinstance(part, PreparedLeafProgram) for part in Hooked().render().parts)


def test_whole_leaf_artifact_reuse_matches_general_assembly_and_validates_each_occurrence() -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class Leaf(Component):
        citry = registry
        template = '<p c-for="item in items" c-title="item">{{ item }}</p>'

        def template_data(self, kwargs, slots):
            return {"items": kwargs["items"]}

    class Root(Component):
        citry = registry
        template = "<c-Leaf #c-key=\"'a'\" c-items=\"['A']\" /><c-Leaf #c-key=\"'b'\" c-items=\"['B']\" />"

    def assemble(rendered):
        return assemble_typed_render(
            rendered,
            revision=0,
            tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
        )

    shared_render = Root().render()
    shared = assemble(shared_render)
    leaf_definitions = [item for item in shared.view.definitions if item.type_key == Leaf.class_id]
    assert len(leaf_definitions) == 1

    general_render = Root().render()
    for child in (part for part in general_render.parts if isinstance(part, CitryRender)):
        assert isinstance(child.parts[0], PreparedLeafProgram)
        child.parts.insert(0, PreparedStaticRun(""))
    general = assemble(general_render)
    assert shared.view == general.view
    assert shared.compile_inputs == general.compile_inputs

    invalid_render = Root().render()
    leaves = [part for part in invalid_render.parts if isinstance(part, CitryRender)]
    invalid_program = leaves[1].parts[0]
    assert isinstance(invalid_program, PreparedLeafProgram)
    invalid_program.prepared_data["citryLoop0"][0]["citryAttrs0"]["title"] = float("nan")
    with pytest.raises(ValueError, match="finite numbers"):
        assemble(invalid_render)

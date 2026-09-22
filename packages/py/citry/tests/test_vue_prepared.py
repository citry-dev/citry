from __future__ import annotations

from dataclasses import replace

import pytest

from citry import Citry, Component
from citry._vue import compiler as vue_compiler
from citry._vue.capture import render_prepared_direct
from citry._vue.compiler import (
    HELPER_CONTRACT,
    NativeCompiler,
    compile_view,
    definition_compile_inputs,
    definition_templates,
)
from citry._vue.direct_capture import assemble_typed_render
from citry._vue.prepared import (
    ComponentCall,
    ElementClose,
    ElementOpen,
    FillClosure,
    ForwardedSlot,
    Html,
    LocalComponentCall,
    PreparedDefinition,
    PreparedFill,
    PreparedOccurrence,
    PreparedSlotOutlet,
    PreparedView,
    RuntimeDirective,
    SlotOutlet,
    TextBinding,
    replace_definition_ids,
)
from citry._vue.protocol import DefinitionAsset, prepared_manifest, revision_envelope


def _direct_definition_template(source: str) -> str:
    registry = Citry(autodiscover=False)

    class Page(Component):
        citry = registry
        template = source

    assembly = assemble_typed_render(
        render_prepared_direct(Page()),
        revision=0,
        tag_for_type=lambda type_key: f"x-{type_key.lower().replace('_', '-')}",
    )
    root = next(item for item in assembly.view.occurrences if item.id == assembly.view.root_id)
    return assembly.compile_inputs[root.definition_id].template


def test_direct_definition_composer_preserves_bindings_calls_slots_and_utf8_spans() -> None:
    site = "citrySlotA"
    child_definition = PreparedDefinition(
        "child-def",
        "Child",
        (PreparedSlotOutlet(site, "body", (TextBinding("citryTextFallback"),)),),
    )
    root_definition = PreparedDefinition(
        "root-def",
        "Root",
        (
            ElementOpen("main", ('v-show="shown"',), "citryAttrsA", "citryKeyA", (0, 1)),
            TextBinding("citryTextA"),
            LocalComponentCall(
                "citryCallA",
                "Child",
                "citry-child",
                (1, 2),
                (PreparedFill(site, "body", (TextBinding("citryTextFill"),)),),
            ),
            ForwardedSlot(site, "body"),
            ElementClose("main", (2, 3)),
        ),
    )
    root = PreparedOccurrence(
        "root",
        "Root",
        "root-def",
        {},
        {"calls": {"citryCallA": {"id": "child", "key": "child", "parentId": "root"}}},
        None,
        None,
    )
    child = PreparedOccurrence("child", "Child", "child-def", {}, {}, "root", "child")
    view = PreparedView(0, "root", (root, child), (root_definition, child_definition))

    inputs = definition_compile_inputs(view)
    root_input = inputs["root-def"]
    assert 'v-bind="preparedData.citryAttrsA"' in root_input.template
    assert "v-slot:['citrySlotA']" in root_input.template
    assert '<slot name="citrySlotA" :key="JSON.stringify([preparedData.citryKeyA, 0])"></slot>' in root_input.template
    encoded = root_input.template.encode()
    call_start = encoded.find(b"<citry-child")
    assert root_input.local_calls[0]["sourceEnd"] == call_start + encoded[call_start:].find(b">") + 1
    assert root_input.element_bindings[0]["attrsBindingKey"] == "citryAttrsA"
    assert "<slot v-if=\"preparedData.selectedSlots['citrySlotA']" in inputs["child-def"].template
    with NativeCompiler() as compiler:
        compiled = compile_view(view, compiler)
    assert compiled.view.occurrences[0].definition_id == compiled.definitions["root-def"].id
    assert compiled.definitions["root-def"].directive_signature[0].name == "v-show"


def test_compatibility_definition_composer_emits_native_state_metadata() -> None:
    view = PreparedView(
        0,
        "root",
        (PreparedOccurrence("root", "Root", "root-def", {}, {}, None, None),),
        (
            PreparedDefinition(
                "root-def",
                "Root",
                (
                    ElementOpen("input", (), None, None, (0, 1)),
                    ElementClose("input", (1, 2)),
                ),
            ),
        ),
    )

    template = definition_compile_inputs(view)["root-def"].template
    assert '<input v-citry-vue-owned="[]"></input>' in template


def test_direct_capture_keys_slots_by_nearest_prepared_element_and_preserves_void_boundaries() -> None:
    template = _direct_definition_template(
        """
        <div #c-key="'outer'">
          <span #c-key="'inner'"><c-slot name="inner" /><c-slot name="inner-second" /></span>
          <input #c-key="'void'">
          <c-slot name="outer" />
        </div>
        """
    )

    assert template.count(':key="JSON.stringify([preparedData.citryKey1,') == 2
    assert ':key="JSON.stringify([preparedData.citryKey1, 0])"' in template
    assert ':key="JSON.stringify([preparedData.citryKey1, 1])"' in template
    assert ':key="JSON.stringify([preparedData.citryKey0, 0])"' in template
    assert ':key="JSON.stringify([preparedData.citryKey1, 2])"' not in template


def test_direct_capture_leaves_unkeyed_slots_without_a_synthetic_key() -> None:
    template = _direct_definition_template('<div><c-slot name="body" /></div>')
    assert '<slot v-if="preparedData.selectedSlots[' in template
    assert ':key="' not in template


def test_direct_capture_keys_slots_under_a_keyed_dynamic_element() -> None:
    template = _direct_definition_template(
        """<c-element c-is="'section'" #c-key="'dynamic'"><c-slot name="body" /></c-element>"""
    )

    assert ':key="JSON.stringify([preparedData.citryKey0, 0])"' in template


def test_prepared_compiler_keys_slot_outlets_from_the_balanced_element_stream() -> None:
    site = "citrySlotKeyed"
    nodes = (
        ElementOpen("div", (), None, "citryKeyOuter", (0, 1)),
        ElementOpen("span", (), None, "citryKeyInner", (1, 2)),
        PreparedSlotOutlet(site, "body", ()),
        ForwardedSlot("citrySlotForwarded", "forwarded"),
        ElementClose("span", (2, 3)),
        ForwardedSlot("citrySlotOuter", "outer"),
        ElementClose("div", (3, 4)),
    )

    template = definition_compile_inputs(
        PreparedView(
            0,
            "root",
            (PreparedOccurrence("root", "Root", "root-def", {}, {}, None, None),),
            (PreparedDefinition("root-def", "Root", nodes),),
        )
    )["root-def"].template

    assert ':key="JSON.stringify([preparedData.citryKeyInner, 0])"' in template
    assert ':key="JSON.stringify([preparedData.citryKeyInner, 1])"' in template
    assert ':key="JSON.stringify([preparedData.citryKeyOuter, 0])"' in template


def test_prepared_compiler_leaves_unkeyed_slot_outlets_without_a_synthetic_key() -> None:
    nodes = (
        ElementOpen("div", (), None, None, (0, 1)),
        PreparedSlotOutlet("citrySlotUnkeyed", "body", ()),
        ForwardedSlot("citrySlotForwardedUnkeyed", "forwarded"),
        ElementClose("div", (1, 2)),
    )
    template = definition_compile_inputs(
        PreparedView(
            0,
            "root",
            (PreparedOccurrence("root", "Root", "root-def", {}, {}, None, None),),
            (PreparedDefinition("root-def", "Root", nodes),),
        )
    )["root-def"].template
    assert ':key="' not in template


def test_compiled_identity_binds_preamble_and_compatibility_metadata() -> None:
    response = {
        "compiler": "vize_atelier_dom",
        "compilerVersion": "0.420.0",
        "options": {"prefixIdentifiers": True, "hoistStatic": False, "cacheHandlers": False},
        "transformedSourceSha256": "source",
        "codeSha256": "code",
    }
    base = vue_compiler._compiled_content_id("request", response, "const a=1", "function render(){}", (), ())
    assert base != vue_compiler._compiled_content_id("request", response, "const a=2", "function render(){}", (), ())
    signature = (RuntimeDirective("citryDirectiveSiteD0", "v-show", None, ()),)
    assert base != vue_compiler._compiled_content_id(
        "request", response, "const a=1", "function render(){}", signature, ()
    )


def test_inprocess_native_compiler_discovers_multiple_directives_and_bounds_cache() -> None:
    with NativeCompiler() as compiler:
        compiled = compiler.compile('<input v-model="value" v-show="visible">', type_key="Input")
        assert [item.name for item in compiled.directive_signature] == ["v-model", "v-show"]
        assert len(compiled.replacement_sites) == 1
        first = compiler.compile("<p>0</p>", type_key="Cache")
        assert compiler.compile("<p>0</p>", type_key="Cache") is first
        for index in range(1, 257):
            compiler.compile(f"<p>{index}</p>", type_key="Cache")
        assert compiler.compile("<p>0</p>", type_key="Cache") is not first


def test_native_compiler_accepts_generated_prepared_data_loop_alias() -> None:
    template = (
        '<ul><li v-for="preparedData in preparedData.citryLoop0" '
        'v-bind="preparedData.citryAttrs0">{{ preparedData.citryText0 }}</li></ul>'
    )
    opening = '<li v-for="preparedData in preparedData.citryLoop0" v-bind="preparedData.citryAttrs0">'
    start = len(b"<ul>")
    end = start + len(opening.encode())
    with NativeCompiler() as compiler:
        compiled = compiler.compile(
            template,
            type_key="LeafLoop",
            element_bindings=(
                {
                    "sourceStart": start,
                    "sourceEnd": end,
                    "attrsBindingKey": "citryAttrs0",
                    "keyBindingKey": None,
                },
            ),
        )
    assert "_renderList(_ctx.preparedData.citryLoop0, (preparedData) =>" in compiled.javascript
    assert "preparedData.citryAttrs0" in compiled.javascript
    assert "preparedData.citryText0" in compiled.javascript


def occurrence(
    occurrence_id: str, type_key: str, definition_id: str, parent_id: str | None = None
) -> PreparedOccurrence:
    placement_key = None if parent_id is None else occurrence_id
    return PreparedOccurrence(occurrence_id, type_key, definition_id, {}, {}, parent_id, placement_key)


def test_prepared_view_validates_graph_and_detaches_json_data() -> None:
    data = {"nested": [1]}
    definition = PreparedDefinition("root-def", "Root", ())
    root = PreparedOccurrence("root", "Root", "root-def", data, {}, None, None)
    view = PreparedView(0, "root", (root,), (definition,))
    data["nested"].append(2)
    assert view.occurrences[0].server_data == {"nested": [1]}

    child_definition = PreparedDefinition("root-def", "Root", (ComponentCall("missing"),))
    with pytest.raises(ValueError, match="unknown occurrence"):
        PreparedView(0, "root", (root,), (child_definition,))


def test_definition_templates_keep_data_out_of_compiler_input_and_make_slots_dynamic() -> None:
    site = "citrySlotabc123"
    fill = FillClosure(site, "body", "root", "root", (Html('<b v-text="label"></b>', "template"),))
    child_definition = PreparedDefinition("child-def", "Child", (SlotOutlet(site, "body", "child", fill),))
    root_definition = PreparedDefinition("root-def", "Root", (TextBinding("citryTextDanger"), ComponentCall("child")))
    root = PreparedOccurrence(
        "root", "Root", "root-def", {}, {"citryTextDanger": "{{ malicious() }} <script>"}, None, None
    )
    child = occurrence("child", "Child", "child-def", "root")
    view = PreparedView(0, "root", (root, child), (root_definition, child_definition))
    templates = definition_templates(view, tag_for_type=lambda key: f"citry-{key.lower()}")
    root_template = templates["root-def"]
    assert "malicious" not in root_template
    assert "{{ preparedData['citryTextDanger'] }}" in root_template
    assert "v-slot:['citrySlotabc123']" in root_template


def test_protocol_requires_exact_assets_and_known_updates() -> None:
    definition = PreparedDefinition("root-def", "Root", ())
    view = PreparedView(1, "root", (occurrence("root", "Root", "root-def"),), (definition,))
    digest = "0" * 64
    asset = DefinitionAsset(
        "root-def", f"/definitions/{digest}.js", digest, "ordinary-vnodes/1", HELPER_CONTRACT, (), ()
    )
    assert prepared_manifest(app_id="app", view=view, assets=(asset,))["rootId"] == "root"
    compiled_asset = replace(asset, id="compiled-root", url=f"/citry/ext/events/definitions/{digest}.js")
    mapped = prepared_manifest(
        app_id="app", view=view, assets=(compiled_asset,), definition_ids={"root-def": "compiled-root"}
    )
    assert mapped["occurrences"][0]["definitionId"] == "compiled-root"
    assert revision_envelope(app_id="app", base_revision=0, view=view, assets=(asset,), updated_ids=("root",))[
        "updatedIds"
    ] == ["root"]
    with pytest.raises(ValueError, match="unknown"):
        revision_envelope(app_id="app", base_revision=0, view=view, assets=(asset,), updated_ids=("other",))
    replacement = ({"ownerId": "root", "siteId": "site", "expectedRemountIds": []},)
    assert revision_envelope(
        app_id="app", base_revision=0, view=view, assets=(asset,), updated_ids=("root",), replacements=replacement
    )["replacements"] == list(replacement)
    with pytest.raises(ValueError, match="unknown or unupdated"):
        revision_envelope(
            app_id="app",
            base_revision=0,
            view=view,
            assets=(asset,),
            updated_ids=("root",),
            replacements=({"ownerId": "other", "siteId": "site", "expectedRemountIds": []},),
        )
    with pytest.raises(ValueError, match="target"):
        prepared_manifest(
            app_id="app",
            view=view,
            assets=(
                DefinitionAsset("root-def", f"/definitions/{digest}.js", digest, "optimized", HELPER_CONTRACT, (), ()),
            ),
        )


def test_protocol_requires_exact_declared_opaque_html_records() -> None:
    definition = PreparedDefinition("root-def", "Root", ())
    digest = "0" * 64
    site = {"key": "citryOpaque0", "sourceStart": 0, "sourceEnd": 1, "origin": "markup"}
    asset = DefinitionAsset(
        "root-def",
        f"/definitions/{digest}.js",
        digest,
        "ordinary-vnodes/1",
        HELPER_CONTRACT,
        (),
        (),
        opaque_html_sites=(site,),
    )

    def manifest(data):
        root = PreparedOccurrence("root", "Root", "root-def", {}, data, None, None)
        return prepared_manifest(app_id="app", view=PreparedView(0, "root", (root,), (definition,)), assets=(asset,))

    assert (
        manifest({"opaqueHtml": {"citryOpaque0": {"html": "<b>x</b>"}}})["occurrences"][0]["preparedData"][
            "opaqueHtml"
        ]["citryOpaque0"]["html"]
        == "<b>x</b>"
    )
    for malformed in (
        {},
        {"opaqueHtml": {}},
        {"opaqueHtml": {"citryOpaque0": {"html": "x", "extra": True}}},
        {"opaqueHtml": {"citryOpaque0": {"html": 1}}},
    ):
        with pytest.raises(ValueError, match="opaque HTML"):
            manifest(malformed)


def test_prepared_graph_rejects_extra_root_parent_mismatch_and_wrong_slot_owner() -> None:
    root_definition = PreparedDefinition("root-def", "Root", (ComponentCall("child"),))
    child_definition = PreparedDefinition("child-def", "Child", ())
    root = occurrence("root", "Root", "root-def")
    child = occurrence("child", "Child", "child-def", "root")
    with pytest.raises(ValueError, match="exactly one rooted tree"):
        PreparedView(
            0,
            "root",
            (root, occurrence("child", "Child", "child-def")),
            (root_definition, child_definition),
        )
    with pytest.raises(ValueError, match="placement parent"):
        PreparedView(
            0,
            "root",
            (root, child),
            (
                PreparedDefinition("root-def", "Root", (ComponentCall("child"), ComponentCall("child"))),
                child_definition,
            ),
        )

    site = "citrySlotOwner"
    bad_fill = FillClosure(site, "body", "root", "root", ())
    bad_child_definition = PreparedDefinition("child-def", "Child", (SlotOutlet(site, "body", "root", bad_fill),))
    with pytest.raises(ValueError, match="receiver is not"):
        PreparedView(0, "root", (root, child), (root_definition, bad_child_definition))


def test_component_tags_are_safe_injective_and_occurrence_ids_are_escaped() -> None:
    child_id = 'child"quoted'
    root_definition = PreparedDefinition("root-def", "Root", (ComponentCall(child_id),))
    child_definition = PreparedDefinition("child-def", "Child", ())
    view = PreparedView(
        0,
        "root",
        (occurrence("root", "Root", "root-def"), occurrence(child_id, "Child", "child-def", "root")),
        (root_definition, child_definition),
    )
    templates = definition_templates(view, tag_for_type=lambda key: f"citry-{key.lower()}")
    assert 'citry-id="child&amp;quot;quoted"' not in templates["root-def"]
    assert 'citry-id="child&quot;quoted"' in templates["root-def"]
    with pytest.raises(ValueError, match="unsafe"):
        definition_templates(view, tag_for_type=lambda key: f"Unsafe-{key}")
    with pytest.raises(ValueError, match="injective"):
        definition_templates(view, tag_for_type=lambda _key: "citry-same")


def test_native_compiler_binds_ordinary_target_and_final_definition_identity() -> None:
    signature: tuple[RuntimeDirective, ...] = ()
    with NativeCompiler() as compiler:
        compiled = compiler.compile(
            '<main><span v-text="label"></span></main>',
            type_key="Root",
            directive_signature=signature,
        )
        changed = compiler.compile(
            '<main class="changed"><span v-text="label"></span></main>',
            type_key="Root",
        )
    assert compiled.target == "ordinary-vnodes/1"
    assert "window.CitryStable.compilerRuntime" in compiled.javascript
    assert "window.Vue=" not in compiled.javascript
    assert HELPER_CONTRACT in compiled.javascript
    assert compiled.id not in {"root-def", ""}
    assert changed.id != compiled.id

    original = PreparedView(
        0,
        "root",
        (occurrence("root", "Root", "root-def"),),
        (PreparedDefinition("root-def", "Root", (), signature),),
    )
    rebound = replace_definition_ids(original, {"root-def": compiled.id})
    assert rebound.occurrences[0].definition_id == compiled.id
    assert rebound.definitions[0].directive_signature == signature


def test_ordinary_compiler_validates_source_maps_model_directives_and_raw_text() -> None:
    with NativeCompiler() as compiler:
        with pytest.raises(ValueError, match="source maps"):
            compiler.compile("<main/>", type_key="Root", source_map=True)
        model = compiler.compile('<input v-model="label">', type_key="Root")
        assert [item.name for item in model.directive_signature] == ["v-model"]
        assert model.replacement_sites
        with pytest.raises(ValueError, match="raw-text"):
            compiler.compile("<script>alert(1)</script>", type_key="Root")


def test_composed_fill_change_changes_parent_final_compiler_identity() -> None:
    site = "citrySlotComposed"
    root_definition = PreparedDefinition("same-root-def", "Root", (ComponentCall("child"),))
    root = occurrence("root", "Root", "same-root-def")
    child = occurrence("child", "Child", "child-def", "root")

    def view_with_fill(tag: str) -> PreparedView:
        fill = FillClosure(site, "body", "root", "root", (Html(f"<{tag}>value</{tag}>", "template"),))
        child_definition = PreparedDefinition("child-def", "Child", (SlotOutlet(site, "body", "child", fill),))
        return PreparedView(0, "root", (root, child), (root_definition, child_definition))

    first = definition_templates(view_with_fill("strong"), tag_for_type=lambda key: f"citry-{key.lower()}")
    second = definition_templates(view_with_fill("em"), tag_for_type=lambda key: f"citry-{key.lower()}")
    assert first["same-root-def"] != second["same-root-def"]
    with NativeCompiler() as compiler:
        first_id = compiler.compile(first["same-root-def"], type_key="Root").id
        second_id = compiler.compile(second["same-root-def"], type_key="Root").id
    assert first_id != second_id

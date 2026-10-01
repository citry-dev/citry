from __future__ import annotations

import hashlib
import re
from dataclasses import replace
from pathlib import Path
from typing import Any

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


def test_browser_client_checks_the_helper_contract_the_compiler_emits() -> None:
    # The browser refuses every definition whose helper contract differs from
    # its own copy, so a hash updated on one side only breaks every page.
    vue_dir = Path(vue_compiler.__file__).parent
    # The value appears as the declaration and, in the bundle, as the guard
    # that stops a second runtime copy with a different contract.
    declaration = re.compile(r'(?:const HELPER_CONTRACT\s*=\s*|helperContract\s*!==\s*)"([0-9a-f]{64})"')
    # client.js is the hand-written source and declares the value once.
    assert declaration.findall((vue_dir / "client.js").read_text(encoding="utf-8")) == [HELPER_CONTRACT]
    # runtime.js is the bundle the server sends, generated from client.js.
    bundled = declaration.findall((vue_dir / "runtime.js").read_text(encoding="utf-8"))
    assert len(bundled) >= 2
    assert set(bundled) == {HELPER_CONTRACT}


def _direct_definition_root(source: str, **kwargs: Any) -> tuple[str, dict[str, object]]:
    registry = Citry(autodiscover=False)

    class Page(Component):
        citry = registry
        template = source

        # Kwargs reach the template unchanged, so a test can vary a key
        # value while the template source (and so every site id) stays fixed.
        def template_data(self, kwargs: dict[str, object], slots: object) -> dict[str, object]:
            return dict(kwargs)

    assembly = assemble_typed_render(
        render_prepared_direct(Page(**kwargs)),
        revision=0,
        tag_for_type=lambda type_key: f"x-{type_key.lower().replace('_', '-')}",
    )
    root = next(item for item in assembly.view.occurrences if item.id == assembly.view.root_id)
    return assembly.compile_inputs[root.definition_id].template, dict(root.prepared_data)


def _direct_definition_template(source: str) -> str:
    return _direct_definition_root(source)[0]


def _slot_keys_in_outlet_order(template: str, prepared_data: dict[str, object]) -> list[str]:
    # Each keyed outlet reads its own entry from `slotKeys`; resolve them in
    # template order so a test can compare one outlet across two renders.
    sites = re.findall(r":key=\"\$citryPrepared\.slotKeys\['(\w+)'\]\"", template)
    slot_keys = prepared_data["slotKeys"]
    assert isinstance(slot_keys, dict)
    assert set(slot_keys) == set(sites)
    return [slot_keys[site] for site in sites]


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
    assert 'v-bind="$citryPrepared.citryAttrsA"' in root_input.template
    assert "v-slot:['citrySlotA']" in root_input.template
    slot_outlet = '<slot name="citrySlotA" :key="JSON.stringify([$citryPrepared.citryKeyA, 0])"></slot>'
    assert slot_outlet in root_input.template
    encoded = root_input.template.encode()
    call_start = encoded.find(b"<citry-child")
    assert root_input.local_calls[0]["sourceEnd"] == call_start + encoded[call_start:].find(b">") + 1
    assert root_input.element_bindings[0]["attrsBindingKey"] == "citryAttrsA"
    assert "<slot v-if=\"$citryPrepared.selectedSlots['citrySlotA']" in inputs["child-def"].template
    with NativeCompiler() as compiler:
        compiled = compile_view(view, compiler)
    assert compiled.view.occurrences[0].definition_id == compiled.definitions["root-def"].id
    assert compiled.definitions["root-def"].directive_signature[0].name == "v-show"
    # The compiler builds a complete hydration plan for Citry's generated
    # slot names and outlets.
    plans = {key: value.hydration_plan for key, value in compiled.definitions.items()}
    assert all(plan is not None and plan.status == "complete" for plan in plans.values())
    anchors = {
        key: [(item.kind, item.origin, item.comment, item.path) for item in plan.anchors]
        for key, plan in plans.items()
        if plan is not None
    }
    assert anchors == {
        # The forwarded slot outlet inside the root's slot fill.
        "root-def": [("fragment", "slot", None, ("i:0:6d61696e", "i:1:736c6f74"))],
        # The child's selected-slot outlet heads a `v-if` chain with no
        # `v-else`; its text-only `<template v-else-if>` branch is wrapped
        # in a Fragment, and no match renders `<!--v-if-->`.
        "child-def": [
            ("fragment", "slot", None, ("i:0:736c6f74",)),
            ("fragment", "v-if-branch", None, ("i:1:74656d706c617465",)),
            ("comment", "v-if", "v-if", ("i:0:736c6f74",)),
        ],
    }


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
    source = """
        <div #c-key="'outer'">
          <span #c-key="inner_key"><c-slot name="inner" /><c-slot name="inner-second" /></span>
          <input #c-key="void_key">
          <c-slot name="outer" />
        </div>
        """
    template, prepared_data = _direct_definition_root(source, inner_key="a", void_key="v")
    keys = _slot_keys_in_outlet_order(template, prepared_data)
    # Every outlet under a keyed element gets its own key, so the two
    # outlets that share the inner span still get different keys.
    assert len(keys) == 3
    assert len(set(keys)) == 3

    # A slot key follows the key of its nearest keyed ancestor: renaming the
    # inner span's key moves only the two outlets inside it.
    renamed_inner = _slot_keys_in_outlet_order(*_direct_definition_root(source, inner_key="b", void_key="v"))
    assert renamed_inner[0] != keys[0]
    assert renamed_inner[1] != keys[1]
    assert renamed_inner[2] == keys[2]

    # A keyed void element closes at once, so the outer outlet written after
    # it stays under the outer div and does not follow the void key.
    renamed_void = _slot_keys_in_outlet_order(*_direct_definition_root(source, inner_key="a", void_key="w"))
    assert renamed_void == keys


def test_direct_capture_leaves_unkeyed_slots_without_a_synthetic_key() -> None:
    template = _direct_definition_template('<div><c-slot name="body" /></div>')
    assert '<slot v-if="$citryPrepared.selectedSlots[' in template
    assert ':key="' not in template


def test_direct_capture_keys_slots_under_a_keyed_dynamic_element() -> None:
    source = """<c-element c-is="'section'" #c-key="element_key"><c-slot name="body" /></c-element>"""
    template, prepared_data = _direct_definition_root(source, element_key="first")

    # The outlet inside the keyed dynamic element carries its own key.
    keys = _slot_keys_in_outlet_order(template, prepared_data)
    assert len(keys) == 1
    # That key follows the dynamic element's key value.
    assert _slot_keys_in_outlet_order(*_direct_definition_root(source, element_key="second")) != keys


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

    assert ':key="JSON.stringify([$citryPrepared.citryKeyInner, 0])"' in template
    assert ':key="JSON.stringify([$citryPrepared.citryKeyInner, 1])"' in template
    assert ':key="JSON.stringify([$citryPrepared.citryKeyOuter, 0])"' in template


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


def test_authored_text_plan_validator_binds_utf8_spans_and_compiler_source() -> None:
    source = "<p>éX</p>"
    encoded = source.encode("utf-8")
    source_hash = hashlib.sha256(encoded).hexdigest()
    plan = {
        "source": "transformedTemplate",
        "sourceSha256": source_hash,
        "originalSourceSha256": source_hash,
        "status": "unsupported",
        "reasonCode": "atelier_text_mismatch",
        "actions": [
            {
                "type": "rewrite",
                "sourceStart": 3,
                "sourceEnd": 6,
                "originalStart": 3,
                "originalEnd": 6,
                "rule": "condense.whitespace",
                "content": "é Y",
            }
        ],
    }
    response = {
        "compiler": {"name": "vize_atelier_dom", "version": "0.420.0+citry.2"},
        "transformedTemplate": source,
        "transformedSourceSha256": source_hash,
        "authoredTextPlan": plan,
    }
    validated = vue_compiler._validate_authored_text_plan(response, source)
    assert validated.status == "unsupported"
    assert validated.actions[0].source_start == 3
    assert validated.actions[0].source_end == len("<p>éX".encode())
    assert validated.actions[0].original_start == 3
    assert validated.actions[0].original_end == len("<p>éX".encode())

    complete = {
        **response,
        "authoredTextPlan": {
            "source": "transformedTemplate",
            "sourceSha256": source_hash,
            "originalSourceSha256": source_hash,
            "status": "complete",
            "actions": [],
        },
    }
    assert vue_compiler._validate_authored_text_plan(complete, source).status == "complete"

    malformed = {
        **response,
        "authoredTextPlan": {**plan, "actions": [{**plan["actions"][0], "sourceStart": True}]},
    }
    with pytest.raises(RuntimeError, match="invalid spans"):
        vue_compiler._validate_authored_text_plan(malformed, source)

    split_character = {
        **response,
        "authoredTextPlan": {
            **plan,
            "actions": [{**plan["actions"][0], "sourceStart": 4}],
        },
    }
    with pytest.raises(RuntimeError, match="splits a UTF-8 character"):
        vue_compiler._validate_authored_text_plan(split_character, source)

    mismatched_hash = {**response, "transformedSourceSha256": "0" * 64}
    with pytest.raises(RuntimeError, match="hash"):
        vue_compiler._validate_authored_text_plan(mismatched_hash, source)

    overlap = {
        **response,
        "authoredTextPlan": {
            **plan,
            "actions": [
                *plan["actions"],
                {
                    "type": "drop",
                    "sourceStart": 5,
                    "sourceEnd": 6,
                    "rule": "condense.drop-whitespace",
                },
            ],
        },
    }
    with pytest.raises(RuntimeError, match="invalid spans or rule"):
        vue_compiler._validate_authored_text_plan(overlap, source)

    wrong_original_span = {
        **response,
        "authoredTextPlan": {
            **plan,
            "actions": [{**plan["actions"][0], "originalEnd": 5}],
        },
    }
    with pytest.raises(RuntimeError, match="does not map"):
        vue_compiler._validate_authored_text_plan(wrong_original_span, source)

    wrong_original_hash = {
        **response,
        "authoredTextPlan": {**plan, "originalSourceSha256": "0" * 64},
    }
    with pytest.raises(RuntimeError, match="targets a different source"):
        vue_compiler._validate_authored_text_plan(wrong_original_hash, source)


def test_hydration_plan_changes_the_compiled_identity() -> None:
    response: dict[str, object] = {"transformedSourceSha256": "source", "codeSha256": "code"}
    base = vue_compiler._compiled_content_id("request", response, "", "", (), ())
    with_plan = {**response, "hydrationPlan": {"status": "complete", "anchors": [], "elements": []}}
    assert base != vue_compiler._compiled_content_id("request", with_plan, "", "", (), ())


def _hydration_response(source: str, plan: dict[str, object]) -> dict[str, object]:
    source_hash = hashlib.sha256(source.encode()).hexdigest()
    return {
        "transformedTemplate": source,
        "transformedSourceSha256": source_hash,
        "hydrationPlan": {
            "source": "transformedTemplate",
            "sourceSha256": source_hash,
            "originalSourceSha256": source_hash,
            **plan,
        },
    }


def test_hydration_plan_validator_reads_facts_and_rejects_malformed_records() -> None:
    source = '<é v-if="a" :title="t"></é>'
    opening_end = len('<é v-if="a" :title="t">'.encode())
    title_start = len('<é v-if="a" '.encode())
    attribute = {
        "kind": "bind",
        "name": "title",
        "propKey": "title",
        "hydration": "checked",
        "sourceStart": title_start,
        "sourceEnd": opening_end - 1,
        "originalStart": title_start,
        "originalEnd": opening_end - 1,
    }
    element = {
        "vnode": "element",
        "tag": "é",
        "sourceStart": 0,
        "sourceEnd": opening_end,
        "originalStart": 0,
        "originalEnd": opening_end,
        "path": ["i:0:c3a9"],
        "patchFlag": 0,
        "dynamicProps": None,
        "attributes": [attribute],
    }
    anchor = {
        "kind": "comment",
        "origin": "v-if",
        "comment": "v-if",
        "sourceStart": 0,
        "sourceEnd": opening_end,
        "originalStart": 0,
        "originalEnd": opening_end,
        "path": ["i:0:c3a9"],
    }
    response = _hydration_response(source, {"status": "complete", "anchors": [anchor], "elements": [element]})
    plan = vue_compiler._validate_hydration_plan(response, source)
    assert plan.status == "complete"
    assert plan.anchors[0].comment == "v-if"
    assert plan.anchors[0].path == ("i:0:c3a9",)
    assert plan.elements[0].attributes[0].prop_key == "title"
    assert plan.elements[0].attributes[0].original_end == opening_end - 1

    # A compiler-inserted attribute has no compiler-input span.
    inserted = {key: value for key, value in attribute.items() if not key.startswith("original")}
    inserted_response = _hydration_response(
        source,
        {"status": "complete", "anchors": [], "elements": [{**element, "attributes": [inserted]}]},
    )
    assert (
        vue_compiler._validate_hydration_plan(inserted_response, source).elements[0].attributes[0].original_start
        is None
    )

    unsupported = _hydration_response(
        source, {"status": "unsupported", "reasonCode": "unsupported_render_shape", "anchors": [], "elements": []}
    )
    assert vue_compiler._validate_hydration_plan(unsupported, source).reason_code == "unsupported_render_shape"

    malformed: list[tuple[dict[str, object], str]] = [
        (
            {"status": "unsupported", "reasonCode": "unsupported_render_shape", "anchors": [anchor], "elements": []},
            "carries facts",
        ),
        ({"status": "unsupported", "reasonCode": "guess", "anchors": [], "elements": []}, "unsupported reason"),
        ({"status": "complete", "anchors": [{**anchor, "origin": "v-for"}], "elements": []}, "anchor"),
        ({"status": "complete", "anchors": [{**anchor, "comment": ""}], "elements": []}, "anchor"),
        ({"status": "complete", "anchors": [{**anchor, "sourceEnd": 999}], "elements": []}, "source span"),
        ({"status": "complete", "anchors": [{**anchor, "path": [1]}], "elements": []}, "element path"),
        (
            {
                "status": "complete",
                "anchors": [],
                "elements": [{**element, "attributes": [{**attribute, "originalStart": 1}]}],
            },
            "does not map",
        ),
        (
            {
                "status": "complete",
                "anchors": [],
                "elements": [{**element, "attributes": [{**attribute, "hydration": "maybe"}]}],
            },
            "attribute",
        ),
        ({"status": "complete", "anchors": [], "elements": [{**element, "dynamicProps": [1]}]}, "dynamic props"),
    ]
    for plan_fields, message in malformed:
        with pytest.raises(RuntimeError, match=message):
            vue_compiler._validate_hydration_plan(_hydration_response(source, plan_fields), source)
    wrong_original = {**response, "hydrationPlan": {**response["hydrationPlan"], "originalSourceSha256": "0" * 64}}  # type: ignore[dict-item]
    with pytest.raises(RuntimeError, match="different source"):
        vue_compiler._validate_hydration_plan(wrong_original, source)


def test_native_compiler_reports_where_the_render_creates_hydration_markers() -> None:
    template = (
        '<ul><li v-for="row in $citryPrepared.rows" :key="row.id" :aria-expanded="row.open">'
        '{{ row.label }}</li></ul><p v-if="$citryPrepared.empty">none</p>'
    )
    with NativeCompiler() as compiler:
        plan = compiler.compile(template, type_key="Rows").hydration_plan
    assert plan is not None
    assert plan.status == "complete"
    encoded = template.encode()
    assert [(item.kind, item.origin, item.comment) for item in plan.anchors] == [
        ("fragment", "root", None),
        ("fragment", "v-for", None),
        ("comment", "v-if", "v-if"),
    ]
    loop = plan.anchors[1]
    assert encoded[loop.original_start : loop.original_end].startswith(b"<li v-for=")
    row = plan.elements[1]
    assert row.tag == "li"
    assert row.dynamic_props == ("aria-expanded",)
    assert [(item.kind, item.prop_key, item.hydration) for item in row.attributes] == [
        ("structural", None, "none"),
        ("reserved", "key", "none"),
        ("bind", "aria-expanded", "patched"),
    ]


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
        '<ul><li v-for="$citryPrepared in $citryPrepared.citryLoop0" '
        'v-bind="$citryPrepared.citryAttrs0">{{ $citryPrepared.citryText0 }}</li></ul>'
    )
    opening = '<li v-for="$citryPrepared in $citryPrepared.citryLoop0" v-bind="$citryPrepared.citryAttrs0">'
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
    assert "_renderList(_ctx.$citryPrepared.citryLoop0, ($citryPrepared) =>" in compiled.javascript
    assert "$citryPrepared.citryAttrs0" in compiled.javascript
    assert "$citryPrepared.citryText0" in compiled.javascript


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
    assert "{{ $citryPrepared['citryTextDanger'] }}" in root_template
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

    record = {"html": "<b>x</b>", "nodeCount": 1}
    assert manifest({"opaqueHtml": {"citryOpaque0": record}})["occurrences"][0]["preparedData"]["opaqueHtml"] == {
        "citryOpaque0": record
    }
    for malformed in (
        {},
        {"opaqueHtml": {}},
        {"opaqueHtml": {"citryOpaque0": {"html": "x", "nodeCount": 1, "extra": True}}},
        {"opaqueHtml": {"citryOpaque0": {"html": 1, "nodeCount": 1}}},
        {"opaqueHtml": {"citryOpaque0": {"html": "x"}}},
        {"opaqueHtml": {"citryOpaque0": {"html": "x", "nodeCount": -1}}},
        {"opaqueHtml": {"citryOpaque0": {"html": "x", "nodeCount": True}}},
        {"opaqueHtml": {"citryOpaque0": {"html": "", "nodeCount": 1}}},
    ):
        with pytest.raises(ValueError, match="opaque HTML"):
            manifest(malformed)

    # An opaque site whose origin is neither raw nor markup is rejected before its record is read.
    root = PreparedOccurrence(
        "root", "Root", "root-def", {}, {"opaqueHtml": {"citryOpaque0": {"html": "<b>x</b>"}}}, None, None
    )
    for origin in ("grouped", "unknown"):
        unknown_origin_asset = replace(asset, opaque_html_sites=({**site, "origin": origin},))
        with pytest.raises(ValueError, match="opaque HTML site is invalid"):
            prepared_manifest(
                app_id="app", view=PreparedView(0, "root", (root,), (definition,)), assets=(unknown_origin_asset,)
            )


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
    assert "window.__citryRuntime.compilerRuntime" in compiled.javascript
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

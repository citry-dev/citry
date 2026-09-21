"""
Secondary behavioral coverage for the prepared Vue runtime boundary.

The larger migration tests exercise complete component trees.  These tests
cover the small public-facing contracts around freezing prepared data,
publishing assets, validating serialization hosts, and selecting the bounded
leaf program.  They intentionally test both accepted values and the rejection
paths that protect the browser-facing protocol.
"""

from __future__ import annotations

import re
from types import SimpleNamespace

import pytest

from citry import Citry, Component
from citry._vue.capture import PreparedAttribute, PreparedElementOpen, render_prepared_direct
from citry._vue.events import (
    DirectVueEventsProducer,
    _BuiltInPreparationMetadata,
    default_events_producer,
    definition_bundle,
    style_asset,
)
from citry._vue.leaf_program import (
    PreparedLeafProgram,
    _source_target,
    _validate_data_attrs,
    _validate_open,
    static_leaf_parts,
    typed_leaf_parts,
)
from citry._vue.prepared import (
    ComponentCall,
    PreparedDefinition,
    PreparedMarker,
    PreparedOccurrence,
    PreparedView,
    TextBinding,
)
from citry._vue.serialization import VueSerializationPlan, _HostValidator, _record_component_has_js
from citry.citry_context import CitryContext
from citry.citry_render import CitryRender
from citry.ext.dependencies.types import DependencyRecord, Script, Style


def _root_view() -> tuple[PreparedDefinition, PreparedOccurrence]:
    definition = PreparedDefinition("root-def", "Root", (TextBinding("citryText0"),))
    occurrence = PreparedOccurrence("root", "Root", "root-def", {}, {}, None, None)
    return definition, occurrence


def test_builder_owned_occurrence_detaches_server_data_but_adopts_prepared_data() -> None:
    server_data = {"nested": [1]}
    prepared_data = {"citryText0": "ready"}
    occurrence = PreparedOccurrence._from_assembly("root", "Root", "root-def", server_data, prepared_data, None, None)

    server_data["nested"].append(2)
    assert occurrence.server_data == {"nested": [1]}
    assert occurrence.prepared_data is prepared_data

    with pytest.raises(ValueError, match="root occurrence"):
        PreparedOccurrence._from_assembly("root", "Root", "root-def", {}, {}, None, "unexpected")
    with pytest.raises(TypeError, match="builder-owned prepared_data"):
        PreparedOccurrence._from_assembly(
            "root",
            "Root",
            "root-def",
            {},
            {1: "unsafe"},
            None,
            None,  # type: ignore[dict-item]
        )


def test_prepared_view_rejects_duplicate_identity_and_invalid_marker_order() -> None:
    definition, root = _root_view()
    duplicate_root = PreparedOccurrence("root", "Root", "root-def", {}, {}, None, None)

    with pytest.raises(ValueError, match="duplicate prepared occurrence"):
        PreparedView(0, "root", (root, duplicate_root), (definition,))

    with pytest.raises(ValueError, match="duplicate prepared definition"):
        PreparedView(0, "root", (root,), (definition, definition))

    with pytest.raises(ValueError, match="missing"):
        PreparedView(0, "missing", (root,), (definition,))

    child_definition = PreparedDefinition("child-def", "Child", ())
    root_with_child = PreparedDefinition("root-def", "Root", (ComponentCall("child"),))
    root_with_child_occurrence = PreparedOccurrence(
        "root",
        "Root",
        "root-def",
        {},
        {"calls": {"child": {"id": "child", "key": "child", "parentId": "root"}}},
        None,
        None,
    )
    child = PreparedOccurrence("child", "Child", "child-def", {}, {}, "root", "child")
    with pytest.raises(ValueError, match="strictly sorted"):
        PreparedView(
            0,
            "root",
            (root_with_child_occurrence, child),
            (root_with_child, child_definition),
            (PreparedMarker("root", "z", "root"), PreparedMarker("root", "a", "child")),
        )


def test_built_in_metadata_rejects_class_replacement_before_and_after_resolution() -> None:
    registry = Citry(autodiscover=False)

    class Root(Component):
        citry = registry
        template = "<p>root</p>"

    metadata = _BuiltInPreparationMetadata(registry, lambda type_key: f"fallback-{type_key}")
    assert metadata.resolve(Root.class_id, Root) == metadata.tags[Root.class_id]

    with pytest.raises(ValueError, match="class changed"):
        metadata.resolve(Root.class_id, Component)

    type.__setattr__(Root, "__name__", "RenamedRoot")
    try:
        with pytest.raises(ValueError, match="registry metadata changed"):
            metadata.validate()
    finally:
        type.__setattr__(Root, "__name__", "Root")


def test_events_producer_requires_request_credentials_and_typed_render() -> None:
    registry = Citry(autodiscover=False)
    producer = default_events_producer(registry)
    render = CitryRender(parts=[], context=CitryContext(), render_target="static")

    from citry.ext.events.results import RenderEncodingContext

    missing_headers = RenderEncodingContext(registry, None, object(), "http", "vue-prepared/1", headers={})
    with pytest.raises(ValueError, match="current app"):
        producer(render, missing_headers)

    valid_headers = RenderEncodingContext(
        registry,
        None,
        object(),
        "http",
        "vue-prepared/1",
        headers={
            "X-Citry-Vue-App": "app",
            "X-Citry-Vue-Occurrence": "root",
            "X-Citry-Vue-Revision": "3",
        },
    )
    with pytest.raises(TypeError, match="typed prepared"):
        producer(render, valid_headers)

    assert default_events_producer(registry) is producer
    assert definition_bundle(registry, "missing") is None
    assert style_asset(registry, "missing") is None


def test_direct_producer_rejects_untyped_render_before_preparation() -> None:
    registry = Citry(autodiscover=False)
    producer = DirectVueEventsProducer(
        tag_for_type=lambda type_key: f"citry-{type_key.lower()}",
        compile_view=lambda _assembly: {},
        request_scope=lambda _renderable, _context: ("app", 1, 0, "root"),
        publish_bundle=lambda _digest, _content: None,
    )
    render = CitryRender(parts=[], context=CitryContext(), render_target="static")

    with pytest.raises(TypeError, match="typed prepared"):
        producer(render, SimpleNamespace(citry=registry))


def test_host_validator_treats_entities_references_and_comments_as_content() -> None:
    validator = _HostValidator("mount")
    validator.feed('<div id="mount">&amp;&#x41;<!--comment--></div>')
    validator.close()

    assert validator.count == 1
    assert not validator.empty
    assert validator.valid_attrs

    invalid = _HostValidator("mount")
    invalid.feed('<div id="mount"/>')
    invalid.close()
    assert invalid.count == 1
    assert not invalid.valid_attrs


def test_vue_serialization_plan_validates_hook_output_and_can_defer_assets() -> None:
    context = CitryContext()
    plan = VueSerializationPlan(
        shell_html='<div id="mount"></div>',
        host_id="mount",
        configuration="{}",
        scripts=(Script(content="globalThis.ready = true", wrap=False),),
        styles=(Style(content=".ready { color: red }"),),
        script_security=None,
        javascript_policy=None,
        render_context=context,
        validate_metadata=lambda: None,
    )
    output = plan.finalize('<div id="mount"></div>')
    assert "globalThis.ready = true" in output
    assert ".ready { color: red }" in output

    document = '<!doctype html><html><head><title>Page</title></head><body><div id="mount"></div></body></html>'
    output = plan.finalize(document)
    assert output.index(".ready { color: red }") < output.index("</head>")
    assert output.index("globalThis.ready = true") < output.rindex("</body>")
    assert output.index(".ready { color: red }") < output.index("globalThis.ready = true")

    with pytest.raises(ValueError, match="preserve exactly one"):
        plan.finalize('<div id="mount"><span></span></div>')

    deferred = VueSerializationPlan(
        '<div id="mount"></div>',
        "mount",
        "{}",
        (Script(content="should not be emitted", wrap=False),),
        (),
        None,
        None,
        context,
        lambda: None,
        deferred_to_dependency_manager=True,
    )
    assert deferred.finalize('<div id="mount"></div>') == '<div id="mount"></div>'


def test_explicit_id_generator_makes_vue_app_id_deterministic() -> None:
    app = Citry(autodiscover=False, id_generator=lambda: "snapshot")

    class Page(Component):
        citry = app
        template = "<button :title=\"'ready'\">ready</button>"

    first = Page().render().serialize()
    second = Page().render().serialize()

    assert first == second
    app_ids = re.findall(r'"appId":"([0-9a-f]{32})"', first)
    assert len(app_ids) == 1


def test_default_vue_app_ids_remain_unique_between_serializations() -> None:
    app = Citry(autodiscover=False)

    class Page(Component):
        citry = app
        template = "<button :title=\"'ready'\">ready</button>"

    first = Page().render().serialize()
    second = Page().render().serialize()

    first_id = re.search(r'"appId":"([0-9a-f]{32})"', first)
    second_id = re.search(r'"appId":"([0-9a-f]{32})"', second)
    assert first_id is not None
    assert second_id is not None
    assert first_id.group(1) != second_id.group(1)


def test_serialization_js_detection_is_conservative_without_component_identity() -> None:
    render_without_component = CitryRender(parts=[], context=CitryContext())
    record = DependencyRecord("Unknown", "render", component_class=None)
    assert _record_component_has_js(record, render_without_component)

    registry = Citry(autodiscover=False)

    class Static(Component):
        citry = registry
        template = "<p>static</p>"

    render = render_prepared_direct(Static())
    resolved = DependencyRecord(Static.class_id, render.frame.render_id or "render", Static)
    assert not _record_component_has_js(resolved, render)


def test_leaf_program_materializes_reusable_attribute_and_text_data() -> None:
    registry = Citry(autodiscover=False)

    class Card(Component):
        citry = registry
        template = '<article c-title="title">{{ label }}</article>'

        def template_data(self, kwargs, slots):
            return {"title": "card", "label": "ready"}

    rendered = render_prepared_direct(Card())
    [program] = [part for part in rendered.parts if isinstance(part, PreparedLeafProgram)]
    assert static_leaf_parts(program) == ['<article title="card">', "ready", "</article>"]
    typed = typed_leaf_parts(program)
    assert [type(part).__name__ for part in typed] == [
        "PreparedElementOpen",
        "PreparedTextValue",
        "PreparedStaticRun",
    ]
    assert static_leaf_parts(program) == ['<article title="card">', "ready", "</article>"]


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("key", "key"),
        (":title.once", "title"),
        ("v-bind:aria-label", "aria-label"),
        ("data-role", "data-role"),
        ("not valid", None),
    ],
)
def test_leaf_attribute_projection_keeps_vue_syntax_out_of_python_data(name: str, expected: str | None) -> None:
    assert _source_target(name) == expected
    if expected is None:
        return
    assert _validate_data_attrs({expected: "value"}, tag="button") is None

    if expected == "title":
        value = PreparedElementOpen(
            source="<button>",
            span=(0, 8),
            tag="button",
            attrs=(
                PreparedAttribute(":title", "source", (0, 1), ":title"),
                PreparedAttribute("title", "data", (1, 2), "x"),
            ),
            is_void=False,
            is_self_closing=False,
            element_metadata=(),
        )
        assert _validate_open(value) is not None

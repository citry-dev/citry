from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from citry import Citry, Component, Extension
from citry._simple_runtime import SimpleRender
from citry._vue.capture import render_prepared_direct
from citry._vue.compiler import HELPER_CONTRACT
from citry._vue.direct_capture import Assembly, UnsupportedPreparedView, assemble_typed_render
from citry._vue.prepared import ComponentCall, PreparedDefinition, PreparedMarker, PreparedOccurrence, PreparedView
from citry._vue.protocol import DefinitionAsset, prepared_manifest
from citry.citry_render import CitryRender
from citry.ext.events import actions
from citry.ext.events.renderers import dispatcher_for
from citry.ext.events.results import RenderEncodingContext, encode_actions

if TYPE_CHECKING:
    from collections.abc import Iterator

    from citry.citry_element import CitryElement


def _tag_for_type(type_key: str) -> str:
    return f"x-{type_key.lower().replace('_', '-')}"


def _assemble(element: CitryElement) -> Assembly:
    return assemble_typed_render(render_prepared_direct(element), revision=0, tag_for_type=_tag_for_type)


def _nested_renders(rendered: CitryRender) -> Iterator[CitryRender]:
    yield rendered
    for part in rendered.parts:
        if isinstance(part, CitryRender):
            yield from _nested_renders(part)


def _encode_marker_response(
    app: Citry, caller: type[Component], payload: CitryElement | CitryRender
) -> dict[str, object]:
    dispatcher = dispatcher_for(app)
    handler = app.extensions.get_extension("events").resolve(caller).handlers["refresh"]
    context = RenderEncodingContext(
        app,
        "caller_occurrence",
        handler,
        "http",
        "vue-prepared/1",
        headers={
            "x-citry-vue-app": "marker-app",
            "x-citry-vue-occurrence": "caller_occurrence",
            "x-citry-vue-revision": "4",
        },
    )
    [encoded] = encode_actions(
        [actions.Render(payload, target="mark:summary")],
        instance_id="caller_occurrence",
        handler="refresh",
        render_encoder=dispatcher._render_encoders["vue-prepared/1"],
        render_context=context,
    )
    return encoded


def test_mark_only_static_component_serializes_without_client_runtime() -> None:
    app = Citry(autodiscover=False)

    class StaticPage(Component):
        citry = app
        template = '<main><c-mark name="Summary"><b>static</b></c-mark></main>'

    html = StaticPage().render().serialize()

    assert "<main" in html
    assert "<b" in html
    assert "static</b>" in html
    assert "<script" not in html.lower()
    assert "citrystable" not in html.lower()
    assert "citry-events" not in html.lower()


def test_interactive_parent_retains_case_sensitive_marker_aliases() -> None:
    app = Citry(autodiscover=False)

    class InteractivePage(Component):
        citry = app
        template = (
            '<main><c-Mark name="Summary"><b>upper</b></c-Mark><c-mark name="summary"><i>lower</i></c-mark></main>'
        )

        def js_data(self, kwargs, slots):
            return {"ready": True}

    assembly = _assemble(InteractivePage())
    root = next(item for item in assembly.view.occurrences if item.id == assembly.view.root_id)

    assert root.server_data == {"ready": True}
    assert [(item.owner_id, item.name) for item in assembly.view.markers] == [
        (root.id, "Summary"),
        (root.id, "summary"),
    ]
    assert all(
        next(item for item in assembly.view.occurrences if item.id == marker.occurrence_id).type_key
        == app.get("mark").class_id
        for marker in assembly.view.markers
    )


def test_supplied_fill_marker_keeps_caller_owner_and_receiver_parent() -> None:
    app = Citry(autodiscover=False)

    class Receiver(Component):
        citry = app
        template = "<section><c-slot /></section>"

    class Caller(Component):
        citry = app
        template = (
            '<c-Receiver><c-fill name="default"><c-mark name="caller"><b>supplied</b></c-mark></c-fill></c-Receiver>'
        )

        def js_data(self, kwargs, slots):
            return {"ready": True}

    assembly = _assemble(Caller())
    root = next(item for item in assembly.view.occurrences if item.id == assembly.view.root_id)
    receiver = next(item for item in assembly.view.occurrences if item.type_key == Receiver.class_id)
    marker = assembly.view.markers[0]
    marker_occurrence = next(item for item in assembly.view.occurrences if item.id == marker.occurrence_id)

    assert marker.owner_id == root.id
    assert marker.name == "caller"
    assert marker_occurrence.parent_id == receiver.id
    assert marker_occurrence.parent_id != marker.owner_id


def test_cached_parent_with_marker_uses_live_fallback_and_retains_alias() -> None:
    app = Citry(autodiscover=False)
    calls: list[str] = []

    class CachedPage(Component):
        citry = app
        template = '<main><c-mark name="cached"><b>{{ label }}</b></c-mark></main>'

        class Cache:
            enabled = True

        def template_data(self, kwargs, slots):
            calls.append("data")
            return {"label": "live"}

    first = _assemble(CachedPage())
    second = _assemble(CachedPage())

    assert calls == ["data", "data"]
    assert not app.cache._data
    for assembly in (first, second):
        assert [(marker.name, marker.owner_id) for marker in assembly.view.markers] == [
            ("cached", assembly.view.root_id)
        ]


@pytest.mark.parametrize(
    ("template", "expected_error", "message"),
    [
        ('<c-mark name="9bad">x</c-mark>', ValueError, "name must match"),
        ("<c-mark />", SyntaxError, "must have one of the following attributes: 'name', 'c-name'"),
        (
            '<c-mark name="valid" title="extra" />',
            SyntaxError,
            "Found invalid attributes: title",
        ),
        (
            '<c-mark :name="dynamic">x</c-mark>',
            SyntaxError,
            "must have one of the following attributes: 'name', 'c-name'",
        ),
        ('<c-mark c-bind="attrs">x</c-mark>', ValueError, "directly authored literal 'name'"),
        (
            '<c-mark name="valid"><c-fill name="aside">x</c-fill></c-mark>',
            SyntaxError,
            "does not allow a slot named 'aside'",
        ),
        ('<c-component c-is="target" />', TypeError, "Dynamic component selection cannot select <c-mark>"),
    ],
)
def test_mark_rejects_invalid_name_sources_and_named_fills(
    template: str, expected_error: type[Exception], message: str
) -> None:
    app = Citry(autodiscover=False)
    attrs: dict[str, object] = {"citry": app, "template": template}
    if template == '<c-component c-is="target" />':

        def template_data(self, kwargs, slots):
            return {"target": app.get("mark")}

        attrs["template_data"] = template_data

    with pytest.raises(expected_error, match=message):
        type("InvalidMarkerInput", (Component,), attrs)().render()


def test_same_marker_name_is_valid_for_different_owners() -> None:
    app = Citry(autodiscover=False)

    class FirstOwner(Component):
        citry = app
        template = '<section><c-mark name="shared"><b>first</b></c-mark></section>'

    class SecondOwner(Component):
        citry = app
        template = '<section><c-mark name="shared"><b>second</b></c-mark></section>'

    class Page(Component):
        citry = app
        template = "<main><c-FirstOwner /><c-SecondOwner /></main>"

    assembly = _assemble(Page())
    types_by_id = {item.id: item.type_key for item in assembly.view.occurrences}

    assert {(types_by_id[marker.owner_id], marker.name) for marker in assembly.view.markers} == {
        (FirstOwner.class_id, "shared"),
        (SecondOwner.class_id, "shared"),
    }


def test_duplicate_marker_names_within_one_owner_reject_prepared_assembly() -> None:
    app = Citry(autodiscover=False)

    class DuplicateOwner(Component):
        citry = app
        template = (
            '<main><c-mark name="shared"><b>first</b></c-mark><c-mark name="shared"><b>second</b></c-mark></main>'
        )

    with pytest.raises(UnsupportedPreparedView, match="duplicated within its lexical owner"):
        _assemble(DuplicateOwner())


def test_default_dispatcher_encodes_marker_render_once_with_nested_alias() -> None:
    app = Citry(secret="vue-marker-default-dispatcher-secret", autodiscover=False)  # noqa: S106
    renders: list[str] = []

    class Payload(Component):
        citry = app
        template = '<section><c-mark name="inner"><b>{{ label }}</b></c-mark></section>'

        def template_data(self, kwargs, slots):
            renders.append("template_data")
            return {"label": kwargs.get("label", "rendered")}

    class Caller(Component):
        citry = app
        template = "<button>caller</button>"

        class Events:
            def refresh(self):
                return None

    dispatcher = dispatcher_for(app)
    info = app.extensions.get_extension("events").resolve(Caller)
    handler = info.handlers["refresh"]
    context = RenderEncodingContext(
        app,
        "caller_occurrence",
        handler,
        "http",
        "vue-prepared/1",
        headers={
            "x-citry-vue-app": "marker-app",
            "x-citry-vue-occurrence": "caller_occurrence",
            "x-citry-vue-revision": "4",
        },
    )

    [encoded] = encode_actions(
        [actions.Render(Payload(label="one"), target="mark:summary")],
        instance_id="caller_occurrence",
        handler="refresh",
        render_encoder=dispatcher._render_encoders["vue-prepared/1"],
        render_context=context,
    )

    prepared = encoded["prepared"]
    assert encoded["target"] == "mark:caller_occurrence:summary"
    assert prepared["revision"] == 5
    assert prepared["baseRevision"] == 4
    assert renders == ["template_data"]
    occurrences = {item["id"]: item for item in prepared["occurrences"]}
    root = occurrences[prepared["rootId"]]
    assert root["typeKey"] == app.get("mark").class_id
    assert len(prepared["markers"]) == 1
    marker = prepared["markers"][0]
    assert marker["name"] == "inner"
    assert occurrences[marker["ownerId"]]["typeKey"] == Payload.class_id
    assert occurrences[marker["occurrenceId"]]["typeKey"] == app.get("mark").class_id
    assert marker["occurrenceId"] != root["id"]


@pytest.mark.parametrize("return_render", [False, True], ids=["deferred-element", "rendered-hook-result"])
def test_default_dispatcher_wraps_prepared_nested_payload_without_replaying_hook(return_render: bool) -> None:
    app = Citry(secret="vue-marker-prepared-payload-secret", autodiscover=False)  # noqa: S106
    hook_render_ids: list[str | None] = []

    class Payload(Component):
        citry = app
        template = "<p>unused template</p>"

        class Events:
            def refresh(self):
                return None

        def on_render(self):
            hook_render_ids.append(self.id)
            marker = app.get("mark")(name="from-hook", slots={"default": "nested"})
            return marker.render() if return_render else marker

    class Holder(Component):
        citry = app
        template = "<main><c-Payload /></main>"

    class Caller(Component):
        citry = app
        template = "<button>caller</button>"

        class Events:
            def refresh(self):
                return None

    holder_render = render_prepared_direct(Holder())
    payload_render = next(
        item
        for item in _nested_renders(holder_render)
        if item.context.component is not None and type(item.context.component) is Payload
    )
    prepared_metadata = payload_render.frame.prepared_occurrence
    assert prepared_metadata is not None
    original_call = prepared_metadata.call
    assert original_call is not None
    original_render_id = payload_render.frame.render_id
    assert original_render_id is not None
    assert hook_render_ids == [original_render_id]

    encoded = _encode_marker_response(app, Caller, payload_render)
    prepared = encoded["prepared"]
    assert encoded["target"] == "mark:caller_occurrence:summary"
    assert payload_render.frame.prepared_occurrence is prepared_metadata
    assert payload_render.frame.prepared_occurrence.call is original_call
    assert hook_render_ids == [original_render_id]

    occurrences = {item["id"]: item for item in prepared["occurrences"]}
    payload_occurrence = next(item for item in occurrences.values() if item["typeKey"] == Payload.class_id)
    wrapper = occurrences[prepared["rootId"]]
    assert wrapper["typeKey"] == app.get("mark").class_id
    assert payload_occurrence["renderId"] == original_render_id
    assert payload_occurrence["eventContext"]["serverRenderId"] == original_render_id
    assert [(item["name"], item["ownerId"]) for item in prepared["markers"]] == [
        ("from-hook", payload_occurrence["id"])
    ]
    assert prepared["markers"][0]["occurrenceId"] != wrapper["id"]


def test_extension_hook_marker_inside_synthetic_wrapper_keeps_its_alias() -> None:
    class AuthoredMarkDuringReplacement(Extension):
        name = "authored_mark_during_replacement"

        def on_component_rendered(self, ctx):
            mark_class = ctx.citry.get("mark")
            if type(ctx.component) is not mark_class:
                return None
            is_replacement = getattr(ctx.component, "_citry_mark_replacement", False)
            if is_replacement:
                return mark_class(name="hook-authored", slots={"default": "from extension"}).render()
            return None

    app = Citry(
        secret="vue-marker-wrapper-hook-secret",  # noqa: S106
        autodiscover=False,
        extensions=[AuthoredMarkDuringReplacement],
    )

    class Payload(Component):
        citry = app
        template = "<p>payload</p>"

    class Caller(Component):
        citry = app
        template = "<button>caller</button>"

        class Events:
            def refresh(self):
                return None

    prepared = _encode_marker_response(app, Caller, Payload())["prepared"]
    occurrences = {item["id"]: item for item in prepared["occurrences"]}
    wrapper = occurrences[prepared["rootId"]]

    assert wrapper["typeKey"] == app.get("mark").class_id
    assert [(item["name"], item["ownerId"]) for item in prepared["markers"]] == [("hook-authored", wrapper["id"])]
    assert prepared["markers"][0]["occurrenceId"] != wrapper["id"]


def test_default_dispatcher_rejects_foreign_flattened_renders_and_keeps_local_transparent() -> None:
    app = Citry(secret="vue-marker-engine-identity-secret", autodiscover=False)  # noqa: S106
    foreign_app = Citry(autodiscover=False)

    class LocalTransparent(Component):
        citry = app
        transparent = True
        template = "<b>local</b>"

    class ForeignTransparent(Component):
        citry = foreign_app
        transparent = True
        template = "<b>foreign</b>"

    class LocalCaller(Component):
        citry = app
        template = "<button>caller</button>"

        class Events:
            def refresh(self):
                return None

    local_transparent = render_prepared_direct(LocalTransparent())

    class LocalPayload(Component):
        citry = app
        template = "<section>{{ interior }}</section>"

        def template_data(self, kwargs, slots):
            return {"interior": local_transparent}

    local_response = _encode_marker_response(app, LocalCaller, LocalPayload())
    local_types = {item["typeKey"] for item in local_response["prepared"]["occurrences"]}
    assert LocalPayload.class_id in local_types
    assert LocalTransparent.class_id not in local_types

    foreign_transparent = render_prepared_direct(ForeignTransparent())

    class ForeignInteriorPayload(Component):
        citry = app
        template = "<section>{{ interior }}</section>"

        def template_data(self, kwargs, slots):
            return {"interior": foreign_transparent}

    with pytest.raises(
        UnsupportedPreparedView,
        match="prepared transparent render has no class in the encoding engine",
    ):
        _encode_marker_response(app, LocalCaller, ForeignInteriorPayload())

    class ForeignSimple(Component):
        citry = foreign_app
        simple = True
        template = "<em>foreign static interior</em>"

    class ForeignSimpleHost(Component):
        citry = foreign_app
        template = "<div>{{ child }}</div>"

        def template_data(self, kwargs, slots):
            return {"child": ForeignSimple()}

    foreign_simple_root = render_prepared_direct(ForeignSimpleHost())
    foreign_simple = next(item for item in _nested_renders(foreign_simple_root) if type(item) is SimpleRender)

    class ForeignSimplePayload(Component):
        citry = app
        template = "<section>{{ interior }}</section>"

        def template_data(self, kwargs, slots):
            return {"interior": foreign_simple}

    with pytest.raises(UnsupportedPreparedView, match="prepared simple render has no class in the encoding engine"):
        _encode_marker_response(app, LocalCaller, ForeignSimplePayload())


def _protocol_view(markers: tuple[PreparedMarker, ...] = ()) -> PreparedView:
    root_definition = PreparedDefinition(
        "root-definition",
        "Root",
        (ComponentCall("first"), ComponentCall("second")),
    )
    child_definition = PreparedDefinition("child-definition", "Child", ())
    root = PreparedOccurrence("root", "Root", root_definition.id, {}, {}, None, None)
    first = PreparedOccurrence("first", "Child", child_definition.id, {}, {}, "root", "place-first")
    second = PreparedOccurrence("second", "Child", child_definition.id, {}, {}, "root", "place-second")
    return PreparedView(
        0,
        root.id,
        (root, first, second),
        (root_definition, child_definition),
        markers,
    )


def _protocol_assets(view: PreparedView) -> tuple[DefinitionAsset, ...]:
    assets: list[DefinitionAsset] = []
    for index, definition in enumerate(view.definitions, start=1):
        digest = f"{index:064x}"
        assets.append(
            DefinitionAsset(
                definition.id,
                f"/definitions/{digest}.js",
                digest,
                "ordinary-vnodes/1",
                HELPER_CONTRACT,
                (),
                (),
            )
        )
    return tuple(assets)


def test_prepared_protocol_emits_empty_and_sorted_nonempty_marker_arrays() -> None:
    empty_view = _protocol_view()
    empty_manifest = prepared_manifest(app_id="app", view=empty_view, assets=_protocol_assets(empty_view))
    assert empty_manifest["markers"] == []

    markers = (
        PreparedMarker("root", "Alpha", "first"),
        PreparedMarker("root", "beta", "second"),
    )
    marked_view = _protocol_view(markers)
    manifest = prepared_manifest(app_id="app", view=marked_view, assets=_protocol_assets(marked_view))
    assert manifest["markers"] == [
        {"ownerId": "root", "name": "Alpha", "occurrenceId": "first"},
        {"ownerId": "root", "name": "beta", "occurrenceId": "second"},
    ]


@pytest.mark.parametrize(
    ("markers", "message"),
    [
        ((PreparedMarker("unknown", "shared", "first"),), "prepared marker metadata is invalid"),
        (
            (
                PreparedMarker("root", "shared", "first"),
                PreparedMarker("root", "shared", "second"),
            ),
            "prepared marker aliases must be unique",
        ),
    ],
)
def test_prepared_protocol_rejects_unknown_marker_owner_and_duplicate_alias(
    markers: tuple[PreparedMarker, ...], message: str
) -> None:
    valid = _protocol_view()
    invalid = PreparedView._from_assembly(
        valid.revision,
        valid.root_id,
        valid.occurrences,
        valid.definitions,
        markers,
    )

    with pytest.raises(ValueError, match=message):
        prepared_manifest(app_id="app", view=invalid, assets=_protocol_assets(valid))

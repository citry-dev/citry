from __future__ import annotations

import json
from dataclasses import replace

import pytest

from citry import Citry, Component, Extension, InMemoryCache
from citry._vue.capture import render_prepared
from citry._vue.direct import bind_nested_template, direct_render_scope, wrap_nested_template
from citry._vue.direct_capture import assemble_typed_render
from citry.citry_context import CitryContext
from citry.citry_render import CitryRender
from citry.ext.cache.artifact import (
    ArtifactDirectSlotPart,
    ArtifactFrame,
    CacheArtifactError,
    CachedRenderArtifact,
    _decode_artifact,
    _encode_artifact,
)
from citry.ext.cache.replay import _export_component_artifact, _replay_component_artifact


def _assembly(page_type: type[Component]):
    return assemble_typed_render(
        render_prepared(page_type()),
        revision=0,
        tag_for_type=lambda value: f"x-{value.lower().replace('_', '-')}",
    )


def test_nested_template_projects_once_per_insertion_with_lexical_bindings() -> None:
    app = Citry(secret="nested-template-test")  # noqa: S106 - deterministic signing key

    class Card(Component):
        citry = app
        template = "<article>{{ body }}</article>"

        def template_data(self, kwargs, slots):
            return {"body": kwargs["body"]}

    class Page(Component):
        citry = app

        class State:
            value: str = ""

        class Events:
            def save(self, state):
                return None

        template = (
            "<c-Card #c-key=\"'a'\" c-body=\"<button @c-click='save'>A</button>"
            "<input :c-value='save'>\" />"
            "<c-Card #c-key=\"'b'\" c-body=\"<button @c-click='save'>B</button>"
            "<input :c-value='save'>\" />"
        )

    assembly = _assembly(Page)
    page = next(item for item in assembly.view.occurrences if item.id == assembly.view.root_id)
    page_definition = assembly.compile_inputs[page.definition_id].template
    card_definitions = [value.template for key, value in assembly.compile_inputs.items() if key != page.definition_id]
    assert page_definition.count("<template v-slot:") == 2
    assert len({part.split("']", 1)[0] for part in page_definition.split("<template v-slot:['")[1:]}) == 2
    assert sum(value.count('<slot name="citrySlot') for value in card_definitions) == 2
    assert len(page.prepared_data["eventBindings"]) == 1
    assert len(page.prepared_data["controlBindings"]) == 1


def test_nested_template_component_cache_hit_keeps_lexical_event_owner() -> None:
    hits: list[tuple[str, str]] = []
    data_calls = {"page": 0, "card": 0}

    class CacheProbe(Extension):
        name = "nested_template_cache_probe"
        render_cache_mode = "stateless"
        render_cache_version = 1

        def on_component_cache_hit(self, ctx):
            hits.append((type(ctx.component).__name__, ctx.kind))

    app = Citry(secret="nested-template-cache-test", cache=InMemoryCache(), extensions=[CacheProbe])  # noqa: S106

    class Card(Component):
        citry = app
        template = "<article>{{ body }}</article>"

        def template_data(self, kwargs, slots):
            data_calls["card"] += 1
            return {"body": kwargs["body"]}

    class Page(Component):
        citry = app

        class Cache:
            enabled = True

        class Events:
            def save(self):
                return None

        template = "<c-Card c-body=\"<button v-text='label' @c-click='save'>save</button>\" />"

        def template_data(self, kwargs, slots):
            data_calls["page"] += 1
            return {}

        def js_data(self, kwargs, slots):
            return {"label": "page"}

    first = _assembly(Page)
    second = _assembly(Page)

    assert hits == [("Page", "component")]
    assert data_calls == {"page": 1, "card": 1}
    for assembly in (first, second):
        page = next(item for item in assembly.view.occurrences if item.id == assembly.view.root_id)
        [event] = page.prepared_data["eventBindings"].values()
        assert page.type_key == Page.class_id
        assert (event["event"], event["handler"]) == ("click", "save")
        assert "v-on:click" in assembly.compile_inputs[page.definition_id].template


def test_nested_template_inside_supplied_slot_cache_hit_keeps_lexical_event_owner() -> None:
    hits: list[tuple[str, str]] = []
    data_calls = {"shell": 0, "card": 0}

    class CacheProbe(Extension):
        name = "nested_slot_cache_probe"
        render_cache_mode = "stateless"
        render_cache_version = 1

        def on_component_cache_hit(self, ctx):
            hits.append((type(ctx.component).__name__, ctx.kind))

    app = Citry(secret="nested-slot-cache-test", cache=InMemoryCache(), extensions=[CacheProbe])  # noqa: S106

    class Card(Component):
        citry = app
        template = "<article>{{ body }}</article>"

        def template_data(self, kwargs, slots):
            data_calls["card"] += 1
            return {"body": kwargs["body"]}

    class Shell(Component):
        citry = app
        template = "<main><c-slot /></main>"

        class Cache:
            enabled = True

            def vary(self, kwargs, slots):
                return "fixed nested-slot fixture"

        def template_data(self, kwargs, slots):
            data_calls["shell"] += 1
            return {}

    class Page(Component):
        citry = app

        class Events:
            def save(self):
                return None

        template = (
            "<c-Shell><c-Card c-body=\"<button class='nested' v-text='label' @c-click='save'></button>\" /></c-Shell>"
        )

        def js_data(self, kwargs, slots):
            return {"label": "page"}

    first = _assembly(Page)
    second = _assembly(Page)

    assert hits == [("Shell", "component")]
    assert data_calls == {"shell": 1, "card": 1}
    for assembly in (first, second):
        page = next(item for item in assembly.view.occurrences if item.id == assembly.view.root_id)
        shell = next(item for item in assembly.view.occurrences if item.type_key == Shell.class_id)
        [event] = page.prepared_data["eventBindings"].values()
        assert (event["event"], event["handler"]) == ("click", "save")
        assert not shell.prepared_data.get("eventBindings")
        assert "v-on:click" in assembly.compile_inputs[page.definition_id].template


def _projection_artifact(kind: str) -> CachedRenderArtifact:
    child = ArtifactFrame(
        instance=None, class_id=None, class_name=None, is_component_root=False, root_markers=(), parts=()
    )
    root = ArtifactFrame(
        instance=0,
        class_id="tests.Page",
        class_name="Page",
        is_component_root=True,
        root_markers=(),
        parts=(
            ArtifactDirectSlotPart(
                frame=1,
                execution=1,
                parent_execution=None,
                external_parent_execution=False,
                lexical_instance=0,
                lexical_parent_depth=None,
                receiver_instance=0,
                receiver_parent_depth=None,
                kind=kind,
                public_name="c-body",
                fill_source='<c-Card c-body="x" />',
                source="x",
                span=(0, 1),
                origin=None,
            ),
        ),
    )
    return CachedRenderArtifact(0, (root, child), ())


def test_nested_template_cache_kind_roundtrips_and_unknown_kind_rejects() -> None:
    artifact = _projection_artifact("nested-template")
    assert _decode_artifact(_encode_artifact(artifact)) == artifact

    wire = json.loads(_encode_artifact(artifact))
    wire["frames"][0]["parts"][0][9] = "forged-projection"
    with pytest.raises(CacheArtifactError, match="unknown direct projection kind"):
        _decode_artifact(json.dumps(wire))


def test_replay_rejects_a_missing_external_projection_parent() -> None:
    app = Citry()

    class Page(Component):
        citry = app
        template = "<c-slot><b>fallback</b></c-slot>"

    render = render_prepared(Page())
    boundary = render.context.component
    assert boundary is not None
    artifact = _export_component_artifact(render)
    frames = list(artifact.frames)
    root = frames[artifact.root_frame]
    parts = list(root.parts)
    projection_index = next(index for index, part in enumerate(parts) if type(part) is ArtifactDirectSlotPart)
    parts[projection_index] = replace(parts[projection_index], external_parent_execution=True)
    frames[artifact.root_frame] = replace(root, parts=tuple(parts))
    decoded = _decode_artifact(_encode_artifact(replace(artifact, frames=tuple(frames))))

    with pytest.raises(CacheArtifactError, match="external parent is unavailable"):
        _replay_component_artifact(decoded, boundary=boundary, context=render.context)


def test_unbound_nested_template_rejects_a_different_direct_session() -> None:
    context = CitryContext()
    with direct_render_scope():
        value = wrap_nested_template(
            CitryRender(parts=[], context=context),
            lexical_render_id="c1",
            public_name="c-body",
            source="x",
            span=(0, 1),
            origin=None,
        )
    with direct_render_scope(), pytest.raises(RuntimeError, match="different or closed"):
        bind_nested_template(value, context)

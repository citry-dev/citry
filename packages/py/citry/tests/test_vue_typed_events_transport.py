from __future__ import annotations

import pytest

from citry import Citry, Component, Extension, ForeignSpan, ForeignSpanSet
from citry._vue.capture import PreparedElementOpen, render_prepared
from citry._vue.direct_capture import assemble_typed_render
from citry._vue.leaf_program import PreparedLeafProgram, typed_leaf_parts
from citry.ext.events.bindings import RUNTIME_CONTROL_ATTR
from citry.nodes import ForeignNode


def _assembly(rendered):
    return assemble_typed_render(
        rendered,
        revision=0,
        tag_for_type=lambda type_key: f"x-{type_key.lower().replace('_', '-')}",
    )


def _root(assembly):
    return next(item for item in assembly.view.occurrences if item.id == assembly.view.root_id)


def _typed_openings(rendered):
    parts = []
    for part in rendered.parts:
        parts.extend(typed_leaf_parts(part) if isinstance(part, PreparedLeafProgram) else [part])
    return [part for part in parts if isinstance(part, PreparedElementOpen)]


def _assert_no_serialized_carriers(rendered, compiled_template: str) -> None:
    fallback = rendered.serialize(deps_strategy="ignore")
    assert "data-cev-" not in fallback
    assert RUNTIME_CONTROL_ATTR not in fallback
    assert "data-cev-" not in compiled_template
    assert RUNTIME_CONTROL_ATTR not in compiled_template
    for opening in _typed_openings(rendered):
        assert not any(name.lower().startswith("data-cev-") for name in opening.data_attrs)
        assert not any(name.lower() == RUNTIME_CONTROL_ATTR for name in opening.data_attrs)


@pytest.mark.parametrize("general_renderer", [False, True], ids=["leaf", "general"])
def test_literal_event_uses_typed_transport_without_dom_carrier(general_renderer: bool) -> None:
    extensions = []
    if general_renderer:

        class ForceGeneralRenderer(Extension):
            name = "force_general_renderer"

            def on_attrs_resolved(self, ctx):
                return None

        extensions = [ForceGeneralRenderer]

    registry = Citry(secret="typed-events-transport-secret", autodiscover=False, extensions=extensions)  # noqa: S106
    registry.set_mounted_prefix("/citry")

    class Button(Component):
        citry = registry

        class Events:
            def save(self):
                return None

        template = (
            '<button c-title="title" v-show="visible" @c-click="save">Save</button>'
            if general_renderer
            else '<button c-title="title" @c-click="save">Save</button>'
        )

        def template_data(self, kwargs, slots):
            return {"title": "Save this item"}

        def js_data(self, kwargs, slots):
            return {"visible": True} if general_renderer else {}

    rendered = render_prepared(Button())
    has_leaf = any(isinstance(part, PreparedLeafProgram) for part in rendered.parts)
    assert has_leaf == (not general_renderer)
    assembly = _assembly(rendered)
    owner = _root(assembly)
    compiled = assembly.compile_inputs[owner.definition_id]

    [event] = owner.prepared_data["eventBindings"].values()
    assert (event["event"], event["handler"]) == ("click", "save")
    assert "v-on:click" in compiled.template
    assert any(opening.data_attrs.get("title") == "Save this item" for opening in _typed_openings(rendered))
    _assert_no_serialized_carriers(rendered, compiled.template)


def test_authenticated_runtime_state_spread_enters_typed_control_table() -> None:
    registry = Citry(secret="typed-runtime-state-secret", autodiscover=False)  # noqa: S106

    class Search(Component):
        citry = registry

        class State:
            query: str = ""

        class Events:
            def refresh(self, state):
                return None

        template = '<input c-bind="attrs">'

        def template_data(self, kwargs, slots):
            return {"attrs": {":c-query": "refresh"}}

    rendered = render_prepared(Search())
    assembly = _assembly(rendered)
    owner = _root(assembly)
    compiled = assembly.compile_inputs[owner.definition_id]
    [control] = owner.prepared_data["controlBindings"].values()

    assert (control["field"], control["handler"], control["binding_mode"]) == (
        "query",
        "refresh",
        "two-way",
    )
    assert "v-citry-control" in compiled.template
    assert any(opening.control_bindings for opening in _typed_openings(rendered))
    _assert_no_serialized_carriers(rendered, compiled.template)


def test_authored_state_control_survives_ordinary_type_and_title_spread() -> None:
    registry = Citry(secret="typed-literal-state-secret", autodiscover=False)  # noqa: S106

    class Search(Component):
        citry = registry

        class State:
            query: str = ""

        class Events:
            def refresh(self, state):
                return None

        template = '<input c-bind="attrs" :c-query="refresh">'

        def template_data(self, kwargs, slots):
            return {"attrs": {"type": "text", "title": "Search"}}

    rendered = render_prepared(Search())
    assembly = _assembly(rendered)
    owner = _root(assembly)
    compiled = assembly.compile_inputs[owner.definition_id]
    [control] = owner.prepared_data["controlBindings"].values()

    assert (control["field"], control["handler"]) == ("query", "refresh")
    assert "v-citry-control" in compiled.template
    assert any(
        opening.data_attrs.get("type") == "text" and opening.data_attrs.get("title") == "Search"
        for opening in _typed_openings(rendered)
    )
    _assert_no_serialized_carriers(rendered, compiled.template)


def test_literal_and_runtime_state_controls_still_enforce_one_per_element() -> None:
    registry = Citry(secret="typed-one-state-secret", autodiscover=False)  # noqa: S106

    class Search(Component):
        citry = registry

        class State:
            query: str = ""

        class Events:
            def refresh(self, state):
                return None

        template = '<input type="text" c-bind="attrs" :c-query="refresh">'

        def template_data(self, kwargs, slots):
            return {"attrs": {":c-query": "refresh"}}

    with pytest.raises(ValueError, match=r"one element supports exactly one :c-\* State binding"):
        render_prepared(Search())


def test_authored_private_runtime_control_key_is_reserved() -> None:
    registry = Citry(autodiscover=False)

    class Forged(Component):
        citry = registry
        template = f'<input {RUNTIME_CONTROL_ATTR}="forged">'

    with pytest.raises(
        RuntimeError,
        match=r"data-citry-runtime-control.*reserved internal Events namespace",
    ):
        render_prepared(Forged())


@pytest.mark.parametrize(
    ("origin", "untrusted_value"),
    [
        pytest.param("spread", "forged", id="spread-string"),
        pytest.param("spread", object(), id="spread-object"),
        pytest.param("hook", "forged", id="hook-string"),
        pytest.param("hook", object(), id="hook-object"),
    ],
)
def test_untrusted_private_runtime_control_values_have_no_producer_authority(origin, untrusted_value) -> None:
    extensions = []
    if origin == "hook":

        class ForgePrivateControl(Extension):
            name = "forge_private_control"

            def on_attrs_resolved(self, ctx):
                if ctx.tag_name == "input":
                    return {**ctx.attrs, RUNTIME_CONTROL_ATTR: untrusted_value}
                return None

        extensions = [ForgePrivateControl]

    registry = Citry(autodiscover=False, extensions=extensions)

    class Plain(Component):
        citry = registry
        template = '<input c-bind="attrs">'

        def template_data(self, kwargs, slots):
            attrs = {RUNTIME_CONTROL_ATTR: untrusted_value} if origin == "spread" else {"title": "plain value"}
            return {"attrs": attrs}

    exception_type = RuntimeError if origin == "spread" else TypeError
    message = (
        r"(?i)data-citry-runtime-control.*reserved internal Events namespace"
        if origin == "spread"
        else r"runtime State control metadata lacks Events producer provenance"
    )
    with pytest.raises(exception_type, match=message):
        render_prepared(Plain())


@pytest.mark.parametrize(
    ("forged_key", "untrusted_value"),
    [
        pytest.param(RUNTIME_CONTROL_ATTR, "forged", id="exact-key-string"),
        pytest.param(RUNTIME_CONTROL_ATTR, object(), id="exact-key-object"),
        pytest.param(RUNTIME_CONTROL_ATTR.upper(), "forged", id="case-variant-string"),
        pytest.param(RUNTIME_CONTROL_ATTR.upper(), object(), id="case-variant-object"),
    ],
)
def test_forged_runtime_control_key_cannot_be_masked_by_real_state_binding(forged_key, untrusted_value) -> None:
    registry = Citry(secret="typed-state-collision-secret", autodiscover=False)  # noqa: S106

    class Search(Component):
        citry = registry

        class State:
            query: str = ""

        class Events:
            def refresh(self, state):
                return None

        template = '<input type="text" c-bind="attrs">'

        def template_data(self, kwargs, slots):
            return {"attrs": {":c-query": "refresh", forged_key: untrusted_value}}

    with pytest.raises(
        RuntimeError,
        match=r"(?i)data-citry-runtime-control.*reserved internal Events namespace",
    ):
        render_prepared(Search())


def test_late_html_attribute_cannot_stringify_authenticated_runtime_control() -> None:
    class CopyControlToTitle(Extension):
        name = "copy_control_to_title"

        def on_attrs_resolved(self, ctx):
            carrier = ctx.attrs.get(RUNTIME_CONTROL_ATTR)
            if carrier is not None:
                return {**ctx.attrs, "title": carrier}
            return None

    registry = Citry(
        secret="typed-stringify-control-secret",  # noqa: S106
        autodiscover=False,
        extensions=[CopyControlToTitle],
    )

    class Search(Component):
        citry = registry

        class State:
            query: str = ""

        class Events:
            def refresh(self, state):
                return None

        template = '<input c-bind="attrs">'

        def template_data(self, kwargs, slots):
            return {"attrs": {":c-query": "refresh"}}

    rendered = render_prepared(Search())
    with pytest.raises(TypeError, match="runtime State control metadata cannot be serialized as an HTML attribute"):
        rendered.serialize(deps_strategy="ignore")


def test_cached_event_and_control_replay_keeps_typed_semantics_and_fresh_render_id() -> None:
    registry = Citry(secret="typed-cache-transport-secret", autodiscover=False)  # noqa: S106
    registry.set_mounted_prefix("/citry")
    template_data_calls = 0

    class CachedSearch(Component):
        citry = registry

        class Cache:
            enabled = True

        class State:
            query: str = ""

        class Events:
            def save(self):
                return None

            def refresh(self, state):
                return None

        template = '<div><button @c-click="save">{{ label }}</button><input type="text" :c-query="refresh"></div>'

        def template_data(self, kwargs, slots):
            nonlocal template_data_calls
            template_data_calls += 1
            return {"label": "Cached"}

    first_render = render_prepared(CachedSearch())
    second_render = render_prepared(CachedSearch())
    first = _assembly(first_render)
    second = _assembly(second_render)
    first_owner = _root(first)
    second_owner = _root(second)

    def semantics(owner):
        return {
            name: [
                {key: value for key, value in spec.items() if key != "id"}
                for spec in owner.prepared_data.get(name, {}).values()
            ]
            for name in ("eventBindings", "controlBindings")
        }

    assert template_data_calls == 1
    assert first_render.frame.render_id != second_render.frame.render_id
    assert first.render_to_occurrence[first_render.frame.render_id] == first.view.root_id
    assert second.render_to_occurrence[second_render.frame.render_id] == second.view.root_id
    assert semantics(first_owner) == semantics(second_owner)
    assert semantics(first_owner)["eventBindings"][0]["handler"] == "save"
    assert semantics(first_owner)["controlBindings"][0]["field"] == "query"
    first_definition = first.compile_inputs[first_owner.definition_id]
    second_definition = second.compile_inputs[second_owner.definition_id]
    _assert_no_serialized_carriers(first_render, first_definition.template)
    _assert_no_serialized_carriers(second_render, second_definition.template)


def test_plain_opaque_html_without_events_remains_supported() -> None:
    registry = Citry(autodiscover=False)

    class Page(Component):
        citry = registry
        template = "<main><c-raw><em>plain raw markup</em></c-raw></main>"

    rendered = render_prepared(Page())
    assembly = _assembly(rendered)
    owner = _root(assembly)
    compiled = assembly.compile_inputs[owner.definition_id]

    [opaque] = owner.prepared_data["opaqueHtml"].values()
    assert "plain raw markup" in opaque["html"]
    assert "<citry-opaque-html" in compiled.template
    assert "data-cev-" not in compiled.template


def test_foreign_host_node_is_resolved_and_rendered() -> None:
    foreign_source = "{% host_value %}"
    seen_providers: list[tuple[str, ...]] = []

    class ForeignHost(Extension):
        name = "typed_events_foreign_host"

        def on_template_foreign_spans(self, ctx):
            token = foreign_source.encode()
            start = ctx.content.encode().find(token)
            return ForeignSpanSet((ForeignSpan(start, start + len(token)),))

        def on_template_foreign_compiled(self, ctx):
            foreign_nodes = [item for item in ctx.nodes if isinstance(item, ForeignNode)]
            seen_providers.append(tuple(item.provider for item in foreign_nodes))
            ctx.nodes[:] = ["FOREIGN_VALUE" if isinstance(item, ForeignNode) else item for item in ctx.nodes]
            ctx.mark_resolved(*ctx.claims)

    registry = Citry(autodiscover=False, extensions=[ForeignHost])

    class Page(Component):
        citry = registry
        template = f"<p>before {foreign_source} after</p>"

    html = str(Page())

    assert seen_providers == [("typed_events_foreign_host",)]
    assert "before FOREIGN_VALUE after" in html


def test_runtime_event_argument_expressions_are_rejected_before_prepared_capture() -> None:
    registry = Citry(secret="typed-untrusted-event-secret", autodiscover=False)  # noqa: S106

    class Search(Component):
        citry = registry

        class Events:
            def save(self):
                return None

        template = '<button c-bind="attrs">Save</button>'

        def template_data(self, kwargs, slots):
            return {"attrs": {"@c-click": "save({id: item.id})"}}

    with pytest.raises(
        ValueError,
        match=r"runtime-resolved @c-\* event bindings support handler names without argument expressions",
    ):
        render_prepared(Search())

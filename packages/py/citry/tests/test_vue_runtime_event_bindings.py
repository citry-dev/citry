from __future__ import annotations

import re

import pytest

from citry import Citry, Component, Extension
from citry._vue.capture import PreparedElementOpen, render_prepared
from citry._vue.direct_capture import assemble_typed_render
from citry._vue.leaf_program import PreparedLeafProgram, typed_leaf_parts
from citry.ext.events.bindings import RUNTIME_CONTROL_ATTR, RUNTIME_EVENTS_ATTR

_MAX_SAFE_INTEGER = 2**53 - 1


def _assembly(rendered):
    return assemble_typed_render(
        rendered,
        revision=0,
        tag_for_type=lambda type_key: f"x-{type_key.lower().replace('_', '-')}",
    )


def _root(assembly):
    return next(item for item in assembly.view.occurrences if item.id == assembly.view.root_id)


def _openings(rendered) -> list[PreparedElementOpen]:
    parts = []
    for part in rendered.parts:
        parts.extend(typed_leaf_parts(part) if isinstance(part, PreparedLeafProgram) else [part])
    return [part for part in parts if isinstance(part, PreparedElementOpen)]


def _assert_no_private_attribute_output(rendered, compiled_template: str) -> None:
    fallback = rendered.serialize(deps_strategy="ignore")
    assert "data-cev-" not in fallback
    assert RUNTIME_CONTROL_ATTR not in fallback
    assert RUNTIME_EVENTS_ATTR not in fallback
    assert "data-cev-" not in compiled_template
    assert RUNTIME_CONTROL_ATTR not in compiled_template
    assert RUNTIME_EVENTS_ATTR not in compiled_template
    for opening in _openings(rendered):
        assert not any(name.lower().startswith("data-cev-") for name in opening.data_attrs)
        assert not any(name.lower() in {RUNTIME_CONTROL_ATTR, RUNTIME_EVENTS_ATTR} for name in opening.data_attrs)


@pytest.mark.parametrize("general_renderer", [False, True], ids=["leaf", "direct"])
def test_runtime_event_and_state_spreads_keep_coexisting_typed_tables(general_renderer: bool) -> None:
    extensions = []
    if general_renderer:

        class ForceDirectRenderer(Extension):
            name = "force_runtime_event_direct_renderer"

            def on_attrs_resolved(self, ctx):
                return None

        extensions = [ForceDirectRenderer]

    registry = Citry(secret="runtime-event-state-coexist-secret", autodiscover=False, extensions=extensions)  # noqa: S106

    class Search(Component):
        citry = registry

        class State:
            query: str = ""

        class Events:
            def save(self):
                return None

            def refresh(self, state):
                return None

        template = (
            '<input id="state-search" class="field" style="color: red;" disabled '
            'type="text" c-bind="attrs" v-show="visible">'
            if general_renderer
            else '<input id="state-search" class="field" style="color: red;" disabled type="text" c-bind="attrs">'
        )

        def template_data(self, kwargs, slots):
            return {"attrs": {"@c-keyup": "save", ":c-query": "refresh"}}

        def js_data(self, kwargs, slots):
            return {"visible": True} if general_renderer else {}

    rendered = render_prepared(Search())
    has_leaf = any(isinstance(part, PreparedLeafProgram) for part in rendered.parts)
    assert has_leaf is not general_renderer

    assembly = _assembly(rendered)
    owner = _root(assembly)
    compiled = assembly.compile_inputs[owner.definition_id]
    event_bindings = owner.prepared_data["eventBindings"]
    control_bindings = owner.prepared_data["controlBindings"]
    [event] = event_bindings.values()
    [control] = control_bindings.values()

    assert (event["event"], event["handler"], event["args"]) == ("keyup", "save", None)
    assert event["id"].startswith("citryRuntimeEvent")
    assert (control["field"], control["handler"]) == ("query", "refresh")
    assert "v-citry-runtime-events" in compiled.template
    assert "v-citry-control" in compiled.template
    assert "save" not in compiled.template
    assert "refresh" not in compiled.template
    if has_leaf:
        assert owner.prepared_data["citryAttrs0"] == {
            "id": "state-search",
            "class": "field",
            "style": "color: red;",
            "disabled": "",
            "type": "text",
        }
    else:
        assert 'id="state-search"' in compiled.template
        assert 'class="field"' in compiled.template
        assert 'style="color: red;"' in compiled.template
        assert "disabled" in compiled.template
        assert 'type="text"' in compiled.template
    _assert_no_private_attribute_output(rendered, compiled.template)


@pytest.mark.parametrize("force_direct", [False, True], ids=["leaf", "direct"])
@pytest.mark.parametrize("spread_case", ["preserve", "override", "remove"])
def test_runtime_event_spreads_preserve_and_resolve_static_attributes(force_direct: bool, spread_case: str) -> None:
    extensions = []
    if force_direct:

        class ForceDirectRenderer(Extension):
            name = f"force_runtime_event_static_attrs_{spread_case}"

            def on_attrs_resolved(self, ctx):
                return None

        extensions = [ForceDirectRenderer]

    registry = Citry(
        secret=f"runtime-event-static-attrs-{force_direct}-{spread_case}",
        autodiscover=False,
        extensions=extensions,
    )
    spread_attrs: dict[str, object] = {}
    if spread_case == "override":
        spread_attrs = {
            "id": "runtime-id",
            "class": "runtime",
            "style": "color: blue;",
            "disabled": False,
        }
    elif spread_case == "remove":
        spread_attrs = {"id": None, "disabled": False}

    class Mixed(Component):
        citry = registry
        template = (
            '<button id="mixed" class="fixed" style="color: red;" disabled '
            '@c-click.debounce.30ms="authored" c-bind="attrs">run</button>'
        )

        class Events:
            def authored(self):
                return None

            def runtime_event(self):
                return None

        def template_data(self, kwargs, slots):
            return {"attrs": {"@c-keydown": "runtime_event", **spread_attrs}}

    rendered = render_prepared(Mixed())
    has_leaf = any(isinstance(part, PreparedLeafProgram) for part in rendered.parts)
    assert has_leaf is not force_direct

    assembly = _assembly(rendered)
    owner = _root(assembly)
    compiled = assembly.compile_inputs[owner.definition_id]
    bindings = owner.prepared_data["eventBindings"]
    assert {binding["handler"] for binding in bindings.values()} == {"authored", "runtime_event"}
    assert "v-citry-runtime-events" in compiled.template
    attrs = owner.prepared_data.get("citryAttrs0", {})

    if spread_case == "preserve":
        expected = {
            "id": "mixed",
            "class": "fixed",
            "style": "color: red;",
            "disabled": "",
        }
        assert attrs == (expected if has_leaf else {})
        if not has_leaf:
            assert 'id="mixed"' in compiled.template
            assert 'class="fixed"' in compiled.template
            assert 'style="color: red;"' in compiled.template
            assert "disabled" in compiled.template
    elif spread_case == "override":
        assert attrs == {"id": "runtime-id", "class": "fixed runtime", "style": "color: blue;"}
        assert 'id="mixed"' not in compiled.template
        assert 'class="fixed"' not in compiled.template
        assert 'style="color: red;"' not in compiled.template
        assert "disabled" not in compiled.template
    else:
        assert attrs == ({"class": "fixed", "style": "color: red;"} if has_leaf else {})
        assert 'id="mixed"' not in compiled.template
        assert "disabled" not in compiled.template
        if not has_leaf:
            assert 'class="fixed"' in compiled.template
            assert 'style="color: red;"' in compiled.template

    _assert_no_private_attribute_output(rendered, compiled.template)


@pytest.mark.parametrize("force_direct", [False, True], ids=["leaf", "direct"])
def test_runtime_event_spread_preserves_static_attributes_with_authored_poll(force_direct: bool) -> None:
    extensions = []
    if force_direct:

        class ForceDirectRenderer(Extension):
            name = "force_runtime_event_poll_static_attrs"

            def on_attrs_resolved(self, ctx):
                return None

        extensions = [ForceDirectRenderer]

    registry = Citry(
        secret=f"runtime-event-poll-static-attrs-{force_direct}",
        autodiscover=False,
        extensions=extensions,
    )

    class PollSurface(Component):
        citry = registry
        template = (
            '<button id="poll-target" class="poll" style="color: red;" disabled '
            '@c-poll.1s="refresh" c-bind="attrs">poll</button>'
        )

        class Events:
            def refresh(self):
                return None

            def save(self):
                return None

        def template_data(self, kwargs, slots):
            return {"attrs": {"@c-keydown": "save"}}

    rendered = render_prepared(PollSurface())
    has_leaf = any(isinstance(part, PreparedLeafProgram) for part in rendered.parts)
    assert has_leaf is not force_direct

    assembly = _assembly(rendered)
    owner = _root(assembly)
    compiled = assembly.compile_inputs[owner.definition_id]
    assert len(owner.prepared_data["pollBindings"]) == 1
    assert len(owner.prepared_data["eventBindings"]) == 1
    assert "v-citry-runtime-events" in compiled.template
    assert "v-citry-event-timing" in compiled.template
    if has_leaf:
        assert owner.prepared_data["citryAttrs0"] == {
            "id": "poll-target",
            "class": "poll",
            "style": "color: red;",
            "disabled": "",
        }
    else:
        assert 'id="poll-target"' in compiled.template
        assert 'class="poll"' in compiled.template
        assert 'style="color: red;"' in compiled.template
        assert "disabled" in compiled.template
    _assert_no_private_attribute_output(rendered, compiled.template)


def test_runtime_event_loop_instances_keep_distinct_handler_ids_and_specs() -> None:
    registry = Citry(secret="runtime-event-loop-identities-secret", autodiscover=False)  # noqa: S106

    class Rows(Component):
        citry = registry

        class Events:
            def save_first(self):
                return None

            def save_second(self):
                return None

        template = '<button c-for="attrs in handlers" c-bind="attrs">run</button>'

        def template_data(self, kwargs, slots):
            return {
                "handlers": [
                    {"@c-click": "save_first"},
                    {"@c-click": "save_second"},
                ]
            }

    rendered = render_prepared(Rows())
    assembly = _assembly(rendered)
    owner = _root(assembly)
    compiled = assembly.compile_inputs[owner.definition_id]
    bindings = owner.prepared_data["eventBindings"]

    assert len(bindings) == 2
    assert {binding["handler"] for binding in bindings.values()} == {"save_first", "save_second"}
    ids_by_handler = {binding["handler"]: binding["id"] for binding in bindings.values()}
    assert ids_by_handler["save_first"] != ids_by_handler["save_second"]
    assert all(re.fullmatch(r"citryRuntimeEvent[0-9a-f]+", binding_id) for binding_id in ids_by_handler.values())
    assert "v-citry-runtime-events" in compiled.template
    _assert_no_private_attribute_output(rendered, compiled.template)


def test_runtime_event_sites_include_the_selected_branch_and_each_loop_route() -> None:
    registry = Citry(secret="runtime-event-nested-site-route-secret", autodiscover=False)  # noqa: S106

    class Rows(Component):
        citry = registry

        class Events:
            def first(self):
                return None

            def second(self):
                return None

        template = (
            '<c-if cond="show"><button c-for="attrs in handlers" c-bind="attrs">run</button></c-if>'
            "<c-else><p>empty</p></c-else>"
        )

        def template_data(self, kwargs, slots):
            return {
                "show": True,
                "handlers": [{"@c-click": "first"}, {"@c-click": "second"}],
            }

    rendered = render_prepared(Rows())
    assembly = _assembly(rendered)
    owner = _root(assembly)
    compile_input = assembly.compile_inputs[owner.definition_id]
    [site] = compile_input.runtime_event_sites

    bindings = owner.prepared_data["eventBindings"]
    [branch_step, each_step] = site["steps"]
    assert branch_step["kind"] == "branch"
    assert branch_step["index"] == 0
    assert owner.prepared_data[branch_step["key"]] == branch_step["index"]
    assert each_step["kind"] == "each"
    loop_rows = owner.prepared_data[each_step["key"]]
    assert len(bindings) == 2
    assert [row[site["bindingKey"]] for row in loop_rows] == list(bindings)
    assert {binding["handler"] for binding in bindings.values()} == {"first", "second"}
    assert f'v-if="preparedData.{branch_step["key"]} === {branch_step["index"]}"' in compile_input.template
    assert f'v-for="preparedData in preparedData.{each_step["key"]}"' in compile_input.template
    assert "v-citry-runtime-events" in compile_input.template


def test_runtime_event_metadata_declines_cache_replay_without_losing_typed_output() -> None:
    registry = Citry(secret="runtime-event-cache-decline-secret", autodiscover=False)  # noqa: S106
    template_data_calls = 0

    class CachedButton(Component):
        citry = registry

        class Cache:
            enabled = True

        class Events:
            def save(self):
                return None

        template = '<button c-bind="attrs">save</button>'

        def template_data(self, kwargs, slots):
            nonlocal template_data_calls
            template_data_calls += 1
            return {"attrs": {"@c-click.once": "save"}}

    first = render_prepared(CachedButton())
    second = render_prepared(CachedButton())
    first_assembly = _assembly(first)
    second_assembly = _assembly(second)
    first_owner = _root(first_assembly)
    second_owner = _root(second_assembly)

    assert template_data_calls == 2
    for owner, assembly, rendered in (
        (first_owner, first_assembly, first),
        (second_owner, second_assembly, second),
    ):
        [binding] = owner.prepared_data["eventBindings"].values()
        assert (binding["event"], binding["handler"], binding["once"]) == ("click", "save", True)
        definition = assembly.compile_inputs[owner.definition_id]
        assert "v-citry-runtime-events" in definition.template
        _assert_no_private_attribute_output(rendered, definition.template)


@pytest.mark.parametrize(
    ("channel", "timing", "accepted"),
    [
        pytest.param("authored-event", _MAX_SAFE_INTEGER, True, id="literal-event-max-safe"),
        pytest.param("authored-event", _MAX_SAFE_INTEGER + 1, False, id="literal-event-overflow"),
        pytest.param("runtime-event", _MAX_SAFE_INTEGER, True, id="spread-event-max-safe"),
        pytest.param("runtime-event", _MAX_SAFE_INTEGER + 1, False, id="spread-event-overflow"),
        pytest.param("authored-state", _MAX_SAFE_INTEGER, True, id="literal-state-max-safe"),
        pytest.param("authored-state", _MAX_SAFE_INTEGER + 1, False, id="literal-state-overflow"),
        pytest.param("runtime-state", _MAX_SAFE_INTEGER, True, id="spread-state-max-safe"),
        pytest.param("runtime-state", _MAX_SAFE_INTEGER + 1, False, id="spread-state-overflow"),
    ],
)
def test_event_and_state_timing_stays_within_javascript_safe_integer(
    channel: str, timing: int, accepted: bool
) -> None:
    registry = Citry(secret="runtime-event-timing-boundary-secret", autodiscover=False)  # noqa: S106
    attr = f"@c-click.debounce.{timing}ms" if "event" in channel else f":c-query.debounce.{timing}ms"
    handler = "save" if "event" in channel else "refresh"

    class Timed(Component):
        citry = registry

        class State:
            query: str = ""

        class Events:
            def save(self):
                return None

            def refresh(self, state):
                return None

        template = '<input c-bind="attrs">' if channel.startswith("runtime") else ""

        def template_data(self, kwargs, slots):
            return {"attrs": {attr: handler}} if channel.startswith("runtime") else {}

    if not channel.startswith("runtime"):
        if "state" in channel:
            Timed.template = f'<input type="text" {attr}="{handler}">'
        else:
            Timed.template = f'<button {attr}="{handler}">run</button>'

    if accepted:
        assembly = _assembly(render_prepared(Timed()))
        owner = _root(assembly)
        table_name = "eventBindings" if "event" in channel else "controlBindings"
        [binding] = owner.prepared_data[table_name].values()
        assert binding["debounce"] == timing
    else:
        with pytest.raises(ValueError, match="timing exceeds the JavaScript safe-integer limit"):
            render_prepared(Timed())

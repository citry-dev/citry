from __future__ import annotations

import warnings

import pytest

from citry import Citry, Component, Extension
from citry._vue.capture import (
    PreparedElementOpen,
    _normalize_runtime_poll_bindings,
    render_prepared,
)
from citry._vue.direct_capture import assemble_typed_render
from citry._vue.leaf_program import PreparedLeafProgram, typed_leaf_parts
from citry._vue.serialization import analyze_vue_serialization
from citry.ext.events.bindings import RUNTIME_CONTROL_ATTR, RUNTIME_EVENTS_ATTR

_MAX_SAFE_INTEGER = 2**53 - 1
_HANDLER_ONLY_DETAIL = "this control has a browser handler but no native navigation or submission fallback"


class _ForceDirectRenderer(Extension):
    name = "runtime_poll_force_direct_renderer"

    def on_attrs_resolved(self, ctx):
        return None


def _registry(*, force_direct: bool = False) -> Citry:
    extensions = [_ForceDirectRenderer] if force_direct else []
    registry = Citry(
        secret=f"runtime-poll-test-{force_direct}",
        autodiscover=False,
        extensions=extensions,
    )
    return registry


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


@pytest.mark.parametrize("force_direct", [False, True], ids=["leaf", "direct"])
def test_runtime_poll_and_event_ids_share_the_site_but_use_their_own_tables(force_direct: bool) -> None:
    registry = _registry(force_direct=force_direct)

    class PollSurface(Component):
        citry = registry
        template = '<output @c-poll.1s="refresh" c-bind="attrs">waiting</output>'

        class Events:
            def refresh(self):
                return None

            def save(self):
                return None

        def template_data(self, kwargs, slots):
            return {"attrs": {"@c-poll.2s": "refresh", "@c-keyup": "save"}}

    rendered = render_prepared(PollSurface())
    (opening,) = _openings(rendered)
    assert len(opening.poll_bindings) == 1
    assert len(opening.runtime_poll_bindings) == 1
    assert len(opening.runtime_event_bindings) == 1

    authored_poll = opening.poll_bindings[0]
    runtime_poll = opening.runtime_poll_bindings[0]
    runtime_event = opening.runtime_event_bindings[0]
    assert authored_poll["id"].startswith("citryPoll")
    assert runtime_poll["id"].startswith("citryRuntimePoll")
    assert runtime_event["id"].startswith("citryRuntimeEvent")
    assert (authored_poll["interval"], runtime_poll["interval"]) == (1000, 2000)
    assert runtime_poll["args"] is None
    assert runtime_poll["handler"] == "refresh"

    assembly = _assembly(rendered)
    owner = _root(assembly)
    definition = assembly.compile_inputs[owner.definition_id]
    [site] = definition.runtime_event_sites
    selected_ids = owner.prepared_data[site["bindingKey"]].split(",")
    assert set(selected_ids) == {runtime_poll["id"], runtime_event["id"]}
    assert owner.prepared_data["pollBindings"] == {
        authored_poll["id"]: dict(authored_poll),
        runtime_poll["id"]: dict(runtime_poll),
    }
    assert owner.prepared_data["eventBindings"] == {runtime_event["id"]: dict(runtime_event)}
    assert "v-citry-runtime-events" in definition.template
    assert "refresh" not in definition.template
    assert RUNTIME_EVENTS_ATTR not in rendered.serialize(deps_strategy="ignore")


def test_handler_only_runtime_poll_is_accepted_and_argument_expressions_are_rejected() -> None:
    registry = _registry()

    class Poller(Component):
        citry = registry
        template = '<output c-bind="attrs">waiting</output>'

        class Events:
            def refresh(self):
                return None

        def template_data(self, kwargs, slots):
            return {"attrs": {"@c-poll.2s": "refresh"}}

    assembly = _assembly(render_prepared(Poller()))
    owner = _root(assembly)
    definition = assembly.compile_inputs[owner.definition_id]
    [binding] = owner.prepared_data["pollBindings"].values()
    [site] = definition.runtime_event_sites

    assert binding["id"].startswith("citryRuntimePoll")
    assert binding["handler"] == "refresh"
    assert binding["args"] is None
    assert binding["interval"] == 2000
    assert owner.prepared_data[site["bindingKey"]] == binding["id"]

    class PollWithArguments(Component):
        citry = registry
        template = '<output c-bind="attrs">waiting</output>'

        class PollArgs:
            value: int

        class Events:
            def refresh(self, data: PollWithArguments.PollArgs):
                return None

        def template_data(self, kwargs, slots):
            return {"attrs": {"@c-poll.2s": "refresh({value: 1})"}}

    with pytest.raises(
        ValueError,
        match="runtime-resolved @c-poll bindings support handler names without argument expressions",
    ):
        _assembly(render_prepared(PollWithArguments()))


@pytest.mark.parametrize(
    ("interval", "accepted"),
    [
        pytest.param(1, True, id="one-millisecond"),
        pytest.param(_MAX_SAFE_INTEGER, True, id="maximum-safe-integer"),
        pytest.param(0, False, id="zero"),
        pytest.param(-1, False, id="negative"),
        pytest.param(_MAX_SAFE_INTEGER + 1, False, id="unsafe"),
        pytest.param(True, False, id="boolean"),
        pytest.param(1.0, False, id="float"),
    ],
)
def test_runtime_poll_capture_requires_a_positive_exact_safe_integer(interval: object, accepted: bool) -> None:
    binding = {
        "id": "citryRuntimePoll012abc",
        "handler": "refresh",
        "args": None,
        "interval": interval,
    }

    if accepted:
        normalized = _normalize_runtime_poll_bindings((binding,))
        assert dict(normalized[0]) == binding
    else:
        with pytest.raises(TypeError, match="interval must be a positive JavaScript-safe exact integer"):
            _normalize_runtime_poll_bindings((binding,))


def test_poll_only_omit_mode_warns_and_removes_its_private_marker() -> None:
    registry = _registry()

    class Poller(Component):
        citry = registry
        template = '<button type="button" c-bind="attrs">waiting</button>'

        class Events:
            def refresh(self):
                return None

        def template_data(self, kwargs, slots):
            return {"attrs": {"@c-poll.2s": "refresh"}}

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", RuntimeWarning)
        html = render_prepared(Poller()).serialize(deps_strategy="ignore", security_javascript="omit")

    handler_only = [record for record in caught if _HANDLER_ONLY_DETAIL in str(record.message)]
    assert len(handler_only) == 1
    assert "data-citry-omit-handler" not in html.lower()
    assert "data-cev-" not in html
    assert RUNTIME_CONTROL_ATTR not in html.lower()


def test_empty_runtime_candidate_keeps_runtime_support_and_declines_cache_replay() -> None:
    registry = _registry()
    template_data_calls = 0

    class CachedSurface(Component):
        citry = registry

        class Cache:
            enabled = True

        class Events:
            def refresh(self):
                return None

        template = '<button c-bind="attrs">waiting</button>'

        def template_data(self, kwargs, slots):
            nonlocal template_data_calls
            template_data_calls += 1
            return {"attrs": {"title": "ready"}}

    first = render_prepared(CachedSurface())
    second = render_prepared(CachedSurface())
    assert template_data_calls == 2

    for rendered in (first, second):
        analysis = analyze_vue_serialization(rendered)
        assert "events" in analysis.runtime_requirements
        assert "events" not in analysis.active_policy_requirements
        assembly = _assembly(rendered)
        owner = _root(assembly)
        definition = assembly.compile_inputs[owner.definition_id]
        [site] = definition.runtime_event_sites
        assert owner.prepared_data[site["bindingKey"]] == ""
        assert "v-citry-runtime-events" in definition.template

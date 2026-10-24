from __future__ import annotations

import json

import pytest

from citry import Citry, Component
from citry._vue.capture import PreparedElementOpen, prepared_dynamic_element_open, render_prepared
from citry._vue.direct_capture import assemble_typed_render
from citry.ext.cache.artifact import _decode_artifact, _encode_artifact
from citry.ext.cache.replay import _export_typed_leaf, _replay_typed_leaf
from tests.test_ext_cache_typed_artifact import _artifact


def _assembly(component: type[Component]):
    return assemble_typed_render(
        render_prepared(component()),
        revision=0,
        tag_for_type=lambda key: "x-" + key.lower().replace("_", "-"),
    )


def test_dynamic_authored_event_and_control_use_alias_and_final_tag() -> None:
    app = Citry(secret="dynamic-events-unit", autodiscover=False)  # noqa: S106

    class Page(Component):
        citry = app

        class State:
            value: str = ""

        class Events:
            def choose(self, state):
                return None

        def template_data(self, kwargs, slots):
            return {"event_tag": "button", "control_tag": "input"}

        template = (
            '<c-element c-is="event_tag" @c-click="choose">choose</c-element>'
            '<c-element c-is="control_tag" :c-value="choose" />'
        )

    assembly = _assembly(Page)
    owner = next(item for item in assembly.view.occurrences if item.id == assembly.view.root_id)
    [compiled] = assembly.compile_inputs.values()

    assert next(iter(owner.prepared_data["eventBindings"].values()))["handler"] == "choose"
    assert next(iter(owner.prepared_data["controlBindings"].values()))["field"] == "value"
    assert len(compiled.dynamic_elements) == 2
    assert "v-on:click" in compiled.template
    assert "v-citry-control" in compiled.template


def test_dynamic_event_and_control_survive_valid_real_tag_changes() -> None:
    app = Citry(secret="dynamic-events-tags", autodiscover=False)  # noqa: S106
    tags = {"event": "button", "control": "input"}

    class Page(Component):
        citry = app

        class State:
            value: str = ""

        class Events:
            def choose(self, state):
                return None

        def template_data(self, kwargs, slots):
            return {"event_tag": tags["event"], "control_tag": tags["control"]}

        template = (
            '<c-element c-is="event_tag" @c-click="choose">choose</c-element>'
            '<c-element c-is="control_tag" :c-value="choose" />'
        )

    first = _assembly(Page)
    tags.update(event="a", control="textarea")
    second = _assembly(Page)
    [first_compiled] = first.compile_inputs.values()
    [second_compiled] = second.compile_inputs.values()

    assert [item["tag"] for item in first_compiled.dynamic_elements] == [
        "button",
        "input",
    ]
    assert [item["tag"] for item in second_compiled.dynamic_elements] == [
        "a",
        "textarea",
    ]


def test_dynamic_runtime_spread_merges_with_literal_binding_under_lexical_owner() -> None:
    app = Citry(secret="dynamic-events-spread", autodiscover=False)  # noqa: S106

    class Page(Component):
        citry = app

        class State:
            value: str = ""

        class Events:
            def literal(self):
                return None

            def spread(self, state):
                return None

        def template_data(self, kwargs, slots):
            return {"tag": "input", "attrs": {"@c-focus": "spread", ":c-value": "spread"}}

        template = '<c-element c-is="tag" @c-click="literal" c-bind="attrs" />'

    assembly = _assembly(Page)
    owner = next(item for item in assembly.view.occurrences if item.id == assembly.view.root_id)

    assert {item["handler"] for item in owner.prepared_data["eventBindings"].values()} == {
        "literal",
        "spread",
    }
    assert next(iter(owner.prepared_data["controlBindings"].values()))["field"] == "value"
    [compiled] = assembly.compile_inputs.values()
    assert compiled.runtime_event_sites


def test_dynamic_authored_event_cache_hits_but_runtime_spread_declines_v1_artifact() -> None:
    app = Citry(secret="dynamic-events-cache", autodiscover=False)  # noqa: S106
    authored_calls: list[str] = []
    runtime_calls: list[str] = []

    class Authored(Component):
        citry = app

        class Cache:
            enabled = True

        class Events:
            def choose(self):
                return None

        def template_data(self, kwargs, slots):
            authored_calls.append("data")
            return {"tag": "button"}

        template = '<c-element c-is="tag" @c-click="choose">choose</c-element>'

    class Runtime(Component):
        citry = app

        class Cache:
            enabled = True

        class Events:
            def choose(self):
                return None

        def template_data(self, kwargs, slots):
            runtime_calls.append("data")
            return {"tag": "button", "attrs": {"@c-click": "choose"}}

        template = '<c-element c-is="tag" c-bind="attrs">choose</c-element>'

    _assembly(Authored)
    _assembly(Authored)
    _assembly(Runtime)
    _assembly(Runtime)

    assert authored_calls == ["data"]
    assert runtime_calls == ["data", "data"]


def test_dynamic_empty_runtime_candidate_does_not_poison_later_cache_value() -> None:
    app = Citry(secret="dynamic-events-empty-cache", autodiscover=False)  # noqa: S106
    attrs: dict[str, str] = {}
    calls: list[str] = []

    class Page(Component):
        citry = app

        class Cache:
            enabled = True

        class Events:
            def choose(self):
                return None

        def template_data(self, kwargs, slots):
            calls.append("data")
            return {"tag": "button", "attrs": dict(attrs)}

        template = '<c-element c-is="tag" c-bind="attrs">choose</c-element>'

    first = _assembly(Page)
    attrs["@c-click"] = "choose"
    second = _assembly(Page)

    assert calls == ["data", "data"]
    first_owner = next(item for item in first.view.occurrences if item.id == first.view.root_id)
    second_owner = next(item for item in second.view.occurrences if item.id == second.view.root_id)
    assert "eventBindings" not in first_owner.prepared_data
    assert next(iter(second_owner.prepared_data["eventBindings"].values()))["handler"] == "choose"


def test_dynamic_cache_replay_rejects_forged_event_metadata() -> None:
    event = {
        "id": "citryEvent1",
        "event": "click",
        "handler": "choose",
        "args": None,
        "prevent": False,
        "stop": False,
        "self": False,
        "once": False,
        "key": None,
        "debounce": None,
        "throttle": None,
    }
    normalized = PreparedElementOpen("", (0, 0), "button", (), False, False, (), (event,))  # noqa: FBT003
    opening = prepared_dynamic_element_open("button", {}, normalized=normalized)
    wire = json.loads(_encode_artifact(_artifact(_export_typed_leaf(opening))))
    del wire["frames"][0]["parts"][0][7][0]["handler"]

    decoded = _decode_artifact(json.dumps(wire))
    with pytest.raises(TypeError, match="exact trusted Events fields"):
        _replay_typed_leaf(decoded.frames[0].parts[0])

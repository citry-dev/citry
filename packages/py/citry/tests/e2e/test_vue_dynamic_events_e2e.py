from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from citry import Citry, Component
from citry.ext.events.renderers import dispatcher_for

pytest.importorskip("playwright.sync_api")
pytestmark = pytest.mark.e2e


@dataclass
class DynamicClickArgs:
    value: int


def test_dynamic_element_dispatches_lexical_event_arguments(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="dynamic-events-browser", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class Page(Component):
        citry = engine

        class Events:
            def choose(self, data: DynamicClickArgs):
                return None

        def template_data(self, kwargs, slots):
            return {"tag": "button"}

        template = '<c-element c-is="tag" id="choice" @c-click="choose({value: 7})">choose</c-element>'

    dispatcher_for(engine)
    calls: list[dict[str, Any]] = []
    page.on(
        "request",
        lambda request: calls.append(request.post_data_json)
        if request.url.endswith("/ext/events/call") and request.post_data_json
        else None,
    )
    page.goto(serve_live(engine, Page().render().serialize(), "") + "/")
    page.locator("#choice").click()
    page.wait_for_function("() => !__citryRuntime._apps.values().next().value.busy")

    [call] = [call for request in calls for call in request["calls"]]
    assert call["handlerName"] == "choose"
    assert call["args"] == {"value": 7}


def test_dynamic_control_keeps_lexical_state_across_real_tag_change(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="dynamic-control-browser", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class Search(Component):
        citry = engine

        class Kwargs:
            tag: str = "input"
            value: str = ""

        class State:
            value: str = ""

        class Events:
            def update(self, state: Search.State):
                return Search(tag="textarea", value=state.value)

        def template_data(self, kwargs: Search.Kwargs, slots):
            return {"tag": kwargs.tag, "value": kwargs.value}

        template = (
            '<main><c-element c-is="tag" id="dynamic-control" :c-value="update" />'
            '<output id="dynamic-value">{{ value }}</output></main>'
        )

    dispatcher_for(engine)
    calls: list[dict[str, Any]] = []
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on(
        "request",
        lambda request: calls.append(request.post_data_json)
        if request.url.endswith("/ext/events/call") and request.post_data_json
        else None,
    )
    page.goto(serve_live(engine, Search().render().serialize(), "") + "/")

    control = page.locator("#dynamic-control")
    assert control.evaluate("element => element.tagName") == "INPUT"
    control.fill("first")
    page.wait_for_function("__citryRuntime._apps.values().next().value.revision === 1")
    assert control.evaluate("element => element.tagName") == "TEXTAREA"
    assert page.locator("#dynamic-value").text_content() == "first"

    control.fill("second")
    page.wait_for_function("__citryRuntime._apps.values().next().value.revision === 2")
    assert page.locator("#dynamic-value").text_content() == "second"
    flat_calls = [call for request in calls for call in request["calls"]]
    assert [call["handlerName"] for call in flat_calls] == ["update", "update"]
    assert [call["stateUpdates"] for call in flat_calls] == [{"value": "first"}, {"value": "second"}]
    assert faults == []


@pytest.mark.parametrize(
    "fill",
    [
        '<c-child id="direct" @c-click="save" />',
        '<c-provide key="theme" mode="dark"><c-child id="direct" @c-click="save" /></c-provide>',
    ],
    ids=["plain-fill", "transparent-in-fill"],
)
def test_component_event_in_a_fill_dispatches_to_the_fill_author(page: Any, serve_live: Any, fill: str) -> None:
    engine = Citry(secret="fill-author-events-browser", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class Child(Component):
        citry = engine
        template = '<button type="button">save</button>'

    class Box(Component):
        citry = engine
        template = "<section><c-slot /></section>"

    class Page(Component):
        citry = engine

        class Events:
            def save(self):
                return None

        # The listener sits in Page's fill, so Page's handler runs even though
        # Box receives the fill and declares no Events of its own.
        template = f"<main><c-box>{fill}</c-box></main>"

    dispatcher_for(engine)
    calls: list[dict[str, Any]] = []
    page.on(
        "request",
        lambda request: calls.append(request.post_data_json)
        if request.url.endswith("/ext/events/call") and request.post_data_json
        else None,
    )
    page_errors: list[str] = []
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.goto(serve_live(engine, Page().render().serialize(), "") + "/")
    page.get_by_role("button", name="save").click()
    page.wait_for_function("() => !__citryRuntime._apps.values().next().value.busy")

    [call] = [call for request in calls for call in request["calls"]]
    assert call["handlerName"] == "save"
    assert page_errors == []

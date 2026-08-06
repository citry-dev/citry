"""
Tests for the events dispatcher (WP13): the per-call pipeline of
docs/design/events.md 6.1, driven directly through
``EventsDispatcher.dispatch`` / ``dispatch_async`` with no HTTP transport
(the routes get their own suite in test_events_routes.py).

Error messages asserted here are the protocol package's example texts
(packages/protocol/events/v1/tests/), which are contract. Everything else
is authored observe-then-lock: run the dispatcher, read the real envelope,
lock it. Volatile values are pinned the way the sibling suites do it: render
ids via the conftest counter, the token clock via the ``tokens._now``
indirection.
"""

import asyncio
import functools
import importlib.util
import json
import logging
import re
from collections import UserDict
from dataclasses import dataclass
from pathlib import Path

import pytest

from citry import Citry, Component
from citry.ext.events import actions, event
from citry.ext.events.dispatcher import (
    CAPABILITIES_BASELINE_V1,
    CallEvent,
    EventRequest,
    EventsDispatcher,
    TransportContext,
)
from citry.ext.events.errors import EventError
from citry.ext.events.tokens import mint_state_token, verify_state_token
from citry.extension import Extension
from citry.util.routing import RouteResponse

SIGNING_KEY = "test-secret-key"
FIXED_NOW = 1_700_000_000.0


@pytest.fixture(autouse=True)
def _pinned_token_clock(monkeypatch):
    """Pin the token mint clock, so tokens are stable and comparable."""
    monkeypatch.setattr("citry.ext.events.tokens._now", lambda: FIXED_NOW)


def _citry(**kwargs):
    c = Citry(secret=SIGNING_KEY, **kwargs)
    c.set_mounted_prefix("/citry")
    return c


def _counter(c):
    """The protocol spec's conformance component, ported locally."""

    class RenameIn:
        name: str

    class SquareIn:
        value: int

    class FailIn:
        status: int

    class CounterState:
        count: int = 0
        name: str = "Counter"

        def render(self):
            return Counter(count=self.count, name=self.name)

    class Counter(Component):
        citry = c

        class Kwargs:
            count: int = 0
            name: str = "Counter"

        State = CounterState

        class Events:
            def _guard(self):
                if self.event.name == "rename":
                    name = self.event.args.get("name")
                    if name == "admin":
                        raise EventError("The name 'admin' is reserved.", status=403)

            def increment(self, state):
                state.count += 1
                return state.render()

            def rename(self, data: RenameIn, state):
                state.name = data.name
                from citry.ext.events.actions import Dispatch

                return [
                    Dispatch("counter:renamed", {"name": state.name}, delay=1.5, wait=False),
                    {"name": state.name},
                ]

            def crash(self, state):
                raise RuntimeError("boom")

            @event(methods=("GET",))
            def square(self, data: SquareIn):
                from citry.ext.events.actions import Data

                return Data({"value": data.value * data.value})

            def fail(self, data: FailIn):
                raise EventError("The counter cannot do that.", status=data.status)

        def template_data(self, kwargs, slots):
            return {"count": kwargs.count, "name": kwargs.name}

        # The template is spec.md section 10's, byte for byte (indentation
        # included): the spec pins the conformance template exactly.
        template = """
      <div>
        <h2>{{ name }}</h2>
        <button @c-click="increment">
          Clicked {{ count }} times
        </button>
      </div>
    """

    return Counter


def test_counter_template_is_pinned_to_protocol_spec_conformance_component():
    spec_path = Path(__file__).resolve().parents[4] / "packages" / "protocol" / "events" / "v1" / "spec.md"
    section = spec_path.read_text().split("## The conformance component", 1)[1]
    match = re.search(r'template = """(.*?)"""', section, re.DOTALL)
    assert match is not None, "spec.md section 10 no longer contains the Counter template assignment"
    assert _counter(_citry()).template == match.group(1)


def _token(comp_cls, **state_kwargs):
    return mint_state_token(
        comp_cls.State(**state_kwargs),
        class_id=comp_cls.class_id,
        secret=SIGNING_KEY,
        max_age=None,
        max_bytes=8192,
    )


def _ctx(c):
    return TransportContext(transport="http", citry=c)


def _envelope(*calls, **extra):
    normalized = [{"args": {}, **call} if isinstance(call, dict) else call for call in calls]
    return {"protocol": "citry-events/1", "requestId": "r1", "calls": normalized, **extra}


def _dispatch(c, *calls, dispatcher=None, **kwargs):
    dispatcher = dispatcher or EventsDispatcher()
    envelope_extra = kwargs.pop("envelope_extra", {})
    url_component = kwargs.get("url_component")
    url_event = kwargs.get("url_event")
    if url_component is not None and url_event is not None:
        calls = tuple(
            {
                "componentClassId": url_component,
                "handlerName": url_event,
                **call,
            }
            if isinstance(call, dict)
            else call
            for call in calls
        )
    return dispatcher.dispatch(_envelope(*calls, **envelope_extra), _ctx(c), **kwargs)


class TestHappyPaths:
    def test_increment_renders_the_calling_instance(self):
        c = _citry()
        counter = _counter(c)
        call = {
            "componentClassId": counter.class_id,
            "handlerName": "increment",
            "callerRenderId": "c9zk1q00",
            "args": {},
            "stateToken": _token(counter),
            "sendSequence": 4,
        }
        result = _dispatch(c, call)

        assert result["protocol"] == "citry-events/1"
        assert result["requestId"] == "r1"
        [item] = result["results"]
        assert item["ok"] is True
        assert item["sendSequence"] == 4
        [action] = item["actions"]
        assert action["action"] == "render"
        assert action["target"] == "render:c9zk1q00"
        # No capabilities field means the baseline, which excludes morph.
        assert action["swap"] == "replace"
        assert "Clicked 1 times" in action["html"]
        # The fragment carries its own manifests; the state action is not
        # needed because the fresh manifest carries the new token.
        assert "data-citry-events" in action["html"]
        assert all(a["action"] != "state" for a in item["actions"])

    def test_morph_when_the_client_advertises_it(self):
        c = _citry()
        counter = _counter(c)
        call = {
            "componentClassId": counter.class_id,
            "handlerName": "increment",
            "callerRenderId": "i1",
            "stateToken": _token(counter),
        }
        result = _dispatch(c, call, envelope_extra={"capabilities": {"swaps": ["replace", "morph"]}})
        [action] = result["results"][0]["actions"]
        assert action["swap"] == "morph"

    def test_rename_emits_state_first_then_event_then_data(self):
        c = _citry()
        counter = _counter(c)
        call = {
            "componentClassId": counter.class_id,
            "handlerName": "rename",
            "callerRenderId": "c9zk1q00",
            "args": {"name": "Tally"},
            "stateToken": _token(counter),
            "sendSequence": 5,
        }
        result = _dispatch(c, call)
        [item] = result["results"]
        assert item["ok"] is True
        assert item["sendSequence"] == 5
        kinds = [action["action"] for action in item["actions"]]
        assert kinds == ["state", "event", "data"]
        state_action, event_action, data_action = item["actions"]
        # The refreshed token carries the mutated state.
        assert state_action["targetRenderId"] == "c9zk1q00"
        verified = verify_state_token(state_action["stateToken"], cls=counter, secrets=[SIGNING_KEY])
        assert verified.state_kwargs == {"count": 0, "name": "Tally"}
        # The handler did not address the dispatch, so the server
        # self-addressed it to the calling instance, with the timing fields.
        assert event_action == {
            "action": "event",
            "eventName": "counter:renamed",
            "detail": {"name": "Tally"},
            "target": "render:c9zk1q00",
            "delay": 1.5,
            "wait": False,
        }
        assert data_action == {"action": "data", "value": {"name": "Tally"}}

    def test_stateless_data_call_has_no_epoch_key(self):
        c = _citry()
        counter = _counter(c)
        call = {"componentClassId": counter.class_id, "handlerName": "square", "args": {"value": 7}}
        result = _dispatch(c, call)
        [item] = result["results"]
        assert item == {"ok": True, "actions": [{"action": "data", "value": {"value": 49}}]}

    def test_batch_mixes_outcomes_per_slot(self):
        c = _citry()
        counter = _counter(c)
        ok_call = {"componentClassId": counter.class_id, "handlerName": "square", "args": {"value": 3}}
        bad_call = {"componentClassId": counter.class_id, "handlerName": "crash", "stateToken": _token(counter)}
        result = _dispatch(c, ok_call, bad_call)
        first, second = result["results"]
        assert first["ok"] is True
        assert second["ok"] is False
        assert second["error"]["code"] == "handler_error"

    def test_compat_targetless_render_uses_the_internal_root_target(self):
        c = _citry()

        class Result(Component):
            citry = c
            template = "<p>done</p>"

        class Endpoint(Component):
            citry = c
            template = "<div>e</div>"

            class Events:
                def run(self):
                    return Result()

        ctx = TransportContext(transport="http", citry=c, response_mode="compat")
        envelope = _envelope({"componentClassId": Endpoint.class_id, "handlerName": "run"})
        [item] = EventsDispatcher().dispatch(envelope, ctx)["results"]
        [action] = item["actions"]
        assert action["action"] == "render"
        assert action["target"] == ":root"


class TestStateResign:
    def test_mutation_without_render_prepends_the_state_action(self):
        c = _citry()
        counter = _counter(c)

        class Bumper(Component):
            citry = c
            State = counter.State
            template = "<div>b</div>"

            class Events:
                def bump(self, state):
                    state.count += 10
                    return {"count": state.count}

        call = {
            "componentClassId": Bumper.class_id,
            "handlerName": "bump",
            "callerRenderId": "i1",
            "stateToken": _token(Bumper, count=1),
        }
        result = _dispatch(c, call)
        [item] = result["results"]
        kinds = [action["action"] for action in item["actions"]]
        assert kinds == ["state", "data"]
        verified = verify_state_token(item["actions"][0]["stateToken"], cls=Bumper, secrets=[SIGNING_KEY])
        assert verified.state_kwargs["count"] == 11

    def test_render_targeting_elsewhere_still_refreshes_the_token(self):
        # A render that does not re-render the calling instance carries no
        # fresh manifest for it, so the companion state action still rides.
        c = _citry()
        counter = _counter(c)

        class Badge(Component):
            citry = c
            template = "<span>badge</span>"

        class Mutator(Component):
            citry = c
            State = counter.State
            template = "<div>m</div>"

            class Events:
                def touch(self, state):
                    from citry.ext.events.actions import Render

                    state.count += 1
                    return Render(Badge(), target="#badge")

        call = {
            "componentClassId": Mutator.class_id,
            "handlerName": "touch",
            "callerRenderId": "i9",
            "stateToken": _token(Mutator),
        }
        result = _dispatch(c, call)
        kinds = [action["action"] for action in result["results"][0]["actions"]]
        assert kinds == ["state", "render"]

    def test_unchanged_state_mints_nothing(self):
        c = _citry()
        counter = _counter(c)
        call = {
            "componentClassId": counter.class_id,
            "handlerName": "rename",
            "args": {"name": "Counter"},
            "stateToken": _token(counter),
            "callerRenderId": "i1",
        }
        # Renaming to the same name leaves the state byte-identical.
        result = _dispatch(c, call)
        kinds = [action["action"] for action in result["results"][0]["actions"]]
        assert kinds == ["event", "data"]

    def test_mutation_without_an_instance_omits_the_state_refresh(self, caplog):
        c = _citry()
        counter = _counter(c)

        class Mutator(Component):
            citry = c
            State = counter.State
            template = "<div>m</div>"

            class Events:
                def bump(self, state):
                    state.count += 1
                    return {"count": state.count}

        call = {"componentClassId": Mutator.class_id, "handlerName": "bump", "stateToken": _token(Mutator)}
        with caplog.at_level(logging.DEBUG, logger="citry"):
            [item] = _dispatch(c, call)["results"]
        assert item["actions"] == [{"action": "data", "value": {"count": 1}}]
        assert any("carries no instance" in record.message for record in caplog.records)

    def test_mutation_without_the_state_capability_keeps_handler_actions(self, caplog):
        c = _citry()
        counter = _counter(c)

        class Mutator(Component):
            citry = c
            State = counter.State
            template = "<div>m</div>"

            class Events:
                def bump(self, state):
                    state.count += 1
                    return {"count": state.count}

        call = {
            "componentClassId": Mutator.class_id,
            "handlerName": "bump",
            "callerRenderId": "i1",
            "stateToken": _token(Mutator),
        }
        with caplog.at_level(logging.WARNING, logger="citry"):
            [item] = _dispatch(c, call, envelope_extra={"capabilities": {"actions": ["data"]}})["results"]
        assert item["actions"] == [{"action": "data", "value": {"count": 1}}]
        assert any("exclude the 'state' action" in record.message for record in caplog.records)


class TestUpdates:
    def _doc(self, c):
        class DocState:
            title: str = ""
            secret_note: str = ""
            _public = ("title",)

        class Doc(Component):
            citry = c
            State = DocState
            template = "<div>d</div>"

            class Events:
                def read_title(self, state):
                    return {"title": state.title}

        return Doc

    def test_updates_apply_before_the_handler_and_resign(self):
        c = _citry()
        doc = self._doc(c)
        call = {
            "componentClassId": doc.class_id,
            "handlerName": "read_title",
            "callerRenderId": "i1",
            "stateToken": _token(doc),
            "stateUpdates": {"title": "Drafts"},
        }
        result = _dispatch(c, call)
        [item] = result["results"]
        kinds = [action["action"] for action in item["actions"]]
        # The handler saw the update, and the applied update re-signed the
        # token even though the handler itself mutated nothing.
        assert kinds == ["state", "data"]
        assert item["actions"][1]["value"] == {"title": "Drafts"}

    def test_non_writable_update_is_a_per_field_422(self):
        c = _citry()
        doc = self._doc(c)
        call = {
            "componentClassId": doc.class_id,
            "handlerName": "read_title",
            "stateToken": _token(doc),
            "stateUpdates": {"secret_note": "x"},
        }
        result = _dispatch(c, call)
        error = result["results"][0]["error"]
        assert error["status"] == 422
        assert error["code"] == "invalid_args"
        assert "secret_note" in error["fieldErrors"]

    def test_updates_on_a_stateless_component_are_rejected(self):
        c = _citry()

        class Plain(Component):
            citry = c
            template = "<div>p</div>"

            class Events:
                def ping(self):
                    return {"pong": True}

        call = {"componentClassId": Plain.class_id, "handlerName": "ping", "stateUpdates": {"x": 1}}
        result = _dispatch(c, call)
        error = result["results"][0]["error"]
        assert error["status"] == 422
        assert error["code"] == "invalid_args"
        assert "declares no State class" in error["message"]


class TestErrors:
    """Each wire code; messages are the protocol examples' locked texts."""

    def test_unknown_component(self):
        c = _citry()
        result = _dispatch(c, {"componentClassId": "Gadget_000000", "handlerName": "square", "args": {}})
        error = result["results"][0]["error"]
        assert error == {
            "status": 404,
            "code": "unknown_component",
            "message": "No component with class id 'Gadget_000000' is registered.",
        }

    def test_unknown_event(self):
        c = _citry()
        counter = _counter(c)
        result = _dispatch(c, {"componentClassId": counter.class_id, "handlerName": "reset", "args": {}})
        error = result["results"][0]["error"]
        assert error == {
            "status": 404,
            "code": "unknown_event",
            "message": "Component 'Counter' has no event 'reset'.",
        }

    def test_invalid_state_on_a_tampered_token(self):
        c = _citry()
        counter = _counter(c)
        token = _token(counter)
        # Corrupt the payload segment: the token no longer parses as one.
        prefix, payload, sig = token.split(".")
        broken = f"{prefix}.{payload[:-4]}!!.{sig}"
        result = _dispatch(c, {"componentClassId": counter.class_id, "handlerName": "increment", "stateToken": broken})
        error = result["results"][0]["error"]
        assert error == {
            "status": 403,
            "code": "invalid_state",
            "message": "The state token failed verification (tampered or malformed).",
        }

    def test_stale_state_on_a_rotated_out_secret(self):
        c = _citry()
        counter = _counter(c)
        stale = mint_state_token(
            counter.State(),
            class_id=counter.class_id,
            secret="an-older-rotated-out-secret",  # noqa: S106 - a dummy test secret, not a credential
            max_age=None,
            max_bytes=8192,
        )
        result = _dispatch(c, {"componentClassId": counter.class_id, "handlerName": "increment", "stateToken": stale})
        error = result["results"][0]["error"]
        assert error == {
            "status": 409,
            "code": "stale_state",
            "message": "The state token is stale (expired or rotated out); reload the page to get a fresh one.",
        }

    def test_missing_token_for_a_state_declaring_handler(self):
        c = _citry()
        counter = _counter(c)
        result = _dispatch(c, {"componentClassId": counter.class_id, "handlerName": "increment"})
        assert result["results"][0]["error"]["code"] == "invalid_state"

    def test_forbidden_from_the_guard_echoes_epoch(self):
        c = _citry()
        counter = _counter(c)
        call = {
            "componentClassId": counter.class_id,
            "handlerName": "rename",
            "args": {"name": "admin"},
            "stateToken": _token(counter),
            "sendSequence": 7,
        }
        result = _dispatch(c, call)
        [item] = result["results"]
        assert item["ok"] is False
        assert item["sendSequence"] == 7
        assert item["error"] == {
            "status": 403,
            "code": "forbidden",
            "message": "The name 'admin' is reserved.",
        }

    def test_invalid_args_carries_the_per_field_map(self):
        c = _citry()
        counter = _counter(c)
        call = {
            "componentClassId": counter.class_id,
            "handlerName": "rename",
            "args": {},
            "stateToken": _token(counter),
        }
        result = _dispatch(c, call)
        error = result["results"][0]["error"]
        assert error == {
            "status": 422,
            "code": "invalid_args",
            "message": "The args for event 'rename' on component 'Counter' did not validate.",
            "fieldErrors": {"name": "This field is required."},
        }

    def test_args_on_a_handler_without_data_are_rejected(self):
        c = _citry()
        counter = _counter(c)
        call = {
            "componentClassId": counter.class_id,
            "handlerName": "increment",
            "args": {"oops": 1},
            "stateToken": _token(counter),
        }
        result = _dispatch(c, call)
        error = result["results"][0]["error"]
        assert error["code"] == "invalid_args"
        assert error["fieldErrors"] == {"oops": "Unexpected field: not declared on the schema."}

    def test_handler_error_is_generic_without_debug(self):
        c = _citry()
        counter = _counter(c)
        call = {"componentClassId": counter.class_id, "handlerName": "crash", "stateToken": _token(counter)}
        result = _dispatch(c, call)
        error = result["results"][0]["error"]
        assert error == {
            "status": 500,
            "code": "handler_error",
            "message": "The event handler raised an unexpected error.",
        }

    def test_handler_error_names_the_exception_in_debug(self, caplog):
        c = _citry()
        counter = _counter(c)
        call = {"componentClassId": counter.class_id, "handlerName": "crash", "stateToken": _token(counter)}
        with caplog.at_level(logging.DEBUG, logger="citry"):
            result = _dispatch(c, call)
        message = result["results"][0]["error"]["message"]
        assert "RuntimeError: boom" in message
        # Never a traceback on the wire.
        assert "Traceback" not in message

    def test_protocol_mismatch(self):
        c = _citry()
        counter = _counter(c)
        envelope = {
            "protocol": "citry-events/2",
            "requestId": "r9",
            "calls": [{"componentClassId": counter.class_id, "handlerName": "square", "args": {"value": 2}}],
        }
        result = EventsDispatcher().dispatch(envelope, _ctx(c))
        assert result["requestId"] == "r9"
        [item] = result["results"]
        assert item["error"] == {
            "status": 400,
            "code": "protocol_mismatch",
            "message": "Unknown protocol 'citry-events/2'; this server speaks 'citry-events/1'.",
        }

    def test_calls_cap_mirrors_into_every_slot(self):
        c = _citry()
        counter = _counter(c)
        calls = [{"componentClassId": counter.class_id, "handlerName": "square", "args": {"value": 2}}] * 17
        result = EventsDispatcher().dispatch(_envelope(*calls), _ctx(c))
        assert len(result["results"]) == 17
        for item in result["results"]:
            assert item["error"] == {
                "status": 413,
                "code": "payload_too_large",
                "message": "The envelope carries 17 calls; the cap is 16.",
            }

    def test_structural_rejections(self):
        c = _citry()
        # Not an envelope object at all.
        result = EventsDispatcher().dispatch(["nope"], _ctx(c))
        assert result["requestId"] is None
        assert result["results"][0]["error"]["code"] == "protocol_mismatch"
        # No calls.
        result = EventsDispatcher().dispatch({"protocol": "citry-events/1", "requestId": "r1", "calls": []}, _ctx(c))
        assert result["results"][0]["error"]["code"] == "protocol_mismatch"
        # A call with a bad epoch.
        counter = _counter(c)
        bad_epoch = {
            "componentClassId": counter.class_id,
            "handlerName": "square",
            "args": {"value": 1},
            "sendSequence": True,
        }
        result = _dispatch(c, bad_epoch)
        assert (
            result["results"][0]["error"]["message"] == "The call's 'sendSequence' must be an integer of at least 0."
        )

    @pytest.mark.parametrize(
        ("field", "message"),
        [
            ("componentClassId", "The call's 'componentClassId' must be a non-empty string."),
            ("handlerName", "The call's 'handlerName' must be a non-empty string."),
            ("callerRenderId", "The call's 'callerRenderId' must be a non-empty string."),
            ("args", "The call's 'args' must be an object."),
            ("stateToken", "The call's 'stateToken' must be a non-empty string."),
            ("stateUpdates", "The call's 'stateUpdates' must be an object."),
        ],
    )
    def test_present_call_fields_reject_null(self, field, message):
        c = _citry()
        counter = _counter(c)
        call = {
            "componentClassId": counter.class_id,
            "handlerName": "square",
            "args": {"value": 1},
            field: None,
        }
        result = _dispatch(c, call)
        assert result["results"][0]["error"] == {
            "status": 400,
            "code": "protocol_mismatch",
            "message": message,
        }

    @pytest.mark.parametrize("capabilities", [None, {"actions": None}, {"swaps": None}])
    def test_present_capabilities_reject_null(self, capabilities):
        c = _citry()
        counter = _counter(c)
        call = {"componentClassId": counter.class_id, "handlerName": "square", "args": {"value": 1}}
        result = _dispatch(c, call, envelope_extra={"capabilities": capabilities})
        assert result["results"][0]["error"]["code"] == "protocol_mismatch"

    @pytest.mark.parametrize("use_async_dispatch", [False, True])
    def test_malformed_later_call_rejects_batch_before_any_handler_runs(self, use_async_dispatch):
        c = _citry()
        runs: list[str] = []

        class Probe(Component):
            citry = c
            template = "<div>probe</div>"

            class Events:
                def run(self):
                    runs.append("ran")

        envelope = _envelope(
            {
                "componentClassId": Probe.class_id,
                "handlerName": "run",
                "sendSequence": 1,
            },
            {
                "componentClassId": Probe.class_id,
                "handlerName": "run",
                "sendSequence": 2,
                "extra": True,
            },
        )
        dispatcher = EventsDispatcher()
        if use_async_dispatch:
            result = asyncio.run(dispatcher.dispatch_async(envelope, _ctx(c)))
        else:
            result = dispatcher.dispatch(envelope, _ctx(c))

        assert runs == []
        assert [item["sendSequence"] for item in result["results"]] == [1, 2]
        assert {item["error"]["code"] for item in result["results"]} == {"protocol_mismatch"}
        assert all("unknown field(s): 'extra'" in item["error"]["message"] for item in result["results"])

    @pytest.mark.parametrize("use_async_dispatch", [False, True])
    def test_non_json_later_call_rejects_batch_before_any_handler_runs(self, use_async_dispatch):
        c = _citry()
        runs: list[str] = []

        class Probe(Component):
            citry = c
            template = "<div>probe</div>"

            class Events:
                def run(self):
                    runs.append("ran")

        envelope = _envelope(
            {"componentClassId": Probe.class_id, "handlerName": "run", "args": {}, "sendSequence": 1},
            {
                "componentClassId": Probe.class_id,
                "handlerName": "run",
                "args": {"value": float("inf")},
                "sendSequence": 2,
            },
        )
        dispatcher = EventsDispatcher()
        if use_async_dispatch:
            result = asyncio.run(dispatcher.dispatch_async(envelope, _ctx(c)))
        else:
            result = dispatcher.dispatch(envelope, _ctx(c))

        assert runs == []
        assert [item["sendSequence"] for item in result["results"]] == [1, 2]
        assert {item["error"]["code"] for item in result["results"]} == {"protocol_mismatch"}
        assert all("only strict JSON values" in item["error"]["message"] for item in result["results"])

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("args", {1: "not a JSON object key"}),
            ("args", {"value": (1, 2)}),
            ("stateUpdates", {"value": float("nan")}),
        ],
    )
    def test_application_bags_reject_non_json_values(self, field, value):
        c = _citry()
        counter = _counter(c)
        call = {"componentClassId": counter.class_id, "handlerName": "square", "args": {"value": 2}, field: value}
        [item] = _dispatch(c, call)["results"]
        assert item["error"] == {
            "status": 400,
            "code": "protocol_mismatch",
            "message": f"The call's {field!r} must contain only strict JSON values under string keys.",
        }

    def test_application_bags_reject_cycles(self):
        c = _citry()
        counter = _counter(c)
        cycle: list[object] = []
        cycle.append(cycle)
        call = {
            "componentClassId": counter.class_id,
            "handlerName": "square",
            "args": {"value": cycle},
        }
        [item] = _dispatch(c, call)["results"]
        assert item["error"]["code"] == "protocol_mismatch"
        assert "only strict JSON values" in item["error"]["message"]

    def test_invalid_protocol_mirrors_slots_and_only_valid_epochs(self):
        c = _citry()
        envelope = {
            "requestId": "r9",
            "calls": ["not-a-call", {"componentClassId": "X", "handlerName": "go", "sendSequence": 8}],
        }
        first, second = EventsDispatcher().dispatch(envelope, _ctx(c))["results"]
        assert first["error"]["message"] == "The envelope names no protocol; this server speaks 'citry-events/1'."
        assert "sendSequence" not in first
        assert second["sendSequence"] == 8
        assert second["error"] == first["error"]

    @pytest.mark.parametrize("envelope_id", [None, ""])
    def test_missing_or_empty_envelope_id_is_rejected(self, envelope_id):
        c = _citry()
        counter = _counter(c)
        call = {"componentClassId": counter.class_id, "handlerName": "square", "args": {"value": 2}}
        envelope = {"protocol": "citry-events/1", "requestId": envelope_id, "calls": [call]}
        [item] = EventsDispatcher().dispatch(envelope, _ctx(c))["results"]
        assert item["error"]["message"] == "The envelope carries no 'requestId' string."

    @pytest.mark.parametrize("capabilities", ["all", {"actions": ["data", 1]}])
    def test_invalid_capability_shapes_are_rejected(self, capabilities):
        c = _citry()
        counter = _counter(c)
        call = {"componentClassId": counter.class_id, "handlerName": "square", "args": {"value": 2}}
        [item] = _dispatch(c, call, envelope_extra={"capabilities": capabilities})["results"]
        assert item["error"]["code"] == "protocol_mismatch"

    @pytest.mark.parametrize(("field", "value"), [("args", []), ("stateUpdates", "title")])
    def test_args_and_updates_must_be_objects(self, field, value):
        c = _citry()
        counter = _counter(c)
        call = {"componentClassId": counter.class_id, "handlerName": "square", "args": {"value": 2}, field: value}
        [item] = _dispatch(c, call)["results"]
        assert item["error"]["message"] == f"The call's {field!r} must be an object."

    def test_non_object_call_is_rejected_by_async_dispatch(self):
        c = _citry()

        async def run():
            return await EventsDispatcher().dispatch_async(_envelope("not-a-call"), _ctx(c))

        [item] = asyncio.run(run())["results"]
        assert item["error"] == {
            "status": 400,
            "code": "protocol_mismatch",
            "message": "Each entry of 'calls' must be a call object.",
        }

    def test_async_dispatch_returns_an_envelope_rejection(self):
        c = _citry()

        async def run():
            envelope = {"protocol": "citry-events/1", "requestId": "r1", "calls": []}
            return await EventsDispatcher().dispatch_async(envelope, _ctx(c))

        [item] = asyncio.run(run())["results"]
        assert item["error"]["code"] == "protocol_mismatch"

    def test_verified_token_with_an_old_state_shape_is_stale(self):
        c = _citry()

        class CurrentState:
            title: str = ""

        class Current(Component):
            citry = c
            State = CurrentState
            template = "<div>c</div>"

            class Events:
                def read(self, state):
                    return {"title": state.title}

        @dataclass
        class LegacyState:
            old_title: str = "draft"

        token = mint_state_token(
            LegacyState(),
            class_id=Current.class_id,
            secret=SIGNING_KEY,
            max_age=None,
            max_bytes=8192,
        )
        call = {"componentClassId": Current.class_id, "handlerName": "read", "stateToken": token, "sendSequence": 6}
        [item] = _dispatch(c, call)["results"]
        assert item["sendSequence"] == 6
        assert item["error"]["code"] == "stale_state"

    def test_state_mutated_to_a_non_json_value_becomes_handler_error(self, caplog):
        c = _citry()

        class OpaqueState:
            value: object = 0

        class Opaque(Component):
            citry = c
            State = OpaqueState
            template = "<div>o</div>"

            class Events:
                def break_state(self, state):
                    state.value = object()

        call = {
            "componentClassId": Opaque.class_id,
            "handlerName": "break_state",
            "callerRenderId": "i1",
            "stateToken": _token(Opaque),
        }
        with caplog.at_level(logging.DEBUG, logger="citry"):
            [item] = _dispatch(c, call)["results"]
        assert item["error"]["code"] == "handler_error"
        assert "ValueError" in item["error"]["message"]


class TestUrlAuthoritative:
    def test_body_component_mismatch_is_rejected(self):
        c = _citry()
        counter = _counter(c)
        call = {"componentClassId": "Other_111111", "handlerName": "square", "args": {"value": 2}}
        result = _dispatch(c, call, url_component=counter.class_id, url_event="square")
        error = result["results"][0]["error"]
        assert error["status"] == 400
        assert "the URL is authoritative" in error["message"]

    def test_body_event_mismatch_is_rejected(self):
        c = _citry()
        counter = _counter(c)
        call = {"componentClassId": counter.class_id, "handlerName": "rename", "args": {}}
        result = _dispatch(c, call, url_component=counter.class_id, url_event="square")
        assert "the URL is authoritative" in result["results"][0]["error"]["message"]

    def test_url_binding_fills_absent_body_fields(self):
        c = _citry()
        counter = _counter(c)
        result = _dispatch(c, {"args": {"value": 6}}, url_component=counter.class_id, url_event="square")
        assert result["results"][0]["actions"] == [{"action": "data", "value": {"value": 36}}]

    def test_batch_requires_component_and_event(self):
        c = _citry()
        result = _dispatch(c, {"handlerName": "square", "args": {}})
        assert "missing required field 'componentClassId'" in result["results"][0]["error"]["message"]
        counter = _counter(c)
        result = _dispatch(c, {"componentClassId": counter.class_id, "args": {}})
        assert "missing required field 'handlerName'" in result["results"][0]["error"]["message"]


class TestPipelineOrder:
    def test_guard_sees_the_context_hooks_result(self):
        c = _citry()
        seen = {}

        class GuardedState:
            n: int = 0

        class Guarded(Component):
            citry = c
            State = GuardedState
            template = "<div>g</div>"

            class Events:
                def _context(self):
                    return {"user": "ada"}

                def _guard(self):
                    seen["context"] = self.context

                def go(self, state, context):
                    return {"user": context["user"]}

        call = {"componentClassId": Guarded.class_id, "handlerName": "go", "stateToken": _token(Guarded)}
        result = _dispatch(c, call)
        assert seen["context"] == {"user": "ada"}
        assert result["results"][0]["actions"][0]["value"] == {"user": "ada"}

    def test_event_error_from_the_context_hook_answers_the_call(self):
        c = _citry()

        class Ctxed(Component):
            citry = c
            template = "<div>c</div>"

            class Events:
                def _context(self):
                    raise EventError("No session.", status=403)

                def go(self):
                    return None

        result = _dispatch(c, {"componentClassId": Ctxed.class_id, "handlerName": "go"})
        assert result["results"][0]["error"]["code"] == "forbidden"

    def test_on_event_can_answer_and_preempts_the_handler(self):
        ran = []

        class Limiter(Extension):
            name = "limiter"

            def on_event(self, ctx):
                ran.append(("hook", ctx.handler.name))
                return {"limited": True}

        c = _citry(extensions=[Limiter])

        class Pinged(Component):
            citry = c
            template = "<div>p</div>"

            class Events:
                def ping(self):
                    ran.append(("handler", "ping"))
                    return {"pong": True}

        result = _dispatch(c, {"componentClassId": Pinged.class_id, "handlerName": "ping"})
        assert ran == [("hook", "ping")]
        assert result["results"][0]["actions"] == [{"action": "data", "value": {"limited": True}}]

    def test_on_event_fires_after_validation_and_can_veto(self):
        fired = []

        class Veto(Extension):
            name = "veto"

            def on_event(self, ctx):
                fired.append(ctx.handler.name)
                raise EventError("Slow down.", status=403)

        c = _citry(extensions=[Veto])
        counter = _counter(c)

        # Invalid args never reach the hook (validation is earlier).
        bad = {
            "componentClassId": counter.class_id,
            "handlerName": "rename",
            "args": {},
            "stateToken": _token(counter),
        }
        result = _dispatch(c, bad)
        assert result["results"][0]["error"]["code"] == "invalid_args"
        assert fired == []

        good = {"componentClassId": counter.class_id, "handlerName": "square", "args": {"value": 2}}
        result = _dispatch(c, good)
        assert fired == ["square"]
        assert result["results"][0]["error"]["message"] == "Slow down."

    def test_on_event_result_maps_the_encoded_actions(self):
        class Rewriter(Extension):
            name = "rewriter"

            def on_event_result(self, ctx):
                return [*ctx.actions, {"action": "data", "value": {"extra": True}}]

        c = _citry(extensions=[Rewriter])

        class Silent(Component):
            citry = c
            template = "<div>s</div>"

            class Events:
                def go(self):
                    return None

        result = _dispatch(c, {"componentClassId": Silent.class_id, "handlerName": "go"})
        assert result["results"][0]["actions"] == [{"action": "data", "value": {"extra": True}}]

    def test_result_hook_sees_handler_actions_before_state_and_may_return_a_tuple(self):
        observed = []

        class Observer(Extension):
            name = "observer"

            def on_event_result(self, ctx):
                observed.append(ctx.actions)
                return tuple(ctx.actions)

        c = _citry(extensions=[Observer])

        class CountState:
            count: int = 0

        class Counter(Component):
            citry = c
            State = CountState
            template = "<div>c</div>"

            class Events:
                def increment(self, state):
                    state.count += 1
                    return {"count": state.count}

        call = {
            "componentClassId": Counter.class_id,
            "handlerName": "increment",
            "callerRenderId": "i1",
            "stateToken": _token(Counter),
        }
        [item] = _dispatch(c, call)["results"]
        assert observed == [[{"action": "data", "value": {"count": 1}}]]
        assert [action["action"] for action in item["actions"]] == ["state", "data"]

    def test_result_hook_cannot_inject_an_unadvertised_action(self):
        class Injector(Extension):
            name = "injector"

            def on_event_result(self, ctx):
                return [*ctx.actions, {"action": "event", "eventName": "injected"}]

        c = _citry(extensions=[Injector])

        class Endpoint(Component):
            citry = c
            template = "<div>e</div>"

            class Events:
                def read(self):
                    return {"value": 1}

        call = {"componentClassId": Endpoint.class_id, "handlerName": "read"}
        [item] = _dispatch(c, call, envelope_extra={"capabilities": {"actions": ["data"]}})["results"]
        assert item["error"]["code"] == "handler_error"

    @pytest.mark.parametrize(
        "replacement",
        [
            ["not-an-object"],
            [{"action": "unknown"}],
            [{"action": "data", "value": 1, "delay": True}],
            [{"action": "data", "value": 1, "wait": 1}],
            [{"action": "data", "value": 1, "wait": False}],
            [{"action": "render", "target": "#target", "swap": "replace", "html": 1}],
            [{"action": "render", "target": "", "swap": "replace", "html": "<p>x</p>"}],
            [{"action": "render", "target": "render:MixedCase", "swap": "replace", "html": "<p>x</p>"}],
            [{"action": "data"}],
            [{"action": "state", "targetRenderId": "", "stateToken": "token"}],
            [{"action": "state", "targetRenderId": "MixedCase", "stateToken": "token"}],
            [{"action": "event", "eventName": "citry:reserved"}],
            [{"action": "redirect", "url": ""}],
            [{"action": "url", "url": "/next", "mode": "reload"}],
            [{"action": "data", "value": 1}, {"action": "data", "value": 2}],
        ],
    )
    def test_malformed_result_hook_actions_become_handler_error(self, replacement):
        class Broken(Extension):
            name = "broken"

            def on_event_result(self, ctx):
                return replacement

        c = _citry(extensions=[Broken])

        class Endpoint(Component):
            citry = c
            template = "<div>e</div>"

            class Events:
                def read(self):
                    return {"value": 1}

        [item] = _dispatch(c, {"componentClassId": Endpoint.class_id, "handlerName": "read"})["results"]
        assert item["error"]["code"] == "handler_error"

    @pytest.mark.parametrize(
        "replacement",
        [
            [{"action": "data", "value": object()}],
            [{"action": "data", "value": 1, "delay": float("nan")}],
            [{"action": "event", "eventName": "done", "detail": object()}],
        ],
    )
    def test_result_hook_actions_must_be_strict_json_for_every_transport(self, replacement):
        class Broken(Extension):
            name = "broken"

            def on_event_result(self, ctx):
                return replacement

        c = _citry(extensions=[Broken])

        class Endpoint(Component):
            citry = c
            template = """
                <div>e</div>
            """

            class Events:
                def read(self):
                    return {"value": 1}

        envelope = _dispatch(c, {"componentClassId": Endpoint.class_id, "handlerName": "read", "sendSequence": 3})
        assert envelope["results"] == [
            {
                "ok": False,
                "sendSequence": 3,
                "error": {
                    "status": 500,
                    "code": "handler_error",
                    "message": (
                        "The handler returned a value strict JSON cannot encode (for example, a Decimal or a "
                        "non-finite number such as inf or nan)."
                    ),
                },
            }
        ]
        assert _result_schema_problems(envelope) == []

    def test_on_event_error_can_replace_the_result(self):
        captured = {}

        class Sentry(Extension):
            name = "sentry"

            def on_event_error(self, ctx):
                captured["error"] = str(ctx.error)
                return {
                    "ok": False,
                    "error": {
                        "status": 500,
                        "code": "handler_error",
                        "message": "Reported.",
                        "fieldErrors": {"report": "saved"},
                    },
                }

        c = _citry(extensions=[Sentry])
        counter = _counter(c)
        call = {"componentClassId": counter.class_id, "handlerName": "crash", "stateToken": _token(counter)}
        result = _dispatch(c, call)
        assert captured["error"] == "boom"
        assert result["results"][0]["error"]["message"] == "Reported."
        assert result["results"][0]["error"]["fieldErrors"] == {"report": "saved"}

    def test_error_hook_non_json_mapping_retains_the_generic_result(self):
        class MappingReporter(Extension):
            name = "mapping_reporter"

            def on_event_error(self, ctx):
                return {
                    "ok": False,
                    "error": UserDict({"status": 500, "code": "handler_error", "message": "Reported."}),
                }

        c = _citry(extensions=[MappingReporter])
        counter = _counter(c)
        call = {"componentClassId": counter.class_id, "handlerName": "crash", "stateToken": _token(counter)}
        [item] = _dispatch(c, call)["results"]
        assert item == {
            "ok": False,
            "error": {
                "status": 500,
                "code": "handler_error",
                "message": "The event handler raised an unexpected error.",
            },
        }

    def test_context_failure_reaches_error_hook_with_resolved_context_and_exact_epoch(self):
        captured = {}

        class Reporter(Extension):
            name = "reporter"

            def on_event_error(self, ctx):
                captured.update(
                    component=ctx.component_class,
                    handler=ctx.handler,
                    events=ctx.events,
                    error=ctx.error,
                )
                return {
                    "ok": False,
                    "sendSequence": 999,
                    "error": {"status": 503, "code": "error", "message": "Context unavailable."},
                }

        c = _citry(extensions=[Reporter])

        class Contextual(Component):
            citry = c
            template = "<div>c</div>"

            class Events:
                def _context(self):
                    raise RuntimeError("context database failed")

                def run(self):
                    return None

        call = {"componentClassId": Contextual.class_id, "handlerName": "run", "sendSequence": 4}
        envelope = _dispatch(c, call)
        [item] = envelope["results"]
        assert captured["component"] is Contextual
        assert captured["handler"].name == "run"
        assert captured["events"].event.name == "run"
        assert str(captured["error"]) == "context database failed"
        assert item == {
            "ok": False,
            "sendSequence": 4,
            "error": {"status": 503, "code": "error", "message": "Context unavailable."},
        }
        assert _result_schema_problems(envelope) == []

    def test_error_hook_exception_retains_the_generic_result(self, caplog):
        class BrokenReporter(Extension):
            name = "broken_reporter"

            def on_event_error(self, ctx):
                raise RuntimeError("reporting failed")

        c = _citry(extensions=[BrokenReporter])
        counter = _counter(c)
        call = {
            "componentClassId": counter.class_id,
            "handlerName": "crash",
            "stateToken": _token(counter),
            "sendSequence": 7,
        }
        with caplog.at_level(logging.ERROR, logger="citry"):
            [item] = _dispatch(c, call)["results"]
        assert item == {
            "ok": False,
            "sendSequence": 7,
            "error": {
                "status": 500,
                "code": "handler_error",
                "message": "The event handler raised an unexpected error.",
            },
        }
        assert any("on_event_error hook" in record.message and "raised" in record.message for record in caplog.records)

    def test_error_hook_in_place_mutation_without_replacement_cannot_change_the_fallback(self):
        class MutatingReporter(Extension):
            name = "mutating_reporter"

            def on_event_error(self, ctx):
                ctx.result.clear()
                ctx.result.update({"ok": True, "actions": "not-an-array"})

        c = _citry(extensions=[MutatingReporter])
        counter = _counter(c)
        call = {
            "componentClassId": counter.class_id,
            "handlerName": "crash",
            "stateToken": _token(counter),
            "sendSequence": 7,
        }
        envelope = _dispatch(c, call)
        assert envelope["results"] == [
            {
                "ok": False,
                "sendSequence": 7,
                "error": {
                    "status": 500,
                    "code": "handler_error",
                    "message": "The event handler raised an unexpected error.",
                },
            }
        ]
        assert _result_schema_problems(envelope) == []

    def test_error_hook_in_place_mutation_then_exception_cannot_change_the_fallback(self, caplog):
        class MutatingReporter(Extension):
            name = "mutating_reporter"

            def on_event_error(self, ctx):
                ctx.result["error"]["status"] = 200
                ctx.result["error"]["message"] = "Leaked mutation."
                raise RuntimeError("reporting failed")

        c = _citry(extensions=[MutatingReporter])
        counter = _counter(c)
        call = {
            "componentClassId": counter.class_id,
            "handlerName": "crash",
            "stateToken": _token(counter),
            "sendSequence": 7,
        }
        with caplog.at_level(logging.ERROR, logger="citry"):
            envelope = _dispatch(c, call)
        assert envelope["results"] == [
            {
                "ok": False,
                "sendSequence": 7,
                "error": {
                    "status": 500,
                    "code": "handler_error",
                    "message": "The event handler raised an unexpected error.",
                },
            }
        ]
        assert _result_schema_problems(envelope) == []
        assert any("on_event_error hook" in record.message and "raised" in record.message for record in caplog.records)

    def test_malformed_error_hook_replacement_retains_the_generic_result(self, caplog):
        class BrokenReporter(Extension):
            name = "broken_reporter"

            def on_event_error(self, ctx):
                return {
                    "ok": False,
                    "sendSequence": 999,
                    "error": {"status": 418, "code": "handler_error", "message": "Wrong pairing."},
                }

        c = _citry(extensions=[BrokenReporter])
        counter = _counter(c)
        call = {
            "componentClassId": counter.class_id,
            "handlerName": "crash",
            "stateToken": _token(counter),
            "sendSequence": 7,
        }
        with caplog.at_level(logging.ERROR, logger="citry"):
            [item] = _dispatch(c, call)["results"]
        assert item["sendSequence"] == 7
        assert item["error"] == {
            "status": 500,
            "code": "handler_error",
            "message": "The event handler raised an unexpected error.",
        }
        assert any("malformed error result" in record.message for record in caplog.records)

    @pytest.mark.parametrize(
        "replacement",
        [
            [],
            {"ok": False, "error": []},
            {"ok": False, "error": {"status": True, "code": "handler_error", "message": "Bad."}},
            {"ok": False, "error": {"status": 500, "code": "handler_error", "message": ""}},
            {"ok": False, "error": {"status": 499, "code": "future_code", "message": "Future."}},
            {
                "ok": False,
                "error": {"status": 500, "code": "handler_error", "message": "Bad.", "fieldErrors": []},
            },
            {
                "ok": False,
                "error": {"status": 500, "code": "handler_error", "message": "Bad.", "fieldErrors": None},
            },
            {
                "ok": False,
                "extra": object(),
                "error": {"status": 500, "code": "handler_error", "message": "Bad."},
            },
        ],
    )
    def test_other_malformed_error_hook_shapes_are_contained(self, replacement):
        class BrokenReporter(Extension):
            name = "broken_reporter"

            def on_event_error(self, ctx):
                return replacement

        c = _citry(extensions=[BrokenReporter])
        counter = _counter(c)
        call = {"componentClassId": counter.class_id, "handlerName": "crash", "stateToken": _token(counter)}
        [item] = _dispatch(c, call)["results"]
        assert item["error"] == {
            "status": 500,
            "code": "handler_error",
            "message": "The event handler raised an unexpected error.",
        }

    def test_unexpected_csrf_policy_failure_is_a_fixed_403(self, caplog):
        c = _citry()
        counter = _counter(c)

        def broken_csrf(handler):
            raise RuntimeError(handler.name)

        call = {"componentClassId": counter.class_id, "handlerName": "square", "args": {"value": 2}, "sendSequence": 5}
        with caplog.at_level(logging.ERROR, logger="citry"):
            [item] = _dispatch(c, call, csrf_check=broken_csrf)["results"]
        assert item == {
            "ok": False,
            "sendSequence": 5,
            "error": {
                "status": 403,
                "code": "csrf_failed",
                "message": "The call failed the CSRF check; reload the page and try again.",
            },
        }
        assert any("CSRF policy" in record.message for record in caplog.records)

    def test_event_error_from_csrf_policy_preserves_its_message_and_fields(self):
        c = _citry()
        counter = _counter(c)

        def denied(handler):
            raise EventError(f"No access to {handler.name}.", fields={"token": "Expired."}, status=403)

        call = {"componentClassId": counter.class_id, "handlerName": "square", "args": {"value": 2}, "sendSequence": 5}
        [item] = _dispatch(c, call, csrf_check=denied)["results"]
        assert item == {
            "ok": False,
            "sendSequence": 5,
            "error": {
                "status": 403,
                "code": "csrf_failed",
                "message": "No access to square.",
                "fieldErrors": {"token": "Expired."},
            },
        }


class TestInjection:
    def test_request_and_event_injectables(self):
        c = _citry()
        seen = {}

        class Probe(Component):
            citry = c
            template = "<div>i</div>"

            class Events:
                def inspect(self, request, event):
                    seen["request"] = request
                    seen["event"] = event

        request = EventRequest(method="POST", form={"a": "1"}, native="native-object")
        call = {"componentClassId": Probe.class_id, "handlerName": "inspect", "callerRenderId": "i3", "args": {}}
        result = _dispatch(c, call, request=request)
        assert result["results"][0] == {"ok": True, "actions": []}
        assert seen["request"] is request
        assert seen["event"] == CallEvent(name="inspect", instance_id="i3", transport="http", args={})

    def test_ambient_attributes_match_the_injectables(self):
        c = _citry()
        seen = {}

        class Ambient(Component):
            citry = c
            template = "<div>a</div>"

            class Events:
                def go(self):
                    seen["state"] = self.state
                    seen["context"] = self.context
                    seen["event_name"] = self.event.name

        _dispatch(c, {"componentClassId": Ambient.class_id, "handlerName": "go"})
        assert seen == {"state": None, "context": None, "event_name": "go"}


class TestAsyncDispatch:
    def test_sync_dispatch_rejects_an_async_handler(self, caplog):
        c = _citry()

        class Slow(Component):
            citry = c
            template = "<div>s</div>"

            class Events:
                async def fetch(self):
                    return {"n": 1}

        with caplog.at_level(logging.DEBUG, logger="citry"):
            result = _dispatch(c, {"componentClassId": Slow.class_id, "handlerName": "fetch"})
        error = result["results"][0]["error"]
        assert error["code"] == "handler_error"
        assert "dispatch_async" in error["message"]

    def test_dispatch_async_awaits_async_and_offloads_sync(self):
        c = _citry()

        class Mixed(Component):
            citry = c
            template = "<div>m</div>"

            class Events:
                async def afetch(self):
                    await asyncio.sleep(0)
                    return {"kind": "async"}

                def sfetch(self):
                    return {"kind": "sync"}

        async def run():
            dispatcher = EventsDispatcher()
            envelope = _envelope(
                {"componentClassId": Mixed.class_id, "handlerName": "afetch"},
                {"componentClassId": Mixed.class_id, "handlerName": "sfetch"},
            )
            return await dispatcher.dispatch_async(envelope, _ctx(c))

        result = asyncio.run(run())
        values = [item["actions"][0]["value"] for item in result["results"]]
        assert values == [{"kind": "async"}, {"kind": "sync"}]

    def test_on_event_answer_preempts_an_async_handler(self):
        ran = []

        class Answerer(Extension):
            name = "answerer"

            def on_event(self, ctx):
                return {"from": "hook"}

        c = _citry(extensions=[Answerer])

        class AsyncEndpoint(Component):
            citry = c
            template = "<div>a</div>"

            class Events:
                async def run(self):
                    ran.append("handler")
                    return {"from": "handler"}

        async def run():
            envelope = _envelope({"componentClassId": AsyncEndpoint.class_id, "handlerName": "run"})
            return await EventsDispatcher().dispatch_async(envelope, _ctx(c))

        [item] = asyncio.run(run())["results"]
        assert ran == []
        assert item["actions"] == [{"action": "data", "value": {"from": "hook"}}]

    def test_async_event_error_preserves_status_fields_and_epoch(self):
        c = _citry()

        class AsyncEndpoint(Component):
            citry = c
            template = "<div>a</div>"

            class Events:
                async def run(self):
                    await asyncio.sleep(0)
                    raise EventError("Try again later.", fields={"name": "Unavailable."}, status=503)

        async def run():
            envelope = _envelope({"componentClassId": AsyncEndpoint.class_id, "handlerName": "run", "sendSequence": 9})
            return await EventsDispatcher().dispatch_async(envelope, _ctx(c))

        [item] = asyncio.run(run())["results"]
        assert item == {
            "ok": False,
            "sendSequence": 9,
            "error": {
                "status": 503,
                "code": "error",
                "message": "Try again later.",
                "fieldErrors": {"name": "Unavailable."},
            },
        }

    def test_async_unexpected_exception_becomes_handler_error(self):
        c = _citry()

        class AsyncEndpoint(Component):
            citry = c
            template = "<div>a</div>"

            class Events:
                async def run(self):
                    await asyncio.sleep(0)
                    raise RuntimeError("async boom")

        async def run():
            envelope = _envelope({"componentClassId": AsyncEndpoint.class_id, "handlerName": "run", "sendSequence": 3})
            return await EventsDispatcher().dispatch_async(envelope, _ctx(c))

        [item] = asyncio.run(run())["results"]
        assert item["sendSequence"] == 3
        assert item["error"]["code"] == "handler_error"


class TestRouteResponseEscape:
    def _download(self, c):
        class Download(Component):
            citry = c
            template = "<div>d</div>"

            class Events:
                @event(bundle=False)
                def export(self):
                    return RouteResponse(content=b"csv,data", content_type="text/csv")

        return Download

    def test_allowed_on_the_per_event_route(self):
        c = _citry()
        download = self._download(c)
        result = _dispatch(
            c,
            {"args": {}},
            url_component=download.class_id,
            url_event="export",
        )
        assert isinstance(result, RouteResponse)
        assert result.content == b"csv,data"

    def test_rejected_loudly_on_the_batch_endpoint(self, caplog):
        c = _citry()
        download = self._download(c)
        with caplog.at_level(logging.DEBUG, logger="citry"):
            result = _dispatch(c, {"componentClassId": download.class_id, "handlerName": "export"})
        error = result["results"][0]["error"]
        assert error["code"] == "handler_error"
        assert "RouteResponse" in error["message"]
        assert "per-event" in error["message"]

    def test_requires_the_complete_per_event_route_pair(self, caplog):
        c = _citry()
        download = self._download(c)
        with caplog.at_level(logging.DEBUG, logger="citry"):
            result = _dispatch(
                c,
                {"componentClassId": download.class_id, "handlerName": "export", "args": {}},
                url_event="export",
            )
        error = result["results"][0]["error"]
        assert error["code"] == "handler_error"
        assert "RouteResponse" in error["message"]
        assert "per-event" in error["message"]

    def test_rejected_without_bundle_opt_out(self, caplog):
        c = _citry()

        class Export(Component):
            citry = c
            template = "<div>export</div>"

            class Events:
                def run(self):
                    return RouteResponse(content=b"x")

        with caplog.at_level(logging.DEBUG, logger="citry"):
            result = _dispatch(c, {"args": {}}, url_component=Export.class_id, url_event="run")
        error = result["results"][0]["error"]
        assert error["code"] == "handler_error"
        assert "@event(bundle=False)" in error["message"]

    def test_rejected_after_state_mutation(self, caplog):
        c = _citry()

        class ExportState:
            count: int = 0

        class Export(Component):
            citry = c
            template = "<div>export</div>"
            State = ExportState

            class Events:
                @event(bundle=False)
                def run(self, state):
                    state.count += 1
                    return RouteResponse(content=b"x")

        call = {"args": {}, "stateToken": _token(Export)}
        with caplog.at_level(logging.DEBUG, logger="citry"):
            result = _dispatch(c, call, url_component=Export.class_id, url_event="run")
        error = result["results"][0]["error"]
        assert error["code"] == "handler_error"
        assert "must leave State unchanged" in error["message"]

    def test_reading_state_without_mutation_is_allowed(self):
        c = _citry()

        class ExportState:
            count: int = 3

        class Export(Component):
            citry = c
            template = "<div>export</div>"
            State = ExportState

            class Events:
                @event(bundle=False)
                def run(self, state):
                    return RouteResponse(content=f"count={state.count}")

        call = {"args": {}, "stateToken": _token(Export, count=7)}
        result = _dispatch(c, call, url_component=Export.class_id, url_event="run")
        assert isinstance(result, RouteResponse)
        assert result.content == "count=7"

    @pytest.mark.parametrize("result_kind", ["download", "route_response"])
    def test_request_updates_are_rejected_before_a_raw_response(self, result_kind, caplog):
        c = _citry()
        seen = []

        class ExportState:
            count: int = 0

        class Export(Component):
            citry = c
            template = """
                <div>export</div>
            """
            State = ExportState

            class Events:
                @event(bundle=False)
                def run(self, state):
                    seen.append(state.count)
                    if result_kind == "download":
                        return actions.Download(b"x", "report.csv")
                    return RouteResponse(content=b"x")

        call = {"args": {}, "stateToken": _token(Export), "stateUpdates": {"count": 7}}
        with caplog.at_level(logging.DEBUG, logger="citry"):
            result = _dispatch(c, call, url_component=Export.class_id, url_event="run")
        error = result["results"][0]["error"]
        assert seen == [7]
        assert error["code"] == "handler_error"
        assert "must leave State unchanged" in error["message"]


class TestDownloadResponse:
    def _export(self, c):
        class Export(Component):
            citry = c
            template = "<div>export</div>"

            class Events:
                @event(bundle=False)
                def csv(self):
                    return actions.Download("name\nAda", "přehled.csv", "text/csv; charset=utf-8")

                @event(bundle=False)
                async def async_csv(self):
                    await asyncio.sleep(0)
                    return [actions.Download(b"name\nAda", "report.csv", "text/csv")]

        return Export

    def test_download_becomes_an_attachment_response(self):
        c = _citry()
        export = self._export(c)
        result = _dispatch(c, {"args": {}}, url_component=export.class_id, url_event="csv")
        assert isinstance(result, RouteResponse)
        assert result.content == "name\nAda"
        assert result.content_type == "text/csv; charset=utf-8"
        disposition = dict(result.headers)["Content-Disposition"]
        assert disposition == ("attachment; filename=\"prehled.csv\"; filename*=UTF-8''p%C5%99ehled.csv")

    def test_async_download_has_the_same_response_path(self):
        c = _citry()
        export = self._export(c)

        async def run():
            return await EventsDispatcher().dispatch_async(
                _envelope(
                    {
                        "componentClassId": export.class_id,
                        "handlerName": "async_csv",
                        "args": {},
                    }
                ),
                _ctx(c),
                url_component=export.class_id,
                url_event="async_csv",
            )

        result = asyncio.run(run())
        assert isinstance(result, RouteResponse)
        assert result.content == b"name\nAda"

    def test_download_is_rejected_on_non_http_transport(self, caplog):
        c = _citry()
        export = self._export(c)
        ctx = TransportContext(transport="ws", citry=c)
        with caplog.at_level(logging.DEBUG, logger="citry"):
            result = EventsDispatcher().dispatch(
                _envelope({"componentClassId": export.class_id, "handlerName": "csv", "args": {}}),
                ctx,
                url_component=export.class_id,
                url_event="csv",
            )
        error = result["results"][0]["error"]
        assert error["code"] == "handler_error"
        assert "actions.Download" in error["message"]
        assert "non-HTTP" in error["message"]

    def test_download_is_rejected_on_the_batch_endpoint(self, caplog):
        c = _citry()
        export = self._export(c)
        with caplog.at_level(logging.DEBUG, logger="citry"):
            result = _dispatch(c, {"componentClassId": export.class_id, "handlerName": "csv", "args": {}})
        error = result["results"][0]["error"]
        assert error["code"] == "handler_error"
        assert "actions.Download" in error["message"]
        assert "per-event" in error["message"]

    def test_download_requires_bundle_opt_out(self, caplog):
        c = _citry()

        class Export(Component):
            citry = c
            template = "<div>export</div>"

            class Events:
                def csv(self):
                    return actions.Download(b"x", "report.csv")

        with caplog.at_level(logging.DEBUG, logger="citry"):
            result = _dispatch(c, {"args": {}}, url_component=Export.class_id, url_event="csv")
        error = result["results"][0]["error"]
        assert error["code"] == "handler_error"
        assert "actions.Download" in error["message"]
        assert "@event(bundle=False)" in error["message"]

    def test_download_is_rejected_after_state_mutation(self, caplog):
        c = _citry()

        class ExportState:
            count: int = 0

        class Export(Component):
            citry = c
            template = "<div>export</div>"
            State = ExportState

            class Events:
                @event(bundle=False)
                def csv(self, state):
                    state.count += 1
                    return actions.Download(b"x", "report.csv")

        with caplog.at_level(logging.DEBUG, logger="citry"):
            result = _dispatch(
                c,
                {"args": {}, "stateToken": _token(Export)},
                url_component=Export.class_id,
                url_event="csv",
            )
        error = result["results"][0]["error"]
        assert error["code"] == "handler_error"
        assert "actions.Download" in error["message"]
        assert "must leave State unchanged" in error["message"]

    def test_async_dispatch_tracks_a_download_dropped_by_a_sync_handler(self, caplog):
        c = _citry()

        class Export(Component):
            citry = c
            template = "<div>export</div>"

            class Events:
                def csv(self):
                    actions.Download(b"x", "report.csv")

        async def run():
            return await EventsDispatcher().dispatch_async(
                _envelope({"componentClassId": Export.class_id, "handlerName": "csv", "args": {}}),
                _ctx(c),
            )

        with caplog.at_level(logging.DEBUG, logger="citry"):
            result = asyncio.run(run())
        assert result["results"][0]["ok"] is True
        warnings = [record.message for record in caplog.records if record.levelno == logging.WARNING]
        assert any("never returned: Download" in message for message in warnings)


class TestCapabilities:
    def test_runtime_literal_matches_the_protocol_package(self):
        # The runtime constant is a mirror of the protocol package's
        # CAPABILITIES_BASELINE_V1; this is the test-time binding that keeps
        # the protocol package out of the runtime dependency graph.
        spec = Path(__file__).resolve().parents[4] / "packages" / "protocol" / "events" / "v1" / "spec.md"
        text = spec.read_text()
        match = re.search(r"`CAPABILITIES_BASELINE_V1`:\s*```json\s*(\{.*?\})\s*```", text, re.DOTALL)
        assert match is not None, "spec.md no longer defines CAPABILITIES_BASELINE_V1 as a JSON block"
        baseline = json.loads(match.group(1))
        assert {key: list(values) for key, values in CAPABILITIES_BASELINE_V1.items()} == baseline

    def test_action_kind_outside_the_advertised_set_never_ships(self):
        c = _citry()

        class Talker(Component):
            citry = c
            template = "<div>t</div>"

            class Events:
                def speak(self):
                    from citry.ext.events.actions import Dispatch

                    return Dispatch("talker:spoke")

        call = {"componentClassId": Talker.class_id, "handlerName": "speak"}
        result = _dispatch(c, call, envelope_extra={"capabilities": {"actions": ["render", "data"]}})
        # The out-of-set action is refused at encode time, never emitted.
        error = result["results"][0]["error"]
        assert error["code"] == "handler_error"

    def test_capability_shape_errors_reject_the_envelope(self):
        c = _citry()
        counter = _counter(c)
        call = {"componentClassId": counter.class_id, "handlerName": "square", "args": {"value": 2}}
        result = _dispatch(c, call, envelope_extra={"capabilities": {"swaps": "morph"}})
        assert result["results"][0]["error"]["code"] == "protocol_mismatch"

    def test_only_morph_may_downgrade_to_replace(self):
        c = _citry()

        class Badge(Component):
            citry = c
            template = "<span>badge</span>"

        class Renderer(Component):
            citry = c
            template = "<div>r</div>"

            class Events:
                def append(self):
                    return actions.Render(Badge(), target="#target", swap="append")

        call = {"componentClassId": Renderer.class_id, "handlerName": "append"}
        capabilities = {"actions": ["render"], "swaps": ["replace"]}
        [item] = _dispatch(c, call, envelope_extra={"capabilities": capabilities})["results"]
        assert item["error"]["code"] == "handler_error"


class TestDebugHint:
    def test_mutation_with_nothing_visible_logs_the_hint(self, caplog):
        c = _citry()
        counter = _counter(c)

        class Quiet(Component):
            citry = c
            State = counter.State
            template = "<div>q</div>"

            class Events:
                def bump(self, state):
                    state.count += 1

        call = {
            "componentClassId": Quiet.class_id,
            "handlerName": "bump",
            "callerRenderId": "i1",
            "stateToken": _token(Quiet),
        }
        with caplog.at_level(logging.DEBUG, logger="citry"):
            _dispatch(c, call)
        assert any("mutated" in record.message and "nothing visible" in record.message for record in caplog.records)

    def test_no_hint_when_a_render_ships(self, caplog):
        c = _citry()
        counter = _counter(c)
        call = {
            "componentClassId": counter.class_id,
            "handlerName": "increment",
            "callerRenderId": "i1",
            "stateToken": _token(counter),
        }
        with caplog.at_level(logging.DEBUG, logger="citry"):
            _dispatch(c, call)
        assert not any("nothing visible" in record.message for record in caplog.records)

    @pytest.mark.parametrize("result", [actions.PushUrl("?page=2"), actions.Redirect("/next")])
    def test_no_hint_when_navigation_or_history_ships(self, caplog, result):
        c = _citry()
        counter = _counter(c)

        class Moving(Component):
            citry = c
            State = counter.State

            class Events:
                def bump(self, state):
                    state.count += 1
                    return result

            template = """
                <div>moving</div>
            """

        call = {
            "componentClassId": Moving.class_id,
            "handlerName": "bump",
            "callerRenderId": "i1",
            "stateToken": _token(Moving),
        }
        with caplog.at_level(logging.DEBUG, logger="citry"):
            _dispatch(c, call)
        assert not any("nothing visible" in record.message for record in caplog.records)


################################################
# USER-RAISED ERROR CODES AND THE WIRE VOCABULARY
################################################


@functools.cache
def _result_schema_checker():
    """
    The protocol package's result schema plus the package's own checker
    (validate.py), both loaded from packages/protocol/events/v1 itself, so
    these tests move the moment the protocol package does.
    """
    package_root = Path(__file__).resolve().parents[4] / "packages" / "protocol" / "events" / "v1"
    spec = importlib.util.spec_from_file_location("citry_events_protocol_validate", package_root / "validate.py")
    assert spec is not None
    assert spec.loader is not None
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    schema = json.loads((package_root / "result.schema.json").read_text(encoding="utf-8"))
    return checker, schema


def _result_schema_problems(envelope):
    """Problems from validating a result envelope against result.schema.json (empty when it conforms)."""
    checker, schema = _result_schema_checker()
    return checker.schema_errors(envelope, schema)


class TestUserRaisedErrorCodes:
    """
    The wire codes of user-raised EventError statuses, all protocol
    vocabulary (packages/protocol/events/v1, spec.md 4.5): 403 -> forbidden,
    404 -> not_found, 409 -> conflict, 422 -> invalid_args, and the
    catch-all code "error" carrying any other status unchanged. The locked
    test pins the exact wire output; the conformance test validates the live
    envelopes against the protocol package's result schema, so it trips the
    moment either side moves.
    """

    def _failing(self, c):
        class StatusIn:
            status: int

        class Failing(Component):
            citry = c
            template = "<div>f</div>"

            class Events:
                def fail(self, data: StatusIn):
                    raise EventError("The thing is unavailable.", status=data.status)

        return Failing

    @pytest.mark.parametrize(
        ("status", "code"),
        [(404, "not_found"), (409, "conflict"), (418, "error"), (503, "error")],
    )
    def test_locked_wire_mapping(self, status, code):
        c = _citry()
        failing = self._failing(c)
        call = {
            "componentClassId": failing.class_id,
            "handlerName": "fail",
            "args": {"status": status},
            "sendSequence": 4,
        }
        [item] = _dispatch(c, call)["results"]
        assert item["sendSequence"] == 4
        assert item["error"] == {
            "status": status,
            "code": code,
            "message": "The thing is unavailable.",
        }

    @pytest.mark.parametrize("status", [403, 404, 409, 418, 422, 503])
    def test_user_raised_errors_conform_to_the_result_schema(self, status):
        c = _citry()
        failing = self._failing(c)
        call = {"componentClassId": failing.class_id, "handlerName": "fail", "args": {"status": status}}
        envelope = _dispatch(c, call)
        assert envelope["results"][0]["ok"] is False
        assert _result_schema_problems(envelope) == []


################################################
# EPOCH ECHO ON REJECTIONS
################################################


class TestEpochEchoOnRejections:
    """Spec 4.1: a result carries the epoch exactly when its call did, rejections included."""

    def test_structural_rejection_echoes_the_epoch(self):
        c = _citry()
        counter = _counter(c)
        call = {"componentClassId": counter.class_id, "handlerName": "square", "callerRenderId": 5, "sendSequence": 7}
        [item] = _dispatch(c, call)["results"]
        assert item == {
            "ok": False,
            "sendSequence": 7,
            "error": {
                "status": 400,
                "code": "protocol_mismatch",
                "message": "The call's 'callerRenderId' must be a non-empty string.",
            },
        }

    def test_unsafe_instance_id_is_a_protocol_rejection(self):
        c = _citry()
        counter = _counter(c)
        call = {
            "componentClassId": counter.class_id,
            "handlerName": "square",
            "callerRenderId": "MixedCase",
            "sendSequence": 7,
        }
        [item] = _dispatch(c, call)["results"]
        assert item == {
            "ok": False,
            "sendSequence": 7,
            "error": {
                "status": 400,
                "code": "protocol_mismatch",
                "message": (
                    "The call's 'callerRenderId' must use only lowercase ASCII letters, digits, hyphens,"
                    " and underscores."
                ),
            },
        }

    def test_a_malformed_epoch_echoes_nothing(self):
        c = _citry()
        counter = _counter(c)
        call = {
            "componentClassId": counter.class_id,
            "handlerName": "square",
            "args": {"value": 1},
            "sendSequence": True,
        }
        [item] = _dispatch(c, call)["results"]
        assert "sendSequence" not in item
        assert item["error"]["message"] == "The call's 'sendSequence' must be an integer of at least 0."

    def test_envelope_rejection_mirrors_each_calls_epoch(self):
        c = _citry()
        envelope = {
            "protocol": "citry-events/2",
            "requestId": "r9",
            "calls": [
                {"componentClassId": "X", "handlerName": "e", "sendSequence": 3},
                {"componentClassId": "X", "handlerName": "e"},
            ],
        }
        results = EventsDispatcher().dispatch(envelope, _ctx(c))["results"]
        assert results[0]["sendSequence"] == 3
        assert "sendSequence" not in results[1]
        # Both slots still mirror the same envelope-level error.
        assert results[0]["error"] == results[1]["error"]

    def test_calls_cap_rejection_echoes_per_slot(self):
        c = _citry()
        calls = [{"componentClassId": "X", "handlerName": "e", "sendSequence": index} for index in range(17)]
        results = EventsDispatcher().dispatch(_envelope(*calls), _ctx(c))["results"]
        assert [item["sendSequence"] for item in results] == list(range(17))

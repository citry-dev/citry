"""Replay every citry-events/1 golden example through the Python dispatcher."""

import copy
import json
import re
from pathlib import Path
from typing import Any

import jsonschema
import pytest

from citry import Citry, Component
from citry.ext.events import EventError, actions, event
from citry.ext.events.dispatcher import EventsDispatcher, TransportContext
from citry.ext.events.tokens import mint_state_token

SIGNING_KEY = "test-secret-key"
FIXED_NOW = 1_700_000_000.0
_ROOT = Path(__file__).resolve().parents[4]
_PROTOCOL = _ROOT / "packages" / "protocol" / "events" / "v1"
_TESTS = _PROTOCOL / "tests"
_PATH_PART_RE = re.compile(r"\.([A-Za-z0-9_]+)|\[([0-9]+)\]")
_EVENTS_TAG_RE = re.compile(r'<script type="application/json" data-citry-events>(.*?)</script>', re.DOTALL)
_DYNAMIC = "<dynamic>"

INDEX = json.loads((_TESTS / "index.json").read_text(encoding="utf8"))
RESULT_SCHEMA = json.loads((_PROTOCOL / "result.schema.json").read_text(encoding="utf8"))
RESULT_VALIDATOR = jsonschema.validators.validator_for(RESULT_SCHEMA)(RESULT_SCHEMA)


@pytest.fixture(autouse=True)
def _pinned_token_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep live-render and replay tokens deterministic within each example case."""
    monkeypatch.setattr("citry.ext.events.tokens._now", lambda: FIXED_NOW)


def _conformance_surface() -> tuple[Citry, type[Component]]:
    """Build the canonical component from protocol spec section 10."""
    engine = Citry(secret=SIGNING_KEY)
    engine.set_mounted_prefix("/citry")

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
        citry = engine

        class Kwargs:
            count: int = 0
            name: str = "Counter"

        State = CounterState

        class Events:
            def _guard(self):
                if self.event.name == "rename" and self.event.args.get("name") == "admin":
                    raise EventError("The name 'admin' is reserved.", status=403)

            def increment(self, state: CounterState):
                state.count += 1
                return state.render()

            def rename(self, data: RenameIn, state: CounterState):
                state.name = data.name
                return [
                    actions.Dispatch("counter:renamed", {"name": state.name}, delay=1.5, wait=False),
                    {"name": state.name},
                ]

            def crash(self, state: CounterState):
                raise RuntimeError("boom")

            @event(methods=("GET",))
            def square(self, data: SquareIn):
                return actions.Data({"value": data.value * data.value})

            def history(self):
                return [
                    actions.PushUrl("/counters?page=2", delay=0.25, wait=False),
                    actions.ReplaceUrl("/counters?page=3"),
                ]

            def fail(self, data: FailIn):
                raise EventError("The counter cannot do that.", status=data.status)

        def template_data(self, kwargs, slots):
            return {"count": kwargs.count, "name": kwargs.name}

        template = """
      <div>
        <h2>{{ name }}</h2>
        <button @c-click="increment">
          Clicked {{ count }} times
        </button>
      </div>
    """

    return engine, Counter


def _render_live_instance(comp_cls: type[Component]) -> tuple[str, str, str, dict[str, Any]]:
    """Read the named instance values actually emitted by a fresh render."""
    match = _EVENTS_TAG_RE.search(str(comp_cls()))
    assert match is not None, "The conformance component emitted no Events manifest"
    manifest = json.loads(match.group(1))
    assert manifest["protocol"] == "citry-events/1"
    [instance] = manifest["componentInstances"]
    return (
        instance["renderId"],
        instance["componentClassId"],
        instance["stateToken"],
        instance["publicState"],
    )


def _path_parts(path: str) -> list[str | int]:
    """Parse the protocol package's deliberately small dynamic-field grammar."""
    parts: list[str | int] = []
    offset = 0
    for match in _PATH_PART_RE.finditer("." + path):
        if match.start() != offset:
            msg = f"Invalid dynamic field {path!r}"
            raise AssertionError(msg)
        key, index = match.groups()
        parts.append(key if key is not None else int(index))
        offset = match.end()
    if offset != len(path) + 1:
        msg = f"Invalid dynamic field {path!r}"
        raise AssertionError(msg)
    return parts


def _resolve(document: Any, path: str) -> Any:
    """Read one declared path, failing loudly if the live result omitted it."""
    current = document
    for part in _path_parts(path):
        current = current[part]
    return current


def _replace(document: Any, path: str, value: Any) -> None:
    """Replace one declared path in an example or a comparison copy."""
    parts = _path_parts(path)
    current = document
    for part in parts[:-1]:
        current = current[part]
    current[parts[-1]] = value


def _strict_json_equal(left: Any, right: Any) -> bool:
    """Compare JSON structures without Python's ``True == 1`` equivalence."""
    options = {"sort_keys": True, "separators": (",", ":"), "ensure_ascii": False, "allow_nan": False}
    return json.dumps(left, **options) == json.dumps(right, **options)


def _load(entry: dict[str, Any], key: str) -> dict[str, Any]:
    return json.loads((_TESTS / entry[key]).read_text(encoding="utf8"))


def _arrange_call(
    entry: dict[str, Any], call: dict[str, Any], *, comp_cls: type, instance_id: str, class_id: str, token: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Substitute live call values and return dispatcher keyword arrangements."""
    fixture_name = entry["call"].removesuffix(".call.json")
    if fixture_name == "error_stale_state":
        token = mint_state_token(
            comp_cls.State(),
            class_id=class_id,
            secret="rotated-out-test-secret",  # noqa: S106 - deliberate removed test key
            max_age=None,
            max_bytes=8192,
        )

    live_values = {"componentClassId": class_id, "callerRenderId": instance_id, "stateToken": token}
    for dynamic_field in entry["dynamic_fields"]:
        document, _, path = dynamic_field.partition(".")
        if document != "call":
            continue
        leaf = _path_parts(path)[-1]
        if leaf not in live_values:
            msg = f"No live substitution is defined for {dynamic_field!r}"
            raise AssertionError(msg)
        _replace(call, path, live_values[leaf])

    dispatch_kwargs: dict[str, Any] = {}
    if fixture_name == "error_csrf_failed":

        def reject_csrf(_handler: Any) -> None:
            raise EventError("The call failed the CSRF check; reload the page and try again.", status=403)

        dispatch_kwargs["csrf_check"] = reject_csrf
    return call, dispatch_kwargs


def _mask_dynamic_results(entry: dict[str, Any], expected: dict[str, Any], actual: dict[str, Any]) -> None:
    """Require each dynamic result value to exist, then mask it on both sides."""
    for dynamic_field in entry["dynamic_fields"]:
        document, _, path = dynamic_field.partition(".")
        if document != "result":
            continue
        _resolve(expected, path)
        _resolve(actual, path)
        _replace(expected, path, _DYNAMIC)
        _replace(actual, path, _DYNAMIC)


@pytest.mark.parametrize("entry", INDEX, ids=[entry["call"].removesuffix(".call.json") for entry in INDEX])
def test_python_dispatcher_replays_protocol_fixture(entry: dict[str, Any]) -> None:
    """One fresh serializer-to-dispatcher round trip must reproduce each golden result."""
    citry, counter = _conformance_surface()
    instance_id, class_id, token, values = _render_live_instance(counter)
    assert class_id == counter.class_id
    assert values == {"count": 0, "name": "Counter"}

    call, dispatch_kwargs = _arrange_call(
        entry,
        _load(entry, "call"),
        comp_cls=counter,
        instance_id=instance_id,
        class_id=class_id,
        token=token,
    )
    result = EventsDispatcher().dispatch(
        call,
        TransportContext(transport="conformance", citry=citry),
        **dispatch_kwargs,
    )
    assert isinstance(result, dict), "The conformance component never uses the raw-response escape hatch"

    schema_errors = sorted(error.message for error in RESULT_VALIDATOR.iter_errors(result))
    assert schema_errors == [], f"{entry['result']} failed result.schema.json: {schema_errors}"

    expected = _load(entry, "result")
    comparable_result = copy.deepcopy(result)
    _mask_dynamic_results(entry, expected, comparable_result)
    assert _strict_json_equal(comparable_result, expected), entry["result"]
